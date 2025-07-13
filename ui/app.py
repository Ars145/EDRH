"""
Main application class for Elite Dangerous Records Helper.
Coordinates between services, components, and screens.
"""

import os
import sys
import threading
import time
import customtkinter as ctk
from typing import Dict, Any, Optional, List

# Constants
APP_TITLE = "EDRH - Elite Dangerous Records Helper"
APP_VERSION = "v1.4.0"
MAIN_BG_COLOR = "#0a0a0a"
CARD_BG_COLOR = "#141414"
SECONDARY_BG_COLOR = "#1f1f1f"
TERTIARY_BG_COLOR = "#2a2a2a"
ACCENT_COLOR = "#FF7F50"
ACCENT_HOVER = "#FF9068"
ACCENT_GRADIENT_START = "#FF7F50"
ACCENT_GRADIENT_END = "#FF5722"
SUCCESS_COLOR = "#4ECDC4"
SUCCESS_HOVER = "#5ED4CC"
DANGER_COLOR = "#E74C3C"
DANGER_HOVER = "#EC5F4F"
WARNING_COLOR = "#F39C12"
INFO_COLOR = "#3498DB"
TEXT_COLOR = "#FFFFFF"
TEXT_SECONDARY = "#B0B0B0"
TEXT_MUTED = "#808080"
BORDER_COLOR = "#2a2a2a"


