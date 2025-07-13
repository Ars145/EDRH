"""
Splash screen for Elite Dangerous Records Helper.
Displays a loading animation while the application initializes.
"""

import os
import time
import threading
import customtkinter as ctk

# Try to import PIL, with fallback
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    print("[WARNING] PIL not available, using text-based logo")
    HAS_PIL = False


try:
    SplashBaseClass = ctk.CTkToplevel
except AttributeError:
    # Fallback for older versions of customtkinter
    print("[WARNING] CTkToplevel not available, using Toplevel")
    import tkinter as tk
    SplashBaseClass = tk.Toplevel

class SplashScreen(SplashBaseClass):
    """Splash screen with loading animation."""

    def __init__(self, parent):
        """Initialize the splash screen.

        Args:
            parent: The parent window.
        """
        super().__init__(parent)

        # Set window properties
        self.title("")
        self.geometry("600x400")
        self.resizable(False, False)

        # Remove window decorations
        self.overrideredirect(True)

        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Set as topmost window
        self.attributes("-topmost", True)

        # Set background color
        try:
            self.configure(fg_color="#0a0a0a")
        except (AttributeError, TypeError):
            # Fallback for older versions of tkinter
            try:
                self.configure(background="#0a0a0a")
            except:
                pass

        # Create main frame
        try:
            self.main_frame = ctk.CTkFrame(self, fg_color="#0a0a0a", corner_radius=0)
        except (AttributeError, TypeError):
            # Fallback for older versions of customtkinter
            import tkinter as tk
            self.main_frame = tk.Frame(self, background="#0a0a0a")
        self.main_frame.pack(fill="both", expand=True)

        # Load logo if PIL is available and logo exists
        if HAS_PIL:
            logo_path = os.path.join(self._get_base_dir(), "resources", "images", "logo.png")
            if os.path.exists(logo_path):
                try:
                    # Load and resize logo
                    logo_img = Image.open(logo_path)
                    # Use LANCZOS if available, otherwise fall back to ANTIALIAS
                    try:
                        resize_method = Image.LANCZOS
                    except AttributeError:
                        try:
                            resize_method = Image.ANTIALIAS
                        except AttributeError:
                            # If neither is available, use default
                            resize_method = Image.NEAREST
                    logo_img = logo_img.resize((300, 300), resize_method)
                    self.logo_photo = ImageTk.PhotoImage(logo_img)

                    # Create logo label
                    self.logo_label = ctk.CTkLabel(self.main_frame, image=self.logo_photo, text="")
                    self.logo_label.pack(pady=(50, 20))
                except Exception as e:
                    print(f"[ERROR] Error loading logo: {e}")
                    self._create_text_logo()
            else:
                self._create_text_logo()
        else:
            # Use text-based logo if PIL is not available
            self._create_text_logo()

        # Create title label
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Elite Dangerous Records Helper",
            font=("Segoe UI", 24, "bold"),
            text_color="#FF7F50"
        )
        self.title_label.pack(pady=(0, 10))

        # Create version label
        self.version_label = ctk.CTkLabel(
            self.main_frame,
            text="v1.4.0",
            font=("Segoe UI", 14),
            text_color="#B0B0B0"
        )
        self.version_label.pack(pady=(0, 20))

        # Create loading frame
        self.loading_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.loading_frame.pack(pady=(0, 10))

        # Create loading bar
        self.loading_bar = ctk.CTkProgressBar(
            self.loading_frame,
            width=300,
            height=15,
            corner_radius=7,
            fg_color="#1f1f1f",
            progress_color="#FF7F50"
        )
        self.loading_bar.pack(pady=(0, 5))
        self.loading_bar.set(0)

        # Create loading text
        self.loading_text = ctk.CTkLabel(
            self.loading_frame,
            text="Initializing...",
            font=("Segoe UI", 12),
            text_color="#B0B0B0"
        )
        self.loading_text.pack()

        # Initialize variables
        self.progress = 0
        self.loading_animation_active = False
        self.dots_animation_active = False
        self._stop_event = threading.Event()

        # Emergency close timer (in case something goes wrong)
        self.after(15000, self.emergency_close)

    def _get_base_dir(self) -> str:
        """Get the base directory of the application.

        Returns:
            str: The base directory path.
        """
        import sys
        if getattr(sys, 'frozen', False):
            return os.path.dirname(os.path.abspath(sys.executable))
        else:
            return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _create_text_logo(self):
        """Create a text-based logo when image is not available."""
        self.logo_label = ctk.CTkLabel(
            self.main_frame,
            text="EDRH",
            font=("Segoe UI", 72, "bold"),
            text_color="#FF7F50"
        )
        self.logo_label.pack(pady=(50, 20))

    def start_loading_animation(self):
        """Start the loading animation."""
        if not self.loading_animation_active:
            self.loading_animation_active = True
            self.animate_loading()

        if not self.dots_animation_active:
            self.dots_animation_active = True
            self.animate_dots()

    def animate_loading(self):
        """Animate the loading bar."""
        if self._stop_event.is_set() or not self.loading_animation_active:
            return

        def update_progress():
            """Update the progress bar."""
            if self._stop_event.is_set() or not self.loading_animation_active:
                return

            # Increment progress
            self.progress += 0.01
            if self.progress >= 1:
                self.progress = 0

            # Update progress bar
            self.loading_bar.set(self.progress)

            # Schedule next update
            if not self._stop_event.is_set() and self.loading_animation_active:
                self.after(30, update_progress)

        # Start progress updates
        update_progress()

    def animate_dots(self):
        """Animate the loading text dots."""
        if self._stop_event.is_set() or not self.dots_animation_active:
            return

        # Cycle through different dot patterns
        dots = ["", ".", "..", "..."]
        self.dot_index = getattr(self, 'dot_index', 0)

        # Update text with current dot pattern
        self.loading_text.configure(text=f"Initializing{dots[self.dot_index]}")

        # Increment dot index
        self.dot_index = (self.dot_index + 1) % len(dots)

        # Schedule next update
        if not self._stop_event.is_set() and self.dots_animation_active:
            self.after(300, self.animate_dots)

    def close_splash(self):
        """Close the splash screen."""
        self.loading_animation_active = False
        self.dots_animation_active = False
        self._stop_event.set()
        self.destroy()

    def emergency_close(self):
        """Emergency close if the application takes too long to initialize."""
        if self.winfo_exists():
            print("Emergency closing splash screen after timeout")
            self.close_splash()
