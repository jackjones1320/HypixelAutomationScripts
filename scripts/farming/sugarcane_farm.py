"""
Script: Sugarcane Farm
Purpose: Walk a sugarcane farm row, break all cane, wait for regrowth detected
         via pixel color, then repeat.  Leaves the bottom block intact so
         cane re-grows without replanting.
Author: Claude
Version: 1.0

Setup:
  1. Stand at one end of your sugarcane row, facing along the row.
  2. Equip your farming tool (or fist) in slot 1.
  3. Set regrowth_pixel_x/y to a screen coordinate that shows the TOP of a
     sugarcane stalk when fully grown (green pixel).  When the cane is broken
     that pixel turns to the background color (water/dirt).
  4. Adjust row_walk_time and turn_pixels to match your farm.
"""

import sys
import os
import time
import random

import pyautogui

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_utils import human_key, random_sleep, camera_turn
from screen_utils import pixel_matches
from config_utils import load_config

DEFAULTS = {
    "tool_slot": "1",
    "start_delay": 5,

    # Seconds to hold W while swinging to traverse the farm row
    "row_walk_time": 5.0,
    "turn_pixels": 1200,

    # A pixel that shows GREEN when sugarcane is fully grown (height 3).
    # Set to a point on screen that will be green when cane is tall.
    "regrowth_pixel_x": 960,
    "regrowth_pixel_y": 400,
    # RGB of grown sugarcane (green stalk)
    "regrowth_color": [106, 127, 68],
    "regrowth_tolerance": 30,

    # How often to poll the regrowth pixel (seconds)
    "poll_interval": 3.0,
    # Maximum time to wait for regrowth before swinging anyway
    "regrowth_timeout": 180,

    # Anti-detection
    "idle_break_chance": 0.06,
    "idle_break_min": 8,
    "idle_break_max": 35,
}

CONFIG = load_config("sugarcane_farm", DEFAULTS)
running = True


def _walk_and_swing(duration: float):
    pyautogui.keyDown("w")
    pyautogui.mouseDown(button="left")
    time.sleep(duration + random.uniform(-0.2, 0.3))
    pyautogui.mouseUp(button="left")
    pyautogui.keyUp("w")


def _turn_180():
    half = CONFIG["turn_pixels"] // 2
    camera_turn(half + random.randint(-8, 8))
    time.sleep(random.uniform(0.05, 0.10))
    camera_turn(CONFIG["turn_pixels"] - half + random.randint(-8, 8))
    random_sleep(0.2, 0.4)


def _wait_for_regrowth() -> bool:
    """
    Poll regrowth_pixel until it matches the sugarcane green color.
    Returns True when cane is ready, False on timeout.
    """
    px = CONFIG["regrowth_pixel_x"]
    py = CONFIG["regrowth_pixel_y"]
    color = tuple(CONFIG["regrowth_color"])
    tol = CONFIG["regrowth_tolerance"]
    timeout = CONFIG["regrowth_timeout"]
    poll = CONFIG["poll_interval"]

    start = time.time()
    while time.time() - start < timeout:
        if pixel_matches(px, py, color, tolerance=tol):
            return True
        time.sleep(poll + random.uniform(-0.5, 0.5))
    return False


def harvest_pass(pass_num: int):
    """Walk the row there-and-back, breaking sugarcane the whole way."""
    print(f"[SugarcaneFarm] Harvest #{pass_num} — forward")
    _walk_and_swing(CONFIG["row_walk_time"])
    random_sleep(0.3, 0.5)

    _turn_180()

    print(f"[SugarcaneFarm] Harvest #{pass_num} — back")
    _walk_and_swing(CONFIG["row_walk_time"])
    random_sleep(0.3, 0.5)

    _turn_180()


def main():
    global running
    print(f"[SugarcaneFarm] Starting in {CONFIG['start_delay']}s — switch to Minecraft!")
    time.sleep(CONFIG["start_delay"])

    human_key(CONFIG["tool_slot"])
    random_sleep(0.3, 0.6)

    pass_num = 1
    while running:
        try:
            harvest_pass(pass_num)
            pass_num += 1

            if random.random() < CONFIG["idle_break_chance"]:
                pause = random.uniform(CONFIG["idle_break_min"], CONFIG["idle_break_max"])
                print(f"[Anti-detect] Break for {pause:.1f}s")
                time.sleep(pause)

            print("[SugarcaneFarm] Waiting for regrowth...")
            ready = _wait_for_regrowth()
            if ready:
                print("[SugarcaneFarm] Cane regrown — harvesting.")
            else:
                print("[SugarcaneFarm] Regrowth timeout — harvesting anyway.")

        except KeyboardInterrupt:
            print("[SugarcaneFarm] Stopped by user.")
            running = False
        finally:
            pyautogui.keyUp("w")
            pyautogui.mouseUp(button="left")


if __name__ == "__main__":
    main()
