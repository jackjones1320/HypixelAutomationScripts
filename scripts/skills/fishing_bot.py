"""
Script: Fishing Bot
Purpose: Automated fishing with mob detection, bait management, inventory monitoring,
         and a live always-on-top status GUI.
Author: Claude
Version: 1.0

Usage:
  run.bat skills\\fishing_bot
  OR: python scripts/skills/fishing_bot.py

Calibration:
  On first run a config is written to configs/fishing_bot.json.
  Adjust bobber_region, health_region, bait_scan_region, and inv_sample_x/y
  to match your screen resolution and Minecraft window position.
  Default values assume vanilla Minecraft at 1920x1080 fullscreen.
"""

import sys
import os
import time
import random
import threading
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_utils import human_key, random_sleep
from screen_utils import screenshot, get_pixel_color
from config_utils import load_config

try:
    import pyautogui
except ImportError:
    raise ImportError("Required libraries not found. Run: pip install pyautogui")

# ── Default Config ──────────────────────────────────────────────────────────────
DEFAULTS = {
    # Hotbar slots (string keys)
    "rod_slot":   "1",
    "sword_slot": "2",

    # Seconds to wait before starting (time to switch to Minecraft)
    "start_delay": 5,

    # Region [left, top, width, height] where the bobber sits on screen.
    # The script watches this area for the brightness spike of a fish bite.
    "bobber_region": [860, 430, 200, 150],
    # Average brightness per channel (0-255) to flag a pixel as a splash flash
    "splash_brightness_threshold": 200,
    # Minimum number of such bright pixels before declaring a bite
    "splash_pixel_count": 8,
    # Seconds to wait for a bite before forcing a reel-in
    "cast_timeout": 22,

    # Health bar region [left, top, width, height] — vanilla 1080p default.
    # Red heart pixels are counted; a drop signals a mob is attacking.
    "health_region": [40, 950, 210, 14],
    # If current red-pixel count falls below this fraction of the baseline, combat triggers
    "health_drop_trigger": 0.65,

    # How long to swing the sword before returning to rod
    "combat_duration": 3.5,
    "combat_swing_interval_min": 0.10,
    "combat_swing_interval_max": 0.20,

    # Open-inventory area to scan for bait [left, top, width, height].
    # Vanilla 1080p: the top two rows of the main inventory grid.
    "bait_scan_region": [623, 278, 390, 100],
    # Pixel stride when scanning inventory slots
    "bait_slot_size": 18,
    # Sum of R+G+B above which we consider the slot non-empty (has a bait item)
    "bait_brightness_min": 160,
    # Seconds between automatic bait-application attempts
    "bait_check_interval": 60,

    # Pixel at the center of the rightmost hotbar slot.
    # If R+G+B > 80 the slot is occupied; used as a proxy for inventory-full detection.
    "inv_sample_x": 1007,
    "inv_sample_y": 979,
    # Seconds between inventory-full checks
    "inv_check_interval": 90,

    # Anti-detection random idle breaks
    "idle_break_chance": 0.04,   # probability of a break before each cast
    "idle_break_min": 6,         # minimum break length in seconds
    "idle_break_max": 28,        # maximum break length in seconds
}

CONFIG = load_config("fishing_bot", DEFAULTS)

# ── Shared State (written by bot thread, read by GUI thread) ────────────────────
_state = {
    "status":     "Idle",
    "casts":      0,
    "fish":       0,
    "running":    False,
    "health_pct": 100.0,
    "bait_ok":    True,
    "alert":      None,    # non-None string triggers a popup on the GUI thread
}

_start_time      = None
_health_baseline = None


