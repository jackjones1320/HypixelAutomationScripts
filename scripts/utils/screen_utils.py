"""
screen_utils.py — Screen capture and image detection utilities
Part of the Hypixel Skyblock Scripts toolkit
"""

import time
import numpy as np

try:
    import pyautogui
    import cv2
    from PIL import ImageGrab, Image
except ImportError:
    raise ImportError("Required libraries not found. Run: pip install pyautogui opencv-python pillow numpy")


def screenshot(region=None):
    """
    Capture the screen (or a region) and return as a numpy array (BGR).
    region: (left, top, width, height) or None for full screen.
    """
    img = ImageGrab.grab(bbox=region)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def find_image(template_path: str, threshold=0.85, region=None):
    """
    Search for a template image on screen.
    Returns (x, y) center of best match if found above threshold, else None.
    """
    screen = screenshot(region)
    template = cv2.imread(template_path)
    if template is None:
        raise FileNotFoundError(f"Template not found: {template_path}")

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape[:2]
        cx = max_loc[0] + w // 2
        cy = max_loc[1] + h // 2
        if region:
            cx += region[0]
            cy += region[1]
        return (cx, cy)
    return None


def wait_for_image(template_path: str, timeout=10.0, threshold=0.85, region=None, poll_interval=0.25):
    """
    Block until a template image appears on screen or timeout is reached.
    Returns (x, y) if found, None on timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        result = find_image(template_path, threshold=threshold, region=region)
        if result:
            return result
        time.sleep(poll_interval)
    return None


def get_pixel_color(x: int, y: int):
    """
    Return the (R, G, B) color of the pixel at (x, y).
    """
    img = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
    return img.getpixel((0, 0))[:3]


def pixel_matches(x: int, y: int, expected_rgb: tuple, tolerance=10):
    """
    Check if a pixel at (x, y) matches an expected RGB color within a tolerance.
    """
    r, g, b = get_pixel_color(x, y)
    er, eg, eb = expected_rgb
    return (abs(r - er) <= tolerance and
            abs(g - eg) <= tolerance and
            abs(b - eb) <= tolerance)


def wait_for_pixel(x: int, y: int, expected_rgb: tuple, timeout=10.0, tolerance=10, poll_interval=0.2):
    """
    Block until a pixel at (x, y) matches a color, or timeout.
    Returns True if matched, False on timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        if pixel_matches(x, y, expected_rgb, tolerance):
            return True
        time.sleep(poll_interval)
    return False


def get_screen_size():
    """Return (width, height) of the primary monitor."""
    return pyautogui.size()
