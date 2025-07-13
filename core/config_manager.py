"""
Configuration manager for Elite Dangerous Records Helper.
Handles loading, saving, and validating configuration.
"""

import os
import json
import sys


class ConfigManager:
    """Manages application configuration with validation and defaults"""
    
    DEFAULT_CONFIG = {
        "journal_path": "",
        "journal_verified": False,
        "commander_name": "Unknown",
        "current_journal": "",
        "supabase_url": "https://nxrvrnnaxxykwaugkxnw.supabase.co",
        "supabase_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im54cnZybm5heHh5a3dhdWdreG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkyMzIxMjksImV4cCI6MjA2NDgwODEyOX0.KkLMT5bQBuTEC4Qhx9y04OO82A4D2FlrjnyvEGx_lo4",
        "supabase_auth_confirmation": True,
        "category_colors": {}
    }
    
    def __init__(self, config_path=None):
        """Initialize the configuration manager.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                If None, uses the default path in the application directory.
        """
        if getattr(sys, 'frozen', False):
            self.exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            self.exe_dir = os.path.dirname(os.path.abspath(__file__))
            # Move up one directory to get to the project root
            self.exe_dir = os.path.dirname(self.exe_dir)
            
        self.config_path = config_path or os.path.join(self.exe_dir, "config.json")
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from file with validation and defaults.
        
        Returns:
            dict: The loaded configuration with defaults applied.
        """
        config = self.DEFAULT_CONFIG.copy()
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                
                # Update config with loaded values
                config.update(loaded_config)
            except Exception as e:
                print(f"Error loading configuration: {e}")
        
        return config
    
    def save(self):
        """Save the current configuration to file.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a configuration value.
        
        Args:
            key (str): The configuration key.
            default: The default value to return if the key is not found.
        
        Returns:
            The configuration value or the default.
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value and save.
        
        Args:
            key (str): The configuration key.
            value: The value to set.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        self.config[key] = value
        return self.save()
    
    def save_current_journal_path(self, path):
        """Save the current journal path.
        
        Args:
            path (str): The path to the current journal file.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        self.config["current_journal"] = path
        return self.save()
    
    def get_current_journal_path(self):
        """Get the current journal path.
        
        Returns:
            str: The path to the current journal file.
        """
        return self.config.get("current_journal", "")