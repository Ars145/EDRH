import os
import json
import time
import threading
import re
import sys
import urllib.request
from io import BytesIO
import random
import colorsys

import customtkinter as ctk
from customtkinter import CTkImage
from tkinter import filedialog, font as tkFont, messagebox
from PIL import Image, ImageTk, ImageFile, ImageFilter, ImageEnhance
from PIL.Image import Resampling
from supabase import create_client

# Try to import requests for better image loading
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Note: Install 'requests' package for better image loading: pip install requests")

# ----------------------------
# Simple Configuration Variables (Edit these as needed)
# ----------------------------
APP_TITLE = "EDRH - Elite Dangerous Records Helper"
APP_VERSION = "v1.0 beta - There may be bugs with this plugin"
MAIN_BG_COLOR = "#0f0f0f"
CARD_BG_COLOR = "#1a1a1a"
SECONDARY_BG_COLOR = "#2b2b2b"
ACCENT_COLOR = "#FFA500"
ACCENT_HOVER = "#FFB52E"
TEXT_COLOR = "white"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#666666"

# ----------------------------
# Resource & Config helpers
# ----------------------------
# Determine if we're running as a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    BASE_DIR = sys._MEIPASS  # For bundled resources (images)
    EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))  # Where the .exe is located
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BASE_DIR

def resource(name: str) -> str:
    """Get path for bundled resources like images"""
    return os.path.join(BASE_DIR, name)

# Config file and other persistent files go next to the exe
CONFIG_FILE = os.path.join(EXE_DIR, "config.json")

def load_config():
    config_path = os.path.join(EXE_DIR, "config.json")
    return json.load(open(config_path)) if os.path.exists(config_path) else {}

def save_config(cfg):
    config_path = os.path.join(EXE_DIR, "config.json")
    json.dump(cfg, open(config_path, "w"), indent=2)

def save_current_journal_path(path):
    """Save current journal path to file"""
    try:
        journal_file = os.path.join(EXE_DIR, "CURRENT_JOURNAL.txt")
        with open(journal_file, "w") as f:
            f.write(path)
    except:
        pass

# ----------------------------
# Journal helpers (must be top-level)
# ----------------------------
def list_sorted_journals(jd):
    p = re.compile(r"Journal\.(\d{4}-\d{2}-\d{2}T\d{6})\.01\.log$")
    out = []
    for fn in os.listdir(jd):
        m = p.match(fn)
        if m:
            out.append((m.group(1), os.path.join(jd, fn)))
    out.sort(reverse=True)
    return [fp for _, fp in out]

def has_fsdjump(fp):
    try:
        for line in reversed(open(fp, encoding="utf-8").readlines()):
            if '"event":"FSDJump"' in line:
                return True
    except:
        pass
    return False

def find_latest_journal_with_fsdjump(jd):
    for fp in list_sorted_journals(jd):
        if has_fsdjump(fp):
            return fp
    return None

def extract_commander_name(fp):
    """Extract commander name from journal file - checks both Commander and LoadGame events"""
    try:
        with open(fp, encoding="utf-8") as f:
            for line in f:
                # Check for Commander event
                if '"event":"Commander"' in line:
                    m = re.search(r'"Name"\s*:\s*"([^"]+)"', line)
                    if m:
                        return m.group(1)
                # Also check for LoadGame event
                elif '"event":"LoadGame"' in line:
                    m = re.search(r'"Commander"\s*:\s*"([^"]+)"', line)
                    if m:
                        return m.group(1)
    except:
        pass
    return "Unknown"

def save_current_journal_path(path):
    open(resource("CURRENT_JOURNAL.txt"), "w").write(path)

def get_latest_journal_file(jd):
    """Get the absolute latest journal file (regardless of FSDJump)"""
    journals = list_sorted_journals(jd)
    return journals[0] if journals else None

# ----------------------------
# Supabase client setup
# ----------------------------
_cfg = load_config()
try:
    supabase = create_client(_cfg.get("supabase_url"), _cfg.get("supabase_key"))
except Exception:
    supabase = None
    print("⚠️ Supabase client not available – some features disabled.")

ImageFile.LOAD_TRUNCATED_IMAGES = True

# ----------------------------
# Constants
# ----------------------------
WINDOW_WIDTH     = 1200
WINDOW_HEIGHT    = 800
SIDEBAR_WIDTH    = 350  # Increased for screenshots
SIDEBAR_COLLAPSED = 50
FRAME_WIDTH      = 425
FRAME_HEIGHT     = 40
CMD_FRAME_X      = 30
CMD_FRAME_Y_OFF  = 520
SYS_FRAME_X      = 30
SYS_FRAME_Y_OFF  = 480

IMAGE_BUTTON_X   = 30
IMAGE_BUTTON_Y   = 30
IMAGE_BUTTON_SZ  = 400

SCROLL_X         = 10
SCROLL_Y         = 280
SCROLL_W         = SIDEBAR_WIDTH - 50
SCROLL_H         = 470

MIN_ZOOM         = 0.8
MAX_ZOOM         = 6.0
DOT_RADIUS       = 5
LY_PER_PIXEL     = 40.0
ORIG_OFF_X       = 1124
ORIG_OFF_Y       = 1749

DOSIS_BOLD       = 20
DOSIS_REG        = 16
LBL_SIZE         = 14
FILTER_BG        = "#2b2b2b"

VERSION_TEXT     = APP_VERSION

# ----------------------------
# Image Loading Helper with Caching
# ----------------------------
image_cache = {}

def load_image_from_url(url, size=(100, 100)):
    """Load an image from a URL with caching and return a CTkImage"""
    # Check cache first
    cache_key = f"{url}_{size[0]}x{size[1]}"
    if cache_key in image_cache:
        return image_cache[cache_key]
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        if HAS_REQUESTS:
            # Use requests if available (more reliable)
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
        else:
            # Fallback to urllib with headers
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=10)
            img_data = response.read()
            img = Image.open(BytesIO(img_data))
        
        # Resize image to fit
        img.thumbnail(size, Resampling.LANCZOS)
        photo = CTkImage(dark_image=img, size=(img.width, img.height))
        
        # Cache the image
        image_cache[cache_key] = photo
        return photo
    except Exception as e:
        print(f"Failed to load image from {url}: {e}")
        return None

# ----------------------------
# Category Images Cache
# ----------------------------
category_images = {}

def get_category_images():
    """Fetch category images from database"""
    global category_images
    if supabase and not category_images:
        try:
            response = supabase.table("preset_images").select("*").execute()
            if response.data:
                category_images = {item["category"]: item["image"] for item in response.data}
        except Exception as e:
            print(f"Error fetching category images: {e}")
    return category_images

# ----------------------------
# Category Color Management
# ----------------------------
def get_category_colors():
    """Load or create category colors, automatically assigning new colors to new categories"""
    # Default colors for existing categories
    default_colors = {
        "The Legend (False)": "#FF6B6B",
        "ringed ELW with tilted close landable": "#4ECDC4",
        "BarycentreWD+ Atmospheric Landable": "#45B7D1",
        "tilted water atmosphere body orbiting a tilted gas giant": "#96CEB4",
        "High inclined closely orbiting atmosphere body": "#FECA57",
        "Pandora (no blue giant tho)": "#48C9B0",
        "Highly inclined closely orbiting non-atmospheric": "#F97F51",
        "ringed exotic + landable tilted": "#B983FF"
    }
    
    # Load saved colors from config
    saved_colors = _cfg.get("category_colors", {})
    
    # Merge with defaults (defaults take precedence for consistency)
    all_colors = default_colors.copy()
    all_colors.update(saved_colors)
    
    return all_colors

def generate_unique_color(existing_colors):
    """Generate a unique color that's visually distinct from existing colors"""
    import colorsys
    
    existing_hex_values = list(existing_colors.values())
    
    # Convert existing colors to HSV for better comparison
    existing_hsv = []
    for hex_color in existing_hex_values:
        rgb = tuple(int(hex_color.lstrip('#')[i:i+2], 16)/255.0 for i in (0, 2, 4))
        hsv = colorsys.rgb_to_hsv(*rgb)
        existing_hsv.append(hsv)
    
    # Try to generate a visually distinct color
    max_attempts = 100
    for _ in range(max_attempts):
        # Generate random HSV values
        h = random.random()  # Hue: 0-1
        s = random.uniform(0.5, 1.0)  # Saturation: 50-100% (avoid grays)
        v = random.uniform(0.6, 0.9)  # Value: 60-90% (avoid too dark/light)
        
        # Check if this color is distinct enough from existing colors
        is_distinct = True
        for existing_h, existing_s, existing_v in existing_hsv:
            # Check if colors are too similar
            hue_diff = min(abs(h - existing_h), 1 - abs(h - existing_h))  # Circular difference
            if hue_diff < 0.1 and abs(s - existing_s) < 0.3 and abs(v - existing_v) < 0.3:
                is_distinct = False
                break
        
        if is_distinct:
            # Convert to RGB and then to hex
            rgb = colorsys.hsv_to_rgb(h, s, v)
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            return hex_color
    
    # Fallback: generate any random color if we couldn't find a distinct one
    return '#{:06x}'.format(random.randint(0, 0xFFFFFF))

def get_or_create_category_color(category):
    """Get color for a category, creating a new one if it doesn't exist"""
    colors = get_category_colors()
    
    if category not in colors:
        # Generate new color
        new_color = generate_unique_color(colors)
        colors[category] = new_color
        
        # Save to config
        if "category_colors" not in _cfg:
            _cfg["category_colors"] = {}
        _cfg["category_colors"][category] = new_color
        save_config(_cfg)
    
    return colors[category]