class App(ctk.CTk):
    """Main application class for Elite Dangerous Records Helper"""

    def destroy(self):
        """Override destroy to handle early exit gracefully."""
        if not hasattr(self, '_app_initialized') or not self._app_initialized:
            try:
                super().destroy()
            except:
                pass
            os._exit(0)
        else:
            self.on_closing()

    def __init__(self):
        """Initialize the application."""
        super().__init__()

        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Initialize variables
        self.current_system = None
        self.current_journal = None
        self.cmdr_name = "Unknown"
        self.is_admin = False
        self._stop_event = threading.Event()
        self._app_initialized = False
        self._is_shutting_down = False

        # Set window properties
        self.title(f"{APP_TITLE} {APP_VERSION}")
        self.geometry("1280x720")
        self.minsize(1024, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Set icon if available
        icon_path = os.path.join(self._get_base_dir(), "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # Initialize services and managers
        self._initialize_services()

        # Show splash screen and initialize UI
        self._show_splash_screen()

    def _get_base_dir(self) -> str:
        """Get the base directory of the application.

        Returns:
            str: The base directory path.
        """
        if getattr(sys, 'frozen', False):
            return os.path.dirname(os.path.abspath(sys.executable))
        else:
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _initialize_services(self):
        """Initialize services and managers."""
        # Import services and managers
        from core.config_manager import ConfigManager
        from core.journal_manager import JournalManager
        from core.commander_manager import CommanderManager
        from data.database import DatabaseService
        from data.repositories import SystemRepository, CommanderRepository, CategoryRepository
        from services.image_service import ImageService
        from services.category_service import CategoryService
        from services.security_service import SecurityService

        # Initialize configuration manager
        self.config_manager = ConfigManager()

        # Initialize database service
        self.database_service = DatabaseService(self.config_manager)

        # Initialize repositories
        self.system_repository = SystemRepository(self.database_service)
        self.commander_repository = CommanderRepository(self.database_service)
        self.category_repository = CategoryRepository(self.database_service)

        # Initialize services
        self.image_service = ImageService(self.config_manager, self.database_service)
        self.category_service = CategoryService(self.config_manager, self.category_repository)

        # Initialize journal and commander managers
        self.commander_manager = CommanderManager(self.config_manager, self.database_service)
        self.journal_manager = JournalManager(self.config_manager, self._on_journal_event)

        # Initialize security service
        self.security_service = SecurityService(
            self.config_manager,
            self.database_service,
            self.commander_manager
        )

    def _show_splash_screen(self):
        """Show the splash screen and initialize the application."""
        # Import splash screen
        from ui.screens.splash_screen import SplashScreen

        # Create and show splash screen
        self.splash = SplashScreen(self)
        self.splash.start_loading_animation()

        # Schedule initialization after splash screen
        self.after(1000, self._initialize_app)

    def _initialize_app(self):
        """Initialize the application after splash screen."""
        # Auto-setup journals
        self._auto_setup_journals()

        # Initialize UI
        self._initialize_ui()

        # Start services
        self._start_services()

        # Close splash screen
        if hasattr(self, 'splash') and self.splash:
            self.splash.close_splash()
            self.splash = None

        # Mark application as initialized
        self._app_initialized = True

    def _auto_setup_journals(self):
        """Auto-setup journal folder and verify commander."""
        # Check if journal path is already set and verified
        if self.config_manager.get("journal_verified", False):
            return

        # Import journal confirmation dialog
        from ui.screens.journal_confirmation_dialog import JournalConfirmationDialog

        # Auto-detect journal folder
        journal_path = self._auto_detect_journal_folder()
        if journal_path:
            # Analyze journal folder
            analysis_data = self._analyze_journal_folder(journal_path)
            if analysis_data:
                # Show confirmation dialog
                dialog = JournalConfirmationDialog(self, analysis_data)
                self.wait_window(dialog)

                # If confirmed, save journal path and mark as verified
                if dialog.result:
                    self.config_manager.set("journal_path", journal_path)
                    self.config_manager.set("journal_verified", True)
                    self.cmdr_name = dialog.get_primary_commander()
                    self.config_manager.set("commander_name", self.cmdr_name)
                else:
                    # If not confirmed, ask for journal folder
                    self._ask_for_journal_folder()
            else:
                # If analysis failed, ask for journal folder
                self._ask_for_journal_folder()
        else:
            # If auto-detection failed, ask for journal folder
            self._ask_for_journal_folder()

    def _auto_detect_journal_folder(self) -> Optional[str]:
        """Auto-detect the Elite Dangerous journal folder.

        Returns:
            Optional[str]: The journal folder path, or None if not found.
        """
        # Common journal folder paths
        common_paths = [
            os.path.expanduser("~\\Saved Games\\Frontier Developments\\Elite Dangerous"),
            "C:\\Users\\%USERNAME%\\Saved Games\\Frontier Developments\\Elite Dangerous",
            "D:\\Users\\%USERNAME%\\Saved Games\\Frontier Developments\\Elite Dangerous"
        ]

        # Try common paths
        for path in common_paths:
            path = os.path.expandvars(path)
            if os.path.exists(path):
                # Check if path contains journal files
                for filename in os.listdir(path):
                    if filename.startswith("Journal.") and filename.endswith(".log"):
                        return path

        return None

    def _analyze_journal_folder(self, folder_path: str) -> Optional[Dict[str, Any]]:
        """Analyze the journal folder to find commanders.

        Args:
            folder_path (str): The journal folder path.

        Returns:
            Optional[Dict[str, Any]]: Analysis data, or None if failed.
        """
        if not os.path.exists(folder_path):
            return None

        # Find journal files
        journal_files = []
        for filename in os.listdir(folder_path):
            if filename.startswith("Journal.") and filename.endswith(".log"):
                journal_files.append(os.path.join(folder_path, filename))

        if not journal_files:
            return None

        # Extract commander names from journal files
        commanders = {}
        for journal_file in journal_files:
            try:
                with open(journal_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            import json
                            event = json.loads(line)
                            if event.get("event") == "Commander" and "Name" in event:
                                cmdr_name = event["Name"]
                                if cmdr_name not in commanders:
                                    commanders[cmdr_name] = {"count": 0, "latest_file": None, "latest_time": 0}
                                commanders[cmdr_name]["count"] += 1

                                # Update latest file if newer
                                file_time = os.path.getmtime(journal_file)
                                if file_time > commanders[cmdr_name]["latest_time"]:
                                    commanders[cmdr_name]["latest_file"] = journal_file
                                    commanders[cmdr_name]["latest_time"] = file_time

                            elif event.get("event") == "LoadGame" and "Commander" in event:
                                cmdr_name = event["Commander"]
                                if cmdr_name not in commanders:
                                    commanders[cmdr_name] = {"count": 0, "latest_file": None, "latest_time": 0}
                                commanders[cmdr_name]["count"] += 1

                                # Update latest file if newer
                                file_time = os.path.getmtime(journal_file)
                                if file_time > commanders[cmdr_name]["latest_time"]:
                                    commanders[cmdr_name]["latest_file"] = journal_file
                                    commanders[cmdr_name]["latest_time"] = file_time
                        except:
                            continue
            except:
                continue

        if not commanders:
            return None

        # Determine primary commander (most occurrences or latest)
        primary_commander = max(commanders.items(), key=lambda x: (x[1]["count"], x[1]["latest_time"]))[0]

        return {
            "folder_path": folder_path,
            "commanders": commanders,
            "primary_commander": primary_commander
        }

    def _ask_for_journal_folder(self):
        """Ask the user to select the journal folder."""
        try:
            from tkinter import filedialog, messagebox
        except ImportError:
            # Fallback for Windows
            import tkinter
            filedialog = tkinter.filedialog
            messagebox = tkinter.messagebox

        while True:
            messagebox.showinfo(
                "Journal Folder Selection",
                "Please select your Elite Dangerous journal folder.\n\n"
                "This is usually located at:\n"
                "%USERPROFILE%\\Saved Games\\Frontier Developments\\Elite Dangerous"
            )

            try:
                folder_path = filedialog.askdirectory(
                    title="Select Elite Dangerous Journal Folder"
                )
            except Exception as e:
                print(f"[ERROR] Error in directory selection dialog: {e}")
                folder_path = ""

            if not folder_path:
                if messagebox.askyesno(
                    "Exit Application",
                    "Journal folder is required for the application to work.\n\n"
                    "Do you want to exit the application?"
                ):
                    self.destroy()
                    sys.exit(0)
                continue

            # Analyze selected folder
            analysis_data = self._analyze_journal_folder(folder_path)
            if analysis_data:
                # Import journal confirmation dialog
                from ui.screens.journal_confirmation_dialog import JournalConfirmationDialog

                # Show confirmation dialog
                dialog = JournalConfirmationDialog(self, analysis_data)
                self.wait_window(dialog)

                # If confirmed, save journal path and mark as verified
                if dialog.result:
                    self.config_manager.set("journal_path", folder_path)
                    self.config_manager.set("journal_verified", True)
                    self.cmdr_name = dialog.get_primary_commander()
                    self.config_manager.set("commander_name", self.cmdr_name)
                    break
            else:
                if messagebox.askyesno(
                    "No Journals Found",
                    "No journal files found in this folder.\n"
                    "Is this the correct folder?\n\n"
                    "It should contain files like:\n"
                    "Journal.2024-01-01T000000.01.log\n\n"
                    "Try another folder?"
                ):
                    continue
                else:
                    self.destroy()
                    sys.exit(0)

    def _initialize_ui(self):
        """Initialize the UI components."""
        # Import screens
        from ui.screens.main_screen import MainScreen

        # Create main screen
        self.main_screen = MainScreen(self)
        self.main_screen.pack(fill="both", expand=True)

        # Check admin status
        self._check_admin_status()

        # Update commander location in a background thread
        threading.Thread(target=self._update_commander_location_thread, daemon=True).start()

    def _start_services(self):
        """Start background services."""
        # Start journal monitoring
        self.journal_manager.start_monitoring()

    def _on_journal_event(self, event: Dict[str, Any]):
        """Handle journal events.

        Args:
            event (Dict[str, Any]): The journal event.
        """
        try:
            event_type = event.get("event", "Unknown")

            # Handle LoadGame event (commander login)
            if event_type == "LoadGame" and "Commander" in event:
                try:
                    cmdr_name = event["Commander"]

                    if cmdr_name != self.cmdr_name:
                        self.cmdr_name = cmdr_name
                        self.config_manager.set("commander_name", cmdr_name)
                        self.commander_manager.set_commander_name(cmdr_name)

                        # Verify commander security status
                        try:
                            self._verify_commander()
                        except Exception as e:
                            print(f"[ERROR] Error verifying commander: {e}")

                        # Update UI
                        if hasattr(self, 'main_screen'):
                            try:
                                self.main_screen.update_commander_info(cmdr_name)
                            except Exception as e:
                                print(f"[ERROR] Error updating commander info in UI: {e}")
                except Exception as e:
                    print(f"[ERROR] Error processing LoadGame event: {e}")

            # Handle system change events
            elif "StarSystem" in event and event_type in ["FSDJump", "Location", "ApproachBody", "LeaveBody", "Docked", "Undocked"]:
                try:
                    system_name = event["StarSystem"]

                    if system_name != self.current_system:
                        self.current_system = system_name

                        # Update UI
                        if hasattr(self, 'main_screen'):
                            try:
                                self.main_screen.update_current_system(system_name)
                            except Exception as e:
                                print(f"[ERROR] Error updating current system in UI: {e}")

                            # Check if system is visited
                            try:
                                system = self.system_repository.get_by_name(system_name)
                                if system and not system.visited:
                                    # Mark system as visited
                                    self.system_repository.mark_visited(system_name)
                            except Exception as e:
                                print(f"[ERROR] Error checking/marking system as visited: {e}")
                except Exception as e:
                    print(f"[ERROR] Error processing system change event: {e}")

        except Exception as e:
            print(f"[ERROR] Unhandled exception in journal event processing: {e}")
            import traceback
            traceback.print_exc()

    def _check_admin_status(self):
        """Check if the current commander has admin status."""
        if self.cmdr_name != "Unknown":
            self.is_admin = self.security_service.check_admin_status(self.cmdr_name)

            # Update UI
            if hasattr(self, 'main_screen'):
                self.main_screen.update_admin_status(self.is_admin)

    def _update_commander_location_thread(self):
        """Update the commander's current location in a background thread."""
        try:
            # Show loading status in the UI
            self.after(0, lambda: self._update_status("Loading commander location..."))

            # Find the latest journal file
            journal_path = self.config_manager.get("journal_path", "")
            if not journal_path or not os.path.exists(journal_path):
                self.after(0, lambda: self._update_status("Ready"))
                return

            # Get the latest journal file
            latest_journal = self.journal_manager.get_latest_journal_file()
            if not latest_journal:
                self.after(0, lambda: self._update_status("Ready"))
                return

            # Find the latest FSDJump event
            system_name = self._find_latest_system_in_journal(latest_journal)

            # Update UI on the main thread if a system was found
            if system_name:
                self.current_system = system_name
                self.after(0, self._update_ui_with_system)

            # Reset status
            self.after(0, lambda: self._update_status("Ready"))
        except Exception as e:
            print(f"[ERROR] Error updating commander location: {e}")
            self.after(0, lambda: self._update_status("Ready"))

    def _update_ui_with_system(self):
        """Update the UI with the current system (called on the main thread)."""
        if hasattr(self, 'main_screen') and self.current_system:
            self.main_screen.update_current_system(self.current_system)

    def _update_status(self, status_text):
        """Update the status text in the UI.

        Args:
            status_text (str): The status text to display.
        """
        if hasattr(self, 'main_screen'):
            self.main_screen.status_label.configure(text=status_text)

    def _find_latest_system_in_journal(self, journal_file):
        """Find the latest system in a journal file.

        Args:
            journal_file (str): Path to the journal file.

        Returns:
            str: The system name, or None if not found.
        """
        try:
            with open(journal_file, 'r', encoding='utf-8') as f:
                # Start from the end of the file
                f.seek(0, os.SEEK_END)
                file_size = f.tell()

                # Read the file backwards in chunks
                chunk_size = 4096
                position = max(file_size - chunk_size, 0)

                while position >= 0:
                    f.seek(position)
                    chunk = f.read(min(chunk_size, file_size - position))

                    # Split chunk into lines
                    lines = chunk.split('\n')

                    # Process lines in reverse order
                    for line in reversed(lines):
                        if not line.strip():
                            continue

                        try:
                            import json
                            event = json.loads(line)
                            # Check for various event types that indicate current system
                            if "StarSystem" in event:
                                if event.get("event") in ["FSDJump", "Location", "ApproachBody", "LeaveBody", "Docked", "Undocked"]:
                                    return event["StarSystem"]
                        except:
                            continue

                    # Move to the previous chunk
                    position = max(position - chunk_size, 0)

                    # If we've reached the beginning of the file, break
                    if position == 0:
                        break

            return None
        except Exception as e:
            print(f"[ERROR] Error reading journal file: {e}")
            return None

    def _update_commander_location(self):
        """Update the commander's current location (legacy method, use _update_commander_location_thread instead)."""
        threading.Thread(target=self._update_commander_location_thread, daemon=True).start()

    def _verify_commander(self):
        """Verify the commander's security status."""
        if self.cmdr_name == "Unknown":
            return

        # Show status
        self.after(0, lambda: self._update_status("Verifying commander..."))

        # Start verification in a background thread
        threading.Thread(target=self._verify_commander_thread, daemon=True).start()

    def _verify_commander_thread(self):
        """Verify the commander's security status in a background thread."""
        try:
            # Verify commander
            result = self.security_service.verify_commander(
                self.cmdr_name,
                self.config_manager.get("journal_path", "")
            )

            # Handle verification result on the main thread
            if result["status"] == "blocked":
                self.after(0, lambda: self._show_blocked_message(result["message"]))
            else:
                self.after(0, lambda: self._update_status("Ready"))
        except Exception as e:
            print(f"[ERROR] Error verifying commander: {e}")
            self.after(0, lambda: self._update_status("Ready"))

    def _show_blocked_message(self, message):
        """Show a blocked message and exit the application.

        Args:
            message (str): The message to display.
        """
        from tkinter import messagebox
        messagebox.showerror("Access Denied", message)
        self.destroy()
        sys.exit(1)

    def on_closing(self):
        """Handle application closing."""
        try:
            # Set flag to indicate we're shutting down
            self._is_shutting_down = True

            # Stop journal monitoring
            self.journal_manager.stop_monitoring()

            # Set stop event
            self._stop_event.set()

            # Wait for threads to finish
            time.sleep(0.5)

            # Unbind all event handlers
            try:
                def unbind_all(widget):
                    try:
                        for sequence in widget.bind():
                            try:
                                widget.unbind(sequence)
                            except:
                                pass
                        for child in widget.winfo_children():
                            unbind_all(child)
                    except:
                        pass

                unbind_all(self)
            except:
                pass

            # Hide window during cleanup
            self.withdraw()
            self.update_idletasks()

            # Cancel all scheduled "after" callbacks
            try:
                while True:
                    after_ids = self.tk.call('after', 'info')
                    if not after_ids:
                        break
                    for after_id in after_ids:
                        try:
                            self.after_cancel(after_id)
                        except:
                            pass
            except:
                pass

            # Close instance lock if it exists
            if hasattr(self, '_instance_lock') and self._instance_lock:
                try:
                    if sys.platform == 'win32':
                        import ctypes
                        ctypes.windll.kernel32.CloseHandle(self._instance_lock)
                except:
                    pass

            # Destroy all child widgets
            def destroy_children(widget):
                children = list(widget.winfo_children())
                for child in children:
                    destroy_children(child)
                    try:
                        child.destroy()
                    except:
                        pass

            destroy_children(self)

            # Quit the application
            try:
                self.quit()
            except:
                pass
        except Exception as e:
            print(f"[ERROR] Error during application shutdown: {e}")
        finally:
            # Force exit to ensure all resources are released
            os._exit(0)
