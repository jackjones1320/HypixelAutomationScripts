"""
config_utils.py — Configuration loading and saving utilities
Part of the Hypixel Skyblock Scripts toolkit
"""

import os
import json

CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'configs')


def _config_path(script_name: str) -> str:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    return os.path.join(CONFIG_DIR, f"{script_name}.json")


def load_config(script_name: str, defaults: dict = None) -> dict:
    """
    Load config for a script from configs/<script_name>.json.
    If the file doesn't exist, creates it with defaults.
    """
    path = _config_path(script_name)
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
        if defaults:
            for k, v in defaults.items():
                data.setdefault(k, v)
        return data
    elif defaults:
        save_config(script_name, defaults)
        return defaults.copy()
    else:
        return {}


def save_config(script_name: str, data: dict):
    """
    Save config dict to configs/<script_name>.json.
    """
    path = _config_path(script_name)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[Config] Saved config to {path}")
