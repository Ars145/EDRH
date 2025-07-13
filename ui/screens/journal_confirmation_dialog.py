"""
Journal confirmation dialog for Elite Dangerous Records Helper.
Confirms journal folder and selects primary commander.
"""

import os
import customtkinter as ctk
from typing import Dict, Any, Optional, List


try:
    DialogBaseClass = ctk.CTkToplevel
except AttributeError:
    # Fallback for older versions of customtkinter
    print("[WARNING] CTkToplevel not available, using Toplevel")
    import tkinter as tk
    DialogBaseClass = tk.Toplevel

class JournalConfirmationDialog(DialogBaseClass):
    """Dialog for confirming journal folder and selecting primary commander."""

    def __init__(self, parent, analysis_data: Dict[str, Any], is_verification: bool = False):
        """Initialize the journal confirmation dialog.

        Args:
            parent: The parent window.
            analysis_data: Data from journal folder analysis.
            is_verification: Whether this is a verification dialog.
        """
        super().__init__(parent)

        # Store parameters
        self.parent = parent
        self.analysis_data = analysis_data
        self.is_verification = is_verification
        self.result = False
        self.selected_commander = None

        # Set window properties
        self.title("Journal Folder Confirmation")
        self.geometry("600x500")
        self.resizable(False, False)

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Set up UI
        self.setup_ui()

        # Set protocol for window close
        self.protocol("WM_DELETE_WINDOW", self.choose_different)

    def get_primary_commander(self) -> str:
        """Get the selected primary commander.

        Returns:
            str: The selected commander name.
        """
        if self.selected_commander:
            return self.selected_commander

        # If no commander is explicitly selected, use the one from analysis
        return self.analysis_data.get("primary_commander", "Unknown")

    def setup_ui(self):
        """Set up the UI components."""
        # Create main frame
        try:
            self.main_frame = ctk.CTkFrame(self)
        except (AttributeError, TypeError):
            # Fallback for older versions of customtkinter
            import tkinter as tk
            self.main_frame = tk.Frame(self, background="#1a1a1a")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Create title label
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Journal Folder Detected",
            font=("Segoe UI", 20, "bold"),
            text_color="#FF7F50"
        )
        self.title_label.pack(pady=(0, 10))

        # Create folder path label
        folder_path = self.analysis_data.get("folder_path", "Unknown")
        self.folder_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Folder: {folder_path}",
            font=("Segoe UI", 12),
            text_color="#B0B0B0"
        )
        self.folder_label.pack(pady=(0, 20))

        # Create commanders frame
        try:
            self.commanders_frame = ctk.CTkScrollableFrame(
                self.main_frame,
                width=500,
                height=250,
                label_text="Detected Commanders",
                label_font=("Segoe UI", 14, "bold")
            )
        except (AttributeError, TypeError):
            # Fallback for older versions of customtkinter
            import tkinter as tk
            self.commanders_frame_label = tk.Label(
                self.main_frame,
                text="Detected Commanders",
                font=("Segoe UI", 14, "bold"),
                background="#1a1a1a",
                foreground="#FFFFFF"
            )
            self.commanders_frame_label.pack(anchor="w", pady=(0, 5))

            self.commanders_frame_container = tk.Frame(self.main_frame, background="#1a1a1a")
            self.commanders_frame_container.pack(fill="both", expand=True, pady=(0, 20))

            self.commanders_frame_canvas = tk.Canvas(
                self.commanders_frame_container,
                background="#1a1a1a",
                highlightthickness=0
            )
            self.commanders_frame_scrollbar = tk.Scrollbar(
                self.commanders_frame_container,
                orient="vertical",
                command=self.commanders_frame_canvas.yview
            )
            self.commanders_frame = tk.Frame(self.commanders_frame_canvas, background="#1a1a1a")

            self.commanders_frame.bind(
                "<Configure>",
                lambda e: self.commanders_frame_canvas.configure(
                    scrollregion=self.commanders_frame_canvas.bbox("all")
                )
            )

            self.commanders_frame_canvas.create_window((0, 0), window=self.commanders_frame, anchor="nw")
            self.commanders_frame_canvas.configure(yscrollcommand=self.commanders_frame_scrollbar.set)

            self.commanders_frame_canvas.pack(side="left", fill="both", expand=True)
            self.commanders_frame_scrollbar.pack(side="right", fill="y")
        else:
            self.commanders_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Add commander cards
        commanders = self.analysis_data.get("commanders", {})
        primary_commander = self.analysis_data.get("primary_commander", "")

        # Sort commanders by count (most frequent first)
        sorted_commanders = sorted(
            commanders.items(),
            key=lambda x: (x[1]["count"], x[1]["latest_time"]),
            reverse=True
        )

        # Create a card for each commander
        for i, (cmdr_name, cmdr_data) in enumerate(sorted_commanders):
            is_primary = cmdr_name == primary_commander
            self.create_commander_card(self.commanders_frame, cmdr_name, cmdr_data, is_primary)

        # Create buttons frame
        try:
            self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        except (AttributeError, TypeError):
            # Fallback for older versions of customtkinter
            import tkinter as tk
            self.buttons_frame = tk.Frame(self.main_frame, background="#1a1a1a")
        self.buttons_frame.pack(fill="x", pady=(0, 10))

        # Create confirm button
        try:
            self.confirm_button = ctk.CTkButton(
                self.buttons_frame,
                text="Confirm Folder",
                font=("Segoe UI", 12, "bold"),
                fg_color="#4ECDC4",
                hover_color="#5ED4CC",
                command=self.confirm_folder
            )
        except (AttributeError, TypeError):
            # Fallback for older versions of customtkinter
            import tkinter as tk
            self.confirm_button = tk.Button(
                self.buttons_frame,
                text="Confirm Folder",
                font=("Segoe UI", 12, "bold"),
                background="#4ECDC4",
                foreground="#FFFFFF",
                command=self.confirm_folder
            )
        self.confirm_button.pack(side="right", padx=5)

        # Create choose different button
        try:
            self.choose_button = ctk.CTkButton(
                self.buttons_frame,
                text="Choose Different",
                font=("Segoe UI", 12),
                fg_color="#E74C3C",
                hover_color="#EC5F4F",
                command=self.choose_different
            )
        except (AttributeError, TypeError):
            # Fallback for older versions of customtkinter
            import tkinter as tk
            self.choose_button = tk.Button(
                self.buttons_frame,
                text="Choose Different",
                font=("Segoe UI", 12),
                background="#E74C3C",
                foreground="#FFFFFF",
                command=self.choose_different
            )
        self.choose_button.pack(side="right", padx=5)

    def create_commander_card(self, parent, cmdr_name: str, cmdr_data: Dict[str, Any], is_primary: bool = False):
        """Create a commander card.

        Args:
            parent: The parent widget.
            cmdr_name: The commander name.
            cmdr_data: The commander data.
            is_primary: Whether this is the primary commander.
        """
        # Import tkinter for fallback
        import tkinter as tk

        # Create card frame
        try:
            card = ctk.CTkFrame(parent, corner_radius=10)
        except (AttributeError, TypeError):
            card = tk.Frame(parent, background="#1f1f1f", borderwidth=1, relief="solid")
        card.pack(fill="x", padx=10, pady=5)

        # Create selection variable
        try:
            var = ctk.StringVar(value=cmdr_name if is_primary else "")
        except (AttributeError, TypeError):
            var = tk.StringVar(value=cmdr_name if is_primary else "")

        # Create radio button
        try:
            radio = ctk.CTkRadioButton(
                card,
                text="",
                variable=var,
                value=cmdr_name,
                command=lambda: self.select_commander(cmdr_name)
            )
        except (AttributeError, TypeError):
            radio = tk.Radiobutton(
                card,
                text="",
                variable=var,
                value=cmdr_name,
                command=lambda: self.select_commander(cmdr_name),
                background="#1f1f1f",
                foreground="#FFFFFF",
                selectcolor="#1f1f1f",
                activebackground="#1f1f1f",
                activeforeground="#FFFFFF"
            )
        radio.pack(side="left", padx=10)

        # Set as selected if primary
        if is_primary:
            radio.select()
            self.selected_commander = cmdr_name

        # Create info frame
        try:
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
        except (AttributeError, TypeError):
            info_frame = tk.Frame(card, background="#1f1f1f")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Create commander name label
        try:
            name_label = ctk.CTkLabel(
                info_frame,
                text=cmdr_name,
                font=("Segoe UI", 16, "bold"),
                text_color="#FF7F50" if is_primary else "#FFFFFF"
            )
        except (AttributeError, TypeError):
            name_label = tk.Label(
                info_frame,
                text=cmdr_name,
                font=("Segoe UI", 16, "bold"),
                foreground="#FF7F50" if is_primary else "#FFFFFF",
                background="#1f1f1f"
            )
        name_label.pack(anchor="w")

        # Create commander stats label
        count = cmdr_data.get("count", 0)
        latest_file = cmdr_data.get("latest_file", "")
        latest_time = cmdr_data.get("latest_time", 0)

        # Format latest time
        try:
            import datetime
            latest_time_str = datetime.datetime.fromtimestamp(latest_time).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"[ERROR] Error formatting timestamp: {e}")
            latest_time_str = "Unknown"

        # Create stats label
        try:
            stats_label = ctk.CTkLabel(
                info_frame,
                text=f"Occurrences: {count}  |  Last seen: {latest_time_str}",
                font=("Segoe UI", 12),
                text_color="#B0B0B0"
            )
        except (AttributeError, TypeError):
            stats_label = tk.Label(
                info_frame,
                text=f"Occurrences: {count}  |  Last seen: {latest_time_str}",
                font=("Segoe UI", 12),
                foreground="#B0B0B0",
                background="#1f1f1f"
            )
        stats_label.pack(anchor="w")

        # Create primary indicator if primary
        if is_primary:
            try:
                primary_label = ctk.CTkLabel(
                    info_frame,
                    text="Primary Commander (Most Frequent)",
                    font=("Segoe UI", 12, "italic"),
                    text_color="#4ECDC4"
                )
            except (AttributeError, TypeError):
                primary_label = tk.Label(
                    info_frame,
                    text="Primary Commander (Most Frequent)",
                    font=("Segoe UI", 12, "italic"),
                    foreground="#4ECDC4",
                    background="#1f1f1f"
                )
            primary_label.pack(anchor="w")

    def select_commander(self, cmdr_name: str):
        """Select a commander.

        Args:
            cmdr_name: The commander name.
        """
        self.selected_commander = cmdr_name

    def confirm_folder(self):
        """Confirm the journal folder."""
        self.result = True
        self.destroy()

    def choose_different(self):
        """Choose a different journal folder."""
        self.result = False
        self.destroy()
