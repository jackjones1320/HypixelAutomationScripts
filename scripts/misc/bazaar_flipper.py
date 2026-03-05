"""
Script: Bazaar Flipper
Purpose: Watch configured Bazaar items for a profitable buy-order / sell-order
         spread and alert (or optionally auto-place orders) when the margin
         exceeds your configured threshold.
Author: Claude
Version: 1.0

Requirements:
  pip install pytesseract pillow
  Install Tesseract binary: https://github.com/UB-Mannheim/tesseract/wiki

Setup:
  1. Add items to watch in configs/bazaar_flipper.json under "items":
       [{"name": "Enchanted Sugar", "min_margin_pct": 3.0}]
  2. Calibrate search_bar_x/y, buy_price_region, sell_price_region to match
     where prices appear on screen inside the Bazaar item GUI.
  3. Set auto_order: true to automatically place buy/sell orders when
     a margin is found (requires order_quantity to be set).

Margin calculation:
  margin_pct = (sell_price - buy_price) / buy_price * 100
  If margin_pct >= min_margin_pct → alert or auto-order.
"""

import sys
import os
import time
import random
import re

import pyautogui

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_utils import human_type, random_sleep
from screen_utils import screenshot
from config_utils import load_config

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("[BazaarFlipper] WARNING: pytesseract not installed. Run: pip install pytesseract")

DEFAULTS = {
    "start_delay": 5,

    # Items to monitor — list of {name, min_margin_pct}
    "items": [],

    # How often to complete a full scan of all items (seconds)
    "scan_interval": 60,

    # Bazaar GUI coordinates (vanilla 1080p, calibrate to your window)
    "search_bar_x": 960,
    "search_bar_y": 200,

    # Region where the "Top Buy Order" price appears [left, top, width, height]
    "buy_price_region": [750, 300, 300, 40],
    # Region where the "Top Sell Offer" price appears
    "sell_price_region": [750, 350, 300, 40],

    # Auto-order settings (set auto_order: true to enable)
    "auto_order": False,
    "order_quantity": 1,
    "buy_order_button_x": 750,
    "buy_order_button_y": 500,
    "sell_order_button_x": 1050,
    "sell_order_button_y": 500,
    "quantity_input_x": 960,
    "quantity_input_y": 450,
    "confirm_order_x": 960,
    "confirm_order_y": 530,

    # Anti-detection
    "idle_jitter_min": 5,
    "idle_jitter_max": 20,
}

CONFIG = load_config("bazaar_flipper", DEFAULTS)
running = True
alerts = 0
orders_placed = 0


def _open_bazaar():
    pyautogui.press("t")
    random_sleep(0.3, 0.5)
    human_type("/bz")
    pyautogui.press("enter")
    random_sleep(1.2, 1.8)


def _search_item(name: str):
    """Click the Bazaar search bar and type the item name."""
    pyautogui.click(
        CONFIG["search_bar_x"] + random.randint(-3, 3),
        CONFIG["search_bar_y"] + random.randint(-3, 3),
    )
    random_sleep(0.3, 0.5)
    pyautogui.hotkey("ctrl", "a")
    human_type(name)
    random_sleep(0.4, 0.7)
    # Click first result (assumes it appeared below the search bar)
    pyautogui.press("enter")
    random_sleep(0.6, 1.0)


def _read_price(region: list) -> float | None:
    """
    OCR a region and extract the first valid coin price found.
    Returns float price or None.
    """
    if not OCR_AVAILABLE:
        return None

    x, y, w, h = region
    img_array = screenshot((x, y, x + w, y + h))
    img_rgb = img_array[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)
    # Upscale for Minecraft's small font
    pil_img = pil_img.resize(
        (pil_img.width * 3, pil_img.height * 3),
        Image.NEAREST,
    )

    text = pytesseract.image_to_string(pil_img, config="--psm 7 digits")
    numbers = re.findall(r"[\d,]+\.\d+|[\d,]+", text)
    for n in numbers:
        try:
            val = float(n.replace(",", ""))
            if val > 0:
                return val
        except ValueError:
            continue
    return None


