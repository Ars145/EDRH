"""
Elite Dangerous Records Helper - Main Entry Point
v1.4.0

This is the main entry point for the Elite Dangerous Records Helper application.
It initializes and starts the application.
"""

import os
import sys
import time
import traceback
import customtkinter as ctk
from tkinter import messagebox
from ui.app import App


def check_single_instance():
    """Ensure only one instance of the application is running.

    Returns:
        object: Mutex handle on Windows, None on other platforms.
    """
    if sys.platform == 'win32':
        import ctypes
        mutex_name = "EDRH_SingleInstance_Mutex"
        handle = ctypes.windll.kernel32.CreateMutexW(None, True, mutex_name)
        last_error = ctypes.windll.kernel32.GetLastError()
        if last_error == 183:
            messagebox.showerror(
                "Already Running",
                "EDRH is already running!\n"
                "Check your system tray or task manager."
            )
            sys.exit(1)
        return handle
    return None


def custom_tk_error_handler(exc, val, tb):
    """Custom error handler for Tkinter exceptions.

    Args:
        exc: Exception type
        val: Exception value
        tb: Traceback
    """
    global _is_shutting_down
    error_msg = str(val).lower()

    # Ignore common errors during shutdown
    if _is_shutting_down or any(phrase in error_msg for phrase in 
                               ['invalid command name', 'application has been destroyed', 
                                'bad window', 'ctkcanvas']):
        return

    # Print the exception with timestamp for better logging
    print(f"[ERROR] {time.strftime('%Y-%m-%d %H:%M:%S')} - Exception occurred:")
    traceback.print_exception(exc, val, tb)


if __name__ == "__main__":
    # Enable DPI awareness on Windows
    if sys.platform == 'win32':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            try:
                windll.user32.SetProcessDPIAware()
            except:
                pass

    # Set appearance mode and color theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    # Global flag for shutdown state
    _is_shutting_down = False

    # Check for single instance
    instance_lock = check_single_instance()

    # Initialize and start the application
    app = App()
    app._instance_lock = instance_lock

    # Set up custom error handler
    app.report_callback_exception = custom_tk_error_handler

    # Wrap the on_closing method to set the shutdown flag
    original_on_closing = app.on_closing

    def wrapped_on_closing():
        global _is_shutting_down
        _is_shutting_down = True
        app._is_shutting_down = True
        original_on_closing()

    app.on_closing = wrapped_on_closing
    app.protocol("WM_DELETE_WINDOW", wrapped_on_closing)

    # Start the application
    app.mainloop()
