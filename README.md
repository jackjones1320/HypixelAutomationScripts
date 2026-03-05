# 🌌 Hypixel Skyblock Scripts

A personal collection of human-like automation and utility scripts for Hypixel Skyblock.

## ⚡ Quick Start

### Option A — Download & Run (No Python Required)
1. Download the `.exe` from the `builds/` folder for the script you want
2. Double-click and switch to Minecraft when prompted

### Option B — Run from Source
1. Make sure Python 3.10+ is installed
2. Double-click `run.bat <script_name>` or run:
```bat
run.bat farming\pumpkin_farm
```

## 📁 Structure

| Folder | Contents |
|---|---|
| `scripts/farming/` | Crop and mob farming automations |
| `scripts/auction_house/` | AH flipping and snipe tools |
| `scripts/skills/` | Skill grind helpers |
| `scripts/utils/` | Shared input/screen/config utilities |
| `builds/` | Compiled `.exe` files |
| `configs/` | Per-script JSON configuration |

## ⚙️ Configuration

Each script has a matching `configs/<script_name>.json` that is auto-created on first run with defaults. Edit it to customize coordinates, delays, and behavior.

## 🛡️ Safety Features

- All scripts use randomized timing — no fixed loops
- Mouse movement follows bezier curves (non-linear, human-like)
- Click targets include random jitter
- Emergency stop: move mouse to top-left corner of screen

## 🔨 Building an .exe

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole scripts/<script>.py --distpath builds/
```
