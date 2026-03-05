"""
Script: AH Relist
Purpose: Periodically open your Auction House listings, collect coins from
         expired auctions, and relist configured items at set prices.
         Saves time when actively flipping items on the AH.
Author: Claude
Version: 1.0

Setup:
  1. Be near an Auction House NPC.
  2. Edit the "listings" array in configs/ah_relist.json with your items:
       [{"name": "Recombobulator 3000", "price": 4500000, "duration_hours": 12}]
  3. Calibrate all pixel coordinates by opening the AH GUI and using
     get_pixel_color() from screen_utils to identify button locations.

Workflow:
  Open AH → "Manage Auctions" → collect expired → close
  For each item: find in inventory → list on AH at configured price → close
"""

import sys
import os
import time
import random

import pyautogui

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_utils import human_type, random_sleep
from screen_utils import screenshot, pixel_matches
from config_utils import load_config

DEFAULTS = {
    "start_delay": 5,

    # How often to run the relist cycle (seconds)
    "check_interval": 300,

    # AH GUI coordinates — vanilla 1080p defaults, calibrate to your setup
    "manage_auctions_x": 700,   # "Manage Auctions" button in AH main menu
    "manage_auctions_y": 350,

    # "Collect All" button in the manage auctions GUI
    "collect_all_x": 960,
    "collect_all_y": 600,

    # Pixel that turns green/yellow when there are expired items to collect
    "expired_indicator_x": 690,
    "expired_indicator_y": 340,
    "expired_color": [255, 170, 0],
    "expired_tolerance": 40,

    # Create new listing: item slot in inventory, price input field, confirm button
    "inventory_scan_region": [623, 380, 390, 90],  # hotbar area
    "slot_size": 18,
    "price_input_x": 960,
    "price_input_y": 450,
    "confirm_list_x": 960,
    "confirm_list_y": 530,

    # Duration option slot in the listing GUI (1h / 2d / 7d options)
    # Slot positions for 12h, 2d, 7d — click the one matching listing duration
    "duration_12h_x": 850,
    "duration_12h_y": 390,
    "duration_2d_x": 960,
    "duration_2d_y": 390,
    "duration_7d_x": 1070,
    "duration_7d_y": 390,

    # Items to relist: list of {name, price, duration_hours}
    # duration_hours: 12, 48 (2d), or 168 (7d)
    "listings": [],
}

CONFIG = load_config("ah_relist", DEFAULTS)
running = True
relists = 0


def _open_ah():
    pyautogui.press("t")
    random_sleep(0.3, 0.5)
    human_type("/ah")
    pyautogui.press("enter")
    random_sleep(1.2, 1.8)


def _has_expired() -> bool:
    """Check if the expired indicator pixel is lit up."""
    return pixel_matches(
        CONFIG["expired_indicator_x"],
        CONFIG["expired_indicator_y"],
        tuple(CONFIG["expired_color"]),
        CONFIG["expired_tolerance"],
    )


def _collect_expired():
    """Navigate to Manage Auctions and collect all expired listings."""
    print("[AHRelist] Opening Manage Auctions...")
    pyautogui.click(
        CONFIG["manage_auctions_x"] + random.randint(-3, 3),
        CONFIG["manage_auctions_y"] + random.randint(-3, 3),
    )
    random_sleep(0.6, 1.0)

    if _has_expired():
        print("[AHRelist] Collecting expired auctions...")
        pyautogui.click(
            CONFIG["collect_all_x"] + random.randint(-4, 4),
            CONFIG["collect_all_y"] + random.randint(-4, 4),
        )
        random_sleep(0.5, 0.9)
    else:
        print("[AHRelist] No expired auctions to collect.")

    pyautogui.press("escape")
    random_sleep(0.4, 0.7)


def _find_item_in_inventory(item_name: str):
    """
    Scan the hotbar / inventory region for a non-empty slot.
    Returns (cx, cy) of the first occupied slot, or None.
    Note: Full item name matching requires OCR; this returns the first
    available slot as a best-effort approach for simple relisting workflows.
    """
    bx, by, bw, bh = CONFIG["inventory_scan_region"]
    step = CONFIG["slot_size"]

    img = screenshot((bx, by, bx + bw, by + bh))
    for ri in range(0, min(bh, img.shape[0]), step):
        for ci in range(0, min(bw, img.shape[1]), step):
            b, g, r = int(img[ri][ci][0]), int(img[ri][ci][1]), int(img[ri][ci][2])
            if r + g + b > 150:
                return (bx + ci + step // 2, by + ri + step // 2)
    return None


def _select_duration(duration_hours: int):
    """Click the matching duration button in the listing GUI."""
    if duration_hours <= 12:
        target = (CONFIG["duration_12h_x"], CONFIG["duration_12h_y"])
    elif duration_hours <= 48:
        target = (CONFIG["duration_2d_x"], CONFIG["duration_2d_y"])
    else:
        target = (CONFIG["duration_7d_x"], CONFIG["duration_7d_y"])
    pyautogui.click(target[0] + random.randint(-3, 3), target[1] + random.randint(-3, 3))
    random_sleep(0.3, 0.5)


def _relist_item(listing: dict):
    """Create one new AH listing for the given item config."""
    global relists
    name = listing.get("name", "?")
    price = listing.get("price", 0)
    duration = listing.get("duration_hours", 48)

    print(f"[AHRelist] Listing '{name}' for {price:,} coins ({duration}h)")

    slot = _find_item_in_inventory(name)
    if not slot:
        print(f"[AHRelist] '{name}' not found in inventory — skipping.")
        return

    # Click item slot to start listing
    pyautogui.click(slot[0], slot[1])
    random_sleep(0.5, 0.8)

    # Select duration
    _select_duration(duration)

    # Enter price
    pyautogui.click(
        CONFIG["price_input_x"] + random.randint(-3, 3),
        CONFIG["price_input_y"] + random.randint(-3, 3),
    )
    random_sleep(0.2, 0.4)
    pyautogui.hotkey("ctrl", "a")
    human_type(str(price))
    random_sleep(0.2, 0.3)

    # Confirm listing
    pyautogui.click(
        CONFIG["confirm_list_x"] + random.randint(-4, 4),
        CONFIG["confirm_list_y"] + random.randint(-4, 4),
    )
    random_sleep(0.5, 0.9)
    relists += 1
    print(f"[AHRelist] Listed! Total relists this session: {relists}")


def _run_cycle():
    """One full collect + relist cycle."""
    _open_ah()
    _collect_expired()

    listings = CONFIG.get("listings", [])
    if not listings:
        print("[AHRelist] No listings configured — add items to configs/ah_relist.json")
    for listing in listings:
        _open_ah()
        _relist_item(listing)
        pyautogui.press("escape")
        random_sleep(0.8, 1.4)


def main():
    global running
    if not CONFIG.get("listings"):
        print("[AHRelist] WARNING: No listings configured.")
        print("  Edit configs/ah_relist.json and add items to the 'listings' array.")

    print(f"[AHRelist] Starting in {CONFIG['start_delay']}s — switch to Minecraft!")
    time.sleep(CONFIG["start_delay"])

    try:
        while running:
            _run_cycle()
            interval = CONFIG["check_interval"] + random.uniform(-20, 20)
            print(f"[AHRelist] Cycle done. Next check in {interval:.0f}s.")
            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"[AHRelist] Stopped. Total relists: {relists}")
        running = False


if __name__ == "__main__":
    main()
