"""
Main screen for Elite Dangerous Records Helper.
Contains tabs for different functionality.
"""

import os
import customtkinter as ctk
from typing import Dict, Any, Optional, List, Callable
from ui.components.log_display import LogDisplay


class MainScreen(ctk.CTkFrame):
    """Main screen with tabs for different functionality."""

    def __init__(self, parent):
        """Initialize the main screen.

        Args:
            parent: The parent window (App instance).
        """
        super().__init__(parent, corner_radius=0)

        # Store parent reference
        self.app = parent

        # Add attributes needed by ZoomableMap
        self.current_coords = None
        self.supabase = getattr(parent, 'database_service', None)
        if hasattr(self.supabase, 'supabase'):
            self.supabase = self.supabase.supabase
        self.cmdr_name = getattr(parent, 'cmdr_name', "Unknown")
        self.is_admin = getattr(parent, 'is_admin', False)
        self.map_window = None

        # Set up UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        # Create main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create header frame
        self._create_header()

        # Create tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=0)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        # Add tabs
        self.tab_main = self.tabview.add("Main")
        self.tab_galaxy = self.tabview.add("Galaxy")
        self.tab_info = self.tabview.add("Info")

        # Set up tabs
        self._setup_main_tab()
        self._setup_galaxy_tab()
        self._setup_info_tab()

        # Create footer frame
        self._create_footer()

    def _create_header(self):
        """Create the header frame."""
        # Create header frame
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Create logo/title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Elite Dangerous Records Helper",
            font=("Segoe UI", 18, "bold"),
            text_color="#FF7F50"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=10)

        # Create current system frame
        self.system_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.system_frame.grid(row=0, column=1, padx=20, pady=10, sticky="e")

        # Create current system label
        self.system_label = ctk.CTkLabel(
            self.system_frame,
            text="Current System:",
            font=("Segoe UI", 12),
            text_color="#B0B0B0"
        )
        self.system_label.pack(side="left", padx=(0, 5))

        # Create current system value
        self.system_value = ctk.CTkLabel(
            self.system_frame,
            text="Unknown",
            font=("Segoe UI", 12, "bold"),
            text_color="#FFFFFF"
        )
        self.system_value.pack(side="left")

        # Create commander frame
        self.commander_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.commander_frame.grid(row=0, column=2, padx=20, pady=10, sticky="e")

        # Create commander label
        self.commander_label = ctk.CTkLabel(
            self.commander_frame,
            text="Commander:",
            font=("Segoe UI", 12),
            text_color="#B0B0B0"
        )
        self.commander_label.pack(side="left", padx=(0, 5))

        # Create commander value
        self.commander_value = ctk.CTkLabel(
            self.commander_frame,
            text=self.app.cmdr_name,
            font=("Segoe UI", 12, "bold"),
            text_color="#FFFFFF"
        )
        self.commander_value.pack(side="left")

        # Create admin badge if admin
        if self.app.is_admin:
            self.admin_badge = ctk.CTkLabel(
                self.commander_frame,
                text="ADMIN",
                font=("Segoe UI", 10, "bold"),
                text_color="#FFFFFF",
                fg_color="#E74C3C",
                corner_radius=5,
                width=60,
                height=20
            )
            self.admin_badge.pack(side="left", padx=(5, 0))

    def _create_footer(self):
        """Create the footer frame."""
        # Create footer frame
        self.footer_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.footer_frame.grid_columnconfigure(1, weight=1)

        # Create version label
        self.version_label = ctk.CTkLabel(
            self.footer_frame,
            text=f"v1.4.0",
            font=("Segoe UI", 10),
            text_color="#808080"
        )
        self.version_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Create status label
        self.status_label = ctk.CTkLabel(
            self.footer_frame,
            text="Ready",
            font=("Segoe UI", 10),
            text_color="#808080"
        )
        self.status_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")

    def _setup_main_tab(self):
        """Set up the main tab."""
        # Configure grid
        self.tab_main.grid_columnconfigure(0, weight=1)
        self.tab_main.grid_rowconfigure(1, weight=1)

        # Create search frame
        self.search_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        # Create search entry
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Search for a system...",
            width=300,
            height=35,
            font=("Segoe UI", 12)
        )
        self.search_entry.pack(side="left", padx=(0, 10))

        # Create search button
        self.search_button = ctk.CTkButton(
            self.search_frame,
            text="Search",
            font=("Segoe UI", 12),
            width=100,
            height=35,
            command=self._search_systems
        )
        self.search_button.pack(side="left", padx=(0, 10))

        # Create filter button
        self.filter_button = ctk.CTkButton(
            self.search_frame,
            text="Filters",
            font=("Segoe UI", 12),
            width=100,
            height=35,
            command=self._toggle_filters
        )
        self.filter_button.pack(side="left")

        # Create systems frame
        self.systems_frame = ctk.CTkScrollableFrame(
            self.tab_main,
            label_text="Nearby Systems",
            label_font=("Segoe UI", 14, "bold")
        )
        self.systems_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Create placeholder for systems
        self.placeholder_label = ctk.CTkLabel(
            self.systems_frame,
            text="No systems found nearby.\nTry searching for a specific system.",
            font=("Segoe UI", 14),
            text_color="#808080"
        )
        self.placeholder_label.pack(pady=50)

    def _setup_galaxy_tab(self):
        """Set up the galaxy tab."""
        # Configure grid
        self.tab_galaxy.grid_columnconfigure(0, weight=1)
        self.tab_galaxy.grid_rowconfigure(1, weight=1)

        # Create controls frame
        self.galaxy_controls_frame = ctk.CTkFrame(self.tab_galaxy, fg_color="transparent")
        self.galaxy_controls_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        # Create open map button
        self.open_map_button = ctk.CTkButton(
            self.galaxy_controls_frame,
            text="Open Galaxy Map",
            font=("Segoe UI", 12),
            width=150,
            height=35,
            command=self._open_galaxy_map
        )
        self.open_map_button.pack(side="left", padx=(0, 10))

        # Create find unclaimed button
        self.find_unclaimed_button = ctk.CTkButton(
            self.galaxy_controls_frame,
            text="Find Unclaimed",
            font=("Segoe UI", 12),
            width=150,
            height=35,
            command=self._find_unclaimed
        )
        self.find_unclaimed_button.pack(side="left", padx=(0, 10))

        # Create random system button
        self.random_system_button = ctk.CTkButton(
            self.galaxy_controls_frame,
            text="Random System",
            font=("Segoe UI", 12),
            width=150,
            height=35,
            command=self._random_system
        )
        self.random_system_button.pack(side="left")

        # Create stats frame
        self.stats_frame = ctk.CTkFrame(self.tab_galaxy)
        self.stats_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Configure stats frame grid
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.stats_frame.grid_rowconfigure((0, 1), weight=1)

        # Create stat cards
        self._create_stat_card(
            self.stats_frame, "Total Systems", "0", "🌌", "#3498DB", 0, 0
        )
        self._create_stat_card(
            self.stats_frame, "Your Claims", "0", "🚩", "#E74C3C", 0, 1
        )
        self._create_stat_card(
            self.stats_frame, "Session Time", "00:00:00", "⏱️", "#F39C12", 0, 2
        )
        self._create_stat_card(
            self.stats_frame, "Visited Systems", "0", "✅", "#4ECDC4", 1, 0
        )
        self._create_stat_card(
            self.stats_frame, "Unclaimed Systems", "0", "🔍", "#9B59B6", 1, 1
        )
        self._create_stat_card(
            self.stats_frame, "Total Categories", "0", "🏷️", "#FF7F50", 1, 2
        )

    def _setup_info_tab(self):
        """Set up the info tab."""
        # Configure grid
        self.tab_info.grid_columnconfigure(0, weight=1)
        self.tab_info.grid_rowconfigure((0, 1), weight=1)  # Two rows with equal weight

        # Create info frame (top section)
        self.info_frame = ctk.CTkScrollableFrame(self.tab_info, height=300)
        self.info_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))

        # Create title
        self.info_title = ctk.CTkLabel(
            self.info_frame,
            text="About Elite Dangerous Records Helper",
            font=("Segoe UI", 20, "bold"),
            text_color="#FF7F50"
        )
        self.info_title.pack(pady=(0, 20))

        # Create description
        self.info_desc = ctk.CTkLabel(
            self.info_frame,
            text="Elite Dangerous Records Helper is a tool for tracking and sharing interesting star systems in Elite Dangerous.",
            font=("Segoe UI", 14),
            text_color="#FFFFFF",
            wraplength=600
        )
        self.info_desc.pack(pady=(0, 20))

        # Create features title
        self.features_title = ctk.CTkLabel(
            self.info_frame,
            text="Features",
            font=("Segoe UI", 16, "bold"),
            text_color="#FF7F50"
        )
        self.features_title.pack(pady=(0, 10))

        # Create features list
        features = [
            "Track and share interesting star systems",
            "Categorize systems by type and features",
            "Upload and share screenshots",
            "Find nearby systems of interest",
            "View the galaxy map with system locations",
            "Multi-category support for better organization"
        ]

        for feature in features:
            feature_label = ctk.CTkLabel(
                self.info_frame,
                text=f"• {feature}",
                font=("Segoe UI", 14),
                text_color="#FFFFFF",
                anchor="w"
            )
            feature_label.pack(pady=(0, 5), anchor="w")

        # Create credits title
        self.credits_title = ctk.CTkLabel(
            self.info_frame,
            text="Credits",
            font=("Segoe UI", 16, "bold"),
            text_color="#FF7F50"
        )
        self.credits_title.pack(pady=(20, 10))

        # Create credits text
        self.credits_text = ctk.CTkLabel(
            self.info_frame,
            text="Created by the Elite Dangerous community.\nSpecial thanks to all contributors and testers.",
            font=("Segoe UI", 14),
            text_color="#FFFFFF"
        )
        self.credits_text.pack(pady=(0, 20))

        # Create log display (bottom section)
        self.log_display = LogDisplay(self.tab_info, height=300)
        self.log_display.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))

    def _create_stat_card(self, parent, title, value, icon, color, row, col):
        """Create a statistics card.

        Args:
            parent: The parent widget.
            title: The card title.
            value: The card value.
            icon: The card icon.
            color: The card color.
            row: The grid row.
            col: The grid column.
        """
        # Create card frame
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Create icon label
        icon_label = ctk.CTkLabel(
            card,
            text=icon,
            font=("Segoe UI", 36),
            text_color=color
        )
        icon_label.pack(pady=(20, 10))

        # Create value label
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Segoe UI", 24, "bold"),
            text_color="#FFFFFF"
        )
        value_label.pack(pady=(0, 5))

        # Create title label
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 14),
            text_color="#B0B0B0"
        )
        title_label.pack(pady=(0, 20))

        # Store references for updating
        setattr(self, f"{title.lower().replace(' ', '_')}_value", value_label)

    def update_current_system(self, system_name: str):
        """Update the current system display.

        Args:
            system_name: The current system name.
        """
        self.system_value.configure(text=system_name)

        # Update status
        self.status_label.configure(text=f"Current system: {system_name}")

        # Update current coordinates
        try:
            system = self.app.system_repository.get_by_name(system_name)
            if system:
                self.current_coords = (system.x, system.y, system.z)
        except Exception as e:
            print(f"[ERROR] Error updating current coordinates: {e}")

    def update_commander_info(self, commander_name: str):
        """Update the commander information.

        Args:
            commander_name: The commander name.
        """
        self.commander_value.configure(text=commander_name)

        # Update commander name
        self.cmdr_name = commander_name

    def update_admin_status(self, is_admin: bool):
        """Update the admin status display.

        Args:
            is_admin: Whether the commander is an admin.
        """
        # Update admin status
        self.is_admin = is_admin

        if is_admin:
            if not hasattr(self, 'admin_badge'):
                self.admin_badge = ctk.CTkLabel(
                    self.commander_frame,
                    text="ADMIN",
                    font=("Segoe UI", 10, "bold"),
                    text_color="#FFFFFF",
                    fg_color="#E74C3C",
                    corner_radius=5,
                    width=60,
                    height=20
                )
                self.admin_badge.pack(side="left", padx=(5, 0))
        else:
            if hasattr(self, 'admin_badge'):
                self.admin_badge.destroy()
                delattr(self, 'admin_badge')

    def _search_systems(self):
        """Search for systems."""
        search_text = self.search_entry.get().strip()
        if not search_text:
            return

        # Update status
        self.status_label.configure(text=f"Searching for: {search_text}")

        # Get system repository
        system_repo = self.app.system_repository

        # Search for systems
        try:
            # Try exact match first
            system = system_repo.get_by_name(search_text)
            if system:
                # System found, update display
                self.status_label.configure(text=f"System found: {system.name}")

                # Clear existing systems
                for widget in self.systems_frame.winfo_children():
                    widget.destroy()

                # Create system card
                self._create_system_card(system)
                return

            # Try partial match
            systems = system_repo.get_by_filter({"name": search_text})
            if systems:
                # Systems found, update display
                self.status_label.configure(text=f"Found {len(systems)} systems matching '{search_text}'")

                # Clear existing systems
                for widget in self.systems_frame.winfo_children():
                    widget.destroy()

                # Create system cards
                for system in systems:
                    self._create_system_card(system)
                return

            # No systems found
            self.status_label.configure(text=f"No systems found matching '{search_text}'")

            # Clear existing systems
            for widget in self.systems_frame.winfo_children():
                widget.destroy()

            # Show placeholder
            self.placeholder_label = ctk.CTkLabel(
                self.systems_frame,
                text=f"No systems found matching '{search_text}'.\nTry a different search term.",
                font=("Segoe UI", 14),
                text_color="#808080"
            )
            self.placeholder_label.pack(pady=50)
        except Exception as e:
            print(f"[ERROR] Error searching for systems: {e}")
            self.status_label.configure(text=f"Error searching for systems: {str(e)[:50]}")

    def _create_system_card(self, system):
        """Create a system card.

        Args:
            system: The system to display.
        """
        # Create card frame
        card = ctk.CTkFrame(self.systems_frame, corner_radius=10)
        card.pack(fill="x", padx=10, pady=10)

        # Configure grid
        card.grid_columnconfigure(1, weight=1)

        # Create system name
        name_label = ctk.CTkLabel(
            card,
            text=system.name,
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF"
        )
        name_label.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="w")

        # Create categories
        if system.categories:
            categories_text = " • ".join(system.categories[:3])
            if len(system.categories) > 3:
                categories_text += f" (+{len(system.categories) - 3} more)"

            categories_label = ctk.CTkLabel(
                card,
                text=categories_text,
                font=("Segoe UI", 12),
                text_color="#B0B0B0"
            )
            categories_label.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 5), sticky="w")

        # Create coordinates
        coords_label = ctk.CTkLabel(
            card,
            text=f"Coordinates: {system.x:.2f}, {system.y:.2f}, {system.z:.2f}",
            font=("Segoe UI", 12),
            text_color="#808080"
        )
        coords_label.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")

        # Create view button
        view_button = ctk.CTkButton(
            card,
            text="View",
            font=("Segoe UI", 12),
            width=80,
            height=30,
            command=lambda s=system: self._view_system(s)
        )
        view_button.grid(row=3, column=0, padx=(15, 5), pady=(0, 15), sticky="w")

        # Create claim button if not claimed
        if not system.commander:
            claim_button = ctk.CTkButton(
                card,
                text="Claim",
                font=("Segoe UI", 12),
                width=80,
                height=30,
                command=lambda s=system: self._claim_system(s)
            )
            claim_button.grid(row=3, column=1, padx=(5, 15), pady=(0, 15), sticky="e")
        else:
            # Show claimed by
            claimed_label = ctk.CTkLabel(
                card,
                text=f"Claimed by: {system.commander}",
                font=("Segoe UI", 12),
                text_color="#808080"
            )
            claimed_label.grid(row=3, column=1, padx=(5, 15), pady=(0, 15), sticky="e")

    def _view_system(self, system):
        """View a system.

        Args:
            system: The system to view.
        """
        # TODO: Implement system viewing
        self.status_label.configure(text=f"Viewing system: {system.name}")

    def _claim_system(self, system):
        """Claim a system.

        Args:
            system: The system to claim.
        """
        # TODO: Implement system claiming
        self.status_label.configure(text=f"Claiming system: {system.name}")

    def _toggle_filters(self):
        """Toggle filters panel."""
        # Check if filters panel exists
        if hasattr(self, 'filters_panel') and self.filters_panel.winfo_exists():
            # Hide filters panel
            self.filters_panel.destroy()
            delattr(self, 'filters_panel')
            self.filter_button.configure(text="Filters")
            return

        # Create filters panel
        import customtkinter as ctk
        self.filters_panel = ctk.CTkFrame(self.tab_main)
        self.filters_panel.grid(row=0, column=1, sticky="ne", padx=(0, 20), pady=(20, 10))

        # Create title
        ctk.CTkLabel(
            self.filters_panel,
            text="Category Filters",
            font=("Segoe UI", 14, "bold"),
            text_color="#FF7F50"  # ACCENT_COLOR
        ).pack(pady=(10, 5), padx=15)

        # Get categories from category service
        categories = []
        try:
            # Get category repository
            category_repo = self.app.category_repository

            # Get category images (which contains all categories)
            category_images = category_repo.get_category_images()
            categories = list(category_images.keys())

            # Add "All Categories" option
            categories = ["All Categories"] + sorted(categories)
        except Exception as e:
            print(f"[ERROR] Error getting categories: {e}")
            categories = ["All Categories"]

        # Create scrollable frame for categories
        categories_frame = ctk.CTkScrollableFrame(
            self.filters_panel,
            width=200,
            height=300
        )
        categories_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Initialize selected categories
        if not hasattr(self, 'selected_categories'):
            self.selected_categories = ["All Categories"]

        # Create checkboxes for categories
        self.category_vars = {}
        for category in categories:
            var = ctk.BooleanVar(value=category in self.selected_categories)
            self.category_vars[category] = var

            checkbox = ctk.CTkCheckBox(
                categories_frame,
                text=category,
                variable=var,
                command=self._update_selected_categories,
                font=("Segoe UI", 12)
            )
            checkbox.pack(anchor="w", pady=2)

        # Create buttons
        buttons_frame = ctk.CTkFrame(self.filters_panel, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Select all button
        ctk.CTkButton(
            buttons_frame,
            text="Select All",
            font=("Segoe UI", 12),
            width=90,
            height=30,
            command=self._select_all_categories
        ).pack(side="left", padx=(0, 5))

        # Clear all button
        ctk.CTkButton(
            buttons_frame,
            text="Clear All",
            font=("Segoe UI", 12),
            width=90,
            height=30,
            command=self._clear_all_categories
        ).pack(side="right")

        # Update filter button text
        self.filter_button.configure(text="Hide Filters")

    def _update_selected_categories(self):
        """Update the selected categories based on checkboxes."""
        self.selected_categories = []
        for category, var in self.category_vars.items():
            if var.get():
                self.selected_categories.append(category)

        # If "All Categories" is selected, deselect others
        if "All Categories" in self.selected_categories and len(self.selected_categories) > 1:
            for category, var in self.category_vars.items():
                if category != "All Categories":
                    var.set(False)
            self.selected_categories = ["All Categories"]

        # If no categories are selected, select "All Categories"
        if not self.selected_categories:
            self.category_vars["All Categories"].set(True)
            self.selected_categories = ["All Categories"]

    def _select_all_categories(self):
        """Select all categories."""
        for category, var in self.category_vars.items():
            var.set(True)
        self._update_selected_categories()

    def _clear_all_categories(self):
        """Clear all categories."""
        for category, var in self.category_vars.items():
            var.set(False)
        self._update_selected_categories()

    def _open_galaxy_map(self):
        """Open the galaxy map."""
        # Get current system coordinates
        current_system = self.app.current_system
        if not current_system:
            from tkinter import messagebox
            messagebox.showinfo(
                "No Current System",
                "Your current system is unknown.\nPlease jump to a system in Elite Dangerous first."
            )
            return

        # Update status
        self.status_label.configure(text="Opening galaxy map...")

        # Import ZoomableMap
        from ui.screens.galaxy_map import ZoomableMap

        # Check if map window already exists
        if hasattr(self, 'map_window') and self.map_window and hasattr(self.map_window, 'winfo_exists'):
            try:
                if self.map_window.winfo_exists():
                    self.map_window.lift()
                    self.map_window.focus_force()
                    self.map_window.attributes("-topmost", True)
                    self.map_window.after(500, lambda: self.map_window.attributes("-topmost", False))
                    return
            except:
                pass

        # Create new map window
        self.map_window = ZoomableMap(self)

        # Update status
        self.status_label.configure(text="Galaxy map opened")

    def _find_unclaimed(self):
        """Find unclaimed systems."""
        # Get current system coordinates
        current_system = self.app.current_system
        if not current_system:
            from tkinter import messagebox
            messagebox.showinfo(
                "No Current System",
                "Your current system is unknown.\nPlease jump to a system in Elite Dangerous first."
            )
            return

        # Update status
        self.status_label.configure(text="Finding unclaimed systems...")

        # Get system repository
        system_repo = self.app.system_repository

        # Get current system
        system = system_repo.get_by_name(current_system)
        if not system:
            self.status_label.configure(text="Current system not found in database")
            return

        # Get selected categories
        selected_categories = getattr(self, 'selected_categories', ["All Categories"])

        # Find unclaimed systems
        try:
            unclaimed_systems = system_repo.get_unclaimed_systems(
                system.x, system.y, system.z, 
                category_filter=selected_categories
            )

            if not unclaimed_systems:
                from tkinter import messagebox
                messagebox.showinfo(
                    "No Systems",
                    "No unclaimed systems found with the current filters!"
                )
                self.status_label.configure(text="No unclaimed systems found")
                return

            # Store unclaimed systems
            self.unclaimed_systems = unclaimed_systems
            self.unclaimed_index = 0

            # Show nearest unclaimed system
            self._show_nearest_unclaimed()

            # Update status
            self.status_label.configure(text=f"Found {len(unclaimed_systems)} unclaimed systems")
        except Exception as e:
            print(f"[ERROR] Error finding unclaimed systems: {e}")
            self.status_label.configure(text=f"Error finding unclaimed systems: {str(e)[:50]}")

    def _show_nearest_unclaimed(self):
        """Show the nearest unclaimed system."""
        if not hasattr(self, 'unclaimed_systems') or not self.unclaimed_systems:
            return

        # Get the nearest system
        nearest = self.unclaimed_systems[self.unclaimed_index]

        # Create popup
        import customtkinter as ctk
        popup = ctk.CTkToplevel(self.app)
        popup.title("Nearest Unclaimed")
        popup.geometry("400x250")
        popup.transient(self.app)
        popup.grab_set()
        popup.configure(fg_color="#0a0a0a")  # MAIN_BG_COLOR
        popup.update_idletasks()

        # Center popup
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")

        # Create content
        content = ctk.CTkFrame(popup, fg_color="#141414", corner_radius=15)  # CARD_BG_COLOR
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Create title
        ctk.CTkLabel(
            content, 
            text="Nearest Unclaimed System",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FF7F50"  # ACCENT_COLOR
        ).pack(pady=(20, 10))

        # Create system name
        ctk.CTkLabel(
            content,
            text=nearest['systems'],
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#FFFFFF"  # TEXT_COLOR
        ).pack()

        # Create category
        ctk.CTkLabel(
            content,
            text=nearest.get('category', 'Unknown'),
            font=ctk.CTkFont(size=14),
            text_color="#B0B0B0"  # TEXT_SECONDARY
        ).pack(pady=(5, 0))

        # Create distance
        ctk.CTkLabel(
            content,
            text=f"{nearest['distance']:.2f} LY away",
            font=ctk.CTkFont(size=16),
            text_color="#4ECDC4"  # SUCCESS_COLOR
        ).pack(pady=(10, 20))

        # Create buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack()

        # View button
        ctk.CTkButton(
            btn_frame, 
            text="View Details",
            command=lambda: (popup.destroy(), self._view_unclaimed_system(nearest)),
            fg_color="#3498DB",  # INFO_COLOR
            width=120
        ).pack(side="left", padx=5)

        # Close button
        ctk.CTkButton(
            btn_frame,
            text="Close",
            command=popup.destroy,
            fg_color="#1f1f1f",  # SECONDARY_BG_COLOR
            width=120
        ).pack(side="left", padx=5)

    def _view_unclaimed_system(self, system_data):
        """View an unclaimed system.

        Args:
            system_data: The system data to view.
        """
        # TODO: Implement system viewing
        self.status_label.configure(text=f"Viewing system: {system_data['systems']}")

    def prev_unclaimed(self):
        """Show the previous unclaimed system."""
        if hasattr(self, 'unclaimed_systems') and hasattr(self, 'unclaimed_index') and self.unclaimed_index > 0:
            self.unclaimed_index -= 1
            self._show_nearest_unclaimed()

    def next_unclaimed(self):
        """Show the next unclaimed system."""
        if hasattr(self, 'unclaimed_systems') and hasattr(self, 'unclaimed_index') and self.unclaimed_index < len(self.unclaimed_systems) - 1:
            self.unclaimed_index += 1
            self._show_nearest_unclaimed()

    def _random_system(self):
        """Get a random system."""
        # Get current system coordinates
        current_system = self.app.current_system
        if not current_system:
            from tkinter import messagebox
            messagebox.showinfo(
                "No Current System",
                "Your current system is unknown.\nPlease jump to a system in Elite Dangerous first."
            )
            return

        # Update status
        self.status_label.configure(text="Finding random system...")

        # Get system repository
        system_repo = self.app.system_repository

        # Get current system
        system = system_repo.get_by_name(current_system)
        if not system:
            self.status_label.configure(text="Current system not found in database")
            return

        # Get systems
        try:
            # Get all systems
            all_systems = system_repo.get_all()
            if not all_systems:
                from tkinter import messagebox
                messagebox.showinfo(
                    "No Systems",
                    "No systems found in the database!"
                )
                self.status_label.configure(text="No systems found")
                return

            # Filter systems by distance (50-1000 LY)
            import random
            nearby_systems = []

            for sys in all_systems:
                # Calculate distance
                dx = sys.x - system.x
                dy = sys.y - system.y
                dz = sys.z - system.z
                distance = (dx * dx + dy * dy + dz * dz) ** 0.5

                # Check distance range
                if 50 < distance < 1000:
                    nearby_systems.append((sys, distance))

            if not nearby_systems:
                from tkinter import messagebox
                messagebox.showinfo(
                    "No Systems",
                    "No systems found within 50-1000 LY of your current location!"
                )
                self.status_label.configure(text="No systems found in range")
                return

            # Choose random system
            chosen_system, distance = random.choice(nearby_systems)

            # Create popup
            import customtkinter as ctk
            popup = ctk.CTkToplevel(self.app)
            popup.title("Random Destination")
            popup.geometry("400x250")
            popup.transient(self.app)
            popup.grab_set()
            popup.configure(fg_color="#0a0a0a")  # MAIN_BG_COLOR
            popup.update_idletasks()

            # Center popup
            x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
            y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
            popup.geometry(f"+{x}+{y}")

            # Create content
            content = ctk.CTkFrame(popup, fg_color="#141414", corner_radius=15)  # CARD_BG_COLOR
            content.pack(fill="both", expand=True, padx=20, pady=20)

            # Create title
            ctk.CTkLabel(
                content, 
                text="Alternative Destination",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#F39C12"  # WARNING_COLOR
            ).pack(pady=(20, 10))

            # Create system name
            ctk.CTkLabel(
                content,
                text=chosen_system.name,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#FFFFFF"  # TEXT_COLOR
            ).pack()

            # Create category
            categories_text = " • ".join(chosen_system.categories[:3]) if chosen_system.categories else "Unknown"
            if len(chosen_system.categories) > 3:
                categories_text += f" (+{len(chosen_system.categories) - 3} more)"

            ctk.CTkLabel(
                content,
                text=categories_text,
                font=ctk.CTkFont(size=14),
                text_color="#B0B0B0"  # TEXT_SECONDARY
            ).pack(pady=(5, 0))

            # Create distance
            ctk.CTkLabel(
                content,
                text=f"{distance:.2f} LY away",
                font=ctk.CTkFont(size=16),
                text_color="#3498DB"  # INFO_COLOR
            ).pack(pady=(10, 20))

            # Create buttons
            btn_frame = ctk.CTkFrame(content, fg_color="transparent")
            btn_frame.pack()

            # View button
            ctk.CTkButton(
                btn_frame, 
                text="View System",
                command=lambda: (popup.destroy(), self._view_system(chosen_system)),
                fg_color="#F39C12",  # WARNING_COLOR
                width=120
            ).pack(side="left", padx=5)

            # Try another button
            ctk.CTkButton(
                btn_frame,
                text="Try Another",
                command=lambda: (popup.destroy(), self._random_system()),
                fg_color="#1f1f1f",  # SECONDARY_BG_COLOR
                width=120
            ).pack(side="left", padx=5)

            # Update status
            self.status_label.configure(text=f"Random system: {chosen_system.name}")
        except Exception as e:
            print(f"[ERROR] Error finding random system: {e}")
            self.status_label.configure(text=f"Error finding random system: {str(e)[:50]}")
