"""
Elite Dangerous Records Helper (EDRH)
Main application entry point
"""

import os
import sys
import time
import threading
import customtkinter as ctk
from config.settings import load_config, save_config
from ui.app import App
from ui.splash import SplashScreen
from services.journal_monitor import auto_detect_journal_folder, analyze_journal_folder

def main():
    """Main application entry point"""
    # Set up error handling
    sys.excepthook = custom_tk_error_handler
    
    # Initialize the application
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Start the application
    app = App()
    app.mainloop()

def custom_tk_error_handler(exc, val, tb):
    """Custom error handler for Tkinter exceptions"""
    import traceback
    print("".join(traceback.format_exception(exc, val, tb)))
    
    try:
        if 'app' in globals() and hasattr(app, 'on_closing'):
            def wrapped_on_closing():
                try:
                    app.on_closing()
                except:
                    pass
                finally:
                    os._exit(1)
            
            app.after(100, wrapped_on_closing)
        else:
            os._exit(1)
    except:
        os._exit(1)

if __name__ == "__main__":
    main()