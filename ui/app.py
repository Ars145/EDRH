"""
Main application window for EDRH
"""

import os
import sys
import time
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

from config.settings import resource, load_config, save_config, _cfg
from models.system import get_system_manager
from models.commander import get_commander_manager
from services.journal_monitor import JournalMonitor, auto_detect_journal_folder, analyze_journal_folder
from services.image_service import load_image, set_supabase_client
from services.supabase_client import init_supabase
from utils.background_task import init_task_queue, add_task
from ui.splash import SplashScreen

# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
APP_TITLE = "Elite Dangerous Records Helper"
VERSION_TEXT = "v1.0.0"  # This should be imported from a central version file

# Colors
MAIN_BG_COLOR = "#1A1A1A"
SECONDARY_BG_COLOR = "#222222"
TERTIARY_BG_COLOR = "#2A2A2A"
CARD_BG_COLOR = "#333333"
BORDER_COLOR = "#444444"
ACCENT_COLOR = "#3498db"
ACCENT_HOVER = "#2980b9"
SUCCESS_COLOR = "#2ecc71"
WARNING_COLOR = "#f39c12"
DANGER_COLOR = "#e74c3c"
TEXT_COLOR = "#FFFFFF"
TEXT_MUTED = "#AAAAAA"

class App(ctk.CTk):
    """
    Main application window
    """
    def __init__(self):
        """Initialize the application"""
        super().__init__()
        
        # Initialize splash screen
        self.splash = SplashScreen()
        self.withdraw()
        
        # Initialize state
        self._app_initialized = False
        self._is_destroying = False
        self.config_data = _cfg
        self.cmdr_name = self.config_data.get("commander_name", "Unknown")
        self.system_name = "Unknown"
        self.latest_starpos = None
        self.current_coords = None
        self.stop_event = threading.Event()
        self.map_window = None
        self.is_admin = False  # This should be determined by security checks
        self.last_update_time = 0
        self.update_cooldown = 1.0
        self._update_in_progress = False
        self.session_start_time = time.time()
        self.jump_count = 0
        
        # Check if journal path is verified
        if not _cfg.get("journal_verified"):
            self.after(2000, self.auto_setup_journals)
        else:
            self.after(2000, self.finish_splash_and_start)
            
    def destroy(self):
        """Override destroy to handle early exit gracefully"""
        if not hasattr(self, '_app_initialized') or not self._app_initialized:
            try:
                super().destroy()
            except:
                pass
            os._exit(0)
        else:
            self.on_closing()
            
    def finish_splash_and_start(self):
        """Complete splash screen and start main app without confirmation"""
        print("[STARTUP] Existing setup verified, starting main app...")
        if self.splash:
            self.splash.destroy()
            self.splash = None
            
        self.deiconify()
        self.initialize_app()
        
    def auto_setup_journals(self):
        """Auto-detect and setup journal folder"""
        try:
            if self.splash:
                self.splash.status_label.configure(text="Detecting Elite Dangerous folder...")
                self.splash.detail_label.configure(text="Scanning common locations")
                
            detected_path = auto_detect_journal_folder()
            
            if detected_path:
                if self.splash:
                    self.splash.status_label.configure(text="Journal folder detected!")
                    self.splash.detail_label.configure(text="Analyzing commander data...")
                    
                analysis = analyze_journal_folder(detected_path)
                
                if analysis and analysis.get("commanders"):
                    if self.splash:
                        self.splash.status_label.configure(text="Analysis complete!")
                        self.splash.detail_label.configure(text="Ready to confirm setup")
                        
                    self.after(1500, lambda: self.show_detection_dialog(analysis))
                else:
                    if self.splash:
                        self.splash.status_label.configure(text="Analysis failed")
                        self.splash.detail_label.configure(text="Please select folder manually")
                        
                    self.after(1000, self.ask_for_journal_folder_with_splash)
            else:
                if self.splash:
                    self.splash.status_label.configure(text="Manual selection required")
                    self.splash.detail_label.configure(text="Please select your journal folder")
                    
                self.after(1000, self.ask_for_journal_folder_with_splash)
                
        except Exception as e:
            print(f"Error in auto-setup: {e}")
            self.after(1000, self.ask_for_journal_folder_with_splash)
            
    def show_detection_dialog(self, analysis_data):
        """Show the journal detection confirmation dialog"""
        if self.splash:
            self.splash.destroy()
            self.splash = None
            
        self.deiconify()
        
        # This would normally show a dialog to confirm the detected journal folder
        # For simplicity, we'll just accept it automatically
        _cfg["journal_path"] = analysis_data["folder_path"]
        _cfg["journal_verified"] = True
        save_config(_cfg)
        self.initialize_app()
        
    def ask_for_journal_folder_with_splash(self):
        """Ask for journal folder with splash screen handling"""
        if self.splash:
            self.splash.destroy()
            self.splash = None
            
        self.deiconify()
        self.ask_for_journal_folder()
        
    def ask_for_journal_folder(self):
        """Ask the user to select the journal folder"""
        while True:
            folder_path = filedialog.askdirectory(
                title="Select Elite Dangerous Journal Folder",
                mustexist=True
            )
            
            if not folder_path:
                if messagebox.askyesno("Exit Application", 
                                      "No journal folder selected. Exit application?"):
                    os._exit(0)
                continue
                
            # Check if folder contains journal files
            journal_files = [f for f in os.listdir(folder_path) 
                           if f.startswith("Journal.") and f.endswith(".log")]
                           
            if journal_files:
                _cfg["journal_path"] = folder_path
                _cfg["journal_verified"] = True
                save_config(_cfg)
                self.initialize_app()
                break
            else:
                if messagebox.askyesno("No Journals Found",
                                      "No journal files found in this folder.\n"
                                      "Is this the correct folder?\n\n"
                                      "It should contain files like:\n"
                                      "Journal.2024-01-01T000000.01.log\n\n"
                                      "Try another folder?"):
                    continue
                else:
                    os._exit(0)
                    
    def initialize_app(self):
        """Initialize the main application"""
        print("[STARTUP] Initializing main application...")
        
        self.deiconify()
        self.lift()
        self.focus_force()
        
        # Configure window
        self.title(APP_TITLE)
        try: 
            self.iconbitmap(resource("icon.ico"))
        except: 
            pass
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=MAIN_BG_COLOR)
        self.attributes("-topmost", False)
        
        # Initialize task queue
        init_task_queue(max_workers=3, root=self)
        
        # Initialize Supabase client (placeholder - would need actual URL and key)
        # init_supabase("https://your-supabase-url.supabase.co", "your-supabase-key")
        
        # Create tab view
        self.tabview = ctk.CTkTabview(
            self, 
            width=WINDOW_WIDTH-20, 
            height=WINDOW_HEIGHT-40,
            fg_color=CARD_BG_COLOR,
            segmented_button_fg_color=SECONDARY_BG_COLOR,
            segmented_button_selected_color=ACCENT_COLOR,
            segmented_button_selected_hover_color=ACCENT_HOVER,
            segmented_button_unselected_color=TERTIARY_BG_COLOR,
            segmented_button_unselected_hover_color="#363636",
            text_color=TEXT_COLOR,
            corner_radius=15,
            border_width=2,
            border_color=BORDER_COLOR
        )
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Create tabs
        self.main_tab = self.tabview.add("Main")
        self.galaxy_tab = self.tabview.add("Galaxy Map")
        
        # Setup tabs
        self.setup_main_tab()
        self.setup_galaxy_tab()
        
        # Add version label
        version_frame = ctk.CTkFrame(self, fg_color=SECONDARY_BG_COLOR, corner_radius=6)
        version_frame.place(relx=0.98, rely=0.98, anchor="se")
        ctk.CTkLabel(
            version_frame, 
            text=VERSION_TEXT,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_MUTED,
            fg_color=SECONDARY_BG_COLOR
        ).pack(padx=10, pady=4)
        
        # Start journal monitoring
        self._app_initialized = True
        self.after(100, self.start_monitoring)
        
    def setup_main_tab(self):
        """Setup the main tab"""
        # Header frame
        header_frame = ctk.CTkFrame(self.main_tab, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Commander and system info
        info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_frame.pack(side="left", padx=10, pady=10)
        
        self.cmdr_label = ctk.CTkLabel(
            info_frame, 
            text=f"CMDR: {self.cmdr_name}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_COLOR
        )
        self.cmdr_label.pack(anchor="w")
        
        self.system_label = ctk.CTkLabel(
            info_frame, 
            text=self.system_name,
            font=ctk.CTkFont(size=14),
            text_color=TEXT_MUTED
        )
        self.system_label.pack(anchor="w")
        
        # Refresh button
        self.btn_refresh = ctk.CTkButton(
            header_frame,
            text="↻ Refresh",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=SECONDARY_BG_COLOR,
            hover_color=TERTIARY_BG_COLOR,
            text_color=TEXT_COLOR,
            corner_radius=8,
            command=self.refresh_all_data
        )
        self.btn_refresh.pack(side="right", padx=10, pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(self.main_tab, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left panel (nearest systems)
        left_panel = ctk.CTkFrame(content_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=0)
        
        # Nearest systems header
        nearest_header = ctk.CTkFrame(left_panel, fg_color=TERTIARY_BG_COLOR, corner_radius=5)
        nearest_header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            nearest_header,
            text="Nearest Systems",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_COLOR
        ).pack(side="left", padx=10, pady=5)
        
        # Nearest systems scroll area
        self.nearest_scroll = ctk.CTkScrollableFrame(
            left_panel,
            fg_color="transparent",
            corner_radius=0
        )
        self.nearest_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Right panel (controls)
        right_panel = ctk.CTkFrame(content_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10, width=250)
        right_panel.pack(side="right", fill="y", padx=(5, 0), pady=0)
        right_panel.pack_propagate(False)
        
        # Controls header
        controls_header = ctk.CTkFrame(right_panel, fg_color=TERTIARY_BG_COLOR, corner_radius=5)
        controls_header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            controls_header,
            text="Controls",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_COLOR
        ).pack(side="left", padx=10, pady=5)
        
        # Control buttons
        controls_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        controls_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # View closest button
        ctk.CTkButton(
            controls_frame,
            text="View Closest",
            font=ctk.CTkFont(size=14),
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            corner_radius=8,
            command=self.view_closest
        ).pack(fill="x", padx=10, pady=5)
        
        # Claim closest button
        ctk.CTkButton(
            controls_frame,
            text="Claim Closest",
            font=ctk.CTkFont(size=14),
            fg_color=SUCCESS_COLOR,
            hover_color="#27ae60",
            text_color="#000000",
            corner_radius=8,
            command=self.claim_closest
        ).pack(fill="x", padx=10, pady=5)
        
        # Open map button
        ctk.CTkButton(
            controls_frame,
            text="Open Galaxy Map",
            font=ctk.CTkFont(size=14),
            fg_color=TERTIARY_BG_COLOR,
            hover_color="#363636",
            corner_radius=8,
            command=self.open_map
        ).pack(fill="x", padx=10, pady=5)
        
    def setup_galaxy_tab(self):
        """Setup the galaxy map tab"""
        # Placeholder for galaxy map
        map_frame = ctk.CTkFrame(self.galaxy_tab, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
        map_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            map_frame,
            text="Galaxy Map will be displayed here",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_COLOR
        ).pack(expand=True, pady=100)
        
        # Open map button
        ctk.CTkButton(
            map_frame,
            text="Open Galaxy Map",
            font=ctk.CTkFont(size=16),
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            corner_radius=8,
            command=self.open_map
        ).pack(pady=20)
        
    def refresh_all_data(self):
        """Refresh all data"""
        try:
            # Reset display limit
            self.nearest_display_limit = 5
            
            # Reset scroll position
            if hasattr(self, 'nearest_scroll') and hasattr(self.nearest_scroll, '_parent_canvas'):
                self.nearest_scroll._parent_canvas.yview_moveto(0)
                
            # Update system info from journal
            if hasattr(self, 'current_journal_path') and self.current_journal_path:
                # This would normally call find_latest_journal_and_pos
                # For simplicity, we'll just update the UI
                self.system_label.configure(text=self.system_name)
                
            # Update nearest systems
            self.update_nearest_systems()
            
            # Update commander location
            if self.current_coords:
                self.update_commander_location()
                
            # Update map window if open
            if self.map_window and hasattr(self.map_window, 'winfo_exists'):
                try:
                    if self.map_window.winfo_exists():
                        # This would normally call refresh_all_filters
                        pass
                except:
                    pass
                    
            # Update refresh button
            self.btn_refresh.configure(text="✓ Refreshed", fg_color=SUCCESS_COLOR, text_color="#000000")
            self.after(1500, lambda: self.btn_refresh.configure(
                text="↻ Refresh",
                fg_color=SECONDARY_BG_COLOR,
                text_color=TEXT_COLOR
            ))
            
        except Exception as e:
            print(f"Error refreshing data: {e}")
            self.btn_refresh.configure(text="❌ Error", fg_color=DANGER_COLOR)
            self.after(2000, lambda: self.btn_refresh.configure(
                text="↻ Refresh",
                fg_color=SECONDARY_BG_COLOR,
                text_color=TEXT_COLOR
            ))
            
    def update_nearest_systems(self):
        """Update the nearest systems display"""
        # This would normally query the database for nearest systems
        # For simplicity, we'll just show a placeholder
        
        # Clear existing systems
        for widget in self.nearest_scroll.winfo_children():
            widget.destroy()
            
        # Add placeholder systems
        for i in range(5):
            self._create_system_card({
                "name": f"System {i+1}",
                "category": "Example Category",
                "distance": (i+1) * 10.5
            })
            
    def _create_system_card(self, system_data):
        """Create a system card"""
        # Create card frame
        card = ctk.CTkFrame(
            self.nearest_scroll,
            fg_color=CARD_BG_COLOR,
            corner_radius=10,
            border_width=1,
            border_color=BORDER_COLOR,
            height=96
        )
        card.pack(fill="x", padx=5, pady=5)
        card.pack_propagate(False)
        
        # Store data for reference
        card._data = system_data
        
        # Create canvas for background
        card._canvas = ctk.CTkCanvas(
            card,
            highlightthickness=0,
            bg=CARD_BG_COLOR
        )
        card._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Add system name
        name_id = card._canvas.create_text(
            15, 25,
            text=system_data['name'],
            font=("Arial", 18, "bold"),
            fill="white",
            anchor="w",
            tags=("system_name", "clickable", "text")
        )
        
        # Add category
        card._canvas.create_text(
            15, 50,
            text=system_data['category'],
            font=("Arial", 11),
            fill="#DDDDDD",
            anchor="w",
            tags="text"
        )
        
        # Add distance
        card._canvas.create_text(
            15, 75,
            text=f"{system_data['distance']:.1f} ly",
            font=("Arial", 10),
            fill="#BBBBBB",
            anchor="w",
            tags="text"
        )
        
        # Add view button
        view_btn = ctk.CTkButton(
            card,
            text="View",
            font=ctk.CTkFont(size=12),
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            corner_radius=5,
            width=60,
            height=25,
            command=lambda: self.view_system(system_data['name'], system_data['category'])
        )
        view_btn.place(relx=0.9, rely=0.3, anchor="e")
        
        # Add claim button
        claim_btn = ctk.CTkButton(
            card,
            text="Claim",
            font=ctk.CTkFont(size=12),
            fg_color=SUCCESS_COLOR,
            hover_color="#27ae60",
            text_color="#000000",
            corner_radius=5,
            width=60,
            height=25,
            command=lambda: self.claim_system(system_data['name'])
        )
        claim_btn.place(relx=0.9, rely=0.7, anchor="e")
        
        return card
        
    def view_system(self, system_name, category):
        """View a system"""
        print(f"Viewing system: {system_name} (Category: {category})")
        messagebox.showinfo("View System", f"Viewing system: {system_name}\nCategory: {category}")
        
    def claim_system(self, system_name):
        """Claim a system"""
        print(f"Claiming system: {system_name}")
        messagebox.showinfo("Claim System", f"System {system_name} claimed!")
        
    def view_closest(self):
        """View the closest system"""
        print("Viewing closest system")
        messagebox.showinfo("View Closest", "Viewing closest system")
        
    def claim_closest(self):
        """Claim the closest system"""
        print("Claiming closest system")
        messagebox.showinfo("Claim Closest", "Closest system claimed!")
        
    def open_map(self):
        """Open the galaxy map"""
        print("Opening galaxy map")
        messagebox.showinfo("Galaxy Map", "Galaxy map would open here")
        
    def update_commander_location(self):
        """Update the commander's location"""
        # This would normally update the commander's location in the database
        print(f"Updating commander location: {self.cmdr_name} in {self.system_name}")
        
    def start_monitoring(self):
        """Start monitoring journal files"""
        # Create journal monitor
        journal_path = _cfg.get("journal_path")
        if not journal_path:
            print("No journal path configured")
            return
            
        def on_journal_event(event_type, event_data):
            """Handle journal events"""
            if event_type == "commander":
                self.cmdr_name = event_data["name"]
                self.cmdr_label.configure(text=f"CMDR: {self.cmdr_name}")
                
            elif event_type == "system":
                old_system = self.system_name
                self.system_name = event_data["name"]
                self.system_label.configure(text=self.system_name)
                
                if event_data["position"]:
                    self.latest_starpos = event_data["position"]
                    self.current_coords = event_data["position"]
                    
                # If system changed, update nearest systems
                if old_system != self.system_name:
                    self.jump_count += 1
                    self.update_nearest_systems()
                    self.update_commander_location()
                    
        # Create and start journal monitor
        self.journal_monitor = JournalMonitor(journal_path, on_journal_event)
        self.journal_monitor.start()
        
    def on_closing(self):
        """Handle application closing"""
        print("Closing application...")
        
        # Set destroying flag
        self._is_destroying = True
        
        # Stop journal monitor
        if hasattr(self, 'journal_monitor'):
            self.journal_monitor.stop()
            
        # Stop task queue
        from utils.background_task import cancel_all_tasks
        cancel_all_tasks()
        
        # Destroy all windows
        for widget in self.winfo_children():
            if hasattr(widget, 'destroy'):
                try:
                    widget.destroy()
                except:
                    pass
                    
        # Destroy self
        try:
            self.destroy()
        except:
            pass
            
        # Exit
        os._exit(0)