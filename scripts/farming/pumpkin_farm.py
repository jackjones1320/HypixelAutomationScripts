"""
Script: Pumpkin Farm
Purpose: Walk a linear pumpkin farm row, break pumpkins, turn around, repeat.
         Pumpkins grow next to their stems — walking the row while swinging
         collects whatever has grown since the last pass.
Author: Claude
Version: 1.0

Setup:
  1. Stand at one end of your pumpkin farm row, facing the length of the row.
  2. Equip your farming tool in slot 1.
  3. Adjust row_walk_time and turn_pixels in configs/pumpkin_farm.json.
  4. Run the script and switch to Minecraft before start_delay expires.
"""

import sys
import os
import time
import random

import pyautogui

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_utils import human_key, random_sleep, camera_turn
from config_utils import load_config

DEFAULTS = {
    "tool_slot": "1",
    "start_delay": 5,

    # Seconds to hold W while swinging to traverse one row length.
    # Measure by walking your row manually and timing it.
    "row_walk_time": 6.0,

    # Horizontal pixel delta for a 180° camera turn.
    # At Minecraft default sensitivity (100%): ~1200 px ≈ 180°.
    # Lower sensitivity = more pixels needed.
    "turn_pixels": 1200,

    # Seconds to wait after each full pass (there-and-back) for pumpkins to grow.
    # Pumpkin growth is random; 30–90s covers most conditions.
    "growth_wait_min": 30,
    "growth_wait_max": 90,

    # Anti-detection: chance of an extra idle pause between passes.
    "idle_break_chance": 0.05,
    "idle_break_min": 10,
    "idle_break_max": 40,
}

CONFIG = load_config("pumpkin_farm", DEFAULTS)
running = True


def _walk_and_swing(duration: float):
    """Hold W + left-click for duration seconds, then stop."""
    pyautogui.keyDown("w")
    pyautogui.mouseDown(button="left")
    time.sleep(duration + random.uniform(-0.3, 0.3))
    pyautogui.mouseUp(button="left")
    pyautogui.keyUp("w")


def _turn_180():
    """Spin camera 180° using raw relative mouse movement."""
    # Split into two moves with a tiny gap to feel less robotic
    half = CONFIG["turn_pixels"] // 2
    camera_turn(half + random.randint(-10, 10))
    time.sleep(random.uniform(0.05, 0.12))
    camera_turn(CONFIG["turn_pixels"] - half + random.randint(-10, 10))
    random_sleep(0.2, 0.4)


def farm_pass(pass_num: int):
    """One complete there-and-back traversal of the farm row."""
    print(f"[PumpkinFarm] Pass #{pass_num} — forward")
    _walk_and_swing(CONFIG["row_walk_time"])
    random_sleep(0.3, 0.6)

    _turn_180()

    print(f"[PumpkinFarm] Pass #{pass_num} — back")
    _walk_and_swing(CONFIG["row_walk_time"])
    random_sleep(0.3, 0.6)

    _turn_180()


def main():
    global running
    print(f"[PumpkinFarm] Starting in {CONFIG['start_delay']}s — switch to Minecraft!")
    time.sleep(CONFIG["start_delay"])

    human_key(CONFIG["tool_slot"])
    random_sleep(0.3, 0.6)

    pass_num = 1
    while running:
        try:
            farm_pass(pass_num)
            pass_num += 1

            # Anti-detection idle break
            if random.random() < CONFIG["idle_break_chance"]:
                pause = random.uniform(CONFIG["idle_break_min"], CONFIG["idle_break_max"])
                print(f"[Anti-detect] Idle break for {pause:.1f}s")
                time.sleep(pause)

            # Wait for pumpkins to grow
            wait = random.uniform(CONFIG["growth_wait_min"], CONFIG["growth_wait_max"])
            print(f"[PumpkinFarm] Waiting {wait:.0f}s for growth...")
            time.sleep(wait)

        except KeyboardInterrupt:
            print("[PumpkinFarm] Stopped by user.")
            running = False
        finally:
            # Always release keys on exit
            pyautogui.keyUp("w")
            pyautogui.mouseUp(button="left")


if __name__ == "__main__":
    main()
