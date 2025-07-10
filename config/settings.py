"""
Configuration settings for the EDRH application
"""

import os
import json

# Default configuration
DEFAULT_CONFIG = {
    "journal_path": "",
    "journal_verified": False,
    "current_journal": "",
    "category_colors": {}
}

# Global configuration object
_cfg = {}

def resource(name: str):
    """Get the path to a resource file"""
    if getattr(os.sys, 'frozen', False):
        # Running as compiled exe
        return os.path.join(os.path.dirname(os.sys.executable), name)
    else:
        # Running as script
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", name)

def load_config():
    """Load configuration from config.json"""
    global _cfg
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                _cfg = json.load(f)
        else:
            _cfg = DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"Error loading config: {e}")
        _cfg = DEFAULT_CONFIG.copy()
    return _cfg

def save_config(cfg=None):
    """Save configuration to config.json"""
    if cfg is None:
        cfg = _cfg
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

def save_current_journal_path(path):
    """Save the current journal path to the configuration"""
    _cfg["current_journal"] = path
    save_config()

def get_current_journal_path():
    """Get the current journal path from the configuration"""
    return _cfg.get("current_journal")

# Initialize configuration on module import
_cfg = load_config()