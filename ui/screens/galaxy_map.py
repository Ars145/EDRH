"""
Galaxy map for Elite Dangerous Records Helper.
Contains the ZoomableMap class for visualizing star systems.
"""

import os
import json
import threading
import customtkinter as ctk
from tkinter import font as tkFont, messagebox
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageDraw
from PIL.Image import Resampling

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
SIDEBAR_WIDTH = 350
SIDEBAR_COLLAPSED = 50
SCROLL_W = SIDEBAR_WIDTH - 50
MIN_ZOOM = 0.8
MAX_ZOOM = 6.0
DOT_RADIUS = 5
LY_PER_PIXEL = 40.0
ORIG_OFF_X = 1124
ORIG_OFF_Y = 1749
DOSIS_BOLD = 20
DOSIS_REG = 16
FILTER_BG = "#2b2b2b"

# Colors
MAIN_BG_COLOR = "#0a0a0a"
CARD_BG_COLOR = "#141414"
SECONDARY_BG_COLOR = "#1f1f1f"
TERTIARY_BG_COLOR = "#2a2a2a"
ACCENT_COLOR = "#FF7F50"
ACCENT_HOVER = "#FF9068"
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


def parse_categories(category_data):
    """Parse category data which can be a string, list, or JSON string into a list of categories"""
    if not category_data:
        return []

    # If it's already a list, return it
    if isinstance(category_data, list):
        return [cat.strip() for cat in category_data if cat and cat.strip()]

    # If it's a string, try to parse as JSON first
    if isinstance(category_data, str):
        category_data = category_data.strip()

        # Try JSON parsing first
        if category_data.startswith('[') and category_data.endswith(']'):
            try:
                parsed = json.loads(category_data)
                if isinstance(parsed, list):
                    return [cat.strip() for cat in parsed if cat and cat.strip()]
            except json.JSONDecodeError:
                pass

        # If JSON parsing fails or it's not JSON, treat as comma-separated
        if ',' in category_data:
            return [cat.strip() for cat in category_data.split(',') if cat and cat.strip()]
        else:
            # Single category
            return [category_data] if category_data else []

    return []


def categories_match_filter(categories, selected_filters):
    """Check if any of the system's categories match the selected filters"""
    if not selected_filters or "All Categories" in selected_filters:
        return True

    parsed_categories = parse_categories(categories)
    if not parsed_categories:
        return False

    # Check if any category matches any filter
    return any(cat in selected_filters for cat in parsed_categories)


