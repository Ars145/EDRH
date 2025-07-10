"""
Elite Dangerous Records Helper (EDRH)
Main application entry point
"""

import os
import sys
import traceback
import customtkinter as ctk
import signal

# Global reference to the app instance
app = None
is_closing = False


def signal_handler(signum, frame):
    """Handle system signals"""
    global is_closing
    if not is_closing:
        is_closing = True
        print(f"[SIGNAL] Received signal {signum}, shutting down...")
        force_exit()


def force_exit():
    """Force exit the application"""
    global app
    print("[SHUTDOWN] Forcing application exit...")
    try:
        if app and hasattr(app, '_is_destroying'):
            app._is_destroying = True
        if app and hasattr(app, 'quit'):
            app.quit()
    except:
        pass
    os._exit(0)


def main():
    """Main application entry point"""
    global app, is_closing

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Set up error handling
    sys.excepthook = custom_tk_error_handler

    print("[STARTUP] Initializing application...")

    try:
        # Initialize customtkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Import modules after CTK initialization
        from ui.app import App

        print("[STARTUP] Creating main application...")

        # Create and start the application
        app = App()

        # Set up proper window close protocol
        app.protocol("WM_DELETE_WINDOW", safe_close_handler)

        print("[STARTUP] Starting main loop...")
        app.mainloop()

    except ImportError as e:
        print(f"[ERROR] Failed to import required modules: {e}")
        print("Make sure all required modules are installed and accessible.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Critical error during startup: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("[SHUTDOWN] Application shutdown complete.")


def safe_close_handler():
    """Safe close handler to prevent infinite loops"""
    global app, is_closing

    if is_closing:
        print("[CLOSE] Already closing, ignoring...")
        return

    is_closing = True
    print("[CLOSE] Closing application safely...")

    try:
        # Call the app's close method if it exists
        if app and hasattr(app, 'on_closing'):
            app.on_closing()
        else:
            # Fallback: just destroy the app
            if app:
                app.quit()
                app.destroy()
    except Exception as e:
        print(f"[ERROR] Error during close: {e}")
        force_exit()


def custom_tk_error_handler(exc, val, tb):
    """Custom error handler for Tkinter exceptions"""
    global app, is_closing

    print(f"[ERROR] Unhandled exception: {exc.__name__}: {val}")
    print("".join(traceback.format_exception(exc, val, tb)))

    # Prevent recursive closing
    if is_closing:
        print("[ERROR] Already closing, forcing exit...")
        force_exit()
        return

    is_closing = True

    try:
        if app is not None:
            # Check if app window still exists
            try:
                if app.winfo_exists():
                    print("[ERROR] Attempting graceful shutdown...")
                    app.quit()
                    app.destroy()
                else:
                    print("[ERROR] App window already destroyed, forcing exit...")
                    force_exit()
            except:
                print("[ERROR] Cannot check app status, forcing exit...")
                force_exit()
        else:
            print("[ERROR] App not initialized, forcing exit...")
            force_exit()
    except Exception as cleanup_error:
        print(f"[ERROR] Error during cleanup: {cleanup_error}")
        force_exit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Application interrupted by user.")
        force_exit()
    except SystemExit:
        pass
    except Exception as e:
        print(f"[ERROR] Fatal error: {e}")
        traceback.print_exc()
        force_exit()