# ----------------------------
# Galaxy Map Viewer
# ----------------------------
class ZoomableMap(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_ref = master
        self.title("Galaxy Map Viewer")
        try: self.iconbitmap(resource("icon.ico"))
        except: pass
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color="#1e1e1e")
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()
        self.after(300, lambda: self.attributes("-topmost", False))
        
        self.sidebar_expanded = True
        self.current_sidebar_width = SIDEBAR_WIDTH
        self._is_closing = False  # Track if window is closing

        bold = (ctk.CTkFont(family="Dosis", size=DOSIS_BOLD, weight="bold")
                if "Dosis" in tkFont.families() else ctk.CTkFont(size=DOSIS_BOLD, weight="bold"))
        reg  = (ctk.CTkFont(family="Dosis", size=DOSIS_REG)
                if "Dosis" in tkFont.families() else ctk.CTkFont(size=DOSIS_REG))

        # Canvas FIRST (so sidebar appears on top)
        self.canvas = ctk.CTkCanvas(self, bg="#1e1e1e", highlightthickness=0)
        self.update_canvas_position()

        # Sidebar on top of canvas
        self.sidebar = ctk.CTkFrame(self, fg_color=FILTER_BG,
                                    width=SIDEBAR_WIDTH, height=WINDOW_HEIGHT,
                                    corner_radius=0)
        self.sidebar.place(x=0, y=0)
        
        # Filter content frame
        self.filter_content = ctk.CTkFrame(self.sidebar, fg_color=FILTER_BG)
        self.filter_content.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Toggle button (outside sidebar for better visibility)
        self.toggle_btn = ctk.CTkButton(self, text="◀", width=30, height=60,
                                       command=self.toggle_sidebar,
                                       fg_color="#444444", hover_color="#555555",
                                       corner_radius=0)
        self.toggle_btn.place(x=self.current_sidebar_width, y=WINDOW_HEIGHT//2 - 30)
        
        ctk.CTkLabel(self.filter_content, text="Filters & Settings",
                     font=bold, text_color="#FFA500").place(x=20, y=20)

        self.cb_loc = ctk.CTkCheckBox(self.filter_content, text="Show CMDR Location",
                                      font=reg, command=self.draw_image)
        self.cb_loc.place(x=20, y=70)

        self.cb_unv = ctk.CTkCheckBox(self.filter_content, text="Show Unclaimed",
                                      font=reg, command=self.toggle_unvisited)
        self.cb_unv.place(x=20, y=110)
        self.unv_data = []

        self.cb_you = ctk.CTkCheckBox(self.filter_content, text="Show Your Claims",
                                      font=reg, command=self.toggle_your_claims)
        self.cb_you.place(x=20, y=150)
        self.you_data = []

        self.cb_oth = ctk.CTkCheckBox(self.filter_content, text="Show Others' Claims",
                                      font=reg, command=self.toggle_others_claims)
        self.cb_oth.place(x=20, y=190)
        self.oth_data = []

        self.cb_pot_poi = ctk.CTkCheckBox(self.filter_content, text="Show Potential POIs",
                                          font=reg, command=self.toggle_potential_pois)
        self.cb_pot_poi.place(x=20, y=230)
        self.pot_poi_data = []

        self.cb_poi = ctk.CTkCheckBox(self.filter_content, text="Show POIs",
                                      font=reg, command=self.toggle_pois)
        self.cb_poi.place(x=20, y=270)
        self.poi_data = []

        # Admin-only filter
        admin_y = 310
        if self.master_ref.is_admin:
            self.cb_all_cmdrs = ctk.CTkCheckBox(self.filter_content, text="See All CMDR Locations",
                                                font=reg, command=self.toggle_all_cmdrs,
                                                fg_color="#dc3545", hover_color="#c82333",
                                                border_color="#dc3545", checkmark_color="white")
            self.cb_all_cmdrs.place(x=20, y=admin_y)
            self.all_cmdrs_data = []
            admin_y += 40

        # Nearest systems label with filter
        filter_header = ctk.CTkFrame(self.filter_content, fg_color="transparent")
        filter_header.place(x=20, y=admin_y, relwidth=0.9)
        
        ctk.CTkLabel(filter_header, text="Nearest Systems",
                    font=bold, text_color="#FFA500").pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self.filter_content,
                                             width=SCROLL_W, height=SCROLL_H - 100,
                                             fg_color=FILTER_BG)
        self.scroll.place(x=SCROLL_X, y=admin_y + 40)

        try:
            img = Image.open(resource("E47CDFX.png")).convert("RGB")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load galaxy map:\n{e}")
            self.destroy()
            return
        self.base_full = img
        self.base_med  = img.resize((800,800), Resampling.LANCZOS)

        self.zoom      = 1.0
        self._zr       = None
        self.image_id  = None
        self.label_id  = None

        # Bindings - bind mouse wheel to canvas specifically
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>",    self.on_drag)
        self.canvas.bind("<MouseWheel>", self.on_wheel)  # Bind to canvas only
        self.bind("<Key>", self.on_key)
        
        # Override close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Initial draw & update
        self.after(50,   self.draw_image)
        self.after(100,  self.update_nearest_in_filter)
        self.after(1000, self.check_for_starpos_update)

    def on_close(self):
        """Handle window close properly"""
        self._is_closing = True
        if self._zr:
            self.after_cancel(self._zr)
        # Cancel all pending after callbacks
        for after_id in self.tk.call('after', 'info'):
            self.after_cancel(after_id)
        self.destroy()

    def toggle_sidebar(self):
        """Toggle sidebar expansion"""
        self.sidebar_expanded = not self.sidebar_expanded
        target_width = SIDEBAR_WIDTH if self.sidebar_expanded else SIDEBAR_COLLAPSED
        
        # Animate sidebar
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
            self.toggle_btn.place_configure(x=new_width, y=WINDOW_HEIGHT//2 - 30)
            self.update_canvas_position()
            
            if new_width != target_width:
                self.after(10, animate)
            else:
                self.toggle_btn.configure(text="◀" if self.sidebar_expanded else "▶")
                # Hide/show filter content based on state
                if self.sidebar_expanded:
                    self.filter_content.place(x=0, y=0, relwidth=1, relheight=1)
                else:
                    self.filter_content.place_forget()
        
        animate()

    def update_canvas_position(self):
        """Update canvas position based on sidebar width"""
        if not self._is_closing:
            self.canvas.place(x=0, y=0, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

    def update_nearest_in_filter(self):
        """Update nearest systems in filter panel with screenshot support"""
        if self._is_closing or not self.master_ref.current_coords or not supabase:
            return
        
        # Clear current display
        for widget in self.scroll.winfo_children():
            widget.destroy()
        
        try:
            cx, cy, cz = self.master_ref.current_coords
            
            # Get all systems
            all_systems = supabase.table("systems").select("systems,category,x,y,z").execute().data or []
            
            # Get POIs to check for indicators
            pois = supabase.table("pois").select("system_name,potential_or_poi").execute().data or []
            poi_systems = {}
            for poi in pois:
                poi_systems[poi["system_name"]] = poi["potential_or_poi"]
            
            # Get category images
            cat_images = get_category_images()
            
            # Calculate distances
            systems_with_distance = []
            for sys in all_systems:
                if sys["systems"] != self.master_ref.system_name:
                    dx = sys["x"] - cx
                    dy = sys["y"] - cy
                    dz = sys["z"] - cz
                    distance = (dx*dx + dy*dy + dz*dz)**0.5
                    systems_with_distance.append({
                        "name": sys["systems"],
                        "category": sys["category"],
                        "distance": distance,
                        "image": cat_images.get(sys["category"], None)
                    })
            
            # Sort by distance
            systems_with_distance.sort(key=lambda x: x["distance"])
            
            # Display top 20 nearest systems with compact design
            for i, sys in enumerate(systems_with_distance[:20]):
                frame = ctk.CTkFrame(self.scroll, fg_color="#333333", corner_radius=8, height=75)
                frame.pack(fill="x", padx=5, pady=3)
                frame.pack_propagate(False)
                
                # Category color mapping
                cat_color = get_or_create_category_color(sys["category"]) if sys["category"] else "#666666"
                
                # Left color indicator strip
                color_strip = ctk.CTkFrame(frame, width=4, fg_color=cat_color, corner_radius=0)
                color_strip.place(x=0, y=0, relheight=1)
                
                # Category badge
                cat_badge = ctk.CTkFrame(frame, fg_color=cat_color, corner_radius=4,
                                       width=50, height=50)
                cat_badge.place(x=10, y=7.5)
                cat_badge.pack_propagate(False)
                
                # Category abbreviation
                abbrev = ''.join([word[0].upper() for word in sys["category"].split()[:2]])
                ctk.CTkLabel(cat_badge, text=abbrev[:2],
                           font=ctk.CTkFont(size=16, weight="bold"),
                           text_color="white").place(relx=0.5, rely=0.5, anchor="center")
                
                # System info
                info_frame = ctk.CTkFrame(frame, fg_color="transparent")
                info_frame.place(x=70, y=5, relwidth=0.6, relheight=0.9)
                
                # System name
                ctk.CTkLabel(info_frame, text=sys['name'],
                           font=ctk.CTkFont(size=12, weight="bold"),
                           text_color="white", anchor="w").pack(anchor="w")
                
                # Category (truncated)
                cat_text = sys['category']
                if len(cat_text) > 28:
                    cat_text = cat_text[:25] + "..."
                
                ctk.CTkLabel(info_frame, text=cat_text,
                           font=ctk.CTkFont(size=9),
                           text_color="#aaaaaa", anchor="w").pack(anchor="w", pady=(1, 0))
                
                # Distance
                ctk.CTkLabel(info_frame, text=f"{sys['distance']:.1f} LY",
                           font=ctk.CTkFont(size=10, weight="bold"),
                           text_color=cat_color, anchor="w").pack(anchor="w", pady=(1, 0))
                
                # Compact view button
                btn = ctk.CTkButton(frame, text="→", width=30, height=30,
                                   command=lambda s=sys['name']: self.master_ref.view_system(s, None),
                                   fg_color="transparent", hover_color="#444444",
                                   font=ctk.CTkFont(size=16),
                                   text_color=cat_color,
                                   corner_radius=15)
                btn.place(relx=0.95, rely=0.5, anchor="e")
        
        except Exception as e:
            print(f"Error updating nearest systems in filter: {e}")

    def toggle_unvisited(self):
        if self.cb_unv.get() and supabase:
            all_sys = supabase.table("systems").select("systems,category,x,y,z").execute().data or []
            taken   = {r["system"] for r in supabase.table("taken").select("system").execute().data or []}
            
            # Get POIs to exclude
            pois = supabase.table("pois").select("system_name").execute().data or []
            poi_systems = {poi["system_name"] for poi in pois}
            
            # Exclude both taken and POI systems
            self.unv_data = [rec for rec in all_sys if rec["systems"] not in taken and rec["systems"] not in poi_systems]
        else:
            self.unv_data = []
        self.draw_image()

    def toggle_your_claims(self):
        if self.cb_you.get() and supabase:
            cmdr = self.master_ref.cmdr_name
            recs = supabase.table("taken").select("system,by_cmdr").eq("by_cmdr", cmdr).execute().data or []
            names = [r["system"] for r in recs]
            data = supabase.table("systems").select("systems,category,x,y,z").in_("systems", names).execute().data or []
            for rec in data:
                rec["by_cmdr"] = cmdr
            self.you_data = data
        else:
            self.you_data = []
        self.draw_image()

    def toggle_others_claims(self):
        if self.cb_oth.get() and supabase:
            cmdr = self.master_ref.cmdr_name
            recs = supabase.table("taken").select("system,by_cmdr").neq("by_cmdr", cmdr).execute().data or []
            names = [r["system"] for r in recs]
            data = supabase.table("systems").select("systems,category,x,y,z").in_("systems", names).execute().data or []
            by = {r["system"]: r["by_cmdr"] for r in recs}
            for rec in data:
                rec["by_cmdr"] = by.get(rec["systems"], "")
            self.oth_data = data
        else:
            self.oth_data = []
        self.draw_image()

    def toggle_potential_pois(self):
        if self.cb_pot_poi.get() and supabase:
            pois = supabase.table("pois").select("*").eq("potential_or_poi", "Potential POI").execute().data or []
            self.pot_poi_data = []
            
            for poi in pois:
                # Get coordinates from systems table
                sys_data = supabase.table("systems").select("x,y,z,category").eq("systems", poi["system_name"]).execute()
                if sys_data.data:
                    self.pot_poi_data.append({
                        "systems": poi["system_name"],
                        "x": sys_data.data[0]["x"],
                        "y": sys_data.data[0]["y"],
                        "z": sys_data.data[0]["z"],
                        "category": sys_data.data[0]["category"]
                    })
        else:
            self.pot_poi_data = []
        self.draw_image()

    def toggle_pois(self):
        if self.cb_poi.get() and supabase:
            pois = supabase.table("pois").select("*").eq("potential_or_poi", "POI").execute().data or []
            self.poi_data = []
            
            for poi in pois:
                # Get coordinates from systems table
                sys_data = supabase.table("systems").select("x,y,z,category").eq("systems", poi["system_name"]).execute()
                if sys_data.data:
                    self.poi_data.append({
                        "systems": poi["system_name"],
                        "x": sys_data.data[0]["x"],
                        "y": sys_data.data[0]["y"],
                        "z": sys_data.data[0]["z"],
                        "category": sys_data.data[0]["category"]
                    })
        else:
            self.poi_data = []
        self.draw_image()

    def toggle_all_cmdrs(self):
        if self.cb_all_cmdrs.get() and supabase:
            cmdrs = supabase.table("commanders").select("*").execute().data or []
            self.all_cmdrs_data = cmdrs
        else:
            self.all_cmdrs_data = []
        self.draw_image()

    def draw_image(self):
        if self._is_closing:
            return
            
        try:
            if not self.winfo_exists():
                return
                
            im = self.get_med_resized()
            self.photo = ImageTk.PhotoImage(im)
            cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
            if not self.image_id:
                self.image_id = self.canvas.create_image(
                    cw//2, ch//2, image=self.photo, anchor="center", tags="background"
                )
            else:
                self.canvas.itemconfig(self.image_id, image=self.photo)
            self.canvas.tag_lower("background")

            for tag in ("unvisited","your","others","cmdr","all_cmdrs","pot_poi","poi"):
                self.canvas.delete(tag)
            if self.label_id:
                self.canvas.delete(self.label_id)

            self._draw_list(self.unv_data, "unvisited", "blue")
            self._draw_list(self.you_data,  "your",      "green")
            self._draw_list(self.oth_data,  "others",    "orange")
            self._draw_list(self.pot_poi_data, "pot_poi", "yellow")
            self._draw_list(self.poi_data, "poi", "gold")
            
            if self.master_ref.is_admin and hasattr(self, 'cb_all_cmdrs') and self.cb_all_cmdrs.get():
                self._draw_all_cmdrs()
            if self.cb_loc.get() and not (self.master_ref.is_admin and hasattr(self, 'cb_all_cmdrs') and self.cb_all_cmdrs.get()):
                self._draw_cmdr()
        except Exception as e:
            if not self._is_closing:
                print(f"Error in draw_image: {e}")

    def _draw_list(self, data, tag, color):
        if self._is_closing:
            return
            
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        im_w, im_h = self.get_med_resized().size
        x0, y0 = (cw-im_w)/2, (ch-im_h)/2
        scale = im_w/self.base_full.width

        for rec in data:
            px = ORIG_OFF_X + rec["x"]/LY_PER_PIXEL
            py = ORIG_OFF_Y - rec["z"]/LY_PER_PIXEL
            cx, cy = x0 + px*scale, y0 + py*scale
            dot = self.canvas.create_oval(
                cx-DOT_RADIUS, cy-DOT_RADIUS,
                cx+DOT_RADIUS, cy+DOT_RADIUS,
                fill=color, outline="white", width=1, tags=(tag, "dot")
            )
            text = f"{rec['systems']}\n{rec['category']}"
            if tag in ("your","others"):
                text += f"\nby {rec.get('by_cmdr','')}"
            self.canvas.tag_bind(dot, "<Enter>",
                                 lambda e, t=text: self._show_hover(e, t))
            self.canvas.tag_bind(dot, "<Leave>",
                                 lambda e: self._hide_label())
            self.canvas.tag_bind(dot, "<Button-3>",
                                 lambda e, s=rec["systems"], c=rec["category"]: self.master_ref.view_system(s, c))

    def _draw_cmdr(self):
        if self._is_closing:
            return
            
        pos = getattr(self.master_ref, "latest_starpos", None)
        if not pos: return
        xw, yw, zw = pos
        px = ORIG_OFF_X + xw/LY_PER_PIXEL
        py = ORIG_OFF_Y - zw/LY_PER_PIXEL
        im = self.get_med_resized()
        scale = im.width/self.base_full.width
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        x0, y0 = (cw-im.width)/2, (ch-im.height)/2
        cx, cy = x0 + px*scale, y0 + py*scale

        self.canvas.create_oval(
            cx-DOT_RADIUS, cy-DOT_RADIUS,
            cx+DOT_RADIUS, cy+DOT_RADIUS,
            fill="red", outline="white", width=1, tags=("cmdr", "dot")
        )
        txt = f"CMDR {self.master_ref.cmdr_name}\n{self.master_ref.system_name}"
        self.canvas.tag_bind("cmdr", "<Enter>",
                             lambda e, t=txt: self._show_hover(e, t))
        self.canvas.tag_bind("cmdr", "<Leave>",
                             lambda e: self._hide_label())
        self.canvas.tag_bind("cmdr", "<Button-3>",
                             lambda e: self.master_ref.view_system(self.master_ref.system_name, None))

    def _draw_all_cmdrs(self):
        if self._is_closing:
            return
            
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        im_w, im_h = self.get_med_resized().size
        x0, y0 = (cw-im_w)/2, (ch-im_h)/2
        scale = im_w/self.base_full.width

        for rec in self.all_cmdrs_data:
            if rec.get("starpos_x") is None:
                continue
            px = ORIG_OFF_X + rec["starpos_x"]/LY_PER_PIXEL
            py = ORIG_OFF_Y - rec["starpos_z"]/LY_PER_PIXEL
            cx, cy = x0 + px*scale, y0 + py*scale
            
            color = "red" if rec.get("cmdr_name") == self.master_ref.cmdr_name else "purple"
            
            dot = self.canvas.create_oval(
                cx-DOT_RADIUS, cy-DOT_RADIUS,
                cx+DOT_RADIUS, cy+DOT_RADIUS,
                fill=color, outline="white", width=1, tags=("all_cmdrs", "dot")
            )
            text = f"CMDR {rec['cmdr_name']}\n{rec.get('star_system', 'Unknown')}\nLast updated: {(rec.get('updated_at') or 'Unknown')[:10]}"
            self.canvas.tag_bind(dot, "<Enter>",
                                 lambda e, t=text: self._show_hover(e, t))
            self.canvas.tag_bind(dot, "<Leave>",
                                 lambda e: self._hide_label())
            self.canvas.tag_bind(dot, "<Button-3>",
                                 lambda e, s=rec.get('star_system'): self.master_ref.view_system(s, None) if s else None)

    def _show_hover(self, event, text):
        if hasattr(self, 'label_id') and self.label_id:
            self.canvas.delete(self.label_id)
        
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        lbl = ctk.CTkLabel(self.canvas,
                           text=text + "\nRight-click to view",
                           fg_color="#333333", text_color="white",
                           corner_radius=4, justify="center")
        self.label_id = self.canvas.create_window(cx, cy-DOT_RADIUS-5, window=lbl, anchor="s")
        self.canvas.tag_raise(self.label_id)

    def _hide_label(self):
        if hasattr(self, 'label_id') and self.label_id:
            self.canvas.delete(self.label_id)
            self.label_id = None

    def get_med_resized(self):
        z = max(MIN_ZOOM, min(self.zoom, MAX_ZOOM))
        # Use lower quality for better performance
        resample = Resampling.BILINEAR if z < 2.0 else Resampling.LANCZOS
        return self.base_med.resize(
            (int(self.base_med.width*z), int(self.base_med.height*z)),
            resample
        )

    def on_press(self, e):    self.canvas.scan_mark(e.x, e.y)
    def on_drag(self, e):     self.canvas.scan_dragto(e.x, e.y, gain=1)
    def on_wheel(self, e):
        # Improved zoom performance
        factor = 1.1 if e.delta > 0 else 0.9
        self.zoom = max(MIN_ZOOM, min(self.zoom * factor, MAX_ZOOM))
        if self._zr: self.after_cancel(self._zr)
        self._zr = self.after(50, self.draw_image)  # Reduced delay
    
    def on_key(self, e):
        if e.keysym=="Escape": self.on_close()
    
    def check_for_starpos_update(self):
        if self._is_closing:
            return
            
        cur = getattr(self.master_ref, "latest_starpos", None)
        if cur != getattr(self, "prev_pos", None):
            self.prev_pos = cur
            if self.cb_loc.get():
                self.draw_image()
            self.update_nearest_in_filter()
        if not self._is_closing:
            self.after(1000, self.check_for_starpos_update)

# ----------------------------
# Main Application
# ----------------------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config_data    = _cfg
        self.cmdr_name      = self.config_data.get("commander_name", "Unknown")
        self.system_name    = "Unknown"
        self.latest_starpos = None
        self.current_coords = None
        self.stop_event     = threading.Event()
        self.map_window     = None
        self.is_admin       = False

        self.title(APP_TITLE)
        try: self.iconbitmap(resource("icon.ico"))
        except: pass
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False,False)
        self.configure(fg_color=MAIN_BG_COLOR)
        # Make main window not stay on top
        self.attributes("-topmost", False)
        self.lower()  # Start it lowered
        self.update()  # Force update
        self.lift()   # Then bring it back to normal level

        bold = (ctk.CTkFont(family="Dosis", size=DOSIS_BOLD, weight="bold")
               if "Dosis" in tkFont.families() else ctk.CTkFont(size=DOSIS_BOLD, weight="bold"))

        # Main tab view
        self.tabview = ctk.CTkTabview(self, width=WINDOW_WIDTH-20, height=WINDOW_HEIGHT-40,
                                     fg_color=CARD_BG_COLOR,
                                     segmented_button_fg_color=SECONDARY_BG_COLOR,
                                     segmented_button_selected_color=ACCENT_COLOR,
                                     segmented_button_selected_hover_color=ACCENT_HOVER)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Add tabs
        self.main_tab = self.tabview.add("Main")
        self.info_tab = self.tabview.add("Information")
        self.tutorial_tab = self.tabview.add("Tutorial")
        
        # Main tab content
        self.setup_main_tab(bold)
        
        # Information tab content
        self.setup_info_tab()
        
        # Tutorial tab content
        self.setup_tutorial_tab()
        
        # Version label
        ctk.CTkLabel(self, text=VERSION_TEXT,
                    font=ctk.CTkFont(size=10),
                    text_color=TEXT_MUTED).place(relx=0.98, rely=0.98, anchor="se")

        # Check if already admin on startup
        self.check_admin_status()

        self.after(100, self.check_journal_popup)
        
    
    def refresh_all_data(self):
        """Refresh all data from database"""
        try:
            # Update current system info from journal
            if hasattr(self, 'current_journal_path') and self.current_journal_path:
                sysnm, pos = self.find_latest_journal_and_pos(self.current_journal_path)
                if sysnm:
                    self.system_name = sysnm
                    self.system_label.configure(text=sysnm)
                if pos:
                    self.latest_starpos = pos
                    self.current_coords = pos
            
            # Refresh nearest unclaimed
            self.find_nearest_unclaimed()
            
            # Refresh nearest systems
            self.update_nearest_systems()
            
            # Refresh commander location
            if self.current_coords:
                self.update_commander_location()
            
            # Refresh map if open
            if self.map_window and hasattr(self.map_window, 'winfo_exists'):
                try:
                    if self.map_window.winfo_exists():
                        self.map_window.refresh_all_filters()
                except:
                    pass
            
            # Show feedback
            self.btn_refresh.configure(text="✓ Refreshed")
            self.after(1000, lambda: self.btn_refresh.configure(text="🔄 Refresh"))
            
        except Exception as e:
            print(f"Error refreshing data: {e}")
            self.btn_refresh.configure(text="❌ Error")
            self.after(2000, lambda: self.btn_refresh.configure(text="🔄 Refresh"))
        
    

    def setup_main_tab(self, bold):
        """Setup main tab UI with modern theme"""
        # Create a dark background
        main_container = ctk.CTkFrame(self.main_tab, fg_color=MAIN_BG_COLOR, corner_radius=0)
        main_container.pack(fill="both", expand=True)
        
        # Left panel for system info
        left_panel = ctk.CTkFrame(main_container, fg_color=MAIN_BG_COLOR, width=500)
        left_panel.pack(side="left", fill="y", padx=(20, 10), pady=20)
        left_panel.pack_propagate(False)
        
        # CMDR and System Info Card
        info_card = ctk.CTkFrame(left_panel, fg_color=CARD_BG_COLOR, 
                                border_color="#333333", border_width=1, corner_radius=10)
        info_card.pack(fill="x", pady=(0, 20))
        
        # CMDR info
        cmdr_container = ctk.CTkFrame(info_card, fg_color="transparent")
        cmdr_container.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(cmdr_container, text="COMMANDER", 
                    font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(anchor="w")
        self.cmdr_label = ctk.CTkLabel(cmdr_container, text=self.cmdr_name,
                                      font=ctk.CTkFont(size=20, weight="bold"), 
                                      text_color=ACCENT_COLOR)
        self.cmdr_label.pack(anchor="w", pady=(5, 0))
        
        # Separator
        ctk.CTkFrame(info_card, height=1, fg_color="#333333").pack(fill="x", padx=20, pady=10)
        
        # System info
        sys_container = ctk.CTkFrame(info_card, fg_color="transparent")
        sys_container.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkLabel(sys_container, text="CURRENT SYSTEM", 
                    font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(anchor="w")
        self.system_label = ctk.CTkLabel(sys_container, text=self.system_name,
                                        font=ctk.CTkFont(size=20, weight="bold"), 
                                        text_color=ACCENT_COLOR)
        self.system_label.pack(anchor="w", pady=(5, 0))
        
        # Current System Actions Card
        actions_card = ctk.CTkFrame(left_panel, fg_color=CARD_BG_COLOR,
                                   border_color="#333333", border_width=1, corner_radius=10)
        actions_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(actions_card, text="CURRENT SYSTEM ACTIONS",
                    font=ctk.CTkFont(size=14, weight="bold"), 
                    text_color=ACCENT_COLOR).pack(pady=(15, 10), padx=20, anchor="w")
        
        btn_frame = ctk.CTkFrame(actions_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkButton(btn_frame, text="View System", 
                     command=lambda: self.view_system(self.system_name, None),
                     width=140, height=35,
                     fg_color=SECONDARY_BG_COLOR, hover_color="#333333").pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(btn_frame, text="Create POI", 
                     command=lambda: self.view_system(self.system_name, None),
                     width=140, height=35,
                     fg_color="#28a745", hover_color="#218838").pack(side="left")
        
        # Nearest Unclaimed Card
        unclaimed_card = ctk.CTkFrame(left_panel, fg_color=CARD_BG_COLOR,
                                     border_color="#333333", border_width=1, corner_radius=10)
        unclaimed_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(unclaimed_card, text="NEAREST UNCLAIMED",
                    font=ctk.CTkFont(size=14, weight="bold"), 
                    text_color=ACCENT_COLOR).pack(pady=(15, 10), padx=20, anchor="w")
        
        self.closest_label = ctk.CTkLabel(unclaimed_card, text="None",
                                         font=ctk.CTkFont(size=16), 
                                         text_color=TEXT_COLOR)
        self.closest_label.pack(padx=20, anchor="w")
        
        claim_btn_frame = ctk.CTkFrame(unclaimed_card, fg_color="transparent")
        claim_btn_frame.pack(fill="x", padx=20, pady=15)
        
        self.btn_view_closest = ctk.CTkButton(claim_btn_frame, text="View",
                                              state="disabled", command=self.view_closest, 
                                              width=100, height=35,
                                              fg_color=SECONDARY_BG_COLOR, hover_color="#333333")
        self.btn_view_closest.pack(side="left", padx=(0, 10))
        
        self.btn_claim_closest = ctk.CTkButton(claim_btn_frame, text="Claim",
                                               state="disabled", command=self.claim_closest, 
                                               width=100, height=35,
                                               fg_color="#007bff", hover_color="#0056b3")
        self.btn_claim_closest.pack(side="left")
        
        # Galaxy Map Button
        map_card = ctk.CTkFrame(left_panel, fg_color=CARD_BG_COLOR,
                               border_color=ACCENT_COLOR, border_width=2, corner_radius=10)
        map_card.pack(fill="both", expand=True)
        
        img = Image.open(resource("E47CDFX.png")).resize((300, 300), Resampling.LANCZOS)
        btn_img = CTkImage(dark_image=img, size=(300, 300))
        self.galaxy_btn = ctk.CTkButton(map_card, image=btn_img, text="GALAXY MAP",
                                        command=self.open_map,
                                        font=ctk.CTkFont(size=20, weight="bold"), 
                                        compound="bottom", fg_color="transparent",
                                        hover=False, text_color=ACCENT_COLOR)
        self.galaxy_btn.pack(padx=20, pady=20)
        
        # Right panel for nearest systems
        right_panel = ctk.CTkFrame(main_container, fg_color=MAIN_BG_COLOR)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 20), pady=20)
        
        # Nearest Systems Card
        nearest_card = ctk.CTkFrame(right_panel, fg_color=CARD_BG_COLOR,
                                   border_color="#333333", border_width=1, corner_radius=10)
        nearest_card.pack(fill="both", expand=True)
        
        # Header with filter
        header_frame = ctk.CTkFrame(nearest_card, fg_color=SECONDARY_BG_COLOR, 
                                   corner_radius=10, height=60)
        header_frame.pack(fill="x", padx=15, pady=15)
        header_frame.pack_propagate(False)
        
        ctk.CTkLabel(header_frame, text="NEAREST SYSTEMS",
                    font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color=ACCENT_COLOR).place(x=20, rely=0.5, anchor="w")
        
        # Filter dropdown
        self.nearest_filter = ctk.StringVar(value="All Systems")
        filter_dropdown = ctk.CTkComboBox(header_frame, 
                                        values=["All Systems", "Unclaimed Only", "Your Claims"],
                                        variable=self.nearest_filter,
                                        command=lambda x: self.update_nearest_systems(),
                                        width=150,
                                        state="readonly",
                                        fg_color="#333333",
                                        border_color="#444444",
                                        button_color="#555555",
                                        button_hover_color="#666666",
                                        dropdown_fg_color=SECONDARY_BG_COLOR,
                                        dropdown_hover_color="#444444")
        filter_dropdown.place(relx=0.95, rely=0.5, anchor="e")
        
        # Scrollable frame for systems
        self.nearest_scroll = ctk.CTkScrollableFrame(nearest_card,
                                                    fg_color=MAIN_BG_COLOR,
                                                    corner_radius=8)
        self.nearest_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Admin button - more subtle design
        self.btn_admin = ctk.CTkButton(main_container, text="🔐 Admin", 
                                      command=self.admin_login,
                                      width=80, height=30,
                                      fg_color="transparent", 
                                      hover_color="#333333",
                                      border_width=1,
                                      border_color="#666666",
                                      text_color="#999999")
        self.btn_admin.place(relx=0.98, rely=0.02, anchor="ne")
        
        # Add refresh button
        self.btn_refresh = ctk.CTkButton(main_container, text="🔄 Refresh", 
                                command=self.refresh_all_data,
                                width=100, height=30,
                                fg_color="transparent", 
                                hover_color="#333333",
                                border_width=1,
                                border_color="#666666",
                                text_color="#999999")
        self.btn_refresh.place(relx=0.88, rely=0.02, anchor="ne")
        
        # Update nearest systems periodically
        self.update_nearest_systems()

    def setup_info_tab(self):
        """Setup information tab with consistent theme"""
        info_container = ctk.CTkFrame(self.info_tab, fg_color=MAIN_BG_COLOR)
        info_container.pack(fill="both", expand=True)
        
        info_frame = ctk.CTkScrollableFrame(info_container, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(info_frame, text="Elite Dangerous Records Helper",
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color=ACCENT_COLOR).pack(pady=(0, 20))
        
        # Info sections
        sections = [
            ("About", "EDRH is a tool designed to help Elite Dangerous commanders track and manage system discoveries in specific regions of the galaxy."),
            ("Features", "• Real-time system tracking\n• POI management\n• Commander location sharing\n• System claiming\n• Interactive galaxy map\n• Nearest systems finder"),
            ("How to Use", "1. Select your Elite Dangerous journal folder\n2. The tool will automatically track your location\n3. Use the galaxy map to explore regions\n4. Claim systems you've discovered\n5. Mark systems as POIs"),
            ("Admin Features", "Admins have access to additional features:\n• View all commander locations\n• Manage system database\n• Access advanced filters"),
            ("Version", VERSION_TEXT)
        ]
        
        for title, content in sections:
            section_frame = ctk.CTkFrame(info_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
            section_frame.pack(fill="x", pady=10, padx=10)
            
            ctk.CTkLabel(section_frame, text=title,
                        font=ctk.CTkFont(size=18, weight="bold"),
                        text_color=ACCENT_COLOR).pack(pady=(10, 5), padx=20, anchor="w")
            
            ctk.CTkLabel(section_frame, text=content,
                        font=ctk.CTkFont(size=14),
                        text_color=TEXT_COLOR,
                        justify="left",
                        wraplength=700).pack(pady=(0, 10), padx=20, anchor="w")

    def setup_tutorial_tab(self):
        """Setup tutorial tab with consistent theme"""
        tutorial_container = ctk.CTkFrame(self.tutorial_tab, fg_color=MAIN_BG_COLOR)
        tutorial_container.pack(fill="both", expand=True)
        
        tutorial_frame = ctk.CTkScrollableFrame(tutorial_container, fg_color="transparent")
        tutorial_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(tutorial_frame, text="Getting Started Tutorial",
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color=ACCENT_COLOR).pack(pady=(0, 20))
        
        # Tutorial steps
        steps = [
            ("Step 1: Journal Setup", 
             "When you first launch EDRH, you'll be asked to select your Elite Dangerous journal folder.\n"
             "This is typically located at:\n"
             "C:\\Users\\[YourName]\\Saved Games\\Frontier Developments\\Elite Dangerous"),
            
            ("Step 2: Understanding the Interface",
             "• Main Tab: Shows your current location and nearest systems\n"
             "• Galaxy Map: Interactive map with filters\n"
             "• System Info: View and edit system details\n"
             "• POI Management: Mark interesting discoveries"),
            
            ("Step 3: Using the Galaxy Map",
             "• Left-click and drag to pan\n"
             "• Mouse wheel to zoom\n"
             "• Right-click on dots to view system info\n"
             "• Use filters to show/hide different types of systems"),
            
            ("Step 4: Claiming Systems",
             "• Systems you visit are automatically detected\n"
             "• Click 'Claim' to mark a system as yours\n"
             "• Only unclaimed systems can be claimed\n"
             "• Your claims appear in green on the map"),
            
            ("Step 5: Creating POIs",
             "• Visit a system to unlock POI editing\n"
             "• Use 'Current System Settings' for quick POI creation\n"
             "• Add descriptions and images to your discoveries\n"
             "• POIs help other commanders find interesting locations"),
            
            ("Step 6: Finding Nearest Systems",
             "• The 'Nearest Systems' panel shows closest systems\n"
             "• Categories are displayed with visual indicators\n"
             "• Click 'View' to see detailed information\n"
             "• Use this to plan your exploration route")
        ]
        
        for i, (title, content) in enumerate(steps, 1):
            step_frame = ctk.CTkFrame(tutorial_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
            step_frame.pack(fill="x", pady=10, padx=10)
            
            # Step header
            header_frame = ctk.CTkFrame(step_frame, fg_color="#333333", corner_radius=8)
            header_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(header_frame, text=f"{i}",
                        font=ctk.CTkFont(size=20, weight="bold"),
                        text_color=ACCENT_COLOR,
                        width=40, height=40).pack(side="left", padx=10)
            
            ctk.CTkLabel(header_frame, text=title,
                        font=ctk.CTkFont(size=16, weight="bold"),
                        text_color=TEXT_COLOR).pack(side="left", padx=10)
            
            ctk.CTkLabel(step_frame, text=content,
                        font=ctk.CTkFont(size=13),
                        text_color=TEXT_SECONDARY,
                        justify="left",
                        wraplength=650).pack(pady=(0, 10), padx=30, anchor="w")

    def current_system_settings(self):
        """Quick add current system as potential POI"""
        if not self.system_name or self.system_name == "Unknown":
            messagebox.showwarning("No System", "No system currently detected!")
            return
        
        if not supabase:
            messagebox.showerror("Error", "Database not available!")
            return
        
        # Check if already exists as POI
        existing = supabase.table("pois").select("*").eq("system_name", self.system_name).execute()
        if existing.data:
            messagebox.showinfo("Already Exists", f"{self.system_name} is already marked as a POI!")
            return
        
        # Create quick POI entry
        try:
            poi_data = {
                "system_name": self.system_name,
                "name": self.system_name,
                "potential_or_poi": "Potential POI",
                "submitter": self.cmdr_name,
                "discoverer": self.cmdr_name
            }
            
            # First try to get coordinates from journal (FSDJump)
            coords_added = False
            if self.current_coords:
                poi_data["coords_x"] = self.current_coords[0]
                poi_data["coords_y"] = self.current_coords[1]
                poi_data["coords_z"] = self.current_coords[2]
                coords_added = True
                print(f"Using journal coordinates for {self.system_name}: {self.current_coords}")
            
            # If no journal coords, try to get from systems table
            if not coords_added:
                sys_check = supabase.table("systems").select("x,y,z").eq("systems", self.system_name).execute()
                if sys_check.data:
                    poi_data["coords_x"] = sys_check.data[0].get("x", 0)
                    poi_data["coords_y"] = sys_check.data[0].get("y", 0)
                    poi_data["coords_z"] = sys_check.data[0].get("z", 0)
                    coords_added = True
                    print(f"Using systems table coordinates for {self.system_name}")
            
            # Only add POI if we have coordinates
            if not coords_added or (poi_data.get("coords_x") == 0 and poi_data.get("coords_y") == 0 and poi_data.get("coords_z") == 0):
                messagebox.showwarning("No Coordinates", f"Cannot create POI for {self.system_name} - no valid coordinates found!")
                return
            
            supabase.table("pois").insert(poi_data).execute()
            messagebox.showinfo("Success", f"{self.system_name} added as Potential POI with coordinates!")
            
            # Refresh map if open
            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                self.map_window.toggle_potential_pois()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add POI: {e}")

    def update_nearest_systems(self):
        """Update the nearest systems display with enhanced UI"""
        if not supabase or not self.current_coords:
            return
        
        try:
            # Clear current display
            for widget in self.nearest_scroll.winfo_children():
                widget.destroy()
            
            cx, cy, cz = self.current_coords
            
            # Get all systems
            all_systems = supabase.table("systems").select("systems,category,x,y,z").execute().data or []
            
            # Get filter value
            filter_type = self.nearest_filter.get() if hasattr(self, 'nearest_filter') else "All Systems"
            
            # Filter systems based on selection
            if filter_type == "Unclaimed Only":
                # Get taken systems and POIs to exclude
                taken = {r["system"] for r in supabase.table("taken").select("system").execute().data or []}
                pois = supabase.table("pois").select("system_name").execute().data or []
                poi_systems = {poi["system_name"] for poi in pois}
                
                # Filter to only unclaimed systems
                filtered_systems = [s for s in all_systems if s["systems"] not in taken and s["systems"] not in poi_systems]
            elif filter_type == "Your Claims":
                # Get only systems claimed by current commander
                your_claims = supabase.table("taken").select("system").eq("by_cmdr", self.cmdr_name).execute().data or []
                your_claim_names = {r["system"] for r in your_claims}
                filtered_systems = [s for s in all_systems if s["systems"] in your_claim_names]
            else:
                # All systems
                filtered_systems = all_systems
            
            # Get POIs to check for indicators
            pois = supabase.table("pois").select("system_name,potential_or_poi").execute().data or []
            poi_systems = {}
            for poi in pois:
                poi_systems[poi["system_name"]] = poi["potential_or_poi"]
            
            # Get category images
            cat_images = get_category_images()

# Get filter value
            filter_type = self.nearest_filter.get() if hasattr(self, 'nearest_filter') else "All Systems"
            
            # Apply filters based on selection
            if filter_type == "Unclaimed":
                # Get taken systems to exclude
                taken = {r["system"] for r in supabase.table("taken").select("system").execute().data or []}
                # Filter to only unclaimed systems (excluding POIs as well)
                all_systems = [s for s in all_systems if s["systems"] not in taken and s["systems"] not in poi_systems]
            elif filter_type == "POIs Only":
                # Only show systems that are POIs
                all_systems = [s for s in all_systems if s["systems"] in poi_systems]
            elif filter_type == "Non-POIs":
                # Show systems that are NOT POIs
                all_systems = [s for s in all_systems if s["systems"] not in poi_systems]
            # else "All" - no filtering needed
            
            # Calculate distances
            systems_with_distance = []
            for sys in filtered_systems:
                if sys["systems"] != self.system_name:
                    dx = sys["x"] - cx
                    dy = sys["y"] - cy
                    dz = sys["z"] - cz
                    distance = (dx*dx + dy*dy + dz*dz)**0.5
                    systems_with_distance.append({
                        "name": sys["systems"],
                        "category": sys["category"],
                        "distance": distance,
                        "image": cat_images.get(sys["category"], None)
                    })
            
            # Sort by distance
            systems_with_distance.sort(key=lambda x: x["distance"])
            
            # Display top 15 nearest systems with enhanced UI
            for i, sys in enumerate(systems_with_distance[:15]):
                # Main card frame with potential background
                card = ctk.CTkFrame(self.nearest_scroll, fg_color=SECONDARY_BG_COLOR, 
                                   corner_radius=12, height=120,
                                   border_color="#444444", border_width=1)
                card.pack(fill="x", padx=5, pady=5)
                card.pack_propagate(False)
                
                # Category color mapping
                cat_color = get_or_create_category_color(sys["category"]) if sys["category"] else "#666666"
                
                # Create background container first
                bg_container = ctk.CTkFrame(card, fg_color=SECONDARY_BG_COLOR, corner_radius=12)
                bg_container.place(x=0, y=0, relwidth=1, relheight=1)
                
                # Background image implementation
                if sys["image"]:
                    # Create placeholder for background
                    bg_placeholder = ctk.CTkLabel(bg_container, text="", fg_color=SECONDARY_BG_COLOR)
                    bg_placeholder.place(x=0, y=0, relwidth=1, relheight=1)
                    
                    # Load background image asynchronously
                    def load_bg_image(url, container, placeholder):
                        try:
                            # Load a larger version for background
                            if HAS_REQUESTS:
                                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                                response = requests.get(url, headers=headers, timeout=10)
                                response.raise_for_status()
                                img = Image.open(BytesIO(response.content))
                            else:
                                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                                response = urllib.request.urlopen(req, timeout=10)
                                img_data = response.read()
                                img = Image.open(BytesIO(img_data))
                            
                            # Resize to fit card width while maintaining aspect ratio
                            card_width = 590  # Approximate card width
                            card_height = 120
                            
                            # Calculate dimensions to cover the card
                            img_ratio = img.width / img.height
                            card_ratio = card_width / card_height
                            
                            if img_ratio > card_ratio:
                                # Image is wider - fit to height
                                new_height = card_height
                                new_width = int(card_height * img_ratio)
                            else:
                                # Image is taller - fit to width
                                new_width = card_width
                                new_height = int(card_width / img_ratio)
                            
                            img = img.resize((new_width, new_height), Resampling.LANCZOS)
                            
                            # Apply blur effect for better readability
                            img = img.filter(ImageFilter.GaussianBlur(radius=3))
                            
                            # Darken the image
                            enhancer = ImageEnhance.Brightness(img)
                            img = enhancer.enhance(0.4)  # Darken to 40% brightness
                            
                            photo = CTkImage(dark_image=img, size=(new_width, new_height))
                            
                            if container.winfo_exists():
                                container.after(0, lambda: apply_bg_image(placeholder, photo))
                        except Exception as e:
                            print(f"Failed to load background image: {e}")
                    
                    def apply_bg_image(placeholder, photo):
                        if placeholder.winfo_exists():
                            placeholder.configure(image=photo)
                            placeholder.image = photo
                    
                    # Import required modules for image processing
                    from PIL import ImageFilter, ImageEnhance
                    
                    # Start loading in background
                    threading.Thread(target=load_bg_image, 
                                   args=(sys["image"], bg_container, bg_placeholder), 
                                   daemon=True).start()
                
                # Add semi-transparent overlay for better readability
                overlay = ctk.CTkFrame(card, fg_color=SECONDARY_BG_COLOR, corner_radius=12)
                overlay.place(x=0, y=0, relwidth=1, relheight=1)
                
                # Create a darker overlay effect by adding another layer
                if sys["image"]:
                    overlay2 = ctk.CTkFrame(card, fg_color="#000000", corner_radius=12)
                    overlay2.place(x=0, y=0, relwidth=1, relheight=1)
                    overlay2.configure(fg_color=("#000000", "#000000"))
                
                # Category indicator bar at top
                cat_bar = ctk.CTkFrame(card, fg_color=cat_color, height=4, corner_radius=2)
                cat_bar.place(x=0, y=0, relwidth=1)
                
                # Left side - Image container (only show if no background image)
                if not sys["image"]:
                    img_outer = ctk.CTkFrame(card, width=100, height=100, 
                                            fg_color="#0f0f0f", corner_radius=8)
                    img_outer.place(x=10, y=10)
                    img_outer.pack_propagate(False)
                    
                    # Inner image frame
                    img_container = ctk.CTkFrame(img_outer, width=90, height=90,
                                               fg_color=CARD_BG_COLOR, corner_radius=6)
                    img_container.place(relx=0.5, rely=0.5, anchor="center")
                    img_container.pack_propagate(False)
                    
                    # Default placeholder
                    placeholder = ctk.CTkFrame(img_container, fg_color=cat_color, 
                                             corner_radius=4, width=80, height=80)
                    placeholder.place(relx=0.5, rely=0.5, anchor="center")
                    
                    abbrev = ''.join([word[0].upper() for word in sys["category"].split()[:2]])
                    ctk.CTkLabel(placeholder, text=abbrev,
                               font=ctk.CTkFont(size=22, weight="bold"),
                               text_color=TEXT_COLOR).place(relx=0.5, rely=0.5, anchor="center")
                
                # Middle - System info (adjust position based on whether image box is shown)
                info_x = 125 if not sys["image"] else 20
                info_width = 215 if not sys["image"] else 330
                
                info_frame = ctk.CTkFrame(card, fg_color="transparent", width=info_width, height=90)
                info_frame.place(x=info_x, y=15)
                info_frame.pack_propagate(False)
                
                # System name
                ctk.CTkLabel(info_frame, text=sys['name'],
                           font=ctk.CTkFont(size=16, weight="bold"),
                           text_color=TEXT_COLOR, anchor="w").pack(anchor="w")
                
                # Category - with proper wrapping
                ctk.CTkLabel(info_frame, text=sys['category'],
                           font=ctk.CTkFont(size=12),
                           text_color=TEXT_SECONDARY, 
                           anchor="w",
                           justify="left",
                           wraplength=215).pack(anchor="w", pady=(5, 0))  # 250 pixel width
                
                # POI indicator if applicable
                if sys["name"] in poi_systems:
                    poi_type = poi_systems[sys["name"]]
                    if poi_type == "POI":
                        poi_badge = ctk.CTkFrame(info_frame, fg_color="#28a745", corner_radius=3)
                        poi_badge.pack(anchor="w", pady=(5, 0))
                        ctk.CTkLabel(poi_badge, text="✦ POI",
                                   font=ctk.CTkFont(size=10, weight="bold"),
                                   text_color="white").pack(padx=6, pady=1)
                    else:  # Potential POI
                        poi_badge = ctk.CTkFrame(info_frame, fg_color="#ffc107", corner_radius=3)
                        poi_badge.pack(anchor="w", pady=(5, 0))
                        ctk.CTkLabel(poi_badge, text="◎ Potential POI",
                                   font=ctk.CTkFont(size=10, weight="bold"),
                                   text_color="#000000").pack(padx=6, pady=1)
                
                # Right side - Buttons aligned
                button_container = ctk.CTkFrame(card, fg_color="transparent", width=170, height=40)
                button_container.place(relx=0.95, rely=0.5, anchor="e")
                button_container.pack_propagate(False)
                
                # Distance badge (aligned left of VIEW button)
                dist_badge = ctk.CTkFrame(button_container, fg_color=cat_color, corner_radius=4)
                dist_badge.pack(side="left", padx=(0, 10))
                
                ctk.CTkLabel(dist_badge, text=f"{sys['distance']:.1f} LY",
                           font=ctk.CTkFont(size=11, weight="bold"),
                           text_color=TEXT_COLOR).pack(padx=8, pady=2)
                
                # View button
                btn = ctk.CTkButton(button_container, text="VIEW", width=70, height=35,
                                   command=lambda s=sys['name']: self.view_system(s, None),
                                   fg_color=cat_color, hover_color=cat_color,
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   border_width=2, border_color=cat_color)
                btn.pack(side="right")
                
                # Hover effect
                def on_enter(e, card=card, color=cat_color):
                    if card.winfo_exists():
                        card.configure(border_color=color, border_width=2)
                
                def on_leave(e, card=card):
                    if card.winfo_exists():
                        card.configure(border_color="#444444", border_width=1)
                
                card.bind("<Enter>", on_enter)
                card.bind("<Leave>", on_leave)
        
        except Exception as e:
            print(f"Error updating nearest systems: {e}")

    def check_admin_status(self):
        """Check if current commander is already an admin"""
        if supabase and self.cmdr_name != "Unknown":
            try:
                resp = supabase.table("all_admins").select("*").eq("name", self.cmdr_name).eq("passed_check", True).maybe_single().execute()
                if resp and resp.data:
                    self.is_admin = True
                    if hasattr(self, 'btn_admin'):
                        self.btn_admin.destroy()
                    
                    # Create admin label in top right
                    self.admin_label = ctk.CTkLabel(self.main_tab if hasattr(self, 'main_tab') else self, 
                                                   text=f"CMDR {self.cmdr_name}: Admin",
                                                   font=ctk.CTkFont(size=14, weight="bold"),
                                                   text_color="#dc3545")
                    self.admin_label.place(relx=0.98, rely=0.02, anchor="ne")
                    
                    # Add logout button below admin label
                    self.btn_logout = ctk.CTkButton(self.main_tab if hasattr(self, 'main_tab') else self, 
                                                   text="Logout",
                                                   command=self.admin_logout,
                                                   width=80, height=25,
                                                   fg_color="#dc3545", hover_color="#c82333")
                    self.btn_logout.place(relx=0.98, rely=0.06, anchor="ne")
            except Exception as e:
                print(f"Error checking admin status: {e}")

    def view_closest(self):
        if hasattr(self, "closest"):
            self.view_system(self.closest["systems"], self.closest.get("category"))

    def claim_closest(self):
        if hasattr(self, "closest") and supabase:
            visited = (self.system_name == self.closest["systems"])
            supabase.table("taken").insert({
                "system": self.closest["systems"],
                "by_cmdr": self.cmdr_name,
                "visited": visited
            }).execute()
            self.find_nearest_unclaimed()
            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                self.map_window.toggle_unvisited()
                self.map_window.toggle_your_claims()

    def find_nearest_unclaimed(self):
        if not supabase or not self.current_coords:
            return
        cx, cy, cz = self.current_coords
        systems = supabase.table("systems").select("systems,category,x,y,z").execute().data or []
        taken   = {r["system"] for r in supabase.table("taken").select("system").execute().data or []}
        
        # Get POIs to exclude from unclaimed
        pois = supabase.table("pois").select("system_name").execute().data or []
        poi_systems = {poi["system_name"] for poi in pois}
        
        # Exclude both taken and POI systems
        unclaimed = [s for s in systems if s["systems"] not in taken and s["systems"] not in poi_systems]
        
        best, best_d2 = None, None
        for rec in unclaimed:
            dx, dy, dz = rec["x"]-cx, rec["y"]-cy, rec["z"]-cz
            d2 = dx*dx + dy*dy + dz*dz
            if best is None or d2 < best_d2:
                best, best_d2 = rec, d2
        if best:
            self.closest = best
            self.closest_label.configure(text=f"{best['systems']} - {(best_d2**0.5):.2f} LY")
            self.btn_view_closest.configure(state="normal")
            self.btn_claim_closest.configure(state="normal")
        else:
            self.closest_label.configure(text="None")
            self.btn_view_closest.configure(state="disabled")
            self.btn_claim_closest.configure(state="disabled")

    def open_map(self):
        if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
            self.map_window.lift()
        else:
            self.map_window = ZoomableMap(self)

    def check_system_visited_in_journals(self, system_name):
        """Check all journal files to see if commander has visited this system"""
        if not _cfg.get("journal_path"):
            return False
        
        try:
            journal_path = _cfg["journal_path"]
            for filename in os.listdir(journal_path):
                if filename.startswith("Journal.") and filename.endswith(".log"):
                    filepath = os.path.join(journal_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            for line in f:
                                if '"event":"FSDJump"' in line or '"event":"Location"' in line:
                                    data = json.loads(line)
                                    if data.get("StarSystem") == system_name:
                                        return True
                    except:
                        continue
        except:
            pass
        return False

    def view_system(self, system_name, category):
        """Creates a popup window to view POI information with tabs for details and editing."""
        if not system_name:
            return
        
        # Create the popup window with modern theme
        popup = ctk.CTkToplevel(self)
        popup.title(f"POI: {system_name}")
        popup.geometry("800x650")
        popup.resizable(True, True)
        popup.transient(self)
        popup.grab_set()
        popup.configure(fg_color=MAIN_BG_COLOR)
        popup.attributes("-topmost", True)
        popup.lift()
        popup.focus_force()
        
        try:
            popup.iconbitmap(resource("icon.ico"))
        except:
            pass
        
        # Create fonts
        bold_font = ctk.CTkFont(family="Dosis", size=18, weight="bold") if "Dosis" in tkFont.families() else ctk.CTkFont(size=18, weight="bold")
        reg_font = ctk.CTkFont(family="Dosis", size=14) if "Dosis" in tkFont.families() else ctk.CTkFont(size=14)
        
        # Create tabview with modern colors
        tabview = ctk.CTkTabview(popup, width=780, height=610,
                                fg_color=CARD_BG_COLOR,
                                segmented_button_fg_color=SECONDARY_BG_COLOR,
                                segmented_button_selected_color=ACCENT_COLOR,
                                segmented_button_selected_hover_color=ACCENT_HOVER)
        tabview.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Get data from Supabase
        poi_data = None
        claim_data = None
        system_info = None
        is_visited = False
        journal_visited = False
        system_in_database = False
        systems_check = None
        
        if supabase:
            try:
                # Check if system exists in systems table
                systems_check = supabase.table("systems").select("*").eq("systems", system_name).execute()
                system_in_database = bool(systems_check.data)
                
                # Check if system is visited in database
                visited_check = supabase.table("taken").select("*").eq("system", system_name).eq("visited", True).execute()
                is_visited = bool(visited_check.data)
                
                # Check journal files for actual visit
                journal_visited = self.check_system_visited_in_journals(system_name)
                
                # Get from pois table if it exists
                poi_response = supabase.table("pois").select("*").eq("system_name", system_name).execute()
                if poi_response.data:
                    poi_data = poi_response.data[0]
                
                # Get from system_information table
                sys_info_response = supabase.table("system_information").select("*").eq("system", system_name).execute()
                if sys_info_response.data:
                    system_info = sys_info_response.data[0]
                    # Convert to POI-like format for display if no POI data
                    if not poi_data:
                        poi_data = {
                            "name": system_info.get("name", system_name),
                            "system_name": system_info.get("system"),
                            "coords_x": float(system_info.get("x", 0)) if system_info.get("x") else 0,
                            "coords_y": float(system_info.get("y", 0)) if system_info.get("y") else 0,
                            "coords_z": float(system_info.get("z", 0)) if system_info.get("z") else 0,
                            "description": system_info.get("description"),
                            "image_path": system_info.get("images")
                        }
                
                # If still no data, try old systems table
                if not poi_data and not system_info and system_in_database:
                    system_data = systems_check.data[0]
                    poi_data = {
                        "system_name": system_data.get("systems"),
                        "coords_x": system_data.get("x"),
                        "coords_y": system_data.get("y"),
                        "coords_z": system_data.get("z"),
                        "description": system_data.get("category")
                    }
                
                # Get claim information
                claim_response = supabase.table("taken").select("*").eq("system", system_name).execute()
                if claim_response.data:
                    claim_data = claim_response.data[0]
            except Exception as e:
                print(f"Error fetching data: {e}")
        
        # Add tabs
        info_tab = tabview.add("System Info")
        if is_visited or poi_data:
            poi_tab = tabview.add("POI")
        edit_tab = tabview.add("Edit Info")
        
        # --- SYSTEM INFO TAB ---
        info_frame = ctk.CTkScrollableFrame(info_tab, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # System name header with modern design
        header_frame = ctk.CTkFrame(info_frame, fg_color=CARD_BG_COLOR, 
                                   border_color=ACCENT_COLOR, border_width=2, corner_radius=10)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Category image placeholder
        img_frame = ctk.CTkFrame(header_frame, fg_color=MAIN_BG_COLOR, 
                                width=80, height=80, corner_radius=8)
        img_frame.pack(side="left", padx=15, pady=15)
        img_frame.pack_propagate(False)
        
        # Get category color
        cat_color = "#666666"
        if poi_data:
            category = poi_data.get("description", "")
            cat_color = get_or_create_category_color(category) if category else "#666666"
        
        # Category indicator in image frame
        cat_indicator = ctk.CTkFrame(img_frame, fg_color=cat_color, corner_radius=6)
        cat_indicator.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.8)
        
        # System info next to image
        info_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_content.pack(side="left", fill="both", expand=True, padx=(0, 15), pady=15)
        
        ctk.CTkLabel(info_content, text=system_name, 
                    font=ctk.CTkFont(size=24, weight="bold"), 
                    text_color=ACCENT_COLOR).pack(anchor="w")
        
        if poi_data:
            ctk.CTkLabel(info_content, text=poi_data.get("description", "Unknown Category"),
                        font=ctk.CTkFont(size=14), 
                        text_color=TEXT_SECONDARY).pack(anchor="w", pady=(5, 0))
        elif not system_in_database:
            ctk.CTkLabel(info_content, text="System not in records database",
                        font=ctk.CTkFont(size=14), 
                        text_color="#FF6B6B").pack(anchor="w", pady=(5, 0))
        
        # Display basic system information
        if poi_data or system_info:
            data_to_show = poi_data if poi_data else system_info
            
            # Calculate distance from Sol
            try:
                if system_in_database and systems_check.data:
                    # System in database - get coords from systems table
                    x_val = float(systems_check.data[0].get('x', 0))
                    y_val = float(systems_check.data[0].get('y', 0))
                    z_val = float(systems_check.data[0].get('z', 0))
                    distance = (x_val**2 + y_val**2 + z_val**2)**0.5
                    distance_str = f"{distance:.2f} LY"
                else:
                    # System not in database - try to use current journal coordinates
                    if self.system_name == system_name and self.latest_starpos:
                        x_val, y_val, z_val = self.latest_starpos
                        distance = (x_val**2 + y_val**2 + z_val**2)**0.5
                        distance_str = f"{distance:.2f} LY"
                    else:
                        # No coordinates available
                        distance_str = "N/A"
                        x_val = y_val = z_val = 0
            except (ValueError, TypeError):
                distance_str = "N/A"
                x_val = y_val = z_val = 0

            # Get query category from systems table
            query_category = "No category available"
            if system_in_database and systems_check.data:
                query_category = systems_check.data[0].get("category", "Unknown")
            
            info_items = [
                ("System Name:", data_to_show.get("system_name", system_name)),
                ("Coordinates:", f"X: {x_val if x_val else 'N/A'}, Y: {y_val if y_val else 'N/A'}, Z: {z_val if z_val else 'N/A'}"),
                ("Distance from Sol:", distance_str),
                ("Query Category:", query_category)
            ]
            
            # Add system description if available
            if system_info and system_info.get("description"):
                info_items.append(("Description:", system_info.get("description")))
            
            for label, value in info_items:
                row_frame = ctk.CTkFrame(info_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=8)
                row_frame.pack(fill="x", pady=3)
                
                content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                content_frame.pack(fill="x", padx=15, pady=10)
                
                ctk.CTkLabel(content_frame, text=label, font=reg_font, 
                            text_color=ACCENT_COLOR, width=140, anchor="w").pack(side="left", anchor="n" if label == "Description:" else "center")
                ctk.CTkLabel(content_frame, text=str(value), font=reg_font, 
                            text_color=TEXT_COLOR, anchor="w", wraplength=400).pack(side="left", padx=(10, 0), anchor="n" if label == "Description:" else "center")
        elif not system_in_database:
            # System not in database - try to get coords from current position
            coords_text = "Unknown"
            if self.system_name == system_name and self.latest_starpos:
                x, y, z = self.latest_starpos
                coords_text = f"X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}"
                distance = (x**2 + y**2 + z**2)**0.5
                distance_str = f"{distance:.2f} LY"
            else:
                coords_text = "Coordinates not available"
                distance_str = "N/A"
            
            info_items = [
                ("System Name:", system_name),
                ("Coordinates:", coords_text),
                ("Distance from Sol:", distance_str),
                ("Query Category:", "System not in records database")
            ]
            
            for label, value in info_items:
                row_frame = ctk.CTkFrame(info_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=8)
                row_frame.pack(fill="x", pady=3)
                
                content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                content_frame.pack(fill="x", padx=15, pady=10)
                
                ctk.CTkLabel(content_frame, text=label, font=reg_font, 
                            text_color=ACCENT_COLOR, width=140, anchor="w").pack(side="left")
                ctk.CTkLabel(content_frame, text=str(value), font=reg_font, 
                            text_color=TEXT_COLOR if label != "Query Category:" else "#FF6B6B", 
                            anchor="w", wraplength=500).pack(side="left", padx=(10, 0))
        
        # Category Image Display (if available from preset_images)
                # Combined Images Display
        if system_in_database and systems_check.data and (poi_data or system_info):
            # Gather all images
            all_images = []
            
            # Get preset image if available
            category_name = systems_check.data[0].get("category", "")
            preset_img_url = get_category_images().get(category_name)
            
            # Add main image (prefer system_info image over preset)
            if system_info and system_info.get("images"):
                all_images.append(("System Image", system_info.get("images")))
            elif preset_img_url:
                all_images.append(("Example Image", preset_img_url))
            
            # Add additional images
            if system_info and system_info.get("additional_images"):
                try:
                    additional_imgs = json.loads(system_info["additional_images"])
                    for idx, img_url in enumerate(additional_imgs):
                        all_images.append((f"Additional Image {idx + 1}", img_url))
                except Exception as e:
                    print(f"Error parsing additional images: {e}")
            
            # Display all images if any exist
            if all_images:
                img_section = ctk.CTkFrame(info_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=8)
                img_section.pack(fill="x", pady=(10, 3))
                
                img_content = ctk.CTkFrame(img_section, fg_color="transparent")
                img_content.pack(fill="both", expand=True, padx=15, pady=10)
                
                ctk.CTkLabel(img_content, text="Images:", font=reg_font, 
                            text_color=ACCENT_COLOR, width=140, anchor="w").pack(anchor="nw")
                
                # Scrollable frame for all images
                imgs_scroll = ctk.CTkScrollableFrame(img_content, fg_color="#0f0f0f", 
                                                   corner_radius=8, height=min(400, 250 * len(all_images)))
                imgs_scroll.pack(fill="both", expand=True, pady=(5, 0))
                
                for img_label, img_url in all_images:
                    # Individual image container
                    single_img_frame = ctk.CTkFrame(imgs_scroll, fg_color="#1a1a1a", corner_radius=6)
                    single_img_frame.pack(fill="x", pady=5, padx=5)
                    
                    # Header with label
                    header_frame = ctk.CTkFrame(single_img_frame, fg_color="transparent")
                    header_frame.pack(fill="x", padx=10, pady=(10, 5))
                    
                    ctk.CTkLabel(header_frame, text=img_label,
                               font=ctk.CTkFont(size=12, weight="bold"),
                               text_color="#888888").pack(side="left")
                    
                    # Image display - larger size
                    img_container = ctk.CTkFrame(single_img_frame, fg_color="#0f0f0f", 
                                               corner_radius=4, height=220)
                    img_container.pack(fill="x", padx=10, pady=(0, 10))
                    img_container.pack_propagate(False)
                    
                    loading_lbl = ctk.CTkLabel(img_container, text="Loading...",
                                             font=ctk.CTkFont(size=12), 
                                             text_color="#666666")
                    loading_lbl.pack(expand=True)
                    
                    # Load image asynchronously with larger size
                    def load_combined_img(url, container, lbl):
                        photo = load_image_from_url(url, size=(500, 200))
                        if photo and container.winfo_exists():
                            container.after(0, lambda: show_combined_img(container, photo, lbl, url))
                    
                    def show_combined_img(container, photo, lbl, url):
                        if container.winfo_exists():
                            lbl.destroy()
                            img_lbl = ctk.CTkLabel(container, image=photo, text="")
                            img_lbl.pack(expand=True, pady=10)
                            img_lbl.photo = photo
                            
                            # Clickable URL below image
                            url_label = ctk.CTkLabel(container, text=url,
                                                   font=ctk.CTkFont(size=10), 
                                                   text_color="lightblue",
                                                   cursor="hand2",
                                                   wraplength=480)
                            url_label.pack(pady=(0, 10))
                            
                            import webbrowser
                            url_label.bind("<Button-1>", lambda e: webbrowser.open(url))
                    
                    threading.Thread(target=load_combined_img, 
                                   args=(img_url, img_container, loading_lbl), 
                                   daemon=True).start()
        
        # --- POI TAB (if visited) ---
        if is_visited or poi_data:
            poi_frame = ctk.CTkScrollableFrame(poi_tab, fg_color="transparent")
            poi_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            header_frame = ctk.CTkFrame(poi_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
            header_frame.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(header_frame, text="POI Information", 
                        font=bold_font, text_color=ACCENT_COLOR).pack(pady=15)
            
            if poi_data:
                poi_items = [
                    ("POI Name:", poi_data.get("name", system_name)),
                    ("Discoverer:", poi_data.get("discoverer", "Unknown")),
                    ("Submitter:", poi_data.get("submitter", "Unknown")),
                    ("POI Type:", poi_data.get("potential_or_poi", "Unknown"))
                ]
                
                # Add POI Description if exists
                if poi_data.get("poi_description"):
                    poi_items.append(("Description:", poi_data.get("poi_description")))
                
                for label, value in poi_items:
                    row_frame = ctk.CTkFrame(poi_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=8)
                    row_frame.pack(fill="x", pady=3)
                    
                    content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                    content_frame.pack(fill="x", padx=15, pady=10)
                    
                    ctk.CTkLabel(content_frame, text=label, font=reg_font, 
                                text_color=ACCENT_COLOR, width=140, anchor="w").pack(side="left", anchor="n" if label == "Description:" else "center")
                    ctk.CTkLabel(content_frame, text=str(value), font=reg_font, 
                                text_color=TEXT_COLOR, anchor="w", wraplength=400).pack(side="left", padx=(10, 0), anchor="n" if label == "Description:" else "center")
                
                # Display image if available
                if poi_data.get("image_path"):
                    img_section = ctk.CTkFrame(poi_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
                    img_section.pack(fill="x", pady=(10, 5))
                    
                    ctk.CTkLabel(img_section, text="POI Image", 
                                font=bold_font, text_color=ACCENT_COLOR).pack(pady=(10, 5))
                    
                    img_display_frame = ctk.CTkFrame(img_section, fg_color="#0f0f0f", corner_radius=8)
                    img_display_frame.pack(fill="x", padx=15, pady=(5, 15))
                    
                    # Loading indicator
                    loading_label = ctk.CTkLabel(img_display_frame, text="Loading image...",
                                               font=reg_font, text_color="#666666")
                    loading_label.pack(pady=20)
                    
                    def load_poi_image():
                        photo = load_image_from_url(poi_data["image_path"], size=(600, 400))
                        if photo and img_display_frame.winfo_exists():
                            img_display_frame.after(0, lambda: display_poi_image(photo))
                    
                    def display_poi_image(photo):
                        if img_display_frame.winfo_exists():
                            # Remove loading label
                            for widget in img_display_frame.winfo_children():
                                widget.destroy()
                            
                            # Display image
                            img_label = ctk.CTkLabel(img_display_frame, image=photo, text="")
                            img_label.pack(pady=10, padx=10)
                            img_label.photo = photo
                            
                            # Add URL below image
                            url_label = ctk.CTkLabel(img_display_frame, text=poi_data["image_path"],
                                                   font=ctk.CTkFont(size=11), text_color="#666666",
                                                   cursor="hand2")
                            url_label.pack(pady=(0, 10))
                            
                            # Make URL clickable
                            import webbrowser
                            url_label.bind("<Button-1>", lambda e: webbrowser.open(poi_data["image_path"]))
                    
                    # Load image in thread
                    threading.Thread(target=load_poi_image, daemon=True).start()
            else:
                ctk.CTkLabel(poi_frame, text="No POI data available yet", 
                            font=reg_font, text_color="gray").pack(pady=20)
        
        # Claim status (only show if system is in database)
        if system_in_database:
            claim_frame = ctk.CTkFrame(info_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
            claim_frame.pack(fill="x", pady=(20, 10))
            
            ctk.CTkLabel(claim_frame, text="Claim Status", 
                        font=bold_font, text_color=ACCENT_COLOR).pack(pady=(15, 10))
            
            if claim_data:
                claim_items = [
                    ("Status:", "CLAIMED"),
                    ("Claimed by:", claim_data.get("by_cmdr", "Unknown")),
                    ("Visited:", "Yes" if claim_data.get("visited", False) else "No"),
                    ("Claim Date:", claim_data.get("created_at", "Unknown")[:10] if claim_data.get("created_at") else "Unknown")
                ]
                
                for label, value in claim_items:
                    row_frame = ctk.CTkFrame(claim_frame, fg_color="transparent")
                    row_frame.pack(fill="x", pady=2, padx=20)
                    
                    ctk.CTkLabel(row_frame, text=label, font=reg_font, 
                                text_color=ACCENT_COLOR, width=120, anchor="w").pack(side="left")
                    ctk.CTkLabel(row_frame, text=str(value), font=reg_font, 
                                text_color=TEXT_COLOR, anchor="w").pack(side="left", padx=(10, 0))
                
                # Claim/Unclaim button
                if claim_data.get("by_cmdr") == self.cmdr_name:
                    btn_frame = ctk.CTkFrame(claim_frame, fg_color="transparent")
                    btn_frame.pack(pady=(10, 15))
                    
                    ctk.CTkButton(btn_frame, text="Unclaim System", 
                                 command=lambda: self.unclaim_system(system_name, popup),
                                 fg_color="#dc3545", hover_color="#c82333").pack(side="left", padx=5)
                    
                    # Check visited button
                    if not claim_data.get("visited", False):
                        ctk.CTkButton(btn_frame, text="Mark as Visited", 
                                     command=lambda: self.mark_visited(system_name, popup),
                                     fg_color="#28a745", hover_color="#218838").pack(side="left", padx=5)
                else:
                    ctk.CTkLabel(claim_frame, text="System claimed by another commander", 
                                font=reg_font, text_color="orange").pack(pady=(10, 15))
            else:
                ctk.CTkLabel(claim_frame, text="UNCLAIMED", 
                            font=reg_font, text_color="green").pack(pady=10)
                ctk.CTkButton(claim_frame, text="Claim System", 
                             command=lambda: self.claim_system(system_name, popup),
                             fg_color="#28a745", hover_color="#218838").pack(pady=(10, 15))
        
        # --- EDIT INFO TAB ---
        edit_frame = ctk.CTkScrollableFrame(edit_tab, fg_color="transparent")
        edit_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        header_frame = ctk.CTkFrame(edit_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text=f"Edit: {system_name}", 
                    font=bold_font, text_color=ACCENT_COLOR).pack(pady=15)
        
        # Separator
        ctk.CTkFrame(edit_frame, height=2, fg_color="#333333").pack(fill="x", pady=10)
        
        # System Information Editor Button
        def open_system_editor():
            sys_window = ctk.CTkToplevel(popup)
            sys_window.title("System Information Editor")
            sys_window.geometry("800x700")
            sys_window.transient(popup)
            sys_window.grab_set()
            sys_window.configure(fg_color=MAIN_BG_COLOR)
            sys_window.lift()
            sys_window.focus_force()

            sys_frame = ctk.CTkScrollableFrame(sys_window, fg_color="transparent")
            sys_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            header = ctk.CTkFrame(sys_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
            header.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(header, text="System Information Editor",
                        font=bold_font, text_color=ACCENT_COLOR).pack(pady=15)
            
            # Edit fields frame
            fields_frame = ctk.CTkFrame(sys_frame, fg_color=CARD_BG_COLOR, corner_radius=10)
            fields_frame.pack(fill="x", pady=10)
            
            # Name field
            name_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            name_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(name_frame, text="Name:", 
                        font=reg_font, width=120, anchor="w",
                        text_color=TEXT_COLOR).pack(side="left")
            name_entry = ctk.CTkEntry(name_frame, width=400, fg_color=SECONDARY_BG_COLOR, 
                                     border_color="#444444", text_color=TEXT_COLOR)
            name_entry.pack(side="left", padx=(10, 0))
            if system_info and system_info.get("name"):
                name_entry.insert(0, system_info["name"])
            
            # System Description field
            sys_desc_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            sys_desc_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(sys_desc_frame, text="Description:", 
                        font=reg_font, width=120, anchor="w",
                        text_color=TEXT_COLOR).pack(side="left", anchor="n")
            sys_desc_text = ctk.CTkTextbox(sys_desc_frame, width=400, height=100, 
                                          fg_color=SECONDARY_BG_COLOR, border_color="#444444",
                                          text_color=TEXT_COLOR)
            sys_desc_text.pack(side="left", padx=(10, 0))
            if system_info and system_info.get("description"):
                sys_desc_text.insert("1.0", system_info["description"])
            
            # Query Category field - only editable for systems not in records
            cat_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            cat_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(cat_frame, text="Query Category:", 
                        font=reg_font, width=120, anchor="w",
                        text_color=TEXT_COLOR).pack(side="left")
            
            # Get preset image URL if available
            preset_image_url = None
            
            if system_in_database:
                # System is in database - show category as read-only
                category_text = "Unknown"
                if systems_check.data:
                    category_text = systems_check.data[0].get("category", "Unknown")
                    # Check for preset image
                    if category_text in get_category_images():
                        preset_image_url = get_category_images()[category_text]
                
                cat_label = ctk.CTkLabel(cat_frame, text=category_text,
                                       font=reg_font, fg_color=SECONDARY_BG_COLOR,
                                       corner_radius=5, width=400, anchor="w",
                                       text_color="#888888")
                cat_label.pack(side="left", padx=(10, 0), ipady=5, ipadx=10)
                
                # Store None for category dropdown since it's not editable
                cat_dropdown = None
            else:
                # System not in database - allow manual category selection
                categories = []
                if supabase:
                    try:
                        cat_response = supabase.table("systems").select("category").execute()
                        if cat_response.data:
                            categories = sorted(list(set(item["category"] for item in cat_response.data if item["category"])))
                    except:
                        categories = []
                
                if not categories:
                    categories = ["No categories available"]
                
                # Add option for custom category
                categories.insert(0, "Custom/Unknown")
                
                cat_dropdown = ctk.CTkComboBox(cat_frame, values=categories, width=400,
                                              fg_color=SECONDARY_BG_COLOR, border_color="#444444",
                                              button_color="#444444", button_hover_color="#555555",
                                              dropdown_fg_color=SECONDARY_BG_COLOR,
                                              dropdown_text_color=TEXT_COLOR,
                                              dropdown_hover_color="#444444",
                                              text_color=TEXT_COLOR)
                cat_dropdown.set("Custom/Unknown")
                cat_dropdown.pack(side="left", padx=(10, 0))
                
                ctk.CTkLabel(cat_frame, text="(Editable for unrecorded systems)",
                           font=ctk.CTkFont(size=10), text_color="#666666").pack(side="left", padx=(10, 0))
            
            # Image URL field - auto-fill with preset image if available
            img_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            img_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(img_frame, text="Image URL:", 
                        font=reg_font, width=120, anchor="w",
                        text_color=TEXT_COLOR).pack(side="left")
            image_entry = ctk.CTkEntry(img_frame, width=400, placeholder_text="e.g., https://i.imgur.com/example.jpg",
                                     fg_color=SECONDARY_BG_COLOR, border_color="#444444",
                                     text_color=TEXT_COLOR)
            image_entry.pack(side="left", padx=(10, 0))
            
            # Auto-fill with preset image or existing system image
            if preset_image_url:
                image_entry.insert(0, preset_image_url)
            elif system_info and system_info.get("images"):
                image_entry.insert(0, system_info["images"])
            
            # Additional Images section
            additional_imgs_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            additional_imgs_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(additional_imgs_frame, text="Additional Images:", 
                        font=reg_font, width=120, anchor="w",
                        text_color=TEXT_COLOR).pack(side="left", anchor="n")
            
            # Container for additional image entries
            imgs_container = ctk.CTkFrame(additional_imgs_frame, fg_color="transparent")
            imgs_container.pack(side="left", fill="x", expand=True, padx=(10, 0))
            
            additional_entries = []
            
            # Load existing additional images if any
            existing_additional = []
            if system_info and system_info.get("additional_images"):
                try:
                    existing_additional = json.loads(system_info["additional_images"])
                except:
                    existing_additional = []
            
            def add_image_entry(initial_value=""):
                entry_frame = ctk.CTkFrame(imgs_container, fg_color="transparent")
                entry_frame.pack(fill="x", pady=2)
                
                entry = ctk.CTkEntry(entry_frame, width=350, placeholder_text="https://i.imgur.com/...",
                                   fg_color=SECONDARY_BG_COLOR, border_color="#444444",
                                   text_color=TEXT_COLOR)
                entry.pack(side="left")
                
                if initial_value:
                    entry.insert(0, initial_value)
                
                remove_btn = ctk.CTkButton(entry_frame, text="✕", width=30,
                                         fg_color="#dc3545", hover_color="#c82333",
                                         command=lambda: remove_entry(entry_frame, entry))
                remove_btn.pack(side="left", padx=(5, 0))
                
                additional_entries.append(entry)
            
            def remove_entry(frame, entry):
                additional_entries.remove(entry)
                frame.destroy()
            
            # Add existing entries
            for img_url in existing_additional:
                add_image_entry(img_url)
            
            # Add button for more images
            add_img_btn = ctk.CTkButton(imgs_container, text="+ Add Another Image",
                                      fg_color="#28a745", hover_color="#218838",
                                      command=lambda: add_image_entry())
            add_img_btn.pack(pady=5)
            
            ctk.CTkLabel(sys_frame, text="Note: Use Imgur or similar image hosting service", 
                        font=ctk.CTkFont(size=12), text_color="gray").pack(pady=5)
            
            # Save button function
            def save_system_info():
                if not supabase:
                    messagebox.showerror("Error", "Database not available", parent=sys_window)
                    return
                    
                try:
                    updates = {"system": system_name}
                    
                    # Preserve existing coordinates or add current ones
                    if system_info:
                        if "x" in system_info:
                            updates["x"] = system_info["x"]
                        if "y" in system_info:
                            updates["y"] = system_info["y"]
                        if "z" in system_info:
                            updates["z"] = system_info["z"]
                    elif not system_in_database and self.system_name == system_name and self.latest_starpos:
                        # Add coordinates from current position for unrecorded systems
                        x, y, z = self.latest_starpos
                        updates["x"] = x
                        updates["y"] = y
                        updates["z"] = z
                    
                    # Update fields
                    name_value = name_entry.get().strip()
                    if name_value:
                        updates["name"] = name_value
                    
                    # Save description
                    sys_desc_value = sys_desc_text.get("1.0", "end-1c").strip()
                    if sys_desc_value:
                        updates["description"] = sys_desc_value
                    
                    # Save query category only for unrecorded systems
                    if not system_in_database and cat_dropdown:
                        selected_cat = cat_dropdown.get()
                        if selected_cat and selected_cat != "Custom/Unknown":
                            updates["query_category"] = selected_cat
                            
                            # Also add to systems table
                            if self.system_name == system_name and self.latest_starpos:
                                x, y, z = self.latest_starpos
                                new_system = {
                                    "systems": system_name,
                                    "x": x,
                                    "y": y,
                                    "z": z,
                                    "category": selected_cat
                                }
                                supabase.table("systems").insert(new_system).execute()
                    
                    img_url = image_entry.get().strip()
                    # Always update the images field, even if empty (to allow deletion)
                    updates["images"] = img_url if img_url else None
                    
                    # Save additional images
                    additional_urls = []
                    for entry in additional_entries:
                        url = entry.get().strip()
                        if url:
                            additional_urls.append(url)
                    
                    # Always update additional_images, even if empty
                    updates["additional_images"] = json.dumps(additional_urls) if additional_urls else None
                    
                    if updates:
                        existing = supabase.table("system_information").select("id").eq("system", system_name).execute()
                        
                        if existing.data:
                            supabase.table("system_information").update(updates).eq("system", system_name).execute()
                        else:
                            supabase.table("system_information").insert(updates).execute()
                        
                        messagebox.showinfo("Success", "System information saved!", parent=sys_window)
                        sys_window.destroy()
                        popup.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save changes: {e}", parent=sys_window)
            
            # Add the save button at the bottom
            ctk.CTkButton(sys_frame, text="Save System Information", 
                         command=save_system_info, 
                         fg_color="#007bff", hover_color="#0056b3",
                         height=40).pack(pady=20)
            
            # Create the button that calls open_system_editor
        ctk.CTkButton(edit_frame, text="Edit System Information",
                     command=open_system_editor,  # This references the function
                     fg_color="#6c757d", hover_color="#5a6268",
                     height=40).pack(pady=10)
            
            # POI Editor Button (always visible now)
        def open_poi_editor():
            poi_window = ctk.CTkToplevel(popup)
            poi_window.title("POI Editor")
            poi_window.geometry("700x600")
            poi_window.transient(popup)
            poi_window.grab_set()
            poi_window.configure(fg_color=MAIN_BG_COLOR)
            poi_window.lift()
            poi_window.focus_force()
            
            poi_frame = ctk.CTkScrollableFrame(poi_window, fg_color="transparent")
            poi_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            header = ctk.CTkFrame(poi_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
            header.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(header, text="POI Editor",
                        font=bold_font, text_color=ACCENT_COLOR).pack(pady=15)
            
            # Edit fields frame
            fields_frame = ctk.CTkFrame(poi_frame, fg_color=CARD_BG_COLOR, corner_radius=10)
            fields_frame.pack(fill="x", pady=10)
            
            # POI fields
            edit_fields = {}
            poi_fields = [
                ("name", "POI Name"),
                ("discoverer", "Discoverer"),
                ("submitter", "Submitter")
            ]
            
            for field_key, field_label in poi_fields:
                row_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=10, padx=20)
                
                ctk.CTkLabel(row_frame, text=f"{field_label}:", 
                            font=reg_font, width=120, anchor="w",
                            text_color=TEXT_COLOR).pack(side="left")
                
                # Make system_name field read-only
                if field_key == "system_name":
                    entry = ctk.CTkEntry(row_frame, width=400, fg_color="#1a1a1a", 
                                        border_color="#333333", text_color="#888888",
                                        state="readonly")
                    entry.pack(side="left", padx=(10, 0))
                    
                    # Configure readonly state after inserting text
                    entry.configure(state="normal")
                    entry.insert(0, system_name)  # Always use the actual system name
                    entry.configure(state="readonly")
                else:
                    entry = ctk.CTkEntry(row_frame, width=400, fg_color=SECONDARY_BG_COLOR, 
                                        border_color="#444444", text_color=TEXT_COLOR)
                    entry.pack(side="left", padx=(10, 0))
                    
                    if poi_data and field_key in poi_data and poi_data[field_key] is not None:
                        entry.insert(0, str(poi_data[field_key]))
                
                edit_fields[field_key] = entry
            
            # POI Description field
            poi_desc_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            poi_desc_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(poi_desc_frame, text="POI Description:", 
                        font=reg_font, width=120, anchor="w",
                        text_color=TEXT_COLOR).pack(side="left", anchor="n")
            poi_desc_text = ctk.CTkTextbox(poi_desc_frame, width=400, height=100,
                                          fg_color=SECONDARY_BG_COLOR, border_color="#444444",
                                          text_color=TEXT_COLOR)
            poi_desc_text.pack(side="left", padx=(10, 0))
            if poi_data and poi_data.get("poi_description"):
                poi_desc_text.insert("1.0", poi_data["poi_description"])
            
            # POI Type radio buttons
            poi_type_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            poi_type_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(poi_type_frame, text="POI Type:", 
                        font=reg_font, width=120, anchor="w",
                        text_color=TEXT_COLOR).pack(side="left")
            
            poi_type_var = ctk.StringVar(value=poi_data.get("potential_or_poi", "Potential POI") if poi_data else "Potential POI")
            
            radio_frame = ctk.CTkFrame(poi_type_frame, fg_color="transparent")
            radio_frame.pack(side="left", padx=(10, 0))
            
            ctk.CTkRadioButton(radio_frame, text="Potential POI", 
                              variable=poi_type_var, value="Potential POI",
                              fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
                              text_color=TEXT_COLOR).pack(side="left", padx=(0, 20))
            ctk.CTkRadioButton(radio_frame, text="POI", 
                              variable=poi_type_var, value="POI",
                              fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
                              text_color=TEXT_COLOR).pack(side="left")
            
            # Save button
            def save_poi_info():
                if not supabase:
                    messagebox.showerror("Error", "Database not available", parent=poi_window)
                    return
                
                try:
                    updates = {}
                    
                    # Save editable fields
                    for field_key, widget in edit_fields.items():
                        value = widget.get().strip()
                        if value:
                            updates[field_key] = value
                    
                    # Never update coordinates in POI table - they should come from systems table only
                    # Remove any coordinate fields from updates if they exist
                    coords_fields = ['coords_x', 'coords_y', 'coords_z', 'x', 'y', 'z']
                    for coord_field in coords_fields:
                        if coord_field in updates:
                            del updates[coord_field]
                    
                    updates["potential_or_poi"] = poi_type_var.get()
                    
                    # Save POI description
                    poi_desc_value = poi_desc_text.get("1.0", "end-1c").strip()
                    if poi_desc_value:
                        updates["poi_description"] = poi_desc_value
                    
                    if updates:
                        existing_poi = supabase.table("pois").select("id").eq("system_name", system_name).execute()
                        
                        if existing_poi.data:
                            supabase.table("pois").update(updates).eq("system_name", system_name).execute()
                        else:
                            updates["system_name"] = system_name
                            supabase.table("pois").insert(updates).execute()
                        
                        messagebox.showinfo("Success", "POI information saved!", parent=poi_window)
                        poi_window.destroy()
                        popup.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save changes: {e}", parent=poi_window)
            
            # Save and Undo buttons
            btn_frame = ctk.CTkFrame(poi_frame, fg_color="transparent")
            btn_frame.pack(pady=20)
            
            ctk.CTkButton(btn_frame, text="Save POI Information", 
                         command=save_poi_info, 
                         fg_color="#007bff", hover_color="#0056b3",
                         height=40).pack(side="left", padx=5)
            
            # Undo POI button (only if POI exists)
            if poi_data:
                def undo_poi():
                    if messagebox.askyesno("Confirm", "Remove all POI data for this system?", parent=poi_window):
                        try:
                            supabase.table("pois").delete().eq("system_name", system_name).execute()
                            messagebox.showinfo("Success", "POI data removed!", parent=poi_window)
                            poi_window.destroy()
                            popup.destroy()
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to remove POI: {e}", parent=poi_window)
                
                ctk.CTkButton(btn_frame, text="Remove POI", 
                             command=undo_poi, 
                             fg_color="#dc3545", hover_color="#c82333",
                             height=40).pack(side="left", padx=5)
        
        # Create the button (always visible now)
        ctk.CTkButton(edit_frame, text="Edit POI Information",
                     command=open_poi_editor,
                     fg_color="#28a745", hover_color="#218838",
                     height=40).pack(pady=10)
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")

    def claim_system(self, system_name, popup_window):
        """Claim a system for the current commander"""
        if not supabase:
            messagebox.showerror("Error", "Database not available", parent=popup_window)
            return
        
        try:
            # Check if system is already claimed
            existing = supabase.table("taken").select("*").eq("system", system_name).execute()
            if existing.data:
                messagebox.showwarning("Warning", "System is already claimed!", parent=popup_window)
                return
            
            # Check if commander is currently in this system
            visited = (self.system_name == system_name)
            
            # Insert claim
            supabase.table("taken").insert({
                "system": system_name,
                "by_cmdr": self.cmdr_name,
                "visited": visited
            }).execute()
            
            messagebox.showinfo("Success", f"System {system_name} claimed!", parent=popup_window)
            popup_window.destroy()
            
            # Refresh nearest unclaimed
            self.find_nearest_unclaimed()
            
            # Refresh map if open
            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                self.map_window.toggle_unvisited()
                self.map_window.toggle_your_claims()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to claim system: {e}", parent=popup_window)

    def mark_visited(self, system_name, popup_window):
        """Mark a claimed system as visited"""
        if not supabase:
            messagebox.showerror("Error", "Database not available", parent=popup_window)
            return
        
        try:
            # Update visited status
            supabase.table("taken").update({"visited": True}).eq("system", system_name).eq("by_cmdr", self.cmdr_name).execute()
            
            messagebox.showinfo("Success", f"System {system_name} marked as visited!", parent=popup_window)
            popup_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark as visited: {e}", parent=popup_window)

    def unclaim_system(self, system_name, popup_window):
        """Unclaim a system"""
        if not supabase:
            messagebox.showerror("Error", "Database not available", parent=popup_window)
            return
        
        try:
            # Confirm unclaim
            if not messagebox.askyesno("Confirm", f"Unclaim system {system_name}?", parent=popup_window):
                return
            
            # Remove claim
            supabase.table("taken").delete().eq("system", system_name).eq("by_cmdr", self.cmdr_name).execute()
            
            messagebox.showinfo("Success", f"System {system_name} unclaimed!", parent=popup_window)
            popup_window.destroy()
            
            # Refresh nearest unclaimed
            self.find_nearest_unclaimed()
            
            # Refresh map if open
            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                self.map_window.toggle_unvisited()
                self.map_window.toggle_your_claims()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to unclaim system: {e}", parent=popup_window)

    def admin_login(self):
        w = ctk.CTkToplevel(self)
        w.title("Admin Login")
        w.transient(self); w.grab_set()
        w.geometry("300x150")
        w.configure(fg_color=MAIN_BG_COLOR)
        w.lift()
        w.focus_force()
        
        ctk.CTkLabel(w, text="Enter Admin Key:",
                    font=ctk.CTkFont(size=14),
                    text_color=TEXT_COLOR).pack(pady=10)
        ent = ctk.CTkEntry(w, show="*", fg_color=SECONDARY_BG_COLOR, 
                          border_color="#444444", text_color=TEXT_COLOR)
        ent.pack(fill="x", padx=20)
        
        def submit():
            resp = supabase.table("admin_key").select("key").eq("key", ent.get()).maybe_single().execute()
            if resp and getattr(resp, "data", None):
                # Add to all_admins table
                try:
                    supabase.table("all_admins").insert({
                        "name": self.cmdr_name,
                        "passed_check": True
                    }).execute()
                except Exception as e:
                    # May already exist, update it
                    supabase.table("all_admins").update({
                        "passed_check": True
                    }).eq("name", self.cmdr_name).execute()
                
                messagebox.showinfo("Admin","Login successful",parent=w)
                self.is_admin = True
                self.btn_admin.destroy()
                
                # Create admin label in top right
                self.admin_label = ctk.CTkLabel(self.main_tab if hasattr(self, 'main_tab') else self, 
                                               text=f"CMDR {self.cmdr_name}: Admin",
                                               font=ctk.CTkFont(size=14, weight="bold"),
                                               text_color="#dc3545")
                self.admin_label.place(relx=0.98, rely=0.02, anchor="ne")
                
                # Add logout button below admin label
                self.btn_logout = ctk.CTkButton(self.main_tab if hasattr(self, 'main_tab') else self, 
                                               text="Logout",
                                               command=self.admin_logout,
                                               width=80, height=25,
                                               fg_color="#dc3545", hover_color="#c82333")
                self.btn_logout.place(relx=0.98, rely=0.06, anchor="ne")
                
                w.destroy()
            else:
                messagebox.showerror("Admin","Invalid key",parent=w)
        
        ctk.CTkButton(w, text="Login", command=submit,
                     fg_color="#007bff", hover_color="#0056b3").pack(pady=10)

    def admin_logout(self):
        """Logout from admin mode"""
        if not supabase:
            return
        
        try:
            # Update the database to set passed_check to false
            supabase.table("all_admins").update({
                "passed_check": False
            }).eq("name", self.cmdr_name).execute()
            
            # Reset admin status
            self.is_admin = False
            
            # Remove admin UI elements
            if hasattr(self, 'admin_label'):
                self.admin_label.destroy()
            if hasattr(self, 'btn_logout'):
                self.btn_logout.destroy()
            
            # Restore login button
            self.btn_admin = ctk.CTkButton(self.main_tab, text="🔐 Admin", 
                                          command=self.admin_login,
                                          width=80, height=30,
                                          fg_color="transparent", 
                                          hover_color="#333333",
                                          border_width=1,
                                          border_color="#666666",
                                          text_color="#999999")
            self.btn_admin.place(relx=0.98, rely=0.02, anchor="ne")
            
            # Close map window if open to remove admin features
            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                self.map_window.destroy()
            
            messagebox.showinfo("Admin", "Logged out successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to logout: {e}")

    def update_commander_location(self):
        """Update commander location in the commanders table"""
        if not supabase or not self.latest_starpos or self.cmdr_name == "Unknown":
            return
        
        try:
            x, y, z = self.latest_starpos
            data = {
                "cmdr_name": self.cmdr_name,
                "star_system": self.system_name,
                "starpos_x": x,
                "starpos_y": y,
                "starpos_z": z
            }
            
            # Try to update existing record
            existing = supabase.table("commanders").select("*").eq("cmdr_name", self.cmdr_name).maybe_single().execute()
            if existing and existing.data:
                supabase.table("commanders").update(data).eq("cmdr_name", self.cmdr_name).execute()
            else:
                supabase.table("commanders").insert(data).execute()
        except Exception as e:
            print(f"Error updating commander location: {e}")

    def check_journal_popup(self):
        if not _cfg.get("journal_verified"):
            self.ask_for_journal_folder()
        else:
            self.start_monitoring()

    def ask_for_journal_folder(self):
        while True:
            fld = filedialog.askdirectory(title="Select Elite Dangerous journal folder")
            if not fld:
                self.destroy(); return
            if find_latest_journal_with_fsdjump(fld):
                _cfg["journal_path"]     = fld
                _cfg["journal_verified"] = True
                save_config(_cfg)
                self.start_monitoring()
                break
            
    def start_monitoring(self):
        """Start monitoring journal files for changes"""
        def monitor():
            last_journal = None
            last_size = 0
            last_mtime = 0
            
            # Initial load - try to get commander name and system
            initial_journal = find_latest_journal_with_fsdjump(_cfg["journal_path"])
            if not initial_journal:
                initial_journal = get_latest_journal_file(_cfg["journal_path"])
            
            if initial_journal:
                # Set initial journal
                last_journal = initial_journal
                save_current_journal_path(initial_journal)
                
                # Get commander name
                self.cmdr_name = extract_commander_name(initial_journal)
                self.cmdr_label.configure(text=f"CMDR: {self.cmdr_name}")
                
                # Get system and position
                sysnm, pos = self.find_latest_journal_and_pos(initial_journal)
                if sysnm:
                    self.system_name = sysnm
                    self.system_label.configure(text=sysnm)
                if pos:
                    self.latest_starpos = pos
                    self.current_coords = pos
                    self.find_nearest_unclaimed()
                    self.update_nearest_systems()
            
            # Now monitor for changes
            while not self.stop_event.is_set():
                try:
                    latest = get_latest_journal_file(_cfg["journal_path"])
                    if not latest:
                        time.sleep(2)
                        continue
                    
                    stat = os.stat(latest)
                    current_size = stat.st_size
                    current_mtime = stat.st_mtime
                    
                    if latest != last_journal or current_size != last_size or current_mtime != last_mtime:
                        last_journal = latest
                        last_size = current_size
                        last_mtime = current_mtime
                        
                        save_current_journal_path(latest)
                        
                        if self.cmdr_name == "Unknown":
                            self.cmdr_name = extract_commander_name(latest)
                            self.cmdr_label.configure(text=f"CMDR: {self.cmdr_name}")
                        
                        sysnm, pos = self.find_latest_journal_and_pos(latest)
                        
                        if pos:
                            self.latest_starpos = pos
                            self.current_coords = pos
                        
                        if sysnm and sysnm != self.system_name:
                            self.system_name = sysnm
                            self.system_label.configure(text=sysnm)
                            
                            if self.current_coords:
                                self.find_nearest_unclaimed()
                                self.update_nearest_systems()
                                self.update_commander_location()
                            
                            if self.is_admin and hasattr(self, 'admin_label'):
                                self.admin_label.configure(text=f"CMDR {self.cmdr_name}: Admin")
                            
                            if not self.is_admin:
                                self.check_admin_status()
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error in journal monitor: {e}")
                    time.sleep(5)
        
        threading.Thread(target=monitor, daemon=True).start()

    def find_latest_journal_and_pos(self, fp):
        """Extract latest system and position from journal file"""
        last_sys, last_pos = None, None
        try:
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    if '"event":"FSDJump"' in line or '"event":"Location"' in line or '"event":"CarrierJump"' in line:
                        try:
                            d = json.loads(line)
                            if "StarSystem" in d:
                                last_sys = d["StarSystem"]
                            if "StarPos" in d:
                                coords = d["StarPos"]
                            if isinstance(coords, list) and len(coords) == 3:
                                last_pos = tuple(coords)
                        except json.JSONDecodeError:
                            continue
            return last_sys, last_pos
        except Exception as e:
           print(f"Error reading journal: {e}")
        return None, None

    def on_closing(self):
        self.stop_event.set()
        # Close map window if open
        if self.map_window and hasattr(self.map_window, 'winfo_exists'):
            try:
                if self.map_window.winfo_exists():
                    self.map_window.on_close()
            except:
                pass
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
