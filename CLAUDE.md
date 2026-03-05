# CLAUDE.md — Hypixel Skyblock Scripts Repository

## Repository Purpose

This repository contains automation and utility scripts for **Hypixel Skyblock**. Scripts are designed to be:
- **Human-like**: randomized timing, natural mouse paths, anti-detection behavior
- **Efficient**: minimal resource usage, clean logic, fast execution
- **Plug-and-play**: downloadable and runnable without manual Python library installation

---

## Core Principles

### 1. Human-Like Behavior
Every script must simulate realistic human input. This means:
- Randomized delays between actions (never fixed intervals)
- Slight cursor jitter and non-linear mouse movement
- Occasional "mistakes" or pauses to mimic human hesitation
- Randomized click positions within target zones (not pixel-perfect every time)
- Idle/afk-safe patterns where appropriate

### 2. Skyblock Compliance
Before implementing any script:
- Confirm the action is achievable within normal Skyblock gameplay
- Avoid anything that reads/writes game memory directly
- Avoid packet manipulation or anything that bypasses the game client
- When in doubt, ask the user clarifying questions before proceeding

### 3. Distribution Format
- **Primary language**: Python 3.x
- **Default packaging**: bundled as a standalone `.exe` using PyInstaller (Windows) so users don't need Python installed
- **Fallback**: If cross-platform is needed, provide a `requirements.txt` + a `run.bat` / `run.sh` bootstrap script that auto-installs deps
- Never assume the user has any libraries pre-installed

---

## Before Writing Any Script — Ask These Questions

When the user requests a new script, Claude **must** ask clarifying questions if any of the following are unclear:

1. **What is the goal?** (e.g., farming, AH flipping, skill grinding, chat automation)
2. **Is this achievable within normal Skyblock client behavior?** (no memory hacks, no packet injection)
3. **What inputs does it rely on?** (screen coordinates, keybinds, game UI state)
4. **What Minecraft client is being used?** (Vanilla, Forge, Lunar, Badlion — affects overlay detection)
5. **Should it loop indefinitely or run for a set time/count?**
6. **Does it need a GUI or is CLI/config file acceptable?**
7. **Target OS?** (Windows assumed unless stated otherwise)

> **Rule**: If a request is ambiguous or potentially non-compliant with Skyblock's design (e.g., relies on features that don't exist in-game), **stop and ask** rather than assume.

---

## File Structure

```
/
├── CLAUDE.md                  # This file
├── README.md                  # User-facing overview
├── scripts/
│   ├── farming/               # Crop/mob farming automations
│   ├── auction_house/         # AH flipping & sniping tools
│   ├── skills/                # Skill grind helpers (fishing, mining, etc.)
│   ├── utils/                 # Shared utilities (input, screen, timing)
│   └── misc/                  # One-off tools
├── builds/                    # Compiled .exe outputs
├── configs/                   # Per-script config files (.json or .ini)
└── requirements.txt           # Dev-only Python dependencies
```

---

## Shared Utility Modules (`scripts/utils/`)

Every script should pull from these shared modules rather than re-implementing:

### `input_utils.py`
- `human_click(x, y, jitter=5)` — clicks with randomized offset
- `human_move(x, y)` — bezier-curve mouse movement
- `human_key(key, hold_min=0.05, hold_max=0.15)` — keypress with random hold duration
- `random_sleep(min_s, max_s)` — sleep for a random duration in range

### `screen_utils.py`
- `find_image(template_path, threshold=0.85)` — locate UI element on screen
- `get_pixel_color(x, y)` — read screen pixel for state detection
- `wait_for_image(template_path, timeout=10)` — block until image appears

### `config_utils.py`
- `load_config(script_name)` — load `configs/<script_name>.json`
- `save_config(script_name, data)` — persist config changes

---

## Packaging Instructions

### Build a standalone `.exe`

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole scripts/<script_name>.py --name <ScriptName>
# Output will be in /builds/
```

### Bootstrap script (for non-compiled distribution)

`run.bat`:
```bat
@echo off
python -m pip install -r requirements.txt --quiet
python scripts\%1.py
```

---

## Standard Script Template

All scripts should follow this structure:

```python
"""
Script: <Name>
Purpose: <Short description>
Author: Claude
Version: 1.0
"""

import time
import random
import sys
import os

# --- Add utils to path ---
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_utils import human_click, human_key, random_sleep
from screen_utils import find_image, wait_for_image
from config_utils import load_config

# --- Config ---
CONFIG = load_config("script_name")

# --- Main Logic ---
def main():
    print("[ScriptName] Starting in 3 seconds... Switch to Minecraft!")
    time.sleep(3)

    running = True
    while running:
        try:
            # Core loop logic here
            random_sleep(0.8, 1.5)

        except KeyboardInterrupt:
            print("[ScriptName] Stopped by user.")
            running = False

if __name__ == "__main__":
    main()
```

---

## Anti-Detection Checklist

Before finalizing any script, verify:

- [ ] No fixed-interval loops (always use `random_sleep`)
- [ ] Mouse movement uses curves, not teleportation
- [ ] Click targets have jitter/offset applied
- [ ] Script has a configurable start delay
- [ ] Script responds to `Ctrl+C` for clean exit
- [ ] No more than ~20 actions/minute in normal operation (unless specifically needed)
- [ ] Includes occasional longer pauses (5–30s) to simulate natural breaks

---

## What Claude Should NOT Do

- Do not implement anything that modifies game files or memory
- Do not implement packet-level manipulation
- Do not implement scripts that exploit bugs or duplication glitches
- Do not hardcode pixel coordinates — always make them configurable
- Do not skip the clarifying questions step for new script requests

---

## Notes

- Scripts are for personal use and automation quality-of-life — not for gaining unfair advantages over other players in competitive modes
- Always test scripts in a low-stakes area first before deploying on main accounts
- Hypixel's rules evolve — when in doubt, check [Hypixel's official rules](https://hypixel.net/rules) before scripting a new behavior