def _place_buy_order(quantity: int):
    pyautogui.click(
        CONFIG["buy_order_button_x"] + random.randint(-4, 4),
        CONFIG["buy_order_button_y"] + random.randint(-4, 4),
    )
    random_sleep(0.5, 0.8)
    pyautogui.click(CONFIG["quantity_input_x"], CONFIG["quantity_input_y"])
    pyautogui.hotkey("ctrl", "a")
    human_type(str(quantity))
    random_sleep(0.2, 0.4)
    pyautogui.click(CONFIG["confirm_order_x"], CONFIG["confirm_order_y"])
    random_sleep(0.5, 0.9)


def _check_item(item: dict) -> dict | None:
    """
    Open Bazaar, search for item, read buy/sell prices, compute margin.
    Returns a result dict if margin exceeds threshold, else None.
    """
    name = item.get("name", "")
    min_margin = item.get("min_margin_pct", 3.0)

    _open_bazaar()
    _search_item(name)

    buy_price  = _read_price(CONFIG["buy_price_region"])
    sell_price = _read_price(CONFIG["sell_price_region"])

    pyautogui.press("escape")
    random_sleep(0.4, 0.7)

    if buy_price is None or sell_price is None:
        print(f"[Bazaar] '{name}': could not read prices (OCR failed)")
        return None

    if buy_price <= 0:
        return None

    margin_pct = (sell_price - buy_price) / buy_price * 100
    print(f"[Bazaar] '{name}' — buy: {buy_price:,.1f}  sell: {sell_price:,.1f}  margin: {margin_pct:.2f}%")

    if margin_pct >= min_margin:
        return {
            "name":       name,
            "buy_price":  buy_price,
            "sell_price": sell_price,
            "margin_pct": margin_pct,
        }
    return None


def _handle_opportunity(result: dict):
    """Alert the user and optionally place an automatic buy order."""
    global alerts, orders_placed
    alerts += 1
    print(
        f"\n[Bazaar] *** FLIP OPPORTUNITY #{alerts} ***\n"
        f"  Item:   {result['name']}\n"
        f"  Buy at: {result['buy_price']:,.1f}\n"
        f"  Sell:   {result['sell_price']:,.1f}\n"
        f"  Margin: {result['margin_pct']:.2f}%\n"
    )

    if CONFIG.get("auto_order"):
        print(f"[Bazaar] Placing buy order x{CONFIG['order_quantity']}...")
        _open_bazaar()
        _search_item(result["name"])
        _place_buy_order(CONFIG["order_quantity"])
        orders_placed += 1
        print(f"[Bazaar] Order placed (total: {orders_placed})")
        pyautogui.press("escape")


def main():
    global running
    if not OCR_AVAILABLE:
        print("[BazaarFlipper] Cannot run without pytesseract. See setup instructions.")
        return

    items = CONFIG.get("items", [])
    if not items:
        print("[BazaarFlipper] No items configured.")
        print("  Edit configs/bazaar_flipper.json and add items to the 'items' array.")
        return

    print(f"[BazaarFlipper] Watching {len(items)} item(s). Starting in {CONFIG['start_delay']}s...")
    time.sleep(CONFIG["start_delay"])

    try:
        while running:
            for item in items:
                if not running:
                    break
                result = _check_item(item)
                if result:
                    _handle_opportunity(result)
                # Jitter between item checks
                time.sleep(random.uniform(CONFIG["idle_jitter_min"], CONFIG["idle_jitter_max"]))

            interval = CONFIG["scan_interval"] + random.uniform(-10, 10)
            print(f"[BazaarFlipper] Scan complete. Next in {interval:.0f}s.")
            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"[BazaarFlipper] Stopped. Alerts: {alerts}, Orders placed: {orders_placed}")
        running = False


if __name__ == "__main__":
    main()
