"""
Splash screen for EDRH
"""

import os
import time
import threading
import customtkinter as ctk
from PIL import Image
from config.settings import resource

# Constants
SPLASH_WIDTH = 600
SPLASH_HEIGHT = 400
SPLASH_BG_COLOR = "#1A1A1A"
SPLASH_TEXT_COLOR = "#FFFFFF"
SPLASH_ACCENT_COLOR = "#3498db"

class SplashScreen(ctk.CTkToplevel):
    """
    Splash screen shown during application startup
    """
    def __init__(self):
        """Initialize the splash screen"""
        super().__init__()
        
        # Configure window
        self.title("Elite Dangerous Records Helper")
        self.geometry(f"{SPLASH_WIDTH}x{SPLASH_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=SPLASH_BG_COLOR)
        self.attributes("-topmost", True)
        
        # Remove window decorations
        self.overrideredirect(True)
        
        # Center on screen
        self.center_window()
        
        # Setup UI
        self.setup_ui()
        
        # Start loading animation
        self.start_loading_animation()
        
        # Emergency close timer (in case something goes wrong)
        self.after(30000, self.emergency_close)
        
    def setup_ui(self):
        """Setup the splash screen UI"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Logo
        try:
            logo_path = resource("logo.png")
            if os.path.exists(logo_path):
                logo_image = ctk.CTkImage(
                    light_image=Image.open(logo_path),
                    dark_image=Image.open(logo_path),
                    size=(300, 150)
                )
                logo_label = ctk.CTkLabel(self.main_frame, image=logo_image, text="")
                logo_label.pack(pady=(40, 20))
            else:
                # Fallback if logo not found
                title_label = ctk.CTkLabel(
                    self.main_frame,
                    text="Elite Dangerous\nRecords Helper",
                    font=ctk.CTkFont(size=32, weight="bold"),
                    text_color=SPLASH_TEXT_COLOR
                )
                title_label.pack(pady=(40, 20))
        except Exception as e:
            print(f"Error loading logo: {e}")
            # Fallback if logo loading fails
            title_label = ctk.CTkLabel(
                self.main_frame,
                text="Elite Dangerous\nRecords Helper",
                font=ctk.CTkFont(size=32, weight="bold"),
                text_color=SPLASH_TEXT_COLOR
            )
            title_label.pack(pady=(40, 20))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Starting up...",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=SPLASH_ACCENT_COLOR
        )
        self.status_label.pack(pady=(30, 5))
        
        # Detail label
        self.detail_label = ctk.CTkLabel(
            self.main_frame,
            text="Initializing...",
            font=ctk.CTkFont(size=14),
            text_color=SPLASH_TEXT_COLOR
        )
        self.detail_label.pack(pady=(0, 30))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            width=400,
            height=15,
            corner_radius=5,
            fg_color="#333333",
            progress_color=SPLASH_ACCENT_COLOR
        )
        self.progress_bar.pack(pady=(10, 5))
        self.progress_bar.set(0)
        
        # Loading dots
        self.loading_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color=SPLASH_TEXT_COLOR
        )
        self.loading_label.pack(pady=(5, 0))
        
        # Version label
        version_text = "v1.0.0"  # This should be imported from a central version file
        version_label = ctk.CTkLabel(
            self.main_frame,
            text=version_text,
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        version_label.pack(side="bottom", pady=(0, 10))
        
    def center_window(self):
        """Center the window on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def start_loading_animation(self):
        """Start the loading animation"""
        self.loading_progress = 0
        self.animate_loading()
        self.animate_dots()
        
    def animate_loading(self):
        """Animate the progress bar"""
        def update_progress():
            # Simulate loading progress
            if self.loading_progress < 0.95:
                # Gradually increase progress
                if self.loading_progress < 0.3:
                    increment = 0.01
                elif self.loading_progress < 0.6:
                    increment = 0.005
                else:
                    increment = 0.002
                    
                self.loading_progress += increment
                self.progress_bar.set(self.loading_progress)
                
                # Schedule next update
                self.after(50, update_progress)
            else:
                # Hold at 95% until explicitly completed
                self.progress_bar.set(0.95)
                
        # Start progress updates
        self.after(100, update_progress)
        
    def animate_dots(self):
        """Animate the loading dots"""
        dots = ["", ".", "..", "..."]
        dot_index = 0
        
        def update_dots():
            nonlocal dot_index
            self.loading_label.configure(text=f"Loading{dots[dot_index]}")
            dot_index = (dot_index + 1) % len(dots)
            self.after(500, update_dots)
            
        update_dots()
        
    def close_splash(self):
        """Close the splash screen"""
        self.progress_bar.set(1.0)
        self.after(500, self.destroy)
        
    def emergency_close(self):
        """Emergency close if splash screen is stuck"""
        print("Emergency closing splash screen after timeout")
        try:
            self.destroy()
        except:
            pass