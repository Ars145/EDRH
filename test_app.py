"""
Test script for EDRH application
"""

import os
import sys

def test_imports():
    """Test that all modules can be imported"""
    try:
        # Test config imports
        from config.settings import load_config, save_config, _cfg
        print("✓ Config imports successful")
        
        # Test models imports
        from models.system import StarSystem, SystemCategory, get_system_manager
        from models.commander import Commander, CommanderManager, get_commander_manager
        print("✓ Models imports successful")
        
        # Test services imports
        from services.journal_monitor import JournalMonitor, auto_detect_journal_folder
        from services.image_service import load_image, preload_image, clear_image_cache
        from services.supabase_client import init_supabase, get_client, table
        print("✓ Services imports successful")
        
        # Test utils imports
        from utils.background_task import BackgroundTask, TaskQueue, add_task, run_in_background
        print("✓ Utils imports successful")
        
        # Test UI imports
        from ui.splash import SplashScreen
        from ui.app import App
        print("✓ UI imports successful")
        
        # Test main import
        import main
        print("✓ Main module import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test that the App class can be instantiated"""
    try:
        from ui.app import App
        import customtkinter as ctk
        
        # Initialize customtkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create app instance but don't run it
        app = App()
        print("✓ App instance created successfully")
        
        # Clean up
        app.withdraw()
        app.destroy()
        
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

if __name__ == "__main__":
    print("Testing EDRH application...")
    
    # Test imports
    imports_ok = test_imports()
    
    # Test app creation if imports are OK
    if imports_ok:
        app_ok = test_app_creation()
    else:
        app_ok = False
        
    # Print summary
    print("\nTest Summary:")
    print(f"Imports: {'✓ OK' if imports_ok else '❌ Failed'}")
    print(f"App Creation: {'✓ OK' if app_ok else '❌ Failed'}")
    print(f"Overall: {'✓ All tests passed' if imports_ok and app_ok else '❌ Some tests failed'}")