"""
Script: Combat Farm
Purpose: AFK combat farming for XP and drops at stationary mob spawners
         (e.g. Enderman, Zombie, Spider dens in Skyblock).
         Holds left-click, jumps periodically for critical hits, randomly
         rotates to catch mobs in all directions, and takes anti-detection breaks.
Author: Claude
Version: 1.0

Setup:
  1. Stand in the middle of the spawner area.
  2. Equip your weapon in slot 1 and a healing item (e.g. God Potion / Mending)
     in slot 2 if you want auto-heal on health drop.
  3. Run and switch to Minecraft before start_delay expires.
"""

import sys
import os
import time
import random

import pyautogui

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_utils import human_key, random_sleep, camera_turn
from screen_utils import screenshot
from config_utils import load_config

DEFAULTS = {
    "weapon_slot": "1",
    "heal_slot": "2",           # hotbar slot with healing item; set to "" to disable
    "start_delay": 5,

    # Seconds between crit jumps (space bar)
    "jump_interval_min": 0.6,
    "jump_interval_max": 1.0,

    # Seconds between random camera spins to catch mobs around you
    "spin_interval_min": 3.0,
    "spin_interval_max": 7.0,
    # How far to rotate on each spin (pixels; 400 ≈ 60°)
    "spin_pixels_min": -500,
    "spin_pixels_max": 500,

    # Health monitoring: region [left, top, width, height] of health bar
    "health_region": [40, 950, 210, 14],
    # Fraction of baseline red pixels below which we auto-heal
    "heal_threshold": 0.55,

    # Anti-detection long breaks
    "idle_break_chance": 0.03,
    "idle_break_min": 10,
    "idle_break_max": 45,

    # Total session length in minutes (0 = run forever)
    "session_minutes": 0,
}

CONFIG = load_config("combat_farm", DEFAULTS)
running = True
_health_baseline = None
kills_estimate = 0


# ── Health helpers ──────────────────────────────────────────────────────────────
def _count_red_pixels() -> int:
    x, y, w, h = CONFIG["health_region"]
    img = screenshot((x, y, x + w, y + h))
    count = 0
    for row in img:
        for bgr in row:
            b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
            if r > 140 and g < 90 and b < 90:
                count += 1
    return count


def _calibrate():
    global _health_baseline
    _health_baseline = max(_count_red_pixels(), 1)
    print(f"[CombatFarm] Health baseline: {_health_baseline} red pixels")


def _needs_heal() -> bool:
    if not _health_baseline:
        return False
    return (_count_red_pixels() / _health_baseline) < CONFIG["heal_threshold"]


def _do_heal():
    """Briefly release left-click, use healing item, resume attacking."""
    if not CONFIG.get("heal_slot"):
        return
    pyautogui.mouseUp(button="left")
    print("[CombatFarm] Low health — healing")
    human_key(CONFIG["heal_slot"])
    pyautogui.rightClick()
    random_sleep(0.3, 0.6)
    human_key(CONFIG["weapon_slot"])
    random_sleep(0.1, 0.2)
    pyautogui.mouseDown(button="left")


# ── Main loop ───────────────────────────────────────────────────────────────────
def main():
    global running, kills_estimate
    print(f"[CombatFarm] Starting in {CONFIG['start_delay']}s — switch to Minecraft!")
    time.sleep(CONFIG["start_delay"])

    session_end = (
        time.time() + CONFIG["session_minutes"] * 60
        if CONFIG["session_minutes"] > 0 else None
    )

    human_key(CONFIG["weapon_slot"])
    random_sleep(0.3, 0.5)
    _calibrate()

    next_jump = time.time() + random.uniform(CONFIG["jump_interval_min"], CONFIG["jump_interval_max"])
    next_spin = time.time() + random.uniform(CONFIG["spin_interval_min"], CONFIG["spin_interval_max"])
    start_time = time.time()

    # Begin attacking
    pyautogui.mouseDown(button="left")
    print("[CombatFarm] Farming started. Ctrl+C to stop.")

    try:
        while running:
            if session_end and time.time() >= session_end:
                print("[CombatFarm] Session time reached — stopping.")
                break

            now = time.time()

            # Critical jump
            if now >= next_jump:
                pyautogui.press("space")
                next_jump = now + random.uniform(CONFIG["jump_interval_min"], CONFIG["jump_interval_max"])

            # Camera spin
            if now >= next_spin:
                spin = random.randint(CONFIG["spin_pixels_min"], CONFIG["spin_pixels_max"])
                camera_turn(spin)
                next_spin = now + random.uniform(CONFIG["spin_interval_min"], CONFIG["spin_interval_max"])

            # Health check
            if _needs_heal():
                _do_heal()

            # Anti-detection break
            if random.random() < CONFIG["idle_break_chance"] / 100:
                pause = random.uniform(CONFIG["idle_break_min"], CONFIG["idle_break_max"])
                pyautogui.mouseUp(button="left")
                print(f"[Anti-detect] Break for {pause:.1f}s")
                time.sleep(pause)
                pyautogui.mouseDown(button="left")

            elapsed = int(now - start_time)
            if elapsed % 60 == 0 and elapsed > 0:
                print(f"[CombatFarm] Running {elapsed // 60}m")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("[CombatFarm] Stopped by user.")
    finally:
        pyautogui.mouseUp(button="left")
        pyautogui.keyUp("space")
        elapsed = int(time.time() - start_time)
        print(f"[CombatFarm] Session ended after {elapsed // 60}m {elapsed % 60}s")


if __name__ == "__main__":
    main()