def resource(name: str) -> str:
    """Get the path to a resource file"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assets_path = os.path.join(base_dir, "assets", name)
    if os.path.exists(assets_path):
        return assets_path
    return os.path.join(base_dir, name)


class ZoomableMap(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_ref = master
        self.title("Galaxy Map Viewer")
        try:
            self.iconbitmap(resource("icon.ico"))
        except:
            pass
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=MAIN_BG_COLOR)
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()
        self.update_idletasks()
        self.update()
        self.after(500, lambda: self.attributes("-topmost", False))
        self.sidebar_expanded = True
        self.current_sidebar_width = SIDEBAR_WIDTH
        self._is_closing = False
        bold = (ctk.CTkFont(family="Dosis", size=DOSIS_BOLD, weight="bold")
                if "Dosis" in tkFont.families() else ctk.CTkFont(size=DOSIS_BOLD, weight="bold"))
        reg = (ctk.CTkFont(family="Dosis", size=DOSIS_REG)
               if "Dosis" in tkFont.families() else ctk.CTkFont(size=DOSIS_REG))
        self.canvas = ctk.CTkCanvas(self, bg="#0f0f0f", highlightthickness=0)
        self.update_canvas_position()
        self.sidebar = ctk.CTkFrame(self, fg_color=CARD_BG_COLOR,
                                    width=SIDEBAR_WIDTH, height=WINDOW_HEIGHT,
                                    corner_radius=0,
                                    border_width=0)
        self.sidebar.place(x=0, y=0)
        self.filter_content = ctk.CTkFrame(self.sidebar, fg_color=CARD_BG_COLOR)
        self.filter_content.place(x=0, y=0, relwidth=1, relheight=1)
        self.toggle_btn = ctk.CTkButton(self, text="◀", width=35, height=70,
                                        command=self.toggle_sidebar,
                                        fg_color=SECONDARY_BG_COLOR,
                                        hover_color=TERTIARY_BG_COLOR,
                                        border_color=BORDER_COLOR,
                                        border_width=1,
                                        font=ctk.CTkFont(size=14),
                                        corner_radius=0)
        self.toggle_btn.place(x=self.current_sidebar_width, y=WINDOW_HEIGHT // 2 - 35)
        ctk.CTkLabel(self.filter_content, text="FILTERS & SETTINGS",
                     font=bold, text_color=TEXT_COLOR).place(x=20, y=20)
        checkbox_style = {
            "font": reg,
            "fg_color": ACCENT_COLOR,
            "hover_color": ACCENT_HOVER,
            "border_color": BORDER_COLOR,
            "border_width": 2,
            "checkbox_width": 20,
            "checkbox_height": 20,
            "corner_radius": 5,
            "text_color": TEXT_COLOR
        }
        self.cb_loc = ctk.CTkCheckBox(self.filter_content, text="Show CMDR Location",
                                      command=self.draw_image, **checkbox_style)
        self.cb_loc.place(x=25, y=70)
        self.cb_unv = ctk.CTkCheckBox(self.filter_content, text="Show Unclaimed",
                                      command=self.toggle_unvisited, **checkbox_style)
        self.cb_unv.place(x=25, y=110)
        self.unv_data = []
        self.cb_you = ctk.CTkCheckBox(self.filter_content, text="Show Your Claims",
                                      command=self.toggle_your_claims, **checkbox_style)
        self.cb_you.place(x=25, y=150)
        self.you_data = []
        self.cb_oth = ctk.CTkCheckBox(self.filter_content, text="Show Others' Claims",
                                      command=self.toggle_others_claims, **checkbox_style)
        self.cb_oth.place(x=25, y=190)
        self.oth_data = []
        self.cb_pot_poi = ctk.CTkCheckBox(self.filter_content, text="Show Potential POIs",
                                          command=self.toggle_potential_pois, **checkbox_style)
        self.cb_pot_poi.place(x=25, y=230)
        self.pot_poi_data = []
        self.cb_poi = ctk.CTkCheckBox(self.filter_content, text="Show POIs",
                                      command=self.toggle_pois, **checkbox_style)
        self.cb_poi.place(x=25, y=270)
        self.poi_data = []
        self.cb_done = ctk.CTkCheckBox(self.filter_content, text="Show Completed Systems",
                                       command=self.toggle_done_systems, **checkbox_style)
        self.cb_done.place(x=25, y=310)
        self.done_data = []
        admin_y = 350
        if hasattr(self.master_ref, 'is_admin') and self.master_ref.is_admin:
            admin_checkbox_style = checkbox_style.copy()
            admin_checkbox_style.update({
                "fg_color": DANGER_COLOR,
                "hover_color": DANGER_HOVER,
                "border_color": DANGER_COLOR
            })
            self.cb_all_cmdrs = ctk.CTkCheckBox(self.filter_content, text="See All CMDR Locations",
                                                command=self.toggle_all_cmdrs, **admin_checkbox_style)
            self.cb_all_cmdrs.place(x=25, y=admin_y)
            self.all_cmdrs_data = []
            admin_y += 40
        self.category_dropdown_frame = ctk.CTkFrame(self.filter_content,
                                                    fg_color=CARD_BG_COLOR,
                                                    border_color=ACCENT_COLOR,
                                                    border_width=3,
                                                    corner_radius=15,
                                                    width=280,
                                                    height=300)
        self.category_checkboxes = []
        self._dropdown_visible = False

        # Get available categories
        self.available_categories = []
        try:
            # Try to get categories from master's category_dropdown if it exists
            if hasattr(self.master_ref, 'category_dropdown'):
                self.available_categories = list(self.master_ref.category_dropdown.cget("values"))
                if "All Categories" in self.available_categories:
                    self.available_categories.remove("All Categories")
            # Otherwise try to get categories from app's category_repository
            elif hasattr(self.master_ref, 'app') and hasattr(self.master_ref.app, 'category_repository'):
                category_images = self.master_ref.app.category_repository.get_category_images()
                self.available_categories = list(category_images.keys())

            if self.available_categories:
                self.setup_category_dropdown()
        except Exception as e:
            print(f"Error setting up category dropdown: {e}")
        ctk.CTkLabel(self.filter_content, text="CATEGORY FILTER",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_COLOR).place(x=25, y=admin_y)
        self.selected_categories = ["All Categories"]
        self.category_button = ctk.CTkButton(self.filter_content,
                                             text="All Categories",
                                             width=285,
                                             height=36,
                                             fg_color=TERTIARY_BG_COLOR,
                                             hover_color="#363636",
                                             text_color=TEXT_COLOR,
                                             border_color=BORDER_COLOR,
                                             border_width=1,
                                             anchor="w",
                                             font=ctk.CTkFont(size=13, weight="bold"),
                                             corner_radius=8,
                                             command=self.toggle_category_dropdown)
        self.category_button.place(x=25, y=admin_y + 35)
        nearest_y = admin_y + 85
        ctk.CTkLabel(self.filter_content, text="NEAREST SYSTEMS",
                     font=bold, text_color=TEXT_COLOR).place(x=25, y=nearest_y)
        self.scroll = ctk.CTkScrollableFrame(self.filter_content,
                                             width=SCROLL_W - 15,
                                             height=WINDOW_HEIGHT - nearest_y - 90,
                                             fg_color=SECONDARY_BG_COLOR,
                                             corner_radius=10)
        self.scroll.place(x=15, y=nearest_y + 35)

        # FIX SCROLLING for map window filter list
        def _map_scroll_handler(event):
            try:
                self.scroll._parent_canvas.yview_scroll(int(-3 * (event.delta / 120)), "units")
            except:
                pass
            return "break"

        # Bind scroll events to map filter scroll area
        self.scroll.bind("<MouseWheel>", _map_scroll_handler)
        self.scroll._parent_canvas.bind("<MouseWheel>", _map_scroll_handler)
        try:
            img = Image.open(resource("E47CDFX.png")).convert("RGB")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load galaxy map:\n{e}")
            self.destroy()
            return
        self.base_full = img
        self.base_med = img.resize((800, 800), Resampling.LANCZOS)
        self.zoom = 1.0
        self._zr = None
        self.image_id = None
        self.label_id = None
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.bind("<MouseWheel>", self.on_wheel)
        self.bind("<Key>", self.on_key)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(50, self.draw_image)
        self.after(100, self.update_nearest_in_filter)
        self.after(1000, self.check_for_starpos_update)
        self.bind("<Button-1>", self._handle_click)
        self.after(100, lambda: (self.lift(), self.focus_force()))

    def toggle_done_systems(self):
        if self.cb_done.get() and hasattr(self.master_ref, 'supabase') and self.master_ref.supabase:
            supabase = self.master_ref.supabase
            done_records = supabase.table("taken").select("system,by_cmdr").eq("done", True).execute().data or []
            system_names = [r["system"] for r in done_records]
            # Get done systems from main systems table
            systems_data = supabase.table("systems").select("systems,category,x,y,z").in_("systems",
                                                                                          system_names).execute().data or []

            # Also check system_information table for new discoveries that are done
            try:
                new_discoveries = supabase.table("system_information").select("system,category,x,y,z").in_("system",
                                                                                                           system_names).execute().data or []
                for discovery in new_discoveries:
                    if discovery.get("x") and discovery.get("y") and discovery.get("z"):
                        # Convert to same format as systems table
                        discovery_data = {
                            "systems": discovery["system"],
                            "category": discovery.get("category", "New Discovery"),
                            "x": discovery["x"],
                            "y": discovery["y"],
                            "z": discovery["z"]
                        }
                        # Only add if not already in main systems data
                        if not any(s["systems"] == discovery["system"] for s in systems_data):
                            systems_data.append(discovery_data)
            except Exception as e:
                print(f"Error loading done new discoveries for map: {e}")

            richards_categories = []
            try:
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                richards_categories = [item["category"] for item in
                                       richards_response.data] if richards_response.data else []
            except:
                pass
            systems_data = [s for s in systems_data if s.get("category") not in richards_categories]
            if "All Categories" not in self.selected_categories and self.selected_categories:
                systems_data = [s for s in systems_data if
                                categories_match_filter(s.get("category"), self.selected_categories)]
            by_cmdr = {r["system"]: r["by_cmdr"] for r in done_records}
            for sys in systems_data:
                sys["by_cmdr"] = by_cmdr.get(sys["systems"], "")
            self.done_data = systems_data
        else:
            self.done_data = []
        self.draw_image()

    def on_close(self):
        self._is_closing = True
        if self._zr:
            self.after_cancel(self._zr)
        try:
            for after_id in self.tk.call('after', 'info'):
                self.after_cancel(after_id)
        except:
            pass
        self.unbind("<MouseWheel>")
        self.destroy()

    def toggle_sidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded
        target_width = SIDEBAR_WIDTH if self.sidebar_expanded else SIDEBAR_COLLAPSED

        def animate():
            if self._is_closing:
                return
            current = self.current_sidebar_width
            if self.sidebar_expanded:
                new_width = min(current + 20, target_width)
            else:
                new_width = max(current - 20, target_width)
            self.current_sidebar_width = new_width
            self.sidebar.configure(width=new_width)
            self.toggle_btn.place_configure(x=new_width, y=WINDOW_HEIGHT // 2 - 30)
            self.update_canvas_position()
            if new_width != target_width:
                self.after(10, animate)
            else:
                self.toggle_btn.configure(text="◀" if self.sidebar_expanded else "▶")
                if self.sidebar_expanded:
                    self.filter_content.place(x=0, y=0, relwidth=1, relheight=1)
                else:
                    self.filter_content.place_forget()

        animate()

    def apply_category_filter(self):
        if hasattr(self, '_dropdown_visible') and self._dropdown_visible:
            self.category_dropdown_frame.place_forget()
            self._dropdown_visible = False
        if self.cb_unv.get():
            self.toggle_unvisited()
        if self.cb_you.get():
            self.toggle_your_claims()
        if self.cb_oth.get():
            self.toggle_others_claims()
        if self.cb_pot_poi.get():
            self.toggle_potential_pois()
        if self.cb_poi.get():
            self.toggle_pois()
        if self.cb_done.get():
            self.toggle_done_systems()
        self.draw_image()

    def update_canvas_position(self):
        if not self._is_closing:
            self.canvas.place(x=0, y=0, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

    def update_nearest_in_filter(self):
        if self._is_closing or not hasattr(self.master_ref, 'current_coords') or not self.master_ref.current_coords or not hasattr(self.master_ref, 'supabase') or not self.master_ref.supabase:
            return
        try:
            if not self.winfo_exists() or not hasattr(self, 'scroll') or not self.scroll.winfo_exists():
                return
        except:
            return
        for widget in self.scroll.winfo_children():
            widget.destroy()
        loading_label = ctk.CTkLabel(self.scroll, text="Loading...",
                                     font=ctk.CTkFont(size=12), text_color="#666666")
        loading_label.pack(pady=20)

        def load_systems():
            try:
                supabase = self.master_ref.supabase
                cx, cy, cz = self.master_ref.current_coords
                # Get systems from main systems table
                all_systems = supabase.table("systems").select("systems,category,x,y,z").execute().data or []

                # Also get new discoveries from system_information table
                try:
                    new_discoveries = supabase.table("system_information").select(
                        "system,category,x,y,z").execute().data or []
                    for discovery in new_discoveries:
                        if discovery.get("x") and discovery.get("y") and discovery.get("z"):
                            # Convert to same format as systems table
                            discovery_data = {
                                "systems": discovery["system"],
                                "category": discovery.get("category", "New Discovery"),
                                "x": discovery["x"],
                                "y": discovery["y"],
                                "z": discovery["z"]
                            }
                            # Only add if not already in systems table
                            if not any(s["systems"] == discovery["system"] for s in all_systems):
                                all_systems.append(discovery_data)
                except Exception as e:
                    print(f"Error loading new discoveries for map: {e}")

                # Filter out Richard's categories
                richards_categories = []
                try:
                    richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                    richards_categories = [item["category"] for item in
                                           richards_response.data] if richards_response.data else []
                except:
                    pass
                all_systems = [s for s in all_systems if
                               not any(cat in richards_categories for cat in parse_categories(s.get("category")))]

                # Apply category filter
                if "All Categories" not in self.selected_categories and self.selected_categories:
                    all_systems = [s for s in all_systems if
                                   categories_match_filter(s.get("category"), self.selected_categories)]

                # Calculate distances
                systems_with_distance = []
                for sys in all_systems:
                    try:
                        x = float(sys["x"])
                        y = float(sys["y"])
                        z = float(sys["z"])
                        dx = x - cx
                        dy = y - cy
                        dz = z - cz
                        distance = (dx * dx + dy * dy + dz * dz) ** 0.5
                        systems_with_distance.append((sys, distance))
                    except:
                        continue

                # Sort by distance
                systems_with_distance.sort(key=lambda x: x[1])

                # Get top 50
                nearest_systems = systems_with_distance[:50]

                # Update UI on main thread
                self.after(0, lambda: self._update_nearest_list(nearest_systems))
            except Exception as e:
                print(f"Error loading systems for map: {e}")
                self.after(0, lambda: self._show_error_in_list(str(e)))

        threading.Thread(target=load_systems, daemon=True).start()

    def _update_nearest_list(self, systems_with_distance):
        if self._is_closing:
            return
        try:
            if not self.winfo_exists() or not hasattr(self, 'scroll') or not self.scroll.winfo_exists():
                return
        except:
            return

        # Clear loading label
        for widget in self.scroll.winfo_children():
            widget.destroy()

        if not systems_with_distance:
            ctk.CTkLabel(self.scroll, text="No systems found",
                         font=ctk.CTkFont(size=12), text_color="#666666").pack(pady=20)
            return

        # Add system cards
        for sys, distance in systems_with_distance:
            try:
                card = ctk.CTkFrame(self.scroll, fg_color=SECONDARY_BG_COLOR,
                                    corner_radius=10, height=80)
                card.pack(fill="x", padx=10, pady=5)
                card.pack_propagate(False)

                # System name
                name = ctk.CTkLabel(card, text=sys["systems"],
                                    font=ctk.CTkFont(size=14, weight="bold"),
                                    text_color=TEXT_COLOR)
                name.pack(anchor="w", padx=10, pady=(10, 0))

                # Category
                category = ctk.CTkLabel(card, text=sys.get("category", "Unknown"),
                                        font=ctk.CTkFont(size=12),
                                        text_color=TEXT_SECONDARY)
                category.pack(anchor="w", padx=10, pady=(2, 0))

                # Distance
                dist = ctk.CTkLabel(card, text=f"{distance:.2f} LY",
                                    font=ctk.CTkFont(size=12, weight="bold"),
                                    text_color=ACCENT_COLOR)
                dist.pack(anchor="w", padx=10, pady=(2, 10))

                # Make card clickable
                card.bind("<Button-1>", lambda e, s=sys: self.center_on_system(s))
                name.bind("<Button-1>", lambda e, s=sys: self.center_on_system(s))
                category.bind("<Button-1>", lambda e, s=sys: self.center_on_system(s))
                dist.bind("<Button-1>", lambda e, s=sys: self.center_on_system(s))
            except Exception as e:
                print(f"Error creating system card: {e}")

    def _show_error_in_list(self, error_msg):
        if self._is_closing:
            return
        try:
            if not self.winfo_exists() or not hasattr(self, 'scroll') or not self.scroll.winfo_exists():
                return
        except:
            return

        # Clear loading label
        for widget in self.scroll.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.scroll, text=f"Error: {error_msg}",
                     font=ctk.CTkFont(size=12), text_color=DANGER_COLOR).pack(pady=20)

    def center_on_system(self, system):
        try:
            x = float(system["x"])
            y = float(system["y"])
            z = float(system["z"])
            self.center_on_coords(x, y, z)
        except Exception as e:
            print(f"Error centering on system: {e}")

    def center_on_coords(self, x, y, z):
        # Convert galactic coordinates to image coordinates
        img_x = ORIG_OFF_X - x / LY_PER_PIXEL
        img_y = ORIG_OFF_Y - z / LY_PER_PIXEL

        # Center the view on these coordinates
        self.canvas.xview_moveto((img_x - WINDOW_WIDTH / 2) / self.base_full.width)
        self.canvas.yview_moveto((img_y - WINDOW_HEIGHT / 2) / self.base_full.height)

        # Redraw
        self.draw_image()

    def setup_category_dropdown(self):
        if not hasattr(self, 'available_categories'):
            return

        # Clear existing checkboxes
        for cb in self.category_checkboxes:
            cb.destroy()
        self.category_checkboxes = []

        # Create scrollable frame for categories
        category_scroll = ctk.CTkScrollableFrame(self.category_dropdown_frame,
                                                width=260,
                                                height=240,
                                                fg_color="transparent")
        category_scroll.pack(padx=10, pady=10, fill="both", expand=True)

        # Add "All Categories" option
        all_var = ctk.BooleanVar(value="All Categories" in self.selected_categories)
        all_cb = ctk.CTkCheckBox(category_scroll, text="All Categories",
                                 variable=all_var,
                                 command=lambda: self._on_category_select("All Categories", all_var),
                                 font=ctk.CTkFont(size=13),
                                 fg_color=ACCENT_COLOR,
                                 hover_color=ACCENT_HOVER)
        all_cb.pack(anchor="w", pady=2)
        self.category_checkboxes.append(all_cb)

        # Add other categories
        for category in sorted(self.available_categories):
            var = ctk.BooleanVar(value=category in self.selected_categories)
            cb = ctk.CTkCheckBox(category_scroll, text=category,
                                variable=var,
                                command=lambda c=category, v=var: self._on_category_select(c, v),
                                font=ctk.CTkFont(size=13),
                                fg_color=ACCENT_COLOR,
                                hover_color=ACCENT_HOVER)
            cb.pack(anchor="w", pady=2)
            self.category_checkboxes.append(cb)

        # Add buttons
        btn_frame = ctk.CTkFrame(self.category_dropdown_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="Apply",
                     command=self.apply_category_filter,
                     fg_color=ACCENT_COLOR,
                     hover_color=ACCENT_HOVER,
                     font=ctk.CTkFont(size=13),
                     width=80, height=30).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="Cancel",
                     command=lambda: self.category_dropdown_frame.place_forget(),
                     fg_color=SECONDARY_BG_COLOR,
                     hover_color=TERTIARY_BG_COLOR,
                     font=ctk.CTkFont(size=13),
                     width=80, height=30).pack(side="right", padx=5)

    def _on_category_select(self, category, var):
        if category == "All Categories" and var.get():
            # If "All Categories" is selected, deselect others
            for cb in self.category_checkboxes[1:]:  # Skip "All Categories"
                cb.deselect()
            self.selected_categories = ["All Categories"]
        elif category == "All Categories" and not var.get():
            # If "All Categories" is deselected, select it again (can't have none)
            var.set(True)
        elif var.get():
            # If another category is selected, deselect "All Categories"
            if "All Categories" in self.selected_categories:
                self.category_checkboxes[0].deselect()  # Deselect "All Categories"
                self.selected_categories.remove("All Categories")
            if category not in self.selected_categories:
                self.selected_categories.append(category)
        else:
            # If a category is deselected, remove it from selected_categories
            if category in self.selected_categories:
                self.selected_categories.remove(category)
            # If no categories are selected, select "All Categories"
            if not self.selected_categories:
                self.category_checkboxes[0].select()  # Select "All Categories"
                self.selected_categories = ["All Categories"]

        # Update the category button text
        if "All Categories" in self.selected_categories:
            self.category_button.configure(text="All Categories")
        elif len(self.selected_categories) == 1:
            self.category_button.configure(text=self.selected_categories[0])
        else:
            self.category_button.configure(text=f"{len(self.selected_categories)} Categories")

    def toggle_category_dropdown(self):
        if self._dropdown_visible:
            self.category_dropdown_frame.place_forget()
            self._dropdown_visible = False
        else:
            # Find the admin_y position based on the category label position
            category_label_info = self.filter_content.children[next(name for name, child in self.filter_content.children.items() 
                                                                if isinstance(child, ctk.CTkLabel) and child.cget("text") == "CATEGORY FILTER")]
            admin_y = category_label_info.winfo_y()
            self.category_dropdown_frame.place(x=25, y=admin_y + 80)
            self._dropdown_visible = True

    def toggle_unvisited(self):
        if self.cb_unv.get() and hasattr(self.master_ref, 'supabase') and self.master_ref.supabase:
            supabase = self.master_ref.supabase
            # Get systems from main systems table
            systems_data = supabase.table("systems").select("systems,category,x,y,z").execute().data or []

            # Also get new discoveries from system_information table
            try:
                new_discoveries = supabase.table("system_information").select(
                    "system,category,x,y,z").execute().data or []
                for discovery in new_discoveries:
                    if discovery.get("x") and discovery.get("y") and discovery.get("z"):
                        # Convert to same format as systems table
                        discovery_data = {
                            "systems": discovery["system"],
                            "category": discovery.get("category", "New Discovery"),
                            "x": discovery["x"],
                            "y": discovery["y"],
                            "z": discovery["z"]
                        }
                        # Only add if not already in systems table
                        if not any(s["systems"] == discovery["system"] for s in systems_data):
                            systems_data.append(discovery_data)
            except Exception as e:
                print(f"Error loading new discoveries for map: {e}")

            # Get taken systems
            taken = {r["system"] for r in supabase.table("taken").select("system").execute().data or []}
            # Get POI systems
            pois = supabase.table("pois").select("system_name").execute().data or []
            poi_systems = {poi["system_name"] for poi in pois}
            # Filter out taken and POI systems
            unclaimed = [s for s in systems_data if s["systems"] not in taken and s["systems"] not in poi_systems]

            # Filter out Richard's categories
            richards_categories = []
            try:
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                richards_categories = [item["category"] for item in
                                       richards_response.data] if richards_response.data else []
            except:
                pass
            unclaimed = [s for s in unclaimed if
                         not any(cat in richards_categories for cat in parse_categories(s.get("category")))]

            # Apply category filter
            if "All Categories" not in self.selected_categories and self.selected_categories:
                unclaimed = [s for s in unclaimed if
                             categories_match_filter(s.get("category"), self.selected_categories)]

            self.unv_data = unclaimed
        else:
            self.unv_data = []
        self.draw_image()

    def toggle_your_claims(self):
        if self.cb_you.get() and hasattr(self.master_ref, 'supabase') and self.master_ref.supabase and hasattr(self.master_ref, 'cmdr_name'):
            supabase = self.master_ref.supabase
            cmdr_name = self.master_ref.cmdr_name
            # Get systems claimed by this commander
            your_claims = supabase.table("taken").select("system").eq("by_cmdr", cmdr_name).execute().data or []
            system_names = [r["system"] for r in your_claims]
            # Get systems from main systems table
            systems_data = supabase.table("systems").select("systems,category,x,y,z").in_("systems",
                                                                                          system_names).execute().data or []

            # Also check system_information table for new discoveries
            try:
                new_discoveries = supabase.table("system_information").select("system,category,x,y,z").in_("system",
                                                                                                           system_names).execute().data or []
                for discovery in new_discoveries:
                    if discovery.get("x") and discovery.get("y") and discovery.get("z"):
                        # Convert to same format as systems table
                        discovery_data = {
                            "systems": discovery["system"],
                            "category": discovery.get("category", "New Discovery"),
                            "x": discovery["x"],
                            "y": discovery["y"],
                            "z": discovery["z"]
                        }
                        # Only add if not already in systems table
                        if not any(s["systems"] == discovery["system"] for s in systems_data):
                            systems_data.append(discovery_data)
            except Exception as e:
                print(f"Error loading claimed new discoveries for map: {e}")

            # Filter out Richard's categories
            richards_categories = []
            try:
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                richards_categories = [item["category"] for item in
                                       richards_response.data] if richards_response.data else []
            except:
                pass
            systems_data = [s for s in systems_data if
                           not any(cat in richards_categories for cat in parse_categories(s.get("category")))]

            # Apply category filter
            if "All Categories" not in self.selected_categories and self.selected_categories:
                systems_data = [s for s in systems_data if
                               categories_match_filter(s.get("category"), self.selected_categories)]

            self.you_data = systems_data
        else:
            self.you_data = []
        self.draw_image()

    def toggle_others_claims(self):
        if self.cb_oth.get() and hasattr(self.master_ref, 'supabase') and self.master_ref.supabase and hasattr(self.master_ref, 'cmdr_name'):
            supabase = self.master_ref.supabase
            cmdr_name = self.master_ref.cmdr_name
            # Get systems claimed by other commanders
            others_claims = supabase.table("taken").select("system,by_cmdr").neq("by_cmdr", cmdr_name).execute().data or []
            system_names = [r["system"] for r in others_claims]
            # Get systems from main systems table
            systems_data = supabase.table("systems").select("systems,category,x,y,z").in_("systems",
                                                                                          system_names).execute().data or []

            # Also check system_information table for new discoveries
            try:
                new_discoveries = supabase.table("system_information").select("system,category,x,y,z").in_("system",
                                                                                                           system_names).execute().data or []
                for discovery in new_discoveries:
                    if discovery.get("x") and discovery.get("y") and discovery.get("z"):
                        # Convert to same format as systems table
                        discovery_data = {
                            "systems": discovery["system"],
                            "category": discovery.get("category", "New Discovery"),
                            "x": discovery["x"],
                            "y": discovery["y"],
                            "z": discovery["z"]
                        }
                        # Only add if not already in systems table
                        if not any(s["systems"] == discovery["system"] for s in systems_data):
                            systems_data.append(discovery_data)
            except Exception as e:
                print(f"Error loading others' claimed new discoveries for map: {e}")

            # Add by_cmdr field
            by_cmdr = {r["system"]: r["by_cmdr"] for r in others_claims}
            for sys in systems_data:
                sys["by_cmdr"] = by_cmdr.get(sys["systems"], "")

            # Filter out Richard's categories
            richards_categories = []
            try:
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                richards_categories = [item["category"] for item in
                                       richards_response.data] if richards_response.data else []
            except:
                pass
            systems_data = [s for s in systems_data if
                           not any(cat in richards_categories for cat in parse_categories(s.get("category")))]

            # Apply category filter
            if "All Categories" not in self.selected_categories and self.selected_categories:
                systems_data = [s for s in systems_data if
                               categories_match_filter(s.get("category"), self.selected_categories)]

            self.oth_data = systems_data
        else:
            self.oth_data = []
        self.draw_image()

    def toggle_potential_pois(self):
        if self.cb_pot_poi.get() and hasattr(self.master_ref, 'supabase') and self.master_ref.supabase:
            supabase = self.master_ref.supabase
            # Get potential POIs
            pot_pois = supabase.table("system_information").select("system,category,x,y,z").execute().data or []
            self.pot_poi_data = []
            for poi in pot_pois:
                if poi.get("x") and poi.get("y") and poi.get("z"):
                    # Convert to same format as systems table
                    poi_data = {
                        "systems": poi["system"],
                        "category": poi.get("category", "New Discovery"),
                        "x": poi["x"],
                        "y": poi["y"],
                        "z": poi["z"]
                    }
                    self.pot_poi_data.append(poi_data)

            # Filter out Richard's categories
            richards_categories = []
            try:
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                richards_categories = [item["category"] for item in
                                       richards_response.data] if richards_response.data else []
            except:
                pass
            self.pot_poi_data = [s for s in self.pot_poi_data if
                                not any(cat in richards_categories for cat in parse_categories(s.get("category")))]

            # Apply category filter
            if "All Categories" not in self.selected_categories and self.selected_categories:
                self.pot_poi_data = [s for s in self.pot_poi_data if
                                    categories_match_filter(s.get("category"), self.selected_categories)]
        else:
            self.pot_poi_data = []
        self.draw_image()

    def toggle_pois(self):
        if self.cb_poi.get() and hasattr(self.master_ref, 'supabase') and self.master_ref.supabase:
            supabase = self.master_ref.supabase
            # Get POIs
            pois = supabase.table("pois").select("system_name,category,x,y,z").execute().data or []
            self.poi_data = []
            for poi in pois:
                if poi.get("x") and poi.get("y") and poi.get("z"):
                    # Convert to same format as systems table
                    poi_data = {
                        "systems": poi["system_name"],
                        "category": poi.get("category", "POI"),
                        "x": poi["x"],
                        "y": poi["y"],
                        "z": poi["z"]
                    }
                    self.poi_data.append(poi_data)

            # Filter out Richard's categories
            richards_categories = []
            try:
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                richards_categories = [item["category"] for item in
                                       richards_response.data] if richards_response.data else []
            except:
                pass
            self.poi_data = [s for s in self.poi_data if
                            not any(cat in richards_categories for cat in parse_categories(s.get("category")))]

            # Apply category filter
            if "All Categories" not in self.selected_categories and self.selected_categories:
                self.poi_data = [s for s in self.poi_data if
                                categories_match_filter(s.get("category"), self.selected_categories)]
        else:
            self.poi_data = []
        self.draw_image()

    def toggle_all_cmdrs(self):
        if hasattr(self, 'cb_all_cmdrs') and self.cb_all_cmdrs.get() and hasattr(self.master_ref, 'supabase') and self.master_ref.supabase and hasattr(self.master_ref, 'is_admin') and self.master_ref.is_admin:
            supabase = self.master_ref.supabase
            # Get all commander locations
            try:
                cmdr_locations = supabase.table("cmdr_locations").select("cmdr,system,x,y,z").execute().data or []
                self.all_cmdrs_data = []
                for loc in cmdr_locations:
                    if loc.get("x") and loc.get("y") and loc.get("z"):
                        # Convert to same format as systems table
                        loc_data = {
                            "systems": loc["system"],
                            "category": "CMDR Location",
                            "x": loc["x"],
                            "y": loc["y"],
                            "z": loc["z"],
                            "cmdr": loc["cmdr"]
                        }
                        self.all_cmdrs_data.append(loc_data)
            except Exception as e:
                print(f"Error loading CMDR locations: {e}")
                self.all_cmdrs_data = []
        else:
            self.all_cmdrs_data = []
        self.draw_image()

    def refresh_all_filters(self):
        if self.cb_unv.get():
            self.toggle_unvisited()
        if self.cb_you.get():
            self.toggle_your_claims()
        if self.cb_oth.get():
            self.toggle_others_claims()
        if self.cb_pot_poi.get():
            self.toggle_potential_pois()
        if self.cb_poi.get():
            self.toggle_pois()
        if self.cb_done.get():
            self.toggle_done_systems()
        if hasattr(self, 'cb_all_cmdrs') and self.cb_all_cmdrs.get():
            self.toggle_all_cmdrs()

    def check_for_starpos_update(self):
        if self._is_closing:
            return
        self.after(5000, self.check_for_starpos_update)

    def _handle_click(self, event):
        # Ignore clicks on the sidebar
        if hasattr(self, 'current_sidebar_width'):
            mouse_x = event.x_root - self.winfo_rootx()
            if mouse_x <= self.current_sidebar_width:
                return

    def on_press(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.draw_image()

    def on_wheel(self, event):
        # Zoom in/out with mouse wheel
        if event.delta > 0:
            self.zoom = min(self.zoom * 1.1, MAX_ZOOM)
        else:
            self.zoom = max(self.zoom / 1.1, MIN_ZOOM)
        self.draw_image()

    def on_key(self, event):
        # Handle key presses
        if event.keysym == "plus" or event.keysym == "equal":
            self.zoom = min(self.zoom * 1.1, MAX_ZOOM)
            self.draw_image()
        elif event.keysym == "minus":
            self.zoom = max(self.zoom / 1.1, MIN_ZOOM)
            self.draw_image()
        elif event.keysym == "r":
            self.zoom = 1.0
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            self.draw_image()

    def draw_image(self):
        if self._is_closing:
            return
        if self._zr:
            self.after_cancel(self._zr)
        self._zr = self.after(50, self._draw_image_impl)

    def _draw_image_impl(self):
        if self._is_closing:
            return
        try:
            # Clear canvas
            self.canvas.delete("all")

            # Calculate visible region
            visible_width = WINDOW_WIDTH
            visible_height = WINDOW_HEIGHT

            # Create a new image for the visible region
            visible_img = Image.new("RGB", (visible_width, visible_height), "#0f0f0f")

            # Draw the base image
            if self.zoom <= 1.0:
                # Use medium resolution image for zoomed out view
                img = self.base_med
                scale_factor = self.zoom * (self.base_full.width / self.base_med.width)
            else:
                # Use full resolution image for zoomed in view
                img = self.base_full
                scale_factor = self.zoom

            # Calculate the size of the image after scaling
            scaled_width = int(img.width * scale_factor)
            scaled_height = int(img.height * scale_factor)

            # Resize the image
            if scale_factor != 1.0:
                scaled_img = img.resize((scaled_width, scaled_height), Resampling.LANCZOS)
            else:
                scaled_img = img

            # Calculate the position to paste the image
            paste_x = 0
            paste_y = 0

            # Paste the image onto the visible region
            visible_img.paste(scaled_img, (paste_x, paste_y))

            # Draw systems
            draw = ImageDraw.Draw(visible_img)

            # Draw current location
            if self.cb_loc.get() and hasattr(self.master_ref, 'current_coords') and self.master_ref.current_coords:
                try:
                    cx, cy, cz = self.master_ref.current_coords
                    # Convert galactic coordinates to image coordinates
                    img_x = ORIG_OFF_X - cx / LY_PER_PIXEL
                    img_y = ORIG_OFF_Y - cz / LY_PER_PIXEL
                    # Scale and offset for current view
                    x = int(img_x * scale_factor) + paste_x
                    y = int(img_y * scale_factor) + paste_y
                    # Draw current location
                    if 0 <= x < visible_width and 0 <= y < visible_height:
                        r = int(DOT_RADIUS * 1.5)
                        draw.ellipse((x - r, y - r, x + r, y + r), fill=ACCENT_COLOR)
                        draw.text((x + r + 5, y - 7), "You", fill=ACCENT_COLOR)
                except Exception as e:
                    print(f"Error drawing current location: {e}")

            # Draw unclaimed systems
            if self.unv_data:
                for sys in self.unv_data:
                    try:
                        x = float(sys["x"])
                        y = float(sys["y"])
                        z = float(sys["z"])
                        # Convert galactic coordinates to image coordinates
                        img_x = ORIG_OFF_X - x / LY_PER_PIXEL
                        img_y = ORIG_OFF_Y - z / LY_PER_PIXEL
                        # Scale and offset for current view
                        x = int(img_x * scale_factor) + paste_x
                        y = int(img_y * scale_factor) + paste_y
                        # Draw system
                        if 0 <= x < visible_width and 0 <= y < visible_height:
                            draw.ellipse((x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS), fill="#FFFFFF")
                    except Exception as e:
                        print(f"Error drawing unclaimed system: {e}")

            # Draw your claims
            if self.you_data:
                for sys in self.you_data:
                    try:
                        x = float(sys["x"])
                        y = float(sys["y"])
                        z = float(sys["z"])
                        # Convert galactic coordinates to image coordinates
                        img_x = ORIG_OFF_X - x / LY_PER_PIXEL
                        img_y = ORIG_OFF_Y - z / LY_PER_PIXEL
                        # Scale and offset for current view
                        x = int(img_x * scale_factor) + paste_x
                        y = int(img_y * scale_factor) + paste_y
                        # Draw system
                        if 0 <= x < visible_width and 0 <= y < visible_height:
                            draw.ellipse((x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS), fill=SUCCESS_COLOR)
                    except Exception as e:
                        print(f"Error drawing your claim: {e}")

            # Draw others' claims
            if self.oth_data:
                for sys in self.oth_data:
                    try:
                        x = float(sys["x"])
                        y = float(sys["y"])
                        z = float(sys["z"])
                        # Convert galactic coordinates to image coordinates
                        img_x = ORIG_OFF_X - x / LY_PER_PIXEL
                        img_y = ORIG_OFF_Y - z / LY_PER_PIXEL
                        # Scale and offset for current view
                        x = int(img_x * scale_factor) + paste_x
                        y = int(img_y * scale_factor) + paste_y
                        # Draw system
                        if 0 <= x < visible_width and 0 <= y < visible_height:
                            draw.ellipse((x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS), fill=WARNING_COLOR)
                    except Exception as e:
                        print(f"Error drawing others' claim: {e}")

            # Draw potential POIs
            if self.pot_poi_data:
                for sys in self.pot_poi_data:
                    try:
                        x = float(sys["x"])
                        y = float(sys["y"])
                        z = float(sys["z"])
                        # Convert galactic coordinates to image coordinates
                        img_x = ORIG_OFF_X - x / LY_PER_PIXEL
                        img_y = ORIG_OFF_Y - z / LY_PER_PIXEL
                        # Scale and offset for current view
                        x = int(img_x * scale_factor) + paste_x
                        y = int(img_y * scale_factor) + paste_y
                        # Draw system
                        if 0 <= x < visible_width and 0 <= y < visible_height:
                            r = int(DOT_RADIUS * 1.2)
                            draw.ellipse((x - r, y - r, x + r, y + r), fill=INFO_COLOR)
                    except Exception as e:
                        print(f"Error drawing potential POI: {e}")

            # Draw POIs
            if self.poi_data:
                for sys in self.poi_data:
                    try:
                        x = float(sys["x"])
                        y = float(sys["y"])
                        z = float(sys["z"])
                        # Convert galactic coordinates to image coordinates
                        img_x = ORIG_OFF_X - x / LY_PER_PIXEL
                        img_y = ORIG_OFF_Y - z / LY_PER_PIXEL
                        # Scale and offset for current view
                        x = int(img_x * scale_factor) + paste_x
                        y = int(img_y * scale_factor) + paste_y
                        # Draw system
                        if 0 <= x < visible_width and 0 <= y < visible_height:
                            r = int(DOT_RADIUS * 1.5)
                            draw.ellipse((x - r, y - r, x + r, y + r), fill=DANGER_COLOR)
                    except Exception as e:
                        print(f"Error drawing POI: {e}")

            # Draw done systems
            if self.done_data:
                for sys in self.done_data:
                    try:
                        x = float(sys["x"])
                        y = float(sys["y"])
                        z = float(sys["z"])
                        # Convert galactic coordinates to image coordinates
                        img_x = ORIG_OFF_X - x / LY_PER_PIXEL
                        img_y = ORIG_OFF_Y - z / LY_PER_PIXEL
                        # Scale and offset for current view
                        x = int(img_x * scale_factor) + paste_x
                        y = int(img_y * scale_factor) + paste_y
                        # Draw system
                        if 0 <= x < visible_width and 0 <= y < visible_height:
                            draw.rectangle((x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS), fill="#9B59B6")
                    except Exception as e:
                        print(f"Error drawing done system: {e}")

            # Draw all CMDR locations (admin only)
            if hasattr(self, 'cb_all_cmdrs') and self.cb_all_cmdrs.get() and self.all_cmdrs_data:
                for sys in self.all_cmdrs_data:
                    try:
                        x = float(sys["x"])
                        y = float(sys["y"])
                        z = float(sys["z"])
                        # Convert galactic coordinates to image coordinates
                        img_x = ORIG_OFF_X - x / LY_PER_PIXEL
                        img_y = ORIG_OFF_Y - z / LY_PER_PIXEL
                        # Scale and offset for current view
                        x = int(img_x * scale_factor) + paste_x
                        y = int(img_y * scale_factor) + paste_y
                        # Draw system
                        if 0 <= x < visible_width and 0 <= y < visible_height:
                            r = int(DOT_RADIUS * 1.2)
                            draw.ellipse((x - r, y - r, x + r, y + r), fill=DANGER_COLOR)
                            draw.text((x + r + 5, y - 7), sys.get("cmdr", "CMDR"), fill=DANGER_COLOR)
                    except Exception as e:
                        print(f"Error drawing CMDR location: {e}")

            # Convert to PhotoImage and display
            photo = ImageTk.PhotoImage(visible_img)
            if self.image_id:
                self.canvas.delete(self.image_id)
            self.image_id = self.canvas.create_image(0, 0, image=photo, anchor="nw")
            self.canvas.image = photo  # Keep a reference to prevent garbage collection

            # Add zoom indicator
            if self.label_id:
                self.canvas.delete(self.label_id)
            zoom_text = f"Zoom: {self.zoom:.1f}x"
            self.label_id = self.canvas.create_text(
                WINDOW_WIDTH - 80, WINDOW_HEIGHT - 20,
                text=zoom_text, fill="#FFFFFF", font=("Segoe UI", 10)
            )

        except Exception as e:
            print(f"Error drawing image: {e}")