# ── Status GUI ──────────────────────────────────────────────────────────────────
class StatusGUI:
    """Always-on-top status window. Runs on the main thread via mainloop()."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Fishing Bot")
        self.root.geometry("270x240")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1e1e2e")

        label_cfg = {"bg": "#1e1e2e", "fg": "#cdd6f4", "font": ("Segoe UI", 9)}
        value_cfg = {"bg": "#1e1e2e", "fg": "#89b4fa", "font": ("Segoe UI", 9, "bold")}

        self._vars = {}
        for display, key in [
            ("Status",  "status"),
            ("Casts",   "casts"),
            ("Fish",    "fish"),
            ("Runtime", "_runtime"),
            ("Health",  "health_pct"),
            ("Bait",    "bait_ok"),
        ]:
            var = tk.StringVar(value="—")
            self._vars[key] = var
            row = tk.Frame(self.root, bg="#1e1e2e")
            row.pack(fill="x", padx=14, pady=3)
            tk.Label(row, text=f"{display}:", width=9, anchor="w", **label_cfg).pack(side="left")
            tk.Label(row, textvariable=var, anchor="w", **value_cfg).pack(side="left")

        tk.Button(
            self.root, text="Stop", command=self._stop,
            bg="#f38ba8", fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", padx=12, pady=5,
        ).pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self._stop)

    def _stop(self):
        _state["running"] = False

    def _tick(self):
        # Handle alert from bot thread (must be shown on main thread)
        if _state["alert"]:
            msg = _state["alert"]
            _state["alert"] = None
            messagebox.showwarning("Fishing Bot", msg)
            self.root.destroy()
            return

        self._vars["status"].set(_state["status"])
        self._vars["casts"].set(str(_state["casts"]))
        self._vars["fish"].set(str(_state["fish"]))

        elapsed = int(time.time() - _start_time) if _start_time else 0
        h, rem = divmod(elapsed, 3600)
        m, s   = divmod(rem, 60)
        self._vars["_runtime"].set(f"{h:02d}:{m:02d}:{s:02d}")

        self._vars["health_pct"].set(f"{_state['health_pct']:.0f}%")
        self._vars["bait_ok"].set("OK" if _state["bait_ok"] else "LOW ⚠")

        self.root.after(500, self._tick)

    def run(self):
        self.root.after(500, self._tick)
        self.root.mainloop()


# ── Health Monitoring ───────────────────────────────────────────────────────────
def _count_health_pixels() -> int:
    """Count red heart pixels in the configured health bar region."""
    x, y, w, h = CONFIG["health_region"]
    img = screenshot((x, y, x + w, y + h))
    count = 0
    for row in img:
        for bgr in row:
            b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
            if r > 140 and g < 90 and b < 90:
                count += 1
    return count


def _calibrate_health():
    global _health_baseline
    _health_baseline = max(_count_health_pixels(), 1)
    print(f"[Health] Baseline: {_health_baseline} red pixels")


def _is_under_attack() -> bool:
    """Returns True if health has dropped significantly below baseline."""
    if not _health_baseline:
        return False
    current = _count_health_pixels()
    ratio = current / _health_baseline
    _state["health_pct"] = ratio * 100.0
    return ratio < CONFIG["health_drop_trigger"]


# ── Combat ──────────────────────────────────────────────────────────────────────
def _do_combat():
    _state["status"] = "Combat"
    print("[Combat] Mob detected — switching to sword")

    human_key(CONFIG["sword_slot"])
    random_sleep(0.15, 0.25)

    end = time.time() + CONFIG["combat_duration"]
    while time.time() < end and _state["running"]:
        pyautogui.click()   # left-click = sword swing in Minecraft
        random_sleep(
            CONFIG["combat_swing_interval_min"],
            CONFIG["combat_swing_interval_max"],
        )

    human_key(CONFIG["rod_slot"])
    random_sleep(0.2, 0.4)
    print("[Combat] Done — returning to rod")


# ── Bite Detection ──────────────────────────────────────────────────────────────
def _wait_for_bite(timeout: float) -> str:
    """
    Watch the bobber region for the brightness spike that signals a fish bite.
    Simultaneously monitors health every poll cycle.

    Returns:
        'bite'    – fish detected
        'timeout' – no bite within timeout seconds
        'combat'  – health dropped, combat needed
    """
    x, y, w, h  = CONFIG["bobber_region"]
    threshold    = CONFIG["splash_brightness_threshold"]
    min_pixels   = CONFIG["splash_pixel_count"]

    time.sleep(1.5)   # let bobber settle before watching
    deadline = time.time() + timeout - 1.5

    while time.time() < deadline and _state["running"]:
        if _is_under_attack():
            return "combat"

        img = screenshot((x, y, x + w, y + h))
        bright_count = sum(
            1
            for row in img
            for bgr in row
            if (int(bgr[0]) + int(bgr[1]) + int(bgr[2])) / 3 > threshold
        )
        if bright_count >= min_pixels:
            return "bite"

        random_sleep(0.15, 0.25)

    return "timeout"


# ── Bait Management ─────────────────────────────────────────────────────────────
def _apply_bait():
    """
    Open the inventory, scan for the first non-empty slot in the bait scan region,
    and right-click it to apply the bait.  Works with any bait type.
    """
    _state["status"] = "Applying Bait"
    print("[Bait] Opening inventory...")

    pyautogui.press("e")
    random_sleep(0.5, 0.9)

    bx, by, bw, bh = CONFIG["bait_scan_region"]
    step           = CONFIG["bait_slot_size"]
    brightness_min = CONFIG["bait_brightness_min"]

    img   = screenshot((bx, by, bx + bw, by + bh))
    found = False

    for ri in range(0, min(bh, img.shape[0]), step):
        for ci in range(0, min(bw, img.shape[1]), step):
            b, g, r = int(img[ri][ci][0]), int(img[ri][ci][1]), int(img[ri][ci][2])
            if r + g + b >= brightness_min:
                # Non-empty slot — right-click to apply bait
                cx = bx + ci + step // 2
                cy = by + ri + step // 2
                pyautogui.rightClick(cx, cy)
                random_sleep(0.3, 0.5)
                found = True
                break
        if found:
            break

    _state["bait_ok"] = found
    if found:
        print("[Bait] Applied.")
    else:
        print("[Bait] No bait found in inventory!")

    pyautogui.press("e")   # close inventory
    random_sleep(0.4, 0.7)


# ── Inventory Full Check ────────────────────────────────────────────────────────
def _is_inventory_full() -> bool:
    """
    Sample a pixel at the rightmost hotbar slot.
    If it's non-dark an item is present, which we use as a proxy for a full inventory.
    Adjust inv_sample_x/y in config if this gives false positives.
    """
    r, g, b = get_pixel_color(CONFIG["inv_sample_x"], CONFIG["inv_sample_y"])
    return (r + g + b) > 80


# ── Main Fishing Loop ───────────────────────────────────────────────────────────
def _fishing_loop():
    global _start_time

    print(f"[FishingBot] Starting in {CONFIG['start_delay']}s — switch to Minecraft!")
    time.sleep(CONFIG["start_delay"])

    _start_time       = time.time()
    _state["running"] = True

    _calibrate_health()

    last_bait_check = time.time()
    last_inv_check  = time.time()

    # Equip rod
    human_key(CONFIG["rod_slot"])
    random_sleep(0.3, 0.6)

    while _state["running"]:

        # ── Anti-detection idle break ──────────────────────────────────────────
        if random.random() < CONFIG["idle_break_chance"]:
            pause = random.uniform(CONFIG["idle_break_min"], CONFIG["idle_break_max"])
            _state["status"] = f"Break ({pause:.0f}s)"
            print(f"[Anti-detect] Break for {pause:.1f}s")
            time.sleep(pause)
            if not _state["running"]:
                break

        # ── Bait check ────────────────────────────────────────────────────────
        if time.time() - last_bait_check > CONFIG["bait_check_interval"]:
            _apply_bait()
            last_bait_check = time.time()
            human_key(CONFIG["rod_slot"])
            random_sleep(0.3, 0.5)

        # ── Inventory full check ───────────────────────────────────────────────
        if time.time() - last_inv_check > CONFIG["inv_check_interval"]:
            if _is_inventory_full():
                _state["status"]  = "FULL — Stopped"
                _state["running"] = False
                _state["alert"]   = "Inventory is full!\nBot has stopped."
                print("[Alert] Inventory full — stopping.")
                break
            last_inv_check = time.time()

        # ── Cast ──────────────────────────────────────────────────────────────
        _state["status"] = "Casting"
        print(f"[Cast #{_state['casts'] + 1}]")
        pyautogui.rightClick()
        random_sleep(0.4, 0.8)
        _state["casts"] += 1

        # ── Watch for bite ────────────────────────────────────────────────────
        _state["status"] = "Watching"
        result = _wait_for_bite(CONFIG["cast_timeout"])

        if result == "combat":
            # Reel in before fighting so the bobber doesn't drift
            pyautogui.rightClick()
            random_sleep(0.2, 0.4)
            _do_combat()
            continue

        # ── Reel in ───────────────────────────────────────────────────────────
        _state["status"] = "Reeling"
        pyautogui.rightClick()
        random_sleep(0.5, 0.9)

        if result == "bite":
            _state["fish"] += 1
            print(f"[Fish] Total: {_state['fish']}")

        random_sleep(0.5, 1.1)

    _state["status"]  = "Stopped"
    _state["running"] = False
    print("[FishingBot] Stopped.")


# ── Entry Point ─────────────────────────────────────────────────────────────────
def main():
    gui    = StatusGUI()
    thread = threading.Thread(target=_fishing_loop, daemon=True)
    thread.start()
    gui.run()   # blocks on main thread until window is closed


if __name__ == "__main__":
    main()
