"""
input_utils.py — Human-like input simulation utilities
Part of the Hypixel Skyblock Scripts toolkit
"""

import time
import random
import math

try:
    import pyautogui
    import pynput
    from pynput.mouse import Controller as MouseController
except ImportError:
    raise ImportError("Required libraries not found. Run: pip install pyautogui pynput")

pyautogui.FAILSAFE = True  # Move mouse to corner to emergency stop
_mouse = MouseController()


def random_sleep(min_s: float, max_s: float):
    """Sleep for a random duration between min_s and max_s seconds."""
    time.sleep(random.uniform(min_s, max_s))


def _bezier_curve(p0, p1, p2, p3, t):
    """Compute a point on a cubic bezier curve at parameter t."""
    x = (1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] + \
        3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
    y = (1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] + \
        3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
    return (int(x), int(y))


def human_move(target_x: int, target_y: int, duration_min=0.3, duration_max=0.7):
    """
    Move the mouse to (target_x, target_y) using a bezier curve to simulate
    natural human mouse movement.
    """
    start_x, start_y = pyautogui.position()
    duration = random.uniform(duration_min, duration_max)
    steps = max(20, int(duration * 60))

    # Random control points for bezier curve
    cp1 = (
        start_x + random.randint(-80, 80),
        start_y + random.randint(-80, 80)
    )
    cp2 = (
        target_x + random.randint(-80, 80),
        target_y + random.randint(-80, 80)
    )

    for i in range(steps + 1):
        t = i / steps
        # Ease in/out
        t_eased = t * t * (3 - 2 * t)
        px, py = _bezier_curve((start_x, start_y), cp1, cp2, (target_x, target_y), t_eased)
        pyautogui.moveTo(px, py, _pause=False)
        time.sleep(duration / steps)


def human_click(x: int, y: int, jitter: int = 5, button='left', double=False):
    """
    Click at (x, y) with a random offset applied (jitter).
    Simulates realistic click timing.
    """
    jx = x + random.randint(-jitter, jitter)
    jy = y + random.randint(-jitter, jitter)

    human_move(jx, jy)
    random_sleep(0.05, 0.15)

    hold_time = random.uniform(0.05, 0.12)
    pyautogui.mouseDown(jx, jy, button=button)
    time.sleep(hold_time)
    pyautogui.mouseUp(jx, jy, button=button)

    if double:
        random_sleep(0.08, 0.18)
        pyautogui.mouseDown(jx, jy, button=button)
        time.sleep(random.uniform(0.05, 0.10))
        pyautogui.mouseUp(jx, jy, button=button)


def human_key(key: str, hold_min=0.05, hold_max=0.15):
    """
    Press and release a key with a random hold duration.
    """
    hold = random.uniform(hold_min, hold_max)
    pyautogui.keyDown(key)
    time.sleep(hold)
    pyautogui.keyUp(key)
    random_sleep(0.03, 0.1)


def human_type(text: str, wpm_min=60, wpm_max=100):
    """
    Type a string at a human-like WPM rate with occasional typo-and-correct behavior.
    """
    chars_per_second = random.uniform(wpm_min, wpm_max) * 5 / 60
    for char in text:
        pyautogui.typewrite(char, interval=0)
        time.sleep(1 / chars_per_second + random.uniform(-0.02, 0.04))


def scroll(amount: int, direction='down'):
    """
    Scroll up or down by a given amount with slight randomness.
    """
    clicks = amount + random.randint(-1, 1)
    pyautogui.scroll(-clicks if direction == 'down' else clicks)
