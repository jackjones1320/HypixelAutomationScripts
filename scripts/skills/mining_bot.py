"""
Script: Mining Bot
Purpose: Mine a single respawning ore block (mithril, diamond, etc.), wait for
         it to respawn via pixel color detection, then mine again.
         Ideal for Dwarven Mines or Deep Caverns ore respawn grinding.
Author: Claude
Version: 1.0

Setup:
  1. Face the target ore block so it fills the crosshair.
  2. Equip your pickaxe in slot 1.
  3. Set ore_pixel_x/y to a screen coordinate ON the ore block face.
  4. Set ore_color to the ore's RGB (e.g. mithril is teal ~[0, 192, 192]).
  5. Set background_color to what that pixel looks like when the block is gone
     (usually the cave wall behind it, or air — check with get_pixel_color).
"""

import sys
import os
import time
import random

import pyautogui

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_utils import human_key, random_sleep, camera_turn
from screen_utils import pixel_matches, get_pixel_color
from config_utils import load_config

DEFAULTS = {
    "pickaxe_slot": "1",
    "start_delay": 5,

    # Screen coordinate of a pixel ON the ore block face
    "ore_pixel_x": 960,
    "ore_pixel_y": 540,

    # RGB color of the ore (what the pixel looks like when block is present)
    "ore_color": [0, 192, 192],         # teal — mithril default
    "ore_tolerance": 35,

    # RGB color when the block is mined away (empty air / cave wall behind)
    "background_color": [30, 30, 30],
    "background_tolerance": 40,

    # Seconds to hold left-click per mining attempt
    # Set slightly longer than your pickaxe's actual break time
    "mine_hold_time": 1.5,

    # Maximum seconds to wait for respawn before retrying mine
    "respawn_timeout": 30,
    "poll_interval": 0.3,

    # Small random camera jitter between attempts (feels more human)
    "jitter_pixels": 8,

    # Anti-detection
    "idle_break_chance": 0.04,
    "idle_break_min": 8,
    "idle_break_max": 30,
}

CONFIG = load_config("mining_bot", DEFAULTS)
running = True
total_mined = 0


def _block_present() -> bool:
    px, py = CONFIG["ore_pixel_x"], CONFIG["ore_pixel_y"]
    return pixel_matches(px, py, tuple(CONFIG["ore_color"]), CONFIG["ore_tolerance"])


def _block_gone() -> bool:
    px, py = CONFIG["ore_pixel_x"], CONFIG["ore_pixel_y"]
    return pixel_matches(px, py, tuple(CONFIG["background_color"]), CONFIG["background_tolerance"])


def _mine_block():
    """Hold left-click until the block disappears or hold_time expires."""
    hold = CONFIG["mine_hold_time"] + random.uniform(-0.1, 0.2)
    deadline = time.time() + hold
    pyautogui.mouseDown(button="left")
    while time.time() < deadline:
        if _block_gone():
            break
        time.sleep(0.05)
    pyautogui.mouseUp(button="left")


def _wait_for_respawn() -> bool:
    """Poll until ore pixel matches ore_color again. Returns True if respawned."""
    timeout = CONFIG["respawn_timeout"]
    poll = CONFIG["poll_interval"]
    start = time.time()
    while time.time() - start < timeout:
        if _block_present():
            return True
        time.sleep(poll + random.uniform(-0.05, 0.05))
    return False


def _apply_jitter():
    """Tiny random camera nudge so the crosshair isn't pixel-perfect every time."""
    j = CONFIG["jitter_pixels"]
    camera_turn(
        random.randint(-j, j),
        random.randint(-j // 2, j // 2),
    )


def main():
    global running, total_mined
    print(f"[MiningBot] Starting in {CONFIG['start_delay']}s — switch to Minecraft!")
    time.sleep(CONFIG["start_delay"])

    human_key(CONFIG["pickaxe_slot"])
    random_sleep(0.3, 0.6)

    # Confirm initial ore detection
    if not _block_present():
        print("[MiningBot] WARNING: Ore pixel not detected at startup.")
        print(f"  Current pixel color: {get_pixel_color(CONFIG['ore_pixel_x'], CONFIG['ore_pixel_y'])}")
        print("  Adjust ore_pixel_x/y and ore_color in configs/mining_bot.json")

    while running:
        try:
            if not _block_present():
                print("[MiningBot] Waiting for ore to respawn...")
                respawned = _wait_for_respawn()
                if not respawned:
                    print("[MiningBot] Respawn timeout — retrying mine anyway.")

            _apply_jitter()
            random_sleep(0.05, 0.15)

            print(f"[MiningBot] Mining... (total: {total_mined})")
            _mine_block()

            if _block_gone():
                total_mined += 1
                print(f"[MiningBot] Block mined! Total: {total_mined}")
            else:
                print("[MiningBot] Block not fully mined — retrying.")
                continue

            if random.random() < CONFIG["idle_break_chance"]:
                pause = random.uniform(CONFIG["idle_break_min"], CONFIG["idle_break_max"])
                print(f"[Anti-detect] Break for {pause:.1f}s")
                time.sleep(pause)

        except KeyboardInterrupt:
            print(f"[MiningBot] Stopped. Total mined: {total_mined}")
            running = False
        finally:
            pyautogui.mouseUp(button="left")


if __name__ == "__main__":
    main()
