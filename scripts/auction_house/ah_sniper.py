"""
Script: AH Sniper
Purpose: Repeatedly search the Auction House for a target item and instantly
         buy it if the BIN price is at or below your configured max price.
         Uses OCR (pytesseract) to read the price from the item lore tooltip.
Author: Claude
Version: 1.0

Requirements:
  pip install pytesseract pillow
  Install Tesseract binary: https://github.com/UB-Mannheim/tesseract/wiki

Setup:
  1. Be near an Auction House NPC or have /ah access.
  2. Set target_item to the exact item name as shown in the AH search bar.
  3. Set max_price to your maximum buy price in coins.
  4. Calibrate:
     - lore_region: the screen area where item lore (tooltip) appears when
       hovering the first AH result slot.
     - confirm_button_x/y: center of the "Confirm Purchase" button.
     - first_result_x/y: center of the first item slot in AH search results.
"""

import sys
import os
import time
import random
import re

import pyautogui

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_utils import human_key, human_type, random_sleep
from screen_utils import screenshot
from config_utils import load_config

try:
    import pytesseract
    from PIL import Image
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("[AHSniper] WARNING: pytesseract not installed. Price reading disabled.")
    print("  Run: pip install pytesseract  and install the Tesseract binary.")

DEFAULTS = {
    "start_delay": 5,

    # Exact item name to search (must match AH search results)
    "target_item": "Mithril Ore",
    # Maximum price you are willing to pay (coins)
    "max_price": 50000,

    # Screen coordinate of the AH search bar (click here to type)
    "search_bar_x": 960,
    "search_bar_y": 300,

    # Screen coordinate of the first result slot in the AH GUI
    "first_result_x": 350,
    "first_result_y": 350,

    # Region where item lore tooltip appears when hovering first result
    # [left, top, width, height]
    "lore_region": [100, 200, 400, 400],

    # Screen coordinate of "Confirm Purchase" button
    "confirm_button_x": 960,
    "confirm_button_y": 540,

    # Screen coordinate of the close/X button for the AH GUI
    "close_button_x": 1160,
    "close_button_y": 230,

    # Seconds between search attempts
    "search_interval_min": 1.5,
    "search_interval_max": 3.0,

    # Stop after buying this many items (0 = unlimited)
    "max_purchases": 0,
}

CONFIG = load_config("ah_sniper", DEFAULTS)
running = True
purchases = 0


def _open_ah():
    """Open the AH search by pressing T (chat) and typing /ah <item>."""
    pyautogui.press("t")
    random_sleep(0.3, 0.5)
    pyautogui.hotkey("ctrl", "a")
    command = f"/ah {CONFIG['target_item']}"
    human_type(command)
    pyautogui.press("enter")
    random_sleep(1.0, 1.5)


def _read_price_from_lore() -> int | None:
    """
    Screenshot the lore region and use OCR to extract the BIN price.
    Looks for patterns like '500,000 coins' or 'Buy It Now: 500,000'.
    Returns the price as an integer, or None if not parseable.
    """
    if not OCR_AVAILABLE:
        return None

    x, y, w, h = CONFIG["lore_region"]
    img_array = screenshot((x, y, x + w, y + h))
    # Convert BGR to RGB for PIL
    img_rgb = img_array[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)

    # Upscale for better OCR accuracy on small Minecraft font
    scale = 3
    pil_img = pil_img.resize(
        (pil_img.width * scale, pil_img.height * scale),
        Image.NEAREST,
    )

    text = pytesseract.image_to_string(pil_img, config="--psm 6")

    # Look for coin amounts: "123,456 Coins" or "Buy It Now: 123,456"
    matches = re.findall(r"[\d,]+(?=\s*[Cc]oins?)", text)
    if not matches:
        # Fallback: any large number in the text
        matches = re.findall(r"\d[\d,]{2,}", text)

    for match in matches:
        try:
            price = int(match.replace(",", ""))
            if price > 0:
                return price
        except ValueError:
            continue
    return None


def _hover_first_result():
    """Move mouse to the first result slot to trigger lore tooltip."""
    pyautogui.moveTo(
        CONFIG["first_result_x"] + random.randint(-3, 3),
        CONFIG["first_result_y"] + random.randint(-3, 3),
    )
    random_sleep(0.3, 0.5)


def _attempt_snipe() -> bool:
    """
    Open AH, hover first result, read price, buy if under max_price.
    Returns True if a purchase was made.
    """
    global purchases
    _open_ah()
    _hover_first_result()

    price = _read_price_from_lore()
    if price is None:
        print("[AHSniper] Could not read price — closing.")
        pyautogui.press("escape")
        return False

    print(f"[AHSniper] '{CONFIG['target_item']}' — price: {price:,} coins (max: {CONFIG['max_price']:,})")

    if price <= CONFIG["max_price"]:
        print(f"[AHSniper] BUYING at {price:,}!")
        pyautogui.click(
            CONFIG["first_result_x"] + random.randint(-3, 3),
            CONFIG["first_result_y"] + random.randint(-3, 3),
        )
        random_sleep(0.4, 0.7)
        # Click "Confirm Purchase"
        pyautogui.click(
            CONFIG["confirm_button_x"] + random.randint(-5, 5),
            CONFIG["confirm_button_y"] + random.randint(-5, 5),
        )
        random_sleep(0.5, 0.8)
        purchases += 1
        print(f"[AHSniper] Purchase #{purchases} complete!")
        return True
    else:
        pyautogui.press("escape")
        return False


def main():
    global running
    if not OCR_AVAILABLE:
        print("[AHSniper] Cannot run without pytesseract. See setup instructions.")
        return

    print(f"[AHSniper] Sniping '{CONFIG['target_item']}' under {CONFIG['max_price']:,} coins")
    print(f"[AHSniper] Starting in {CONFIG['start_delay']}s — switch to Minecraft!")
    time.sleep(CONFIG["start_delay"])

    try:
        while running:
            _attempt_snipe()

            max_p = CONFIG["max_purchases"]
            if max_p > 0 and purchases >= max_p:
                print(f"[AHSniper] Reached max purchases ({max_p}) — stopping.")
                break

            interval = random.uniform(
                CONFIG["search_interval_min"],
                CONFIG["search_interval_max"],
            )
            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"[AHSniper] Stopped. Purchases this session: {purchases}")
        running = False


if __name__ == "__main__":
    main()
