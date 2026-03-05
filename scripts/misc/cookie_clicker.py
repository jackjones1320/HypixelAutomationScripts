"""
Script: Cookie Clicker (Booster Cookie Manager)
Purpose: Monitor the on-screen buff bar for the Booster Cookie icon.
         When the buff disappears (expired), auto-open inventory, find a
         Booster Cookie, and right-click to consume it — keeping the buff
         active indefinitely.
Author: Claude
Version: 1.0

Setup:
  1. Apply a Booster Cookie manually first to get the buff icon on screen.
  2. Set cookie_icon_x/y to a pixel INSIDE the Booster Cookie buff icon.
  3. Set cookie_icon_color to that pixel's RGB when the buff is active.
  4. Set cookie_scan_region to the area of your inventory where cookies are stored.
  5. Keep Booster Cookies in your inventory (not just the hotbar).

Cookie duration: 4 real-time days.  The script polls every poll_interval seconds.
"""

import sys
import os
import time
import random

import pyautogui

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_utils import random_sleep
from screen_utils import pixel_matches, get_pixel_color
from config_utils import load_config

DEFAULTS = {
    "start_delay": 5,

    # A pixel inside the Booster Cookie buff icon (bottom-right buff bar, vanilla 1080p)
    "cookie_icon_x": 1820,
    "cookie_icon_y": 920,
    # RGB of that pixel when the buff is active (golden/yellow cookie icon)
    "cookie_icon_color": [210, 160, 50],
    "cookie_icon_tolerance": 30,

    # How often (seconds) to check whether the buff is still active.
    # Cookie lasts 4 days = 345,600s; polling every 300s is fine.
    "poll_interval": 300,

    # Inventory scan region [left, top, width, height] to find the cookie item.
    # Vanilla 1080p main inventory: roughly [623, 278, 390, 170]
    "cookie_scan_region": [623, 278, 390, 170],
    "slot_size": 18,
    # Minimum R+G+B sum to consider a slot non-empty
    "item_brightness_min": 150,

    # After consuming, wait this many seconds before resuming polling
    # (gives the buff icon time to appear on screen)
    "post_consume_wait": 5,
}

CONFIG = load_config("cookie_clicker", DEFAULTS)
running = True
cookies_consumed = 0


def _buff_active() -> bool:
    """Check whether the Booster Cookie buff icon is visible."""
    return pixel_matches(
        CONFIG["cookie_icon_x"],
        CONFIG["cookie_icon_y"],
        tuple(CONFIG["cookie_icon_color"]),
        CONFIG["cookie_icon_tolerance"],
    )


def _consume_cookie() -> bool:
    """
    Open inventory, scan for any item in the cookie scan region,
    right-click the first one found (assumes it's a Booster Cookie),
    then close inventory.
    Returns True if an item was found and clicked.
    """
    global cookies_consumed
    print("[Cookie] Buff expired — opening inventory to consume cookie...")

    pyautogui.press("e")
    random_sleep(0.5, 0.8)

    bx, by, bw, bh = CONFIG["cookie_scan_region"]
    step = CONFIG["slot_size"]
    brightness_min = CONFIG["item_brightness_min"]

    from screen_utils import screenshot
    img = screenshot((bx, by, bx + bw, by + bh))
    found = False

    for ri in range(0, min(bh, img.shape[0]), step):
        for ci in range(0, min(bw, img.shape[1]), step):
            b, g, r = int(img[ri][ci][0]), int(img[ri][ci][1]), int(img[ri][ci][2])
            if r + g + b >= brightness_min:
                cx = bx + ci + step // 2
                cy = by + ri + step // 2
                pyautogui.rightClick(cx, cy)
                random_sleep(0.3, 0.5)
                found = True
                break
        if found:
            break

    pyautogui.press("e")
    random_sleep(0.4, 0.7)

    if found:
        cookies_consumed += 1
        print(f"[Cookie] Cookie consumed (total: {cookies_consumed}). Waiting for buff to appear...")
        time.sleep(CONFIG["post_consume_wait"])
        if _buff_active():
            print("[Cookie] Buff confirmed active.")
        else:
            print("[Cookie] WARNING: Buff not detected after consuming — check cookie_icon_x/y.")
    else:
        print("[Cookie] No cookie found in inventory! Please restock.")

    return found


def main():
    global running
    print(f"[Cookie] Starting in {CONFIG['start_delay']}s — switch to Minecraft!")
    time.sleep(CONFIG["start_delay"])

    # Initial calibration check
    if _buff_active():
        print("[Cookie] Buff is currently active. Monitoring...")
    else:
        print("[Cookie] Buff not detected at startup — consuming cookie immediately.")
        _consume_cookie()

    try:
        while running:
            time.sleep(CONFIG["poll_interval"] + random.uniform(-15, 15))

            if not _buff_active():
                print("[Cookie] Buff expired!")
                _consume_cookie()
            else:
                print(f"[Cookie] Buff active. Next check in ~{CONFIG['poll_interval']}s.")

    except KeyboardInterrupt:
        print(f"[Cookie] Stopped. Cookies consumed this session: {cookies_consumed}")
        running = False


if __name__ == "__main__":
    main()
