"""
Elite Dangerous Records Helper - UI Fixed v1.3.1-beta

MULTI-CATEGORY SUPPORT ENHANCEMENT:
====================================
This version adds comprehensive multi-category support for star systems:

FEATURES ADDED:
- Systems can now have multiple categories (e.g., "Wolf-Rayet Star, High Metal Content World, Scenic")
- Backward compatible with existing single-category systems
- Intelligent parsing handles JSON arrays, comma-separated strings, and single categories
- Enhanced UI displays show all categories with proper formatting and indicators
- Smart filtering system works with multi-category systems
- Category editing interface allows comma-separated input
- Visual badges show multiple categories with truncation for space

KEY FUNCTIONS:
- parse_categories(): Converts any category format to standardized list
- format_categories_for_storage(): Prepares categories for database storage
- format_categories_for_display(): Formats categories for UI with length limits
- categories_match_filter(): Advanced filtering for multi-category systems
- get_primary_category(): Gets the main category for backward compatibility

USAGE:
- Single category: "Wolf-Rayet Star" (stored as string)
- Multiple categories: ["Wolf-Rayet Star", "High Metal Content World"] (stored as JSON)
- Comma input: "Wolf-Rayet Star, High Metal Content World" (parsed automatically)
- Display: "Wolf-Rayet Star • High Metal Content World" (formatted for UI)

All existing functionality remains unchanged while adding powerful multi-category capabilities.
"""

import os
import json
import time
import threading
import re
import sys
import urllib.request
import urllib.parse
from io import BytesIO
import random
import hashlib
import winreg
import pyperclip
import colorsys
import ssl
import certifi
import base64
import customtkinter as ctk
from customtkinter import CTkImage
from tkinter import filedialog, font as tkFont, messagebox
from PIL import Image, ImageTk, ImageFile, ImageFilter, ImageEnhance, ImageDraw
from PIL.Image import Resampling
from supabase import create_client
import socket
import sys
import httpx

if getattr(sys, 'frozen', False):
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Note: Install 'requests' package for better image loading: pip install requests")
APP_TITLE = "EDRH - Elite Dangerous Records Helper"
APP_VERSION = "v1.3.1-beta"
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
SHADOW_COLOR = "rgba(0,0,0,0.3)"
if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
    EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BASE_DIR

IMAGES_DIR = os.path.join(EXE_DIR, "images")
try:
    os.makedirs(IMAGES_DIR, exist_ok=True)
except:
    pass


def check_single_instance():
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes
        from tkinter import messagebox
        kernel32 = ctypes.windll.kernel32
        mutex_name = "EDRH_SingleInstance_Mutex"
        handle = kernel32.CreateMutexW(None, True, mutex_name)
        last_error = kernel32.GetLastError()
        if last_error == 183:
            messagebox.showerror("Already Running",
                                 "EDRH is already running!\n"
                                 "Check your system tray or task manager.")
            sys.exit(1)
        return handle
    return None


def resource(name: str) -> str:
    assets_path = os.path.join(BASE_DIR, "assets", name)
    if os.path.exists(assets_path):
        return assets_path
    return os.path.join(BASE_DIR, name)


CONFIG_FILE = os.path.join(EXE_DIR, "config.json")


def load_config():
    config_path = os.path.join(EXE_DIR, "config.json")
    return json.load(open(config_path)) if os.path.exists(config_path) else {}


_cfg = load_config()
_RunSystemGet = False
_supabase_client = None
if _cfg.get("supabase_auth_confirmation") and isinstance(_cfg.get("supabase_auth_confirmation"), str):
    try:
        url = _cfg.get("supabase_url", "")
        key = _cfg.get("supabase_auth_confirmation", "")
        if url and key:
            _supabase_client = create_client(url, key)
            _test_result = _supabase_client.table("admin_access").select("id").limit(1).execute()
            _RunSystemGet = True
            supabase = _supabase_client
    except:
        pass
if not _RunSystemGet:
    if getattr(sys, 'frozen', False):
        custom_http = httpx.Client(
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=0,
                max_connections=10,
            ),
            transport=httpx.HTTPTransport(
                retries=3,
            )
        )
        from supabase import create_client, ClientOptions

        url = _cfg.get("supabase_url", "")
        key = _cfg.get("supabase_key", "")
        if url and key:
            try:
                supabase = create_client(url, key)
            except Exception as e:
                supabase = None
        else:
            supabase = None
    else:
        url = _cfg.get("supabase_url", "")
        key = _cfg.get("supabase_key", "")
        if url and key:
            try:
                supabase = create_client(url, key)
            except Exception:
                supabase = None
        else:
            supabase = None
try:
    url = _cfg.get("supabase_url", "")
    key = _cfg.get("supabase_key", "")
    if url and key:
        if getattr(sys, 'frozen', False):
            try:
                login_events_client = create_client(url, key)
                print("Login events client created successfully (exe mode)")
            except Exception as e:
                login_events_client = None
                print(f"Login events client failed in exe: {e}")
        else:
            login_events_client = create_client(url, key)
            print("Login events client created successfully (dev mode)")
    if login_events_client:
        try:
            login_events_client.table('login_events').select('*').execute()
            print("Login events table exists")
        except Exception as e:
            print(f"Login events table not found: {e}")
    else:
        login_events_client = None
        print("Login events client not created - missing config")
except Exception as e:
    login_events_client = None
    print(f"Login events client not available: {e}")


def create_hidden_lock_file(cmdr_name):
    try:
        import tempfile
        lock_path = os.path.join(tempfile.gettempdir(), f".edrh_{hashlib.md5(cmdr_name.encode()).hexdigest()}.lock")
        with open(lock_path, 'w') as f:
            f.write("LOCKED")
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        FILE_ATTRIBUTE_SYSTEM = 0x04
        ctypes.windll.kernel32.SetFileAttributesW(lock_path, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\EDRH")
            winreg.SetValueEx(key, f"lock_{hashlib.md5(cmdr_name.encode()).hexdigest()}", 0, winreg.REG_SZ, "LOCKED")
            winreg.CloseKey(key)
        except:
            pass
        return True
    except:
        return False


def start_monitoring(self):
    def monitor():
        last_journal = None
        last_size = 0
        last_mtime = 0
        initial_journal = find_latest_journal_with_fsdjump(_cfg["journal_path"])
        if not initial_journal:
            initial_journal = get_latest_journal_file(_cfg["journal_path"])
        if initial_journal:
            last_journal = initial_journal
            save_current_journal_path(initial_journal)
            self.cmdr_name = extract_commander_name(initial_journal)
            if supabase and self.cmdr_name != "Unknown":
                print(f"[DEBUG] Security check for: {self.cmdr_name}")
                security_check_result = None
                security_check_error = None
                try:
                    security_check_result = supabase.table("security").select("name,blocked").eq("name",
                                                                                                 self.cmdr_name).maybe_single().execute()
                except Exception as e:
                    security_check_error = e
                    print(f"[DEBUG] Security query error: {e}")
                if security_check_error and hasattr(security_check_error,
                                                    'code') and security_check_error.code == '204':
                    print(f"[DEBUG] User {self.cmdr_name} not found in security table (204 No Content)")
                    security_check_result = None
                elif security_check_error:
                    print(f"[WARNING] Security check failed with unexpected error: {security_check_error}")
                is_blocked = False
                if not security_check_result or not security_check_result.data:
                    print(f"[DEBUG] {self.cmdr_name} not in security table - adding as new user")
                    try:
                        from datetime import datetime, timezone
                        all_commanders = detect_commander_renames(_cfg.get("journal_path", ""))
                        rename_info = None
                        has_banned_commanders = False

                        if len(all_commanders) > 1:
                            blocked_commanders = []
                            for other_cmdr in all_commanders:
                                if other_cmdr != self.cmdr_name:
                                    try:
                                        check = supabase.table("security").select("name,blocked").eq("name",
                                                                                                     other_cmdr).eq(
                                            "blocked", True).maybe_single().execute()
                                        if check and check.data:
                                            blocked_commanders.append(other_cmdr)
                                            has_banned_commanders = True
                                    except:
                                        pass

                            if blocked_commanders:
                                rename_info = f"⚠️ SUSPICIOUS: Blocked commanders in same journal: {', '.join(blocked_commanders)}"
                            else:
                                rename_info = f"Multiple commanders detected (legitimate alts): {', '.join(all_commanders)}"

                        # Only block if there are actually banned commanders in the journal
                        user_blocked = has_banned_commanders

                        security_data = {
                            "name": self.cmdr_name,
                            "blocked": user_blocked,
                            "first_seen": datetime.now(timezone.utc).isoformat(),
                            "journal_path": _cfg.get("journal_path", "Unknown")
                        }
                        if rename_info:
                            security_data["notes"] = rename_info

                        supabase.table("security").insert(security_data).execute()

                        if user_blocked:
                            print(
                                f"[SECURITY] Added {self.cmdr_name} to security table as BLOCKED (linked to banned commanders)")
                        else:
                            print(f"[DEBUG] Added {self.cmdr_name} to security table as ALLOWED")

                        if login_events_client:
                            try:
                                if user_blocked:
                                    event_type = 'new_user_blocked_rename'
                                elif len(all_commanders) > 1:
                                    event_type = 'new_user_with_alts'
                                else:
                                    event_type = 'new_user'

                                result = login_events_client.table('login_events').insert({
                                    'commander': self.cmdr_name,
                                    'is_admin': False,
                                    'login_time': datetime.now(timezone.utc).isoformat(),
                                    'app_version': VERSION_TEXT,
                                    'event_type': event_type,
                                    'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'}).execute()
                                print(f"[DEBUG] Logged {event_type} event to Discord")
                                time.sleep(1)
                            except Exception as log_e:
                                print(f"[ERROR] Failed to log new user event: {log_e}")
                    except Exception as add_e:
                        print(f"[ERROR] Failed to add to security table: {add_e}")
                    is_blocked = user_blocked if 'user_blocked' in locals() else False
                else:
                    is_blocked = security_check_result.data.get("blocked", False)
                    print(f"[DEBUG] User {self.cmdr_name} found in security table - blocked: {is_blocked}")
                if security_check_result and security_check_result.data:
                    all_commanders = detect_commander_renames(_cfg.get("journal_path", ""))
                    if len(all_commanders) > 1:
                        print(f"[DEBUG] Multiple commanders detected: {all_commanders}")
                        for cmdr in all_commanders:
                            if cmdr != self.cmdr_name:
                                try:
                                    check = supabase.table("security").select("name,blocked").eq("name", cmdr).eq(
                                        "blocked", True).maybe_single().execute()
                                    if check and check.data:
                                        print(
                                            f"[WARNING] RENAME DETECTED! {cmdr} (blocked) renamed to {self.cmdr_name}")
                                        if login_events_client:
                                            try:
                                                from datetime import datetime, timezone
                                                login_events_client.rpc('insert_login_event', {
                                                    'p_commander': f"RENAME: {cmdr} → {self.cmdr_name}",
                                                    'p_is_admin': False,
                                                    'p_login_time': datetime.now(timezone.utc).isoformat(),
                                                    'p_app_version': VERSION_TEXT,
                                                    'p_event_type': 'rename_attempt',
                                                    'p_details': f"{cmdr} renamed to {self.cmdr_name}"
                                                }).execute()
                                                time.sleep(1)
                                            except:
                                                pass
                                        messagebox.showerror("Access Denied",
                                                             f"Rename detected! {cmdr} is banned.\nSpeak to the plugin owner in Discord to gain access.")
                                        self.destroy()
                                        return
                                except:
                                    pass
                if is_blocked:
                    print(f"[DEBUG] User {self.cmdr_name} is blocked - logging attempt")
                    if login_events_client:
                        try:
                            from datetime import datetime, timezone
                            result = login_events_client.table('login_events').insert({
                                'commander': self.cmdr_name,
                                'is_admin': False,
                                'login_time': datetime.now(timezone.utc).isoformat(),
                                'app_version': VERSION_TEXT,
                                'event_type': 'blocked_attempt',
                                'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'}).execute()
                            print(f"[DEBUG] Logged blocked attempt to Discord")
                            time.sleep(1)
                        except Exception as e:
                            print(f"[ERROR] Failed to log blocked attempt: {e}")
                    messagebox.showerror("Access Denied",
                                         "You are unauthenticated. Speak to the plugin owner in Discord to gain access.")
                    self.destroy()
                    return
                else:
                    print(f"[DEBUG] User {self.cmdr_name} authenticated - logging login")
                    if login_events_client:
                        try:
                            from datetime import datetime, timezone
                            result = login_events_client.table('login_events').insert({
                                'commander': self.cmdr_name,
                                'is_admin': self.is_admin,
                                'login_time': datetime.now(timezone.utc).isoformat(),
                                'app_version': VERSION_TEXT,
                                'event_type': 'login',
                                'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'}).execute()
                            print(f"[DEBUG] Logged successful login to Discord")
                        except Exception as login_e:
                            print(f"[ERROR] Failed to log login event: {login_e}")
                    if self.is_admin:
                        try:
                            from datetime import datetime, timezone
                            admin_data = {
                                "name": self.cmdr_name,
                                "passed_check": True,
                                "date_of_login": datetime.now(timezone.utc).isoformat()
                            }
                            supabase.table("all_admins").insert(admin_data).execute()
                            print(f"[DEBUG] Logged admin access for {self.cmdr_name}")
                        except Exception as admin_e:
                            print(f"[ERROR] Failed to log admin access: {admin_e}")
            self.cmdr_label.configure(text=f"CMDR: {self.cmdr_name}")
            sysnm, pos = self.find_latest_journal_and_pos(initial_journal)
            if sysnm:
                self.system_name = sysnm
                self.system_label.configure(text=sysnm)
            if pos:
                self.latest_starpos = pos
                self.current_coords = pos
                self.find_nearest_unclaimed()
                self.update_nearest_systems()
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


def save_config(cfg):
    config_path = os.path.join(EXE_DIR, "config.json")
    json.dump(cfg, open(config_path, "w"), indent=2)


def save_current_journal_path(path):
    try:
        _cfg["current_journal"] = path
        save_config(_cfg)
        print(f"Saved current journal to config: {path}")
    except Exception as e:
        print(f"Error saving current journal path: {e}")


def get_current_journal_path():
    return _cfg.get("current_journal", None)


def check_if_locked(cmdr_name):
    try:
        import tempfile
        lock_path = os.path.join(tempfile.gettempdir(), f".edrh_{hashlib.md5(cmdr_name.encode()).hexdigest()}.lock")
        if os.path.exists(lock_path):
            return True
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\EDRH")
            value, _ = winreg.QueryValueEx(key, f"lock_{hashlib.md5(cmdr_name.encode()).hexdigest()}")
            winreg.CloseKey(key)
            if value == "LOCKED":
                return True
        except:
            pass
        return False
    except:
        return False


def detect_commander_renames(journal_path):
    """Enhanced rename detection that distinguishes between alts and renames"""
    try:
        # Look for both journal formats
        journal_files = []
        for file in os.listdir(journal_path):
            if file.startswith("Journal.") and file.endswith(".log"):
                # Check if it matches either format
                if (re.match(r"Journal\.\d{4}-\d{2}-\d{2}T\d{6}\.01\.log$", file) or
                        re.match(r"Journal\.\d{12}\.01\.log$", file)):
                    journal_files.append(file)

        # Sort using proper timestamp logic
        sorted_journals = []
        for fn in journal_files:
            # Try newer format first
            m = re.match(r"Journal\.(\d{4}-\d{2}-\d{2}T\d{6})\.01\.log$", fn)
            if m:
                sorted_journals.append((m.group(1), fn))
                continue

            # Try older format
            m = re.match(r"Journal\.(\d{12})\.01\.log$", fn)
            if m:
                old_timestamp = m.group(1)
                try:
                    year = int(old_timestamp[:2])
                    full_year = 2000 + year if year <= 50 else 1900 + year
                    month = old_timestamp[2:4]
                    day = old_timestamp[4:6]
                    hour = old_timestamp[6:8]
                    minute = old_timestamp[8:10]
                    second = old_timestamp[10:12]

                    iso_timestamp = f"{full_year:04d}-{month}-{day}T{hour}{minute}{second}"
                    sorted_journals.append((iso_timestamp, fn))
                except (ValueError, IndexError):
                    continue

        sorted_journals.sort(reverse=True, key=lambda x: x[0])
        journal_files = [fn for _, fn in sorted_journals]

        all_commanders = {}
        switch_user_events = []

        print(f"[DEBUG] Scanning {len(journal_files)} journal files for commander history...")

        for journal_file in journal_files:
            journal_full_path = os.path.join(journal_path, journal_file)
            try:
                # Extract file date from filename - try newer format first
                timestamp_match = re.search(r'Journal\.(\d{4}-\d{2}-\d{2}T\d{6})\.', journal_file)
                if timestamp_match:
                    file_date = timestamp_match.group(1)
                else:
                    # Try older format
                    old_match = re.search(r'Journal\.(\d{12})\.', journal_file)
                    if old_match:
                        old_timestamp = old_match.group(1)
                        try:
                            year = int(old_timestamp[:2])
                            full_year = 2000 + year if year <= 50 else 1900 + year
                            month = old_timestamp[2:4]
                            day = old_timestamp[4:6]
                            hour = old_timestamp[6:8]
                            minute = old_timestamp[8:10]
                            second = old_timestamp[10:12]
                            file_date = f"{full_year:04d}-{month}-{day}T{hour}{minute}{second}"
                        except (ValueError, IndexError):
                            file_date = "Unknown"
                    else:
                        file_date = "Unknown"

                with open(journal_full_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '"event":"SwitchUser"' in line:
                            switch_user_events.append((file_date, line))
                            print(f"[DEBUG] Found SwitchUser event at {file_date}")

                        elif '"event":"LoadGame"' in line:
                            cmdr_match = re.search(r'"Commander"\s*:\s*"([^"]+)"', line)
                            fid_match = re.search(r'"FID"\s*:\s*"([^"]+)"', line)

                            if cmdr_match:
                                cmdr_name = cmdr_match.group(1)
                                fid = fid_match.group(1) if fid_match else "Unknown"

                                if cmdr_name not in all_commanders:
                                    print(f"[DEBUG] Found commander '{cmdr_name}' in {journal_file}")
                                    all_commanders[cmdr_name] = {
                                        'fid': fid,
                                        'first_seen': file_date,
                                        'sessions': []
                                    }

                                timestamp_match = re.search(r'"timestamp"\s*:\s*"([^"]+)"', line)
                                if timestamp_match:
                                    all_commanders[cmdr_name]['sessions'].append(timestamp_match.group(1))

                        elif '"event":"Commander"' in line:
                            m = re.search(r'"Name"\s*:\s*"([^"]+)"', line)
                            if m:
                                cmdr_name = m.group(1)
                                if cmdr_name not in all_commanders:
                                    all_commanders[cmdr_name] = {
                                        'fid': "Unknown",
                                        'first_seen': file_date,
                                        'sessions': []
                                    }
            except Exception as e:
                print(f"[DEBUG] Error reading {journal_file}: {e}")
                continue

        cmdr_list = list(all_commanders.keys())

        if len(cmdr_list) > 1:
            print(f"[INFO] Multiple commanders detected: {', '.join(cmdr_list)}")

            if switch_user_events:
                print(f"[INFO] Found {len(switch_user_events)} account switch events - likely legitimate alts")

            unique_fids = set(data['fid'] for data in all_commanders.values() if data['fid'] != "Unknown")
            if len(unique_fids) > 1:
                print(f"[INFO] Multiple unique FIDs found ({len(unique_fids)}) - these are legitimate alt accounts")

        return cmdr_list
    except Exception as e:
        print(f"[ERROR] Failed to detect renames: {e}")
        return []


def list_sorted_journals(jd):
    """List and sort journal files, handling multiple Elite Dangerous journal formats"""
    out = []

    # Pattern for newer format: Journal.YYYY-MM-DDTHHMMSS.01.log
    p_new = re.compile(r"Journal\.(\d{4}-\d{2}-\d{2}T\d{6})\.01\.log$")
    # Pattern for older format: Journal.YYMMDDHHMMSS.01.log
    p_old = re.compile(r"Journal\.(\d{12})\.01\.log$")

    for fn in os.listdir(jd):
        # Try newer format first
        m = p_new.match(fn)
        if m:
            # Use timestamp as-is for sorting (ISO format)
            out.append((m.group(1), os.path.join(jd, fn)))
            continue

        # Try older format
        m = p_old.match(fn)
        if m:
            # Convert old format to sortable format
            # YYMMDDHHMMSS -> YYYY-MM-DDTHHMMSS
            old_timestamp = m.group(1)
            try:
                year = int(old_timestamp[:2])
                # Convert 2-digit year to 4-digit (assume 20xx for years 00-50, 19xx for 51-99)
                full_year = 2000 + year if year <= 50 else 1900 + year
                month = old_timestamp[2:4]
                day = old_timestamp[4:6]
                hour = old_timestamp[6:8]
                minute = old_timestamp[8:10]
                second = old_timestamp[10:12]

                # Create ISO-like format for consistent sorting
                iso_timestamp = f"{full_year:04d}-{month}-{day}T{hour}{minute}{second}"
                out.append((iso_timestamp, os.path.join(jd, fn)))
            except (ValueError, IndexError):
                # If parsing fails, skip this file
                continue

    # Sort by timestamp (newest first)
    out.sort(reverse=True, key=lambda x: x[0])
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


def find_latest_journal_with_valid_data(jd):
    """Find the latest journal that has both commander name and system name"""
    for fp in list_sorted_journals(jd):
        cmdr = extract_commander_name(fp)
        if cmdr and cmdr != "Unknown":
            sysnm, pos = find_latest_journal_and_pos_static(fp)
            if sysnm and sysnm != "Unknown":
                return fp
    return None


def find_latest_journal_and_pos_static(fp):
    """Static version - reads from BOTTOM to TOP (latest entries first)"""
    last_sys, last_pos = None, None
    try:
        with open(fp, encoding="utf-8") as f:
            lines = f.readlines()

        # Read from bottom to top (latest entries first)
        for line in reversed(lines):
            if '"event":"FSDJump"' in line or '"event":"Location"' in line or '"event":"CarrierJump"' in line:
                try:
                    d = json.loads(line)
                    system_name = d.get("StarSystem")
                    star_pos = d.get("StarPos")

                    if system_name and star_pos and isinstance(star_pos, list) and len(star_pos) == 3:
                        return system_name, tuple(star_pos)

                except json.JSONDecodeError:
                    # Fallback regex parsing
                    if '"StarSystem"' in line and '"StarPos"' in line:
                        sys_match = re.search(r'"StarSystem"\s*:\s*"([^"]+)"', line)
                        pos_match = re.search(
                            r'"StarPos"\s*:\s*\[\s*([+-]?\d*\.?\d+)\s*,\s*([+-]?\d*\.?\d+)\s*,\s*([+-]?\d*\.?\d+)\s*\]',
                            line)
                        if sys_match and pos_match:
                            return sys_match.group(1), (float(pos_match.group(1)), float(pos_match.group(2)),
                                                        float(pos_match.group(3)))
                    continue
        return None, None
    except Exception as e:
        print(f"Error reading journal: {e}")
    return None, None


def extract_commander_name(fp):
    """Extract commander name with improved detection and account switching support"""
    last_commander = "Unknown"

    try:
        current_journal_name = os.path.basename(fp)
        print(f"[DEBUG] Starting commander extraction from: {current_journal_name}")

        # First, scan the CURRENT journal from BOTTOM to TOP (latest entries first)
        print(f"[DEBUG] Reading current journal: {current_journal_name}")
        try:
            with open(fp, encoding="utf-8", errors='ignore') as f:
                lines = f.readlines()

            print(f"[DEBUG] Current journal has {len(lines)} lines")

            # Read from bottom to top (latest entries first)
            for i, line in enumerate(reversed(lines)):
                line = line.strip()
                if not line:
                    continue

                try:
                    # Look for LoadGame or Commander events
                    if '"event":"LoadGame"' in line or '"event":"Commander"' in line:
                        print(f"[DEBUG] Found potential commander event at line {len(lines) - i}: {line[:100]}...")

                        try:
                            data = json.loads(line)
                            commander = None

                            if data.get("event") == "LoadGame":
                                commander = data.get("Commander")
                                if commander:
                                    print(f"[DEBUG] ✓ FOUND LoadGame commander in current journal: '{commander}'")
                                    return commander
                            elif data.get("event") == "Commander":
                                commander = data.get("Name")
                                if commander:
                                    print(f"[DEBUG] ✓ FOUND Commander event in current journal: '{commander}'")
                                    return commander

                        except json.JSONDecodeError as je:
                            print(f"[DEBUG] JSON decode error, trying regex: {je}")
                            # Fallback to regex if JSON parsing fails
                            if '"event":"LoadGame"' in line:
                                m = re.search(r'"Commander"\s*:\s*"([^"]+)"', line)
                                if m:
                                    commander = m.group(1)
                                    print(
                                        f"[DEBUG] ✓ FOUND commander via LoadGame regex in current journal: '{commander}'")
                                    return commander
                            elif '"event":"Commander"' in line:
                                m = re.search(r'"Name"\s*:\s*"([^"]+)"', line)
                                if m:
                                    commander = m.group(1)
                                    print(
                                        f"[DEBUG] ✓ FOUND commander via Commander regex in current journal: '{commander}'")
                                    return commander

                except Exception as line_e:
                    continue  # Skip problematic lines

        except Exception as file_e:
            print(f"[ERROR] Could not read current journal {current_journal_name}: {file_e}")

        # If NO commander found in current journal, check the most recent journals with proper sorting
        print(f"[WARNING] No commander found in current journal {current_journal_name}, checking recent journals...")

        journal_dir = os.path.dirname(fp)
        all_journals = list_sorted_journals(journal_dir)  # This now handles both formats correctly

        print(f"[DEBUG] Found {len(all_journals)} total journals to check")

        # Check the most recent journals (excluding current one we already checked)
        for journal_path in all_journals[:10]:  # Check up to 10 most recent
            journal_name = os.path.basename(journal_path)
            if journal_path == fp:  # Skip current journal as we already processed it
                print(f"[DEBUG] Skipping current journal: {journal_name}")
                continue

            print(f"[DEBUG] Checking recent journal: {journal_name}")
            try:
                with open(journal_path, encoding="utf-8", errors='ignore') as f:
                    lines = f.readlines()

                # Read from bottom to top (latest entries first)
                for line in reversed(lines):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        if '"event":"LoadGame"' in line and '"Commander"' in line:
                            try:
                                data = json.loads(line)
                                commander = data.get("Commander")
                                if commander:
                                    print(f"[DEBUG] ✓ FOUND commander '{commander}' in recent journal: {journal_name}")
                                    return commander
                            except json.JSONDecodeError:
                                # Fallback regex
                                cmdr_match = re.search(r'"Commander"\s*:\s*"([^"]+)"', line)
                                if cmdr_match:
                                    commander = cmdr_match.group(1)
                                    print(
                                        f"[DEBUG] ✓ FOUND commander via regex '{commander}' in recent journal: {journal_name}")
                                    return commander
                    except Exception:
                        continue

            except Exception as e:
                print(f"[DEBUG] Error reading recent journal {journal_name}: {e}")
                continue

        print(f"[WARNING] No commander found in any recent journals")
        return "Unknown"

    except Exception as e:
        print(f"[ERROR] Fatal error in commander extraction: {e}")
        import traceback
        traceback.print_exc()
    return "Unknown"


def get_latest_journal_file(jd):
    journals = list_sorted_journals(jd)
    return journals[0] if journals else None


def auto_detect_journal_folder():
    """Automatically detect Elite Dangerous journal folder"""
    print("[AUTO-DETECT] Starting Elite Dangerous journal folder detection...")
    potential_paths = []

    if sys.platform == 'win32':
        try:
            user_profile = os.environ.get('USERPROFILE', '')
            if user_profile:
                print(f"[AUTO-DETECT] User profile: {user_profile}")
                primary_path = os.path.join(user_profile, 'Saved Games', 'Frontier Developments', 'Elite Dangerous')
                potential_paths.append(primary_path)

                potential_paths.append(
                    os.path.join(user_profile, 'Saved Games', 'Frontier Developments', 'Elite Dangerous', 'Logs'))

            documents = os.path.join(user_profile, 'Documents')
            if os.path.exists(documents):
                potential_paths.append(os.path.join(documents, 'Frontier Developments', 'Elite Dangerous'))

            appdata = os.environ.get('APPDATA', '')
            if appdata:
                potential_paths.append(os.path.join(appdata, 'Frontier Developments', 'Elite Dangerous'))

            localappdata = os.environ.get('LOCALAPPDATA', '')
            if localappdata:
                potential_paths.append(os.path.join(localappdata, 'Frontier Developments', 'Elite Dangerous'))

            steam_path = os.path.join(user_profile, 'Documents', 'My Games', 'Frontier Developments', 'Elite Dangerous')
            potential_paths.append(steam_path)

        except Exception as e:
            print(f"[AUTO-DETECT] Error building journal paths: {e}")

    print(f"[AUTO-DETECT] Checking {len(potential_paths)} potential paths...")

    for i, path in enumerate(potential_paths, 1):
        try:
            print(f"[AUTO-DETECT] {i}/{len(potential_paths)}: Checking {path}")
            if os.path.exists(path):
                # Look for both journal formats
                journal_files = []
                for file in os.listdir(path):
                    if file.startswith("Journal.") and file.endswith(".log"):
                        # Check if it matches either format
                        if (re.match(r"Journal\.\d{4}-\d{2}-\d{2}T\d{6}\.01\.log$", file) or
                                re.match(r"Journal\.\d{12}\.01\.log$", file)):
                            journal_files.append(file)

                if journal_files:
                    print(f"[AUTO-DETECT] ✓ SUCCESS! Found {len(journal_files)} valid journal files at: {path}")
                    # Show some examples of what we found
                    examples = journal_files[:3]
                    print(f"[AUTO-DETECT] Examples: {', '.join(examples)}")
                    return path
                else:
                    print(f"[AUTO-DETECT] Path exists but no valid journal files found")
            else:
                print(f"[AUTO-DETECT] Path does not exist")
        except Exception as e:
            print(f"[AUTO-DETECT] Error checking path {path}: {e}")
            continue

    print("[AUTO-DETECT] ✗ FAILED: No Elite Dangerous journals found in standard locations")
    return None


def analyze_journal_folder(folder_path):
    """Analyze journal folder and extract commander information and stats"""
    print(f"[ANALYSIS] Analyzing journal folder: {folder_path}")

    if not os.path.exists(folder_path):
        return None

    # Look for both journal formats
    journal_files = []
    for file in os.listdir(folder_path):
        if file.startswith("Journal.") and file.endswith(".log"):
            # Check if it matches either format
            if (re.match(r"Journal\.\d{4}-\d{2}-\d{2}T\d{6}\.01\.log$", file) or
                    re.match(r"Journal\.\d{12}\.01\.log$", file)):
                journal_files.append(file)

    if not journal_files:
        return None

    # Sort using the same logic as list_sorted_journals but just for filenames
    sorted_journals = []
    for fn in journal_files:
        # Try newer format first
        m = re.match(r"Journal\.(\d{4}-\d{2}-\d{2}T\d{6})\.01\.log$", fn)
        if m:
            sorted_journals.append((m.group(1), fn))
            continue

        # Try older format
        m = re.match(r"Journal\.(\d{12})\.01\.log$", fn)
        if m:
            old_timestamp = m.group(1)
            try:
                year = int(old_timestamp[:2])
                full_year = 2000 + year if year <= 50 else 1900 + year
                month = old_timestamp[2:4]
                day = old_timestamp[4:6]
                hour = old_timestamp[6:8]
                minute = old_timestamp[8:10]
                second = old_timestamp[10:12]

                iso_timestamp = f"{full_year:04d}-{month}-{day}T{hour}{minute}{second}"
                sorted_journals.append((iso_timestamp, fn))
            except (ValueError, IndexError):
                continue

    sorted_journals.sort(reverse=True, key=lambda x: x[0])
    journal_files = [fn for _, fn in sorted_journals]

    print(f"[ANALYSIS] Found {len(journal_files)} valid journal files")
    if journal_files:
        print(f"[ANALYSIS] Latest: {journal_files[0]}")
        print(f"[ANALYSIS] Oldest: {journal_files[-1]}")

    commanders = {}
    total_jumps = 0
    systems_visited = set()
    first_log_date = None
    last_log_date = None
    total_play_time = 0

    for journal_file in journal_files[:50]:
        journal_path = os.path.join(folder_path, journal_file)
        try:
            file_date = None
            # Try newer format first: Journal.YYYY-MM-DDTHHMMSS.01.log
            date_match = re.search(r'Journal\.(\d{4}-\d{2}-\d{2})T\d{6}\.', journal_file)
            if date_match:
                file_date = date_match.group(1)
            else:
                # Try older format: Journal.YYMMDDHHMMSS.01.log
                date_match = re.search(r'Journal\.(\d{2})(\d{2})(\d{2})\d{6}\.', journal_file)
                if date_match:
                    year = int(date_match.group(1))
                    full_year = 2000 + year if year <= 50 else 1900 + year
                    month = date_match.group(2)
                    day = date_match.group(3)
                    file_date = f"{full_year}-{month}-{day}"

            if file_date:
                if not first_log_date:
                    first_log_date = file_date
                    last_log_date = file_date
                else:
                    if file_date > last_log_date:
                        last_log_date = file_date
                    if file_date < first_log_date:
                        first_log_date = file_date

            with open(journal_path, 'r', encoding='utf-8') as f:
                session_jumps = 0
                session_systems = set()
                current_cmdr = None

                for line_num, line in enumerate(f):
                    try:
                        if '"event":"' not in line:
                            continue

                        data = json.loads(line)
                        event = data.get("event", "")

                        if event in ["LoadGame", "Commander"]:
                            cmdr_name = data.get("Commander") or data.get("Name")
                            if cmdr_name:
                                current_cmdr = cmdr_name
                                if cmdr_name not in commanders:
                                    commanders[cmdr_name] = {
                                        "name": cmdr_name,
                                        "jumps": 0,
                                        "systems": set(),
                                        "first_seen": file_date or "Unknown",
                                        "last_seen": file_date or "Unknown",
                                        "play_sessions": 0,
                                        "credits": 0,
                                        "rank_combat": "Unknown",
                                        "rank_trade": "Unknown",
                                        "rank_exploration": "Unknown",
                                        "ship": "Unknown"
                                    }
                                if file_date:
                                    commanders[cmdr_name]["last_seen"] = file_date

                        if current_cmdr and current_cmdr in commanders:
                            if event == "FSDJump":
                                commanders[current_cmdr]["jumps"] += 1
                                session_jumps += 1
                                total_jumps += 1

                                star_system = data.get("StarSystem")
                                if star_system:
                                    commanders[current_cmdr]["systems"].add(star_system)
                                    session_systems.add(star_system)
                                    systems_visited.add(star_system)

                            elif event == "LoadGame":
                                credits = data.get("Credits", 0)
                                if credits > commanders[current_cmdr]["credits"]:
                                    commanders[current_cmdr]["credits"] = credits

                            elif event == "Promotion":
                                rank_type = data.get("Combat")
                                if rank_type is not None:
                                    commanders[current_cmdr]["rank_combat"] = str(rank_type)
                                rank_type = data.get("Trade")
                                if rank_type is not None:
                                    commanders[current_cmdr]["rank_trade"] = str(rank_type)
                                rank_type = data.get("Explore")
                                if rank_type is not None:
                                    commanders[current_cmdr]["rank_exploration"] = str(rank_type)

                            elif event == "LoadGame":
                                ship = data.get("Ship")
                                if ship:
                                    commanders[current_cmdr]["ship"] = ship

                            elif event == "ShipyardBuy":
                                ship = data.get("ShipType")
                                if ship:
                                    commanders[current_cmdr]["ship"] = ship

                    except (json.JSONDecodeError, KeyError):
                        continue

                if session_jumps > 0 and current_cmdr:
                    commanders[current_cmdr]["play_sessions"] += 1

        except Exception as e:
            print(f"[ANALYSIS] Error processing {journal_file}: {e}")
            continue

    for cmdr_data in commanders.values():
        cmdr_data["unique_systems"] = len(cmdr_data["systems"])
        cmdr_data["systems"] = list(cmdr_data["systems"])[:10]

    print(f"[ANALYSIS] Analysis complete: {len(commanders)} commanders found")
    for cmdr_name, cmdr_data in commanders.items():
        print(f"[ANALYSIS]   CMDR {cmdr_name}: {cmdr_data['jumps']} jumps, {cmdr_data['unique_systems']} systems")

    return {
        "folder_path": folder_path,
        "total_journals": len(journal_files),
        "commanders": commanders,
        "total_jumps": total_jumps,
        "unique_systems": len(systems_visited),
        "date_range": f"{first_log_date} to {last_log_date}" if first_log_date and last_log_date else "Unknown",
        "analysis_complete": True
    }


_cfg = load_config()
try:
    supabase = create_client(_cfg.get("supabase_url"), _cfg.get("supabase_key"))
except Exception:
    supabase = None
    print("⚠️ Supabase client not available – some features disabled.")
ImageFile.LOAD_TRUNCATED_IMAGES = True
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
SIDEBAR_WIDTH = 350
SIDEBAR_COLLAPSED = 50
FRAME_WIDTH = 425
FRAME_HEIGHT = 40
CMD_FRAME_X = 30
CMD_FRAME_Y_OFF = 520
SYS_FRAME_X = 30
SYS_FRAME_Y_OFF = 480
IMAGE_BUTTON_X = 30
IMAGE_BUTTON_Y = 30
IMAGE_BUTTON_SZ = 400
SCROLL_X = 10
SCROLL_Y = 280
SCROLL_W = SIDEBAR_WIDTH - 50
SCROLL_H = 470
MIN_ZOOM = 0.8
MAX_ZOOM = 6.0
DOT_RADIUS = 5
LY_PER_PIXEL = 40.0
ORIG_OFF_X = 1124
ORIG_OFF_Y = 1749
DOSIS_BOLD = 20
DOSIS_REG = 16
LBL_SIZE = 14
FILTER_BG = "#2b2b2b"
VERSION_TEXT = APP_VERSION
IMGUR_CLIENT_ID = "8b0158e0f64f692"
IMGBB_API_KEY = "8df93308e43e8a90de4b3a1219f07956"
image_cache = {}


def upload_to_imgur(image_path):
    """Upload an image using multiple methods - prioritizing external services to preserve Supabase Storage quota"""

    try:
        print("Trying ImgBB upload...")
        url = upload_to_imgbb(image_path)
        if url:
            return url
    except Exception as e:
        print(f"ImgBB upload error: {e}")

    try:
        print("Trying Imgur upload...")
        url = upload_to_imgur_simple(image_path)
        if url:
            return url
    except Exception as e:
        print(f"Imgur upload error: {e}")

    try:
        print("Trying database storage...")
        url = upload_to_supabase_base64(image_path)
        if url:
            return url
    except Exception as e:
        print(f"Database storage error: {e}")

    try:
        print("Trying Supabase Storage (last resort)...")
        url = upload_to_supabase_storage(image_path)
        if url:
            return url
    except Exception as e:
        print(f"Supabase Storage upload error: {e}")

    print("Image upload failed - all methods exhausted")
    return None


def upload_to_imgbb(image_path):
    """Upload to ImgBB using their official API specification"""
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()

        if len(image_data) > 32 * 1024 * 1024:
            print(f"ImgBB: Image too large ({len(image_data)} bytes), max 32MB")
            return None

        b64_image = base64.b64encode(image_data).decode()

        if HAS_REQUESTS:
            try:
                import urllib3
                urllib3.disable_warnings()

                data = {
                    'key': IMGBB_API_KEY,
                    'image': b64_image
                }

                response = requests.post(
                    'https://api.imgbb.com/1/upload',
                    data=data,
                    timeout=30,
                    verify=False
                )

                print(f"ImgBB response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"ImgBB error response: {response.text[:500]}")

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"ImgBB upload successful")
                        return result['data']['url']
                    else:
                        print(f"ImgBB API error: {result}")

            except Exception as e:
                print(f"ImgBB requests method failed: {e}")

        try:
            data = urllib.parse.urlencode({
                'key': IMGBB_API_KEY,
                'image': b64_image
            }).encode()

            req = urllib.request.Request(
                'https://api.imgbb.com/1/upload',
                data=data,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=30, context=context) as response:
                result = json.loads(response.read().decode())
                if result.get('success'):
                    print(f"ImgBB urllib upload successful")
                    return result['data']['url']
                else:
                    print(f"ImgBB urllib API error: {result}")

        except Exception as e:
            print(f"ImgBB urllib method failed: {e}")

    except Exception as e:
        print(f"ImgBB upload failed: {e}")

    return None


def upload_to_imgur_simple(image_path):
    """Imgur upload with improved error handling and multiple approaches"""
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()

        if len(image_data) > 20 * 1024 * 1024:
            print(f"Imgur: Image too large ({len(image_data)} bytes), max 20MB")
            return None

        b64_image = base64.b64encode(image_data).decode()

        if HAS_REQUESTS:
            try:
                import urllib3
                urllib3.disable_warnings()

                files = {
                    'image': (None, b64_image)
                }
                headers = {
                    'Authorization': f'Client-ID {IMGUR_CLIENT_ID}',
                    'User-Agent': 'EDRH/1.0'
                }

                response = requests.post(
                    'https://api.imgur.com/3/image',
                    headers=headers,
                    files=files,
                    timeout=30,
                    verify=False
                )

                print(f"Imgur response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"Imgur error response: {response.text[:500]}")

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"Imgur upload successful")
                        return result['data']['link']
                    else:
                        print(f"Imgur API error: {result}")

                if response.status_code != 200:
                    print("Trying Imgur with URL-encoded data...")
                    response = requests.post(
                        'https://api.imgur.com/3/image',
                        headers=headers,
                        data={'image': b64_image},
                        timeout=30,
                        verify=False
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            print(f"Imgur URL-encoded upload successful")
                            return result['data']['link']

            except Exception as e:
                print(f"Imgur requests method failed: {e}")

        try:
            data = urllib.parse.urlencode({'image': b64_image}).encode()

            req = urllib.request.Request(
                'https://api.imgur.com/3/image',
                data=data,
                headers={
                    'Authorization': f'Client-ID {IMGUR_CLIENT_ID}',
                    'User-Agent': 'EDRH/1.0',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=15, context=context) as response:
                result = json.loads(response.read().decode())
                if result.get('success'):
                    print(f"Imgur urllib upload successful")
                    return result['data']['link']
                else:
                    print(f"Imgur urllib API error: {result}")

        except Exception as e:
            print(f"Imgur urllib method failed: {e}")

    except Exception as e:
        print(f"Imgur upload failed: {e}")

    return None


def upload_to_supabase_storage(image_path):
    """Upload image to Supabase Storage - best option for shared viewing"""
    try:
        if not supabase:
            print("Supabase not available")
            return None

        with open(image_path, "rb") as f:
            image_data = f.read()

        filename = f"edrh_image_{int(time.time() * 1000)}_{os.path.basename(image_path)}"

        try:
            try:
                supabase.storage.create_bucket("images", {"public": True})
            except:
                pass

            result = supabase.storage.from_("images").upload(filename, image_data)

            if result:
                public_url = supabase.storage.from_("images").get_public_url(filename)
                if public_url:
                    print(f"Successfully uploaded to Supabase Storage: {filename}")
                    return public_url

        except Exception as storage_e:
            print(f"Supabase Storage upload failed: {storage_e}")
            try:
                b64_image = base64.b64encode(image_data).decode()

                image_record = {
                    "filename": filename,
                    "data": b64_image,
                    "content_type": "image/png",
                    "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "uploader": "EDRH_User"
                }

                result = supabase.table("uploaded_images").insert(image_record).execute()
                if result and result.data:
                    image_id = result.data[0]["id"]
                    return f"supabase://uploaded_images/{image_id}"

            except Exception as table_e:
                print(f"Supabase table fallback failed: {table_e}")

    except Exception as e:
        print(f"Supabase upload failed: {e}")

    return None


def upload_to_supabase_base64(image_path):
    """Store image as base64 in Supabase database (fallback method)"""
    try:
        if not supabase:
            return None

        with open(image_path, "rb") as f:
            image_data = f.read()

        b64_image = base64.b64encode(image_data).decode()

        filename = os.path.basename(image_path)
        image_record = {
            "filename": filename,
            "data": b64_image,
            "content_type": "image/png",
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "uploader": "EDRH_User",
            "size": len(image_data)
        }

        result = supabase.table("base64_images").insert(image_record).execute()
        if result and result.data:
            image_id = result.data[0]["id"]
            print(f"Stored image as base64 in database: ID {image_id}")
            return f"data:image/png;base64,{b64_image}"

    except Exception as e:
        print(f"Base64 database storage failed: {e}")

    return None


def load_image_from_url(url, size=(100, 100)):
    cache_key = f"{url}_{size[0]}x{size[1]}"
    if cache_key in image_cache:
        return image_cache[cache_key]
    try:
        if url.startswith("supabase://uploaded_images/"):
            image_id = url.split("/")[-1]
            if supabase:
                try:
                    result = supabase.table("uploaded_images").select("data").eq("id", image_id).single().execute()
                    if result and result.data:
                        b64_data = result.data["data"]
                        img_data = base64.b64decode(b64_data)
                        img = Image.open(BytesIO(img_data))
                        img.thumbnail(size, Resampling.LANCZOS)
                        photo = CTkImage(dark_image=img, size=(img.width, img.height))
                        image_cache[cache_key] = photo
                        return photo
                except Exception as e:
                    print(f"Failed to load Supabase image {image_id}: {e}")
                    return None

        elif url.startswith("data:image"):
            try:
                header, data = url.split(",", 1)
                img_data = base64.b64decode(data)
                img = Image.open(BytesIO(img_data))
                img.thumbnail(size, Resampling.LANCZOS)
                photo = CTkImage(dark_image=img, size=(img.width, img.height))
                image_cache[cache_key] = photo
                return photo
            except Exception as e:
                print(f"Failed to load base64 image: {e}")
                return None
        else:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        if HAS_REQUESTS:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
        else:
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=10)
            img_data = response.read()
            img = Image.open(BytesIO(img_data))
        img.thumbnail(size, Resampling.LANCZOS)
        photo = CTkImage(dark_image=img, size=(img.width, img.height))
        image_cache[cache_key] = photo
        return photo
    except Exception as e:
        print(f"Failed to load image from {url}: {e}")
        return None


category_images = {}


def get_category_images():
    global category_images
    if supabase and not category_images:
        try:
            response = supabase.table("preset_images").select("*").execute()
            if response.data:
                category_images = {item["category"]: item["image"] for item in response.data}
        except Exception as e:
            print(f"Error fetching category images: {e}")
    return category_images


def get_category_colors():
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
    saved_colors = _cfg.get("category_colors", {})
    all_colors = default_colors.copy()
    all_colors.update(saved_colors)
    return all_colors


def generate_unique_color(existing_colors):
    import colorsys
    existing_hex_values = list(existing_colors.values())
    existing_hsv = []
    for hex_color in existing_hex_values:
        rgb = tuple(int(hex_color.lstrip('#')[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        hsv = colorsys.rgb_to_hsv(*rgb)
        existing_hsv.append(hsv)
    max_attempts = 100
    for _ in range(max_attempts):
        h = random.random()
        s = random.uniform(0.5, 1.0)
        v = random.uniform(0.6, 0.9)
        is_distinct = True
        for existing_h, existing_s, existing_v in existing_hsv:
            hue_diff = min(abs(h - existing_h), 1 - abs(h - existing_h))
            if hue_diff < 0.1 and abs(s - existing_s) < 0.3 and abs(v - existing_v) < 0.3:
                is_distinct = False
                break
        if is_distinct:
            rgb = colorsys.hsv_to_rgb(h, s, v)
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            return hex_color
    return '#{:06x}'.format(random.randint(0, 0xFFFFFF))


def get_or_create_category_color(category):
    colors = get_category_colors()
    if category not in colors:
        new_color = generate_unique_color(colors)
        colors[category] = new_color
        if "category_colors" not in _cfg:
            _cfg["category_colors"] = {}
        _cfg["category_colors"][category] = new_color
        save_config(_cfg)
    return colors[category]


# Multi-category support utility functions
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


def format_categories_for_storage(categories):
    """Format a list of categories for database storage as JSON string"""
    if not categories:
        print("[DEBUG] format_categories_for_storage: No categories provided")
        return None

    # Clean and filter categories
    clean_categories = [cat.strip() for cat in categories if cat and cat.strip()]
    print(f"[DEBUG] format_categories_for_storage: Input categories: {categories}")
    print(f"[DEBUG] format_categories_for_storage: Clean categories: {clean_categories}")

    if len(clean_categories) == 0:
        print("[DEBUG] format_categories_for_storage: No valid categories after cleaning")
        return None
    elif len(clean_categories) == 1:
        # Store single category as string for backward compatibility
        result = clean_categories[0]
        print(f"[DEBUG] format_categories_for_storage: Single category result: '{result}'")
        return result
    else:
        # Store multiple categories as JSON array
        result = json.dumps(clean_categories)
        print(f"[DEBUG] format_categories_for_storage: Multiple categories result: '{result}'")
        return result


def format_categories_for_display(categories, max_length=50, separator=" • "):
    """Format categories for UI display with length limiting"""
    if not categories:
        return "No Category"

    parsed_categories = parse_categories(categories)
    if not parsed_categories:
        return "No Category"

    if len(parsed_categories) == 1:
        cat = parsed_categories[0]
        return cat[:max_length] + "..." if len(cat) > max_length else cat

    # Multiple categories
    display_text = separator.join(parsed_categories)
    if len(display_text) > max_length:
        # Try to fit as many as possible
        result = ""
        for i, cat in enumerate(parsed_categories):
            if i == 0:
                test_text = cat
            else:
                test_text = result + separator + cat

            if len(test_text) > max_length - 3:  # Reserve space for "..."
                if i == 0:
                    # Even first category is too long
                    return cat[:max_length - 3] + "..."
                else:
                    return result + "..."
            result = test_text
        return result

    return display_text


def get_primary_category(categories):
    """Get the primary (first) category from a category list"""
    parsed = parse_categories(categories)
    return parsed[0] if parsed else "Unknown"


def categories_match_filter(categories, selected_filters):
    """Check if any of the system's categories match the selected filters"""
    if not selected_filters or "All Categories" in selected_filters:
        return True

    parsed_categories = parse_categories(categories)
    if not parsed_categories:
        return False

    # Check if any category matches any filter
    return any(cat in selected_filters for cat in parsed_categories)


def get_category_color_for_multi(categories):
    """Get color for display when system has multiple categories"""
    parsed = parse_categories(categories)
    if not parsed:
        return "#666666"

    # Use color of primary (first) category
    return get_or_create_category_color(parsed[0])


def create_category_badges(parent, categories, max_badges=3):
    """Create visual category badges for UI display"""
    parsed = parse_categories(categories)
    if not parsed:
        return

    badges_frame = ctk.CTkFrame(parent, fg_color="transparent")
    badges_frame.pack(anchor="w", pady=(2, 0))

    for i, category in enumerate(parsed[:max_badges]):
        color = get_or_create_category_color(category)

        badge = ctk.CTkLabel(badges_frame,
                             text=category[:20] + "..." if len(category) > 20 else category,
                             fg_color=color,
                             text_color="#000000" if color in ["#FFD700", "#FFFF00", "#90EE90"] else "#FFFFFF",
                             corner_radius=8,
                             font=ctk.CTkFont(size=9, weight="bold"))
        badge.pack(side="left", padx=(0, 3), pady=1, ipadx=4, ipady=1)

    # Show "+" indicator if there are more categories
    if len(parsed) > max_badges:
        more_badge = ctk.CTkLabel(badges_frame,
                                  text=f"+{len(parsed) - max_badges}",
                                  fg_color="#666666",
                                  text_color="#FFFFFF",
                                  corner_radius=8,
                                  font=ctk.CTkFont(size=9, weight="bold"))
        more_badge.pack(side="left", padx=(0, 3), pady=1, ipadx=4, ipady=1)

    return badges_frame


def combine_system_entries(systems_data, system_name=None, skip_db_query=False):
    """Combine multiple system entries with same name into single entry with merged categories and data"""
    if not systems_data:
        return None

    # Use first entry as base
    combined_entry = systems_data[0].copy()

    # Collect all categories from systems table entries
    all_categories = []
    for entry in systems_data:
        category = entry.get("category")
        if category:
            parsed = parse_categories(category)
            all_categories.extend(parsed)

    # ALSO get categories from system_category_info table if we have a system name (optional for performance)
    if system_name and supabase and not skip_db_query:
        try:
            print(f"[DEBUG] Getting additional categories from system_category_info for {system_name}")
            category_info_response = supabase.table("system_category_info").select("category").eq("system_name",
                                                                                                  system_name).execute()
            if category_info_response.data:
                for cat_record in category_info_response.data:
                    additional_cat = cat_record.get("category")
                    if additional_cat and additional_cat not in all_categories:
                        print(f"[DEBUG] Found additional category from system_category_info: '{additional_cat}'")
                        all_categories.append(additional_cat)
        except Exception as e:
            print(f"[DEBUG] Error getting categories from system_category_info: {e}")

    # Remove duplicates while preserving order
    unique_categories = []
    for cat in all_categories:
        if cat and cat.strip() and cat not in unique_categories:  # More robust filtering
            unique_categories.append(cat)

    if system_name and not skip_db_query:
        print(f"[DEBUG] Combined categories for {system_name}: {unique_categories}")

    # Store combined categories
    if len(unique_categories) > 1:
        combined_entry["category"] = format_categories_for_storage(unique_categories)
    elif len(unique_categories) == 1:
        combined_entry["category"] = unique_categories[0]
    else:
        combined_entry["category"] = "Unknown Category"

    # Store individual categories for image/info lookup
    combined_entry["_individual_categories"] = unique_categories

    # Use coordinates from first entry with valid coords
    for entry in systems_data:
        if entry.get("x") and entry.get("y") and entry.get("z"):
            combined_entry["x"] = entry["x"]
            combined_entry["y"] = entry["y"]
            combined_entry["z"] = entry["z"]
            break

    # Combine system info from all entries
    all_system_info = []
    for entry in systems_data:
        if entry.get("system_info"):
            all_system_info.append(entry["system_info"])

    if all_system_info:
        combined_entry["system_info"] = "\n\n".join(all_system_info)

    # Combine additional fields that might be useful
    combined_entry["_source_entries"] = systems_data
    combined_entry["_entry_count"] = len(systems_data)

    return combined_entry


def get_preset_images_for_categories(categories):
    """Get preset images for all categories in a list"""
    preset_images = []
    category_images = get_category_images()

    if isinstance(categories, str):
        categories = parse_categories(categories)

    for category in categories:
        if category in category_images:
            preset_images.append((f"Example Image: {category}", category_images[category]))

    return preset_images


class SplashScreen(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()

        self.title("EDRH - Elite Dangerous Records Helper")
        self.geometry("600x400")
        self.resizable(False, False)
        self.configure(fg_color=MAIN_BG_COLOR)

        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (300)
        y = (self.winfo_screenheight() // 2) - (200)
        self.geometry(f"600x400+{x}+{y}")

        try:
            self.iconbitmap(resource("icon.ico"))
        except:
            pass

        self.main_frame = ctk.CTkFrame(self, fg_color=CARD_BG_COLOR,
                                       corner_radius=20, border_width=3,
                                       border_color=ACCENT_COLOR)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=120)
        header_frame.pack(fill="x", padx=30, pady=(30, 20))
        header_frame.pack_propagate(False)

        title_frame = ctk.CTkFrame(header_frame, fg_color=SECONDARY_BG_COLOR,
                                   corner_radius=15, border_width=2, border_color=ACCENT_COLOR)
        title_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(title_frame, text="EDRH",
                     font=ctk.CTkFont(size=36, weight="bold"),
                     text_color=ACCENT_COLOR).pack(pady=(15, 5))

        ctk.CTkLabel(title_frame, text="Elite Dangerous Records Helper",
                     font=ctk.CTkFont(size=16),
                     text_color=TEXT_SECONDARY).pack()

        ctk.CTkLabel(title_frame, text=VERSION_TEXT,
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_MUTED).pack(pady=(5, 15))

        status_frame = ctk.CTkFrame(self.main_frame, fg_color=SECONDARY_BG_COLOR,
                                    corner_radius=12, height=80)
        status_frame.pack(fill="x", padx=30, pady=20)
        status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(status_frame, text="Initializing...",
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color=TEXT_COLOR)
        self.status_label.pack(pady=(10, 5))

        self.detail_label = ctk.CTkLabel(status_frame, text="Preparing Elite Dangerous integration",
                                         font=ctk.CTkFont(size=12),
                                         text_color=TEXT_SECONDARY)
        self.detail_label.pack()

        progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=100)
        progress_frame.pack(fill="x", padx=30, pady=20)
        progress_frame.pack_propagate(False)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=540, height=20,
                                               fg_color=TERTIARY_BG_COLOR,
                                               progress_color=ACCENT_COLOR,
                                               border_width=1,
                                               border_color=BORDER_COLOR,
                                               corner_radius=10)
        self.progress_bar.pack(pady=(20, 10))
        self.progress_bar.set(0)

        self.progress_text = ctk.CTkLabel(progress_frame, text="0%",
                                          font=ctk.CTkFont(size=11),
                                          text_color=TEXT_MUTED)
        self.progress_text.pack()

        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=40)
        footer_frame.pack(side="bottom", fill="x", padx=30, pady=20)
        footer_frame.pack_propagate(False)

        ctk.CTkLabel(footer_frame, text="Loading Elite Dangerous integration...",
                     font=ctk.CTkFont(size=10, slant="italic"),
                     text_color=TEXT_MUTED).pack(side="bottom")

        self.progress_value = 0
        self.animation_step = 0
        self.loading_dots = 0

        self.start_loading_animation()

        self.after(15000, self.emergency_close)

    def start_loading_animation(self):
        """Start the loading animation sequence"""
        self.loading_sequence = [
            ("Checking system compatibility...", 1000),
            ("Scanning for Elite Dangerous...", 1200),
            ("Analyzing journal files...", 1800),
            ("Processing commander data...", 1500),
            ("Validating installation...", 1000),
            ("Preparing confirmation...", 800)
        ]
        self.sequence_index = 0
        self.animate_loading()

    def animate_loading(self):
        """Animate the loading process"""
        if self.sequence_index < len(self.loading_sequence):
            status_text, duration = self.loading_sequence[self.sequence_index]

            self.status_label.configure(text=status_text)

            progress_per_step = 1.0 / len(self.loading_sequence)
            target_progress = (self.sequence_index + 1) * progress_per_step

            def update_progress():
                current = self.progress_bar.get()
                if current < target_progress:
                    new_progress = min(target_progress, current + 0.02)
                    self.progress_bar.set(new_progress)
                    self.progress_text.configure(text=f"{int(new_progress * 100)}%")
                    self.after(50, update_progress)
                else:
                    self.sequence_index += 1
                    if self.sequence_index < len(self.loading_sequence):
                        self.after(200, self.animate_loading)
                    else:
                        self.progress_bar.set(1.0)
                        self.progress_text.configure(text="100%")
                        self.status_label.configure(text="Initialization complete!")
                        self.detail_label.configure(text="Starting application...")
                        self.after(500, self.close_splash)

            update_progress()

            self.animate_dots()

    def animate_dots(self):
        """Animate loading dots"""
        dots = "." * (self.loading_dots % 4)
        current_text = self.detail_label.cget("text")
        base_text = current_text.split(".")[0]
        self.detail_label.configure(text=f"{base_text}{dots}")
        self.loading_dots += 1

        if self.sequence_index < len(self.loading_sequence):
            self.after(300, self.animate_dots)

    def close_splash(self):
        """Close the splash screen"""
        self.destroy()

    def emergency_close(self):
        """Emergency close if splash hangs"""
        try:
            self.destroy()
        except:
            pass


class JournalConfirmationDialog(ctk.CTkToplevel):
    def __init__(self, parent, analysis_data, is_verification=False):
        super().__init__(parent)

        self.parent = parent
        self.analysis_data = analysis_data
        self.is_verification = is_verification
        self.user_choice = None

        self.title("Elite Dangerous Journal Verification")
        self.geometry("900x700")
        self.resizable(True, True)
        self.configure(fg_color=MAIN_BG_COLOR)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450)
        y = (self.winfo_screenheight() // 2) - (350)
        self.geometry(f"900x700+{x}+{y}")

        try:
            self.iconbitmap(resource("icon.ico"))
        except:
            pass

        self.setup_ui()

    def get_primary_commander(self):
        """Get the primary commander from the latest journal file (same logic as main app)"""
        try:
            latest_journal = get_latest_journal_file(self.analysis_data["folder_path"])
            if latest_journal:
                primary_cmdr = extract_commander_name(latest_journal)
                if primary_cmdr and primary_cmdr != "Unknown":
                    print(f"[DEBUG] Primary commander from latest journal: {primary_cmdr}")
                    return primary_cmdr

            if self.analysis_data["commanders"]:
                fallback = list(self.analysis_data["commanders"].keys())[0]
                print(f"[DEBUG] Using fallback primary commander: {fallback}")
                return fallback

        except Exception as e:
            print(f"[ERROR] Error determining primary commander: {e}")
            if self.analysis_data["commanders"]:
                return list(self.analysis_data["commanders"].keys())[0]

        return None

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=CARD_BG_COLOR, corner_radius=20,
                                  border_width=3, border_color=ACCENT_COLOR)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        header_frame = ctk.CTkFrame(main_frame, fg_color=SECONDARY_BG_COLOR,
                                    corner_radius=15, height=100)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)

        title_text = "Journal Folder Verification" if self.is_verification else "Elite Dangerous Detection Complete"
        ctk.CTkLabel(header_frame, text=title_text,
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=ACCENT_COLOR).pack(pady=(20, 5))

        ctk.CTkLabel(header_frame, text="Please verify the detected information is correct",
                     font=ctk.CTkFont(size=14),
                     text_color=TEXT_SECONDARY).pack()

        content_scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        content_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        folder_frame = ctk.CTkFrame(content_scroll, fg_color=SECONDARY_BG_COLOR, corner_radius=12)
        folder_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(folder_frame, text="DETECTED FOLDER",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=ACCENT_COLOR).pack(pady=(15, 5))

        path_frame = ctk.CTkFrame(folder_frame, fg_color=TERTIARY_BG_COLOR, corner_radius=8)
        path_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(path_frame, text=self.analysis_data["folder_path"],
                     font=ctk.CTkFont(size=12, family="Courier"),
                     text_color=TEXT_COLOR, wraplength=800).pack(pady=10, padx=10)

        stats_frame = ctk.CTkFrame(content_scroll, fg_color=SECONDARY_BG_COLOR, corner_radius=12)
        stats_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(stats_frame, text="JOURNAL SUMMARY",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=ACCENT_COLOR).pack(pady=(15, 10))

        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=15, pady=(0, 15))

        stats = [
            ("Journal Files", str(self.analysis_data["total_journals"])),
            ("Total Jumps", f"{self.analysis_data['total_jumps']:,}"),
            ("Unique Systems", f"{self.analysis_data['unique_systems']:,}"),
            ("Date Range", self.analysis_data["date_range"])
        ]

        for i, (label, value) in enumerate(stats):
            row = i // 2
            col = i % 2

            stat_card = ctk.CTkFrame(stats_grid, fg_color=TERTIARY_BG_COLOR, corner_radius=8)
            stat_card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

            ctk.CTkLabel(stat_card, text=label, font=ctk.CTkFont(size=11),
                         text_color=TEXT_MUTED).pack(pady=(8, 2))
            ctk.CTkLabel(stat_card, text=value, font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=TEXT_COLOR).pack(pady=(0, 8))

        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(1, weight=1)

        cmdrs_frame = ctk.CTkFrame(content_scroll, fg_color=SECONDARY_BG_COLOR, corner_radius=12)
        cmdrs_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(cmdrs_frame, text="DETECTED COMMANDERS",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=ACCENT_COLOR).pack(pady=(15, 10))

        if self.analysis_data["commanders"]:
            primary_cmdr = self.get_primary_commander()

            sorted_cmdrs = []
            for cmdr_name, cmdr_data in self.analysis_data["commanders"].items():
                sorted_cmdrs.append((cmdr_name, cmdr_data))

            sorted_cmdrs.sort(key=lambda x: (x[0] != primary_cmdr, x[0]))

            for cmdr_name, cmdr_data in sorted_cmdrs:
                is_primary = (cmdr_name == primary_cmdr)
                self.create_commander_card(cmdrs_frame, cmdr_name, cmdr_data, is_primary)
        else:
            ctk.CTkLabel(cmdrs_frame, text="No commanders detected in journals",
                         font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(pady=20)

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(button_frame, text="Use This Folder",
                      command=self.confirm_folder,
                      fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      width=200, height=45).pack(side="left", padx=(0, 10))

        ctk.CTkButton(button_frame, text="Choose Different Folder",
                      command=self.choose_different,
                      fg_color=SECONDARY_BG_COLOR, hover_color=TERTIARY_BG_COLOR,
                      border_width=1, border_color=BORDER_COLOR,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      width=200, height=45).pack(side="left", padx=5)

    def create_commander_card(self, parent, cmdr_name, cmdr_data, is_primary=False):
        card = ctk.CTkFrame(parent, fg_color=TERTIARY_BG_COLOR if not is_primary else ACCENT_COLOR,
                            corner_radius=10, border_width=2 if is_primary else 0,
                            border_color=SUCCESS_COLOR if is_primary else BORDER_COLOR)
        card.pack(fill="x", padx=15, pady=5)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))

        name_color = "#000000" if is_primary else TEXT_COLOR
        ctk.CTkLabel(header, text=f"CMDR {cmdr_name}" + (" (Primary)" if is_primary else ""),
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=name_color).pack(side="left")

        if cmdr_data["last_seen"]:
            ctk.CTkLabel(header, text=f"Last Active: {cmdr_data['last_seen']}",
                         font=ctk.CTkFont(size=10),
                         text_color=name_color if is_primary else TEXT_MUTED).pack(side="right")

        stats_container = ctk.CTkFrame(card, fg_color="transparent")
        stats_container.pack(fill="x", padx=15, pady=(0, 15))

        credits_text = "Unknown"
        if cmdr_data['credits'] > 0:
            if cmdr_data['credits'] >= 1_000_000_000:
                credits_text = f"{cmdr_data['credits'] / 1_000_000_000:.1f}B CR"
            elif cmdr_data['credits'] >= 1_000_000:
                credits_text = f"{cmdr_data['credits'] / 1_000_000:.1f}M CR"
            elif cmdr_data['credits'] >= 1_000:
                credits_text = f"{cmdr_data['credits'] / 1_000:.1f}K CR"
            else:
                credits_text = f"{cmdr_data['credits']:,} CR"

        ship_name = cmdr_data['ship'].replace('_', ' ').title() if cmdr_data['ship'] != "Unknown" else "Unknown"

        cmdr_stats = [
            ("Jumps", f"{cmdr_data['jumps']:,}"),
            ("Systems", f"{cmdr_data['unique_systems']:,}"),
            ("Credits", credits_text),
            ("Ship", ship_name),
            ("Combat", cmdr_data['rank_combat']),
            ("Trade", cmdr_data['rank_trade']),
            ("Exploration", cmdr_data['rank_exploration']),
            ("Sessions", f"{cmdr_data['play_sessions']}")
        ]

        for i, (label, value) in enumerate(cmdr_stats):
            if i % 4 == 0:
                row_frame = ctk.CTkFrame(stats_container, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)

            stat_frame = ctk.CTkFrame(row_frame, fg_color="#0a0a0a" if is_primary else "#1a1a1a",
                                      corner_radius=6)
            stat_frame.pack(side="left", fill="x", expand=True, padx=2)

            text_color = "#FFFFFF" if is_primary else TEXT_MUTED
            ctk.CTkLabel(stat_frame, text=label, font=ctk.CTkFont(size=9),
                         text_color=text_color).pack(pady=(4, 1))
            ctk.CTkLabel(stat_frame, text=value, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#FFFFFF" if is_primary else TEXT_COLOR).pack(pady=(0, 4))

    def confirm_folder(self):
        self.user_choice = "confirm"
        self.destroy()

    def choose_different(self):
        self.user_choice = "different"
        self.destroy()


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
        if self.master_ref.is_admin:
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
        if hasattr(self.master_ref, 'category_dropdown'):
            self.available_categories = list(self.master_ref.category_dropdown.cget("values"))
            if "All Categories" in self.available_categories:
                self.available_categories.remove("All Categories")
            self.setup_category_dropdown()
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
        if self.cb_done.get() and supabase:
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
        if self._is_closing or not self.master_ref.current_coords or not supabase:
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
                    print(f"Error loading new discoveries for map filter: {e}")

                richards_categories = []
                try:
                    richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                    richards_categories = [item["category"] for item in
                                           richards_response.data] if richards_response.data else []
                except:
                    pass
                all_systems = [s for s in all_systems if s.get("category") not in richards_categories]
                systems_with_distance = []
                for sys in all_systems:
                    if sys["systems"] != self.master_ref.system_name:
                        dx = sys["x"] - cx
                        dy = sys["y"] - cy
                        dz = sys["z"] - cz
                        distance = (dx * dx + dy * dy + dz * dz) ** 0.5
                        systems_with_distance.append({
                            "name": sys["systems"],
                            "category": sys.get("category", "Unknown"),
                            "distance": distance
                        })
                systems_with_distance.sort(key=lambda x: x["distance"])
                top_systems = systems_with_distance[:20]
                self.after(0, lambda: self._display_filter_systems(top_systems))
            except Exception as e:
                print(f"Error loading filter systems: {e}")
                self.after(0, lambda: self._show_filter_error())

        threading.Thread(target=load_systems, daemon=True).start()

    def _display_filter_systems(self, systems):
        try:
            for widget in self.scroll.winfo_children():
                widget.destroy()
            if not systems:
                ctk.CTkLabel(self.scroll, text="No systems",
                             font=ctk.CTkFont(size=11), text_color="#666666").pack(pady=20)
                return
            for sys in systems:
                frame = ctk.CTkFrame(self.scroll, fg_color="#333333", corner_radius=8, height=60)
                frame.pack(fill="x", padx=5, pady=2)
                frame.pack_propagate(False)
                cat_color = get_or_create_category_color(sys["category"]) if sys["category"] else "#666666"
                color_strip = ctk.CTkFrame(frame, width=4, fg_color=cat_color)
                color_strip.place(x=0, y=0, relheight=1)
                info_frame = ctk.CTkFrame(frame, fg_color="transparent")
                info_frame.place(x=10, y=5, relwidth=0.7, relheight=0.9)
                name_label = ctk.CTkLabel(info_frame, text=sys['name'],
                                          font=ctk.CTkFont(size=12, weight="bold"),
                                          text_color="white", anchor="w",
                                          cursor="hand2")
                name_label.pack(anchor="w")
                name_label.bind("<Button-1>", lambda e, s=sys['name']: self.master_ref.copy_to_clipboard(s))
                cat_text = sys['category'][:32] + "..." if len(sys['category']) > 35 else sys['category']
                ctk.CTkLabel(info_frame, text=cat_text,
                             font=ctk.CTkFont(size=10),
                             text_color="#aaaaaa", anchor="w").pack(anchor="w")
                ctk.CTkLabel(info_frame, text=f"{sys['distance']:.1f} LY",
                             font=ctk.CTkFont(size=10),
                             text_color=cat_color, anchor="w").pack(anchor="w")
                btn = ctk.CTkButton(frame, text="→", width=30, height=30,
                                    command=lambda s=sys['name']: self.master_ref.view_system(s, None),
                                    fg_color="transparent", hover_color="#444444",
                                    font=ctk.CTkFont(size=16),
                                    text_color=cat_color,
                                    corner_radius=15)
                btn.place(relx=0.9, rely=0.5, anchor="center")
        except Exception as e:
            print(f"Error displaying filter systems: {e}")

    def _show_filter_error(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.scroll, text="Error loading",
                     font=ctk.CTkFont(size=11), text_color="#ff6666").pack(pady=20)

    def toggle_unvisited(self):
        if self.cb_unv.get() and supabase:
            # Get systems from main systems table
            all_sys = supabase.table("systems").select("systems,category,x,y,z").execute().data or []

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
                        if not any(s["systems"] == discovery["system"] for s in all_sys):
                            all_sys.append(discovery_data)
            except Exception as e:
                print(f"Error loading new discoveries for map: {e}")

            richards_categories = []
            try:
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                richards_categories = [item["category"] for item in
                                       richards_response.data] if richards_response.data else []
            except:
                pass
            if "All Categories" in self.selected_categories or not self.selected_categories:
                all_sys = [s for s in all_sys if s.get("category") not in richards_categories]
            else:
                pass
            if "All Categories" not in self.selected_categories and self.selected_categories:
                all_sys = [s for s in all_sys if categories_match_filter(s.get("category"), self.selected_categories)]
            taken = {r["system"] for r in supabase.table("taken").select("system").execute().data or []}
            pois = supabase.table("pois").select("system_name").execute().data or []
            poi_systems = {poi["system_name"] for poi in pois}
            self.unv_data = [rec for rec in all_sys if
                             rec["systems"] not in taken and rec["systems"] not in poi_systems]
        else:
            self.unv_data = []
        self.draw_image()

    def toggle_your_claims(self):
        if self.cb_you.get() and supabase:
            cmdr = self.master_ref.cmdr_name
            recs = supabase.table("taken").select("system,by_cmdr,done").eq("by_cmdr", cmdr).execute().data or []
            active_claims = [r for r in recs if not r.get("done", False)]
            names = [r["system"] for r in active_claims]
            if names:
                # Get claimed systems from main systems table
                data = supabase.table("systems").select("systems,category,x,y,z").in_("systems",
                                                                                      names).execute().data or []

                # Also check system_information table for new discoveries
                try:
                    new_discoveries = supabase.table("system_information").select("system,category,x,y,z").in_("system",
                                                                                                               names).execute().data or []
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
                            if not any(s["systems"] == discovery["system"] for s in data):
                                data.append(discovery_data)
                except Exception as e:
                    print(f"Error loading claimed new discoveries for map: {e}")

                richards_categories = []
                try:
                    richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                    richards_categories = [item["category"] for item in
                                           richards_response.data] if richards_response.data else []
                except:
                    pass
                data = [s for s in data if
                        not any(cat in richards_categories for cat in parse_categories(s.get("category")))]
                if "All Categories" not in self.selected_categories and self.selected_categories:
                    data = [s for s in data if categories_match_filter(s.get("category"), self.selected_categories)]
                for rec in data:
                    rec["by_cmdr"] = cmdr
                self.you_data = data
            else:
                self.you_data = []
        else:
            self.you_data = []
        self.draw_image()

    def toggle_others_claims(self):
        if self.cb_oth.get() and supabase:
            cmdr = self.master_ref.cmdr_name
            recs = supabase.table("taken").select("system,by_cmdr").neq("by_cmdr", cmdr).execute().data or []
            names = [r["system"] for r in recs]
            # Get others' claimed systems from main systems table
            data = supabase.table("systems").select("systems,category,x,y,z").in_("systems", names).execute().data or []

            # Also check system_information table for new discoveries claimed by others
            try:
                new_discoveries = supabase.table("system_information").select("system,category,x,y,z").in_("system",
                                                                                                           names).execute().data or []
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
                        if not any(s["systems"] == discovery["system"] for s in data):
                            data.append(discovery_data)
            except Exception as e:
                print(f"Error loading others' claimed new discoveries for map: {e}")

            richards_categories = []
            try:
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                richards_categories = [item["category"] for item in
                                       richards_response.data] if richards_response.data else []
            except:
                pass
            data = [s for s in data if
                    not any(cat in richards_categories for cat in parse_categories(s.get("category")))]
            if "All Categories" not in self.selected_categories and self.selected_categories:
                data = [s for s in data if categories_match_filter(s.get("category"), self.selected_categories)]
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
            sys_category_data = {}
            sys_info_response = supabase.table("system_information").select("system,category").execute()
            if sys_info_response.data:
                for info in sys_info_response.data:
                    if info.get("category"):
                        sys_category_data[info["system"]] = info["category"]
            for poi in pois:
                if (poi.get("coords_x") is not None or poi.get("x") is not None):
                    x_coord = poi.get("coords_x") if poi.get("coords_x") is not None else poi.get("x")
                    y_coord = poi.get("coords_y") if poi.get("coords_y") is not None else poi.get("y")
                    z_coord = poi.get("coords_z") if poi.get("coords_z") is not None else poi.get("z")
                    if x_coord is not None and y_coord is not None and z_coord is not None:
                        saved_category = sys_category_data.get(poi["system_name"], "Potential POI")
                        self.pot_poi_data.append({
                            "systems": poi["system_name"],
                            "x": float(x_coord),
                            "y": float(y_coord),
                            "z": float(z_coord),
                            "category": saved_category
                        })
                else:
                    sys_data = supabase.table("systems").select("x,y,z,category").eq("systems",
                                                                                     poi["system_name"]).execute()
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
            try:
                pois = supabase.table("pois").select("*").eq("potential_or_poi", "POI").execute().data or []
                self.poi_data = []
                for poi in pois:
                    if (poi.get("coords_x") is not None or poi.get("x") is not None):
                        x_coord = poi.get("coords_x") if poi.get("coords_x") is not None else poi.get("x")
                        y_coord = poi.get("coords_y") if poi.get("coords_y") is not None else poi.get("y")
                        z_coord = poi.get("coords_z") if poi.get("coords_z") is not None else poi.get("z")
                        if x_coord is not None and y_coord is not None and z_coord is not None:
                            self.poi_data.append({
                                "systems": poi["system_name"],
                                "x": float(x_coord),
                                "y": float(y_coord),
                                "z": float(z_coord),
                                "category": "POI"
                            })
                    else:
                        try:
                            sys_data = supabase.table("systems").select("x,y,z,category").eq("systems", poi[
                                "system_name"]).execute()
                            if sys_data.data:
                                self.poi_data.append({
                                    "systems": poi["system_name"],
                                    "x": sys_data.data[0]["x"],
                                    "y": sys_data.data[0]["y"],
                                    "z": sys_data.data[0]["z"],
                                    "category": sys_data.data[0]["category"]
                                })
                        except Exception as coord_e:
                            print(f"Error fetching coordinates for POI {poi['system_name']}: {coord_e}")
                            continue
            except Exception as e:
                print(f"Error in toggle_pois: {e}")
                self.poi_data = []
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
                    cw // 2, ch // 2, image=self.photo, anchor="center", tags="background"
                )
            else:
                self.canvas.itemconfig(self.image_id, image=self.photo)
            self.canvas.tag_lower("background")
            for tag in ("unvisited", "your", "others", "cmdr", "all_cmdrs", "pot_poi", "poi", "done"):
                self.canvas.delete(tag)
            if self.label_id:
                self.canvas.delete(self.label_id)
            if not hasattr(self, '_dot_data'):
                self._dot_data = {}
            else:
                self._dot_data.clear()
            if self.cb_unv.get():
                self._draw_list(self.unv_data, "unvisited", "blue")

            self._draw_list(self.you_data, "your", "green")
            self._draw_list(self.oth_data, "others", "orange")
            self._draw_list(self.pot_poi_data, "pot_poi", "yellow")
            self._draw_list(self.poi_data, "poi", "gold")
            self._draw_list(self.done_data, "done", "purple")
            if self.master_ref.is_admin and hasattr(self, 'cb_all_cmdrs') and self.cb_all_cmdrs.get():
                self._draw_all_cmdrs()
            if self.cb_loc.get() and not (
                    self.master_ref.is_admin and hasattr(self, 'cb_all_cmdrs') and self.cb_all_cmdrs.get()):
                self._draw_cmdr()
        except Exception as e:
            if not self._is_closing:
                print(f"Error in draw_image: {e}")

    def _draw_list(self, data, tag, color):
        if self._is_closing:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        im_w, im_h = self.get_med_resized().size
        x0, y0 = (cw - im_w) / 2, (ch - im_h) / 2
        scale = im_w / self.base_full.width
        if not hasattr(self, '_dot_data'):
            self._dot_data = {}
        for rec in data:
            try:
                # Ensure coordinates are converted to float
                x_coord = float(rec["x"]) if rec["x"] is not None else 0.0
                z_coord = float(rec["z"]) if rec["z"] is not None else 0.0

                px = ORIG_OFF_X + x_coord / LY_PER_PIXEL
                py = ORIG_OFF_Y - z_coord / LY_PER_PIXEL
                cx, cy = x0 + px * scale, y0 + py * scale
                dot = self.canvas.create_oval(
                    cx - DOT_RADIUS, cy - DOT_RADIUS,
                    cx + DOT_RADIUS, cy + DOT_RADIUS,
                    fill=color, outline="white", width=1, tags=(tag, "dot")
                )
                text = f"{rec['systems']}\n{rec['category']}"
                if tag in ("your", "others", "done"):
                    text += f"\nby {rec.get('by_cmdr', '')}"
                if tag == "done":
                    text += "\n(Completed)"
                self._dot_data[dot] = {
                    'text': text,
                    'system': rec["systems"],
                    'category': rec.get("category")
                }
            except (ValueError, TypeError) as e:
                print(f"Error drawing system {rec.get('systems', 'Unknown')}: {e}")
                continue
        self.canvas.tag_bind(tag, "<Enter>", self._on_dot_enter)
        self.canvas.tag_bind(tag, "<Leave>", lambda e: self._hide_label())
        self.canvas.tag_bind(tag, "<Button-3>", self._on_dot_rightclick)

    def _draw_cmdr(self):
        if self._is_closing:
            return
        pos = getattr(self.master_ref, "latest_starpos", None)
        if not pos: return
        try:
            xw, yw, zw = pos
            # Ensure coordinates are converted to float
            xw = float(xw) if xw is not None else 0.0
            zw = float(zw) if zw is not None else 0.0
            px = ORIG_OFF_X + xw / LY_PER_PIXEL
            py = ORIG_OFF_Y - zw / LY_PER_PIXEL
        except (ValueError, TypeError) as e:
            print(f"Error drawing commander position: {e}")
            return
        im = self.get_med_resized()
        scale = im.width / self.base_full.width
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        x0, y0 = (cw - im.width) / 2, (ch - im.height) / 2
        cx, cy = x0 + px * scale, y0 + py * scale
        dot = self.canvas.create_oval(
            cx - DOT_RADIUS, cy - DOT_RADIUS,
            cx + DOT_RADIUS, cy + DOT_RADIUS,
            fill="red", outline="white", width=1, tags=("cmdr", "dot")
        )
        if not hasattr(self, '_dot_data'):
            self._dot_data = {}
        txt = f"CMDR {self.master_ref.cmdr_name}\n{self.master_ref.system_name}"
        self._dot_data[dot] = {
            'text': txt,
            'system': self.master_ref.system_name,
            'category': None
        }
        self.canvas.tag_bind("cmdr", "<Enter>", self._on_dot_enter)
        self.canvas.tag_bind("cmdr", "<Leave>", lambda e: self._hide_label())
        self.canvas.tag_bind("cmdr", "<Button-3>", self._on_dot_rightclick)

    def _draw_all_cmdrs(self):
        if self._is_closing:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        im_w, im_h = self.get_med_resized().size
        x0, y0 = (cw - im_w) / 2, (ch - im_h) / 2
        scale = im_w / self.base_full.width
        if not hasattr(self, '_dot_data'):
            self._dot_data = {}
        for rec in self.all_cmdrs_data:
            if rec.get("starpos_x") is None:
                continue
            try:
                # Ensure coordinates are converted to float
                starpos_x = float(rec["starpos_x"]) if rec["starpos_x"] is not None else 0.0
                starpos_z = float(rec["starpos_z"]) if rec["starpos_z"] is not None else 0.0
                px = ORIG_OFF_X + starpos_x / LY_PER_PIXEL
                py = ORIG_OFF_Y - starpos_z / LY_PER_PIXEL
            except (ValueError, TypeError) as e:
                print(f"Error drawing commander {rec.get('cmdr_name', 'Unknown')}: {e}")
                continue
            cx, cy = x0 + px * scale, y0 + py * scale
            color = "red" if rec.get("cmdr_name") == self.master_ref.cmdr_name else "purple"
            dot = self.canvas.create_oval(
                cx - DOT_RADIUS, cy - DOT_RADIUS,
                cx + DOT_RADIUS, cy + DOT_RADIUS,
                fill=color, outline="white", width=1, tags=("all_cmdrs", "dot")
            )
            text = f"CMDR {rec['cmdr_name']}\n{rec.get('star_system', 'Unknown')}\nLast updated: {(rec.get('updated_at') or 'Unknown')[:10]}"
            self._dot_data[dot] = {
                'text': text,
                'system': rec.get('star_system'),
                'category': None
            }
        self.canvas.tag_bind("all_cmdrs", "<Enter>", self._on_dot_enter)
        self.canvas.tag_bind("all_cmdrs", "<Leave>", lambda e: self._hide_label())
        self.canvas.tag_bind("all_cmdrs", "<Button-3>", self._on_dot_rightclick)

    def _on_dot_enter(self, event):
        items = self.canvas.find_withtag("current")
        if items and hasattr(self, '_dot_data'):
            item = items[0]
            if item in self._dot_data:
                self._show_hover(event, self._dot_data[item]['text'])

    def _on_dot_rightclick(self, event):
        items = self.canvas.find_withtag("current")
        if items and hasattr(self, '_dot_data'):
            item = items[0]
            if item in self._dot_data:
                data = self._dot_data[item]
                if data['system']:
                    self.master_ref.view_system(data['system'], data['category'])

    def _show_hover(self, event, text):
        if hasattr(self, 'label_id') and self.label_id:
            self.canvas.delete(self.label_id)
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        lbl = ctk.CTkLabel(self.canvas,
                           text=text + "\nRight-click to view",
                           fg_color="#333333", text_color="white",
                           corner_radius=4, justify="center")
        self.label_id = self.canvas.create_window(cx, cy - DOT_RADIUS - 5, window=lbl, anchor="s")
        self.canvas.tag_raise(self.label_id)

    def _hide_label(self):
        if hasattr(self, 'label_id') and self.label_id:
            self.canvas.delete(self.label_id)
            self.label_id = None

    def get_med_resized(self):
        z = max(MIN_ZOOM, min(self.zoom, MAX_ZOOM))
        cache_key = f"{z:.2f}"
        if not hasattr(self, '_zoom_cache'):
            self._zoom_cache = {}
            self._cache_order = []
        if cache_key in self._zoom_cache:
            self._cache_order.remove(cache_key)
            self._cache_order.append(cache_key)
            return self._zoom_cache[cache_key]
        if z > 2.0:
            resample = Resampling.NEAREST
        elif z > 1.5:
            resample = Resampling.BOX
        else:
            resample = Resampling.BILINEAR
        resized = self.base_med.resize(
            (int(self.base_med.width * z), int(self.base_med.height * z)),
            resample
        )
        self._zoom_cache[cache_key] = resized
        self._cache_order.append(cache_key)
        if len(self._cache_order) > 5:
            oldest = self._cache_order.pop(0)
            del self._zoom_cache[oldest]
        return resized

    def on_press(self, e):
        self.canvas.scan_mark(e.x, e.y)

    def on_drag(self, e):
        self.canvas.scan_dragto(e.x, e.y, gain=1)

    def on_wheel(self, e):
        mouse_x = self.winfo_pointerx() - self.winfo_rootx()
        if mouse_x <= self.current_sidebar_width:
            return
        factor = 1.1 if e.delta > 0 else 0.9
        self.zoom = max(MIN_ZOOM, min(self.zoom * factor, MAX_ZOOM))
        if self._zr: self.after_cancel(self._zr)
        self._zr = self.after(30, self.draw_image)

    def on_key(self, e):
        if e.keysym == "Escape":
            if hasattr(self, '_dropdown_visible') and self._dropdown_visible:
                self.category_dropdown_frame.place_forget()
                self._dropdown_visible = False
            else:
                self.on_close()

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

    def setup_category_dropdown(self):
        self.category_dropdown_frame.place_forget()
        header_frame = ctk.CTkFrame(self.category_dropdown_frame,
                                    fg_color=SECONDARY_BG_COLOR,
                                    height=40,
                                    corner_radius=12)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        header_label = ctk.CTkLabel(header_frame,
                                    text="FILTER CATEGORIES",
                                    font=ctk.CTkFont(size=13, weight="bold"),
                                    text_color=TEXT_COLOR)
        header_label.place(relx=0.5, rely=0.5, anchor="center")
        self.dropdown_header_label = ctk.CTkLabel(self.category_dropdown_frame,
                                                  text="Select categories and click outside to apply",
                                                  font=ctk.CTkFont(size=11, slant="italic"),
                                                  text_color=TEXT_MUTED)
        self.dropdown_header_label.pack(pady=(0, 5))
        scroll_frame = ctk.CTkScrollableFrame(self.category_dropdown_frame,
                                              fg_color=SECONDARY_BG_COLOR,
                                              width=260,
                                              height=200,
                                              corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # FIX SCROLLING for map category dropdown
        def _map_category_scroll_handler(event):
            try:
                scroll_frame._parent_canvas.yview_scroll(int(-3 * (event.delta / 120)), "units")
            except:
                pass
            return "break"

        # Bind scroll events to map category dropdown
        scroll_frame.bind("<MouseWheel>", _map_category_scroll_handler)
        if hasattr(scroll_frame, '_parent_canvas'):
            scroll_frame._parent_canvas.bind("<MouseWheel>", _map_category_scroll_handler)
        all_frame = ctk.CTkFrame(scroll_frame, fg_color=TERTIARY_BG_COLOR, corner_radius=8)
        all_frame.pack(fill="x", padx=5, pady=(5, 10))
        all_cb = ctk.CTkCheckBox(all_frame,
                                 text="All Categories",
                                 font=ctk.CTkFont(size=13, weight="bold"),
                                 text_color=ACCENT_COLOR,
                                 fg_color=ACCENT_COLOR,
                                 hover_color=ACCENT_HOVER,
                                 border_color=ACCENT_COLOR,
                                 checkbox_width=22,
                                 checkbox_height=22,
                                 corner_radius=6,
                                 command=lambda: self.toggle_all_categories())
        all_cb.pack(anchor="w", padx=15, pady=10)
        all_cb.select()
        self.all_categories_cb = all_cb
        cat_style = {
            "font": ctk.CTkFont(size=12, weight="bold"),
            "text_color": TEXT_COLOR,
            "fg_color": SUCCESS_COLOR,
            "hover_color": SUCCESS_HOVER,
            "border_color": "#444444",
            "checkbox_width": 20,
            "checkbox_height": 20,
            "corner_radius": 5
        }
        for category in self.available_categories:
            cat_frame = ctk.CTkFrame(scroll_frame,
                                     fg_color="transparent",
                                     corner_radius=8,
                                     height=35)
            cat_frame.pack(fill="x", padx=5, pady=2)
            cat_frame.pack_propagate(False)
            cat_color = get_or_create_category_color(category)
            color_strip = ctk.CTkFrame(cat_frame, width=4, fg_color=cat_color, corner_radius=2)
            color_strip.place(x=5, y=5, relheight=0.7)
            cb = ctk.CTkCheckBox(cat_frame,
                                 text=category[:50] + "..." if len(category) > 50 else category,
                                 command=self.update_selected_categories,
                                 **cat_style)
            cb.pack(anchor="w", padx=(15, 10), pady=5)
            self.category_checkboxes.append((category, cb))

            def on_enter(e, frame=cat_frame):
                frame.configure(fg_color=TERTIARY_BG_COLOR)

            def on_leave(e, frame=cat_frame):
                frame.configure(fg_color="transparent")

            cat_frame.bind("<Enter>", on_enter)
            cat_frame.bind("<Leave>", on_leave)
        separator_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent", height=30)
        separator_frame.pack(fill="x", pady=(10, 5))
        separator_label = ctk.CTkLabel(separator_frame,
                                       text="———— Richard's Stuff ————",
                                       font=ctk.CTkFont(size=12, weight="bold"),
                                       text_color="#666666")
        separator_label.pack()
        self.richards_categories = []
        if supabase:
            try:
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                if richards_response.data:
                    for item in richards_response.data:
                        category = item["category"]
                        cb = ctk.CTkCheckBox(scroll_frame,
                                             text=category[:50] + "..." if len(category) > 50 else category,
                                             font=ctk.CTkFont(size=12),
                                             text_color="#ff6b6b",
                                             fg_color="#666666",
                                             hover_color="#777777",
                                             border_color="#888888",
                                             checkbox_width=20,
                                             checkbox_height=20,
                                             command=self.update_selected_categories)
                        cb.pack(anchor="w", padx=10, pady=3)
                        self.category_checkboxes.append((category, cb))
                        self.richards_categories.append(category)
            except Exception as e:
                print(f"Error loading Richard's categories: {e}")

    def toggle_category_dropdown(self):
        if not hasattr(self, 'category_dropdown_frame'):
            return
        if hasattr(self, '_dropdown_toggle_pending') and self._dropdown_toggle_pending:
            return
        self._dropdown_toggle_pending = True
        self.after(150, lambda: setattr(self, '_dropdown_toggle_pending', False))
        if hasattr(self, '_dropdown_visible') and self._dropdown_visible:
            self.category_dropdown_frame.place_forget()
            self._dropdown_visible = False
            self.category_dropdown_frame.configure(border_color=ACCENT_COLOR, border_width=3)
            self.apply_category_filter()
            self.update_nearest_in_filter()
        else:
            self._temp_selected_categories = self.selected_categories.copy()
            if hasattr(self, 'dropdown_header_label'):
                self.dropdown_header_label.configure(text="Select categories and click outside to apply",
                                                     text_color=TEXT_MUTED,
                                                     font=ctk.CTkFont(size=11, slant="italic"))
            self.category_dropdown_frame.configure(border_color=ACCENT_COLOR, border_width=3)
            self.category_dropdown_frame.place(x=20, y=self.category_button.winfo_y() + 35)
            self._dropdown_visible = True
            self.category_dropdown_frame.lift()

    def _handle_click(self, event):
        if hasattr(self, '_dropdown_visible') and self._dropdown_visible:
            widget = event.widget
            try:
                if widget != self.category_dropdown_frame and widget not in self.category_dropdown_frame.winfo_children():
                    is_dropdown_child = False
                    parent = widget
                    while parent:
                        if parent == self.category_dropdown_frame:
                            is_dropdown_child = True
                            break
                        try:
                            parent = parent.master
                        except:
                            break
                    if not is_dropdown_child and widget != self.category_button:
                        self.after(10, self.toggle_category_dropdown)
            except:
                pass

    def toggle_all_categories(self):
        if self.all_categories_cb.get():
            self.selected_categories = ["All Categories"]
            for cat, cb in self.category_checkboxes:
                if cat not in getattr(self, 'richards_categories', []):
                    cb.deselect()
                else:
                    cb.deselect()
            self.category_button.configure(text="All Categories")
        else:
            self.selected_categories = []
            for cat, cb in self.category_checkboxes:
                cb.deselect()
            self.category_button.configure(text="No categories selected")
        self.category_dropdown_frame.configure(border_color=WARNING_COLOR, border_width=4)
        if hasattr(self, 'dropdown_header_label'):
            self.dropdown_header_label.configure(text="⚠ Click outside to apply changes",
                                                 text_color=WARNING_COLOR,
                                                 font=ctk.CTkFont(size=12, weight="bold"))

    def update_selected_categories(self):
        self.selected_categories = []
        self.all_categories_cb.deselect()
        for cat, cb in self.category_checkboxes:
            if cb.get():
                self.selected_categories.append(cat)
        if not self.selected_categories:
            self.category_button.configure(text="No categories selected")
        elif len(self.selected_categories) == 1:
            self.category_button.configure(
                text=self.selected_categories[0][:45] + "..." if len(self.selected_categories[0]) > 45 else
                self.selected_categories[0])
        else:
            self.category_button.configure(text=f"{len(self.selected_categories)} categories selected")
        self.category_dropdown_frame.configure(border_color=WARNING_COLOR, border_width=4)
        if hasattr(self, 'dropdown_header_label'):
            self.dropdown_header_label.configure(text="⚠ Click outside to apply changes",
                                                 text_color=WARNING_COLOR,
                                                 font=ctk.CTkFont(size=12, weight="bold"))


class App(ctk.CTk):
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

    def __init__(self):
        super().__init__()

        self.splash = SplashScreen()
        self.withdraw()

        if not _cfg.get("journal_verified"):
            self.after(2000, self.auto_setup_journals)
        else:
            self.after(2000, self.finish_splash_and_start)

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

        dialog = JournalConfirmationDialog(self, analysis_data, is_verification=False)
        self.wait_window(dialog)

        if dialog.user_choice == "confirm":
            _cfg["journal_path"] = analysis_data["folder_path"]
            _cfg["journal_verified"] = True
            save_config(_cfg)
            self.initialize_app()
        elif dialog.user_choice == "different":
            self._from_splash_failure = True
            self.ask_for_journal_folder()
        else:
            os._exit(0)

    def ask_for_journal_folder_with_splash(self):
        """Ask for journal folder with splash screen handling"""
        if self.splash:
            self.splash.destroy()
            self.splash = None

        self.deiconify()
        self._from_splash_failure = True
        self.ask_for_journal_folder()

    def initialize_app(self):
        """Initialize the main application"""
        print("[STARTUP] Initializing main application...")

        self.deiconify()
        self.lift()
        self.focus_force()

        if getattr(sys, 'frozen', False):
            try:
                print("Running as exe, waiting for Windows to settle...")
            except:
                pass
            time.sleep(1)

        try:
            print(f"EXE_DIR: {EXE_DIR}")
            print(f"Current working directory: {os.getcwd()}")
        except:
            pass
        self.config_data = _cfg
        self.cmdr_name = self.config_data.get("commander_name", "Unknown")
        self.system_name = "Unknown"
        self.latest_starpos = None
        self.current_coords = None
        self.stop_event = threading.Event()
        self.map_window = None
        self.is_admin = _RunSystemGet
        self.last_update_time = 0
        self.update_cooldown = 1.0
        self._is_destroying = False
        self._update_in_progress = False
        self._app_initialized = False
        self.session_start_time = time.time()
        self.jump_count = 0
        self.title(APP_TITLE)
        try:
            self.iconbitmap(resource("icon.ico"))
        except:
            pass
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=MAIN_BG_COLOR)
        self.attributes("-topmost", False)
        bold = (ctk.CTkFont(family="Dosis", size=DOSIS_BOLD, weight="bold")
                if "Dosis" in tkFont.families() else ctk.CTkFont(size=DOSIS_BOLD, weight="bold"))
        self.tabview = ctk.CTkTabview(self, width=WINDOW_WIDTH - 20, height=WINDOW_HEIGHT - 40,
                                      fg_color=CARD_BG_COLOR,
                                      segmented_button_fg_color=SECONDARY_BG_COLOR,
                                      segmented_button_selected_color=ACCENT_COLOR,
                                      segmented_button_selected_hover_color=ACCENT_HOVER,
                                      segmented_button_unselected_color=TERTIARY_BG_COLOR,
                                      segmented_button_unselected_hover_color="#363636",
                                      text_color=TEXT_COLOR,
                                      corner_radius=15,
                                      border_width=2,
                                      border_color=BORDER_COLOR)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)
        self.main_tab = self.tabview.add("Main")
        self.galaxy_tab = self.tabview.add("Galaxy Map")
        self.setup_main_tab(bold)
        self.setup_galaxy_tab()

        # Bottom selector (similar to top tab style)
        self.setup_bottom_selector()

        version_frame = ctk.CTkFrame(self, fg_color=SECONDARY_BG_COLOR, corner_radius=6)
        version_frame.place(relx=0.98, rely=0.98, anchor="se")
        ctk.CTkLabel(version_frame, text=VERSION_TEXT,
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED,
                     fg_color=SECONDARY_BG_COLOR).pack(padx=10, pady=4)
        self._app_initialized = True
        self.after(100, self.check_journal_popup)

    def refresh_all_data(self):
        try:
            self.nearest_display_limit = 5

            if hasattr(self, 'nearest_scroll') and hasattr(self.nearest_scroll, '_parent_canvas'):
                self.nearest_scroll._parent_canvas.yview_moveto(0)

            if hasattr(self, 'current_journal_path') and self.current_journal_path:
                sysnm, pos = self.find_latest_journal_and_pos(self.current_journal_path)
                if sysnm:
                    self.system_name = sysnm
                    self.system_label.configure(text=sysnm)
                if pos:
                    self.latest_starpos = pos
                    self.current_coords = pos
            self.find_nearest_unclaimed()
            self.update_nearest_systems()
            if self.current_coords:
                self.update_commander_location()
            if self.map_window and hasattr(self.map_window, 'winfo_exists'):
                try:
                    if self.map_window.winfo_exists():
                        self.map_window.refresh_all_filters()
                except:
                    pass
            self.btn_refresh.configure(text="✓ Refreshed", fg_color=SUCCESS_COLOR, text_color="#000000")
            self.after(1500, lambda: self.btn_refresh.configure(text="↻ Refresh",
                                                                fg_color=SECONDARY_BG_COLOR,
                                                                text_color=TEXT_COLOR))
        except Exception as e:
            print(f"Error refreshing data: {e}")
            self.btn_refresh.configure(text="❌ Error", fg_color=DANGER_COLOR)
            self.after(2000, lambda: self.btn_refresh.configure(text="↻ Refresh",
                                                                fg_color=SECONDARY_BG_COLOR,
                                                                text_color=TEXT_COLOR))

    def get_category_table_data(self, system_name, category):
        """Get category-specific data from the system_category_info table"""
        if not supabase or not category:
            print(f"[DEBUG] get_category_table_data early return: supabase={bool(supabase)}, category='{category}'")
            return None

        print(f"[DEBUG] Getting category data: system='{system_name}', category='{category}'")

        try:
            # First try the new system_category_info table
            print(f"[DEBUG] Querying system_category_info table...")
            result = supabase.table("system_category_info").select("system_info").eq("system_name", system_name).eq(
                "category", category).execute()
            print(f"[DEBUG] Query result: {len(result.data) if result.data else 0} records found")

            if result.data:
                system_info = result.data[0].get("system_info")
                if system_info:
                    print(f"[SUCCESS] Found system info in system_category_info table: {system_info[:100]}..." if len(
                        system_info) > 100 else f"[SUCCESS] Found system info: {system_info}")
                    return system_info
                else:
                    print(f"[DEBUG] Record found but system_info is empty")
            else:
                print(f"[DEBUG] No records found in system_category_info table")

            # Fallback: try the old category-specific table method
            print(f"[DEBUG] Attempting fallback to category-specific table...")
            table_name = category.strip()
            print(f"[DEBUG] Looking for table: '{table_name}' for system: '{system_name}'")
            escaped_table = table_name.replace('"', '""')
            response = supabase.table(table_name).select("*").execute()
            print(f"[DEBUG] Table response: {response.data[:2] if response.data else 'No data'}")
            if not response.data:
                print(f"[DEBUG] No data found in table '{table_name}'")
                return None
            for row in response.data:
                system_value = None
                for col_name in ['system', 'System', 'SYSTEM', 'systems', 'Systems', 'SYSTEMS']:
                    if col_name in row:
                        system_value = row[col_name]
                        print(f"[DEBUG] Found system column '{col_name}' with value: '{system_value}'")
                        break
                if system_value and system_value.lower().strip() == system_name.lower().strip():
                    print(f"[DEBUG] Found matching system!")
                    info_parts = []
                    for key, value in row.items():
                        if key.lower() in ['id', 'system', 'systems'] or value is None:
                            continue
                        formatted_key = key.replace('_', ' ').replace('-', ' ')
                        formatted_key = ' '.join(word.capitalize() for word in formatted_key.split())
                        info_parts.append(f"{formatted_key}: {value}")
                    if info_parts:
                        result = '\n'.join(info_parts)
                        print(f"[SUCCESS] Returning fallback info: {result}")
                        return result
                    return None
            print(f"[DEBUG] No matching system found in fallback table")
            return None
        except Exception as e:
            print(f"[ERROR] Error getting category table data: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_categories(self):
        if not supabase:
            return
        try:
            response = supabase.table("systems").select("category").execute()
            if response.data:
                # Parse all categories including multi-category systems
                all_categories = set()
                for item in response.data:
                    if item["category"]:
                        parsed_cats = parse_categories(item["category"])
                        all_categories.update(parsed_cats)

                categories = sorted(list(all_categories))

                # Filter out Richard's categories
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                richards_categories = {item["category"] for item in
                                       richards_response.data} if richards_response.data else set()
                categories = [cat for cat in categories if cat not in richards_categories]
                categories.insert(0, "All Categories")

                if hasattr(self, 'category_dropdown'):
                    self.category_dropdown.configure(values=categories)
                if hasattr(self, 'category_dropdown_frame_main'):
                    self.setup_category_dropdown_main()
                if self.map_window and hasattr(self.map_window, 'category_dropdown'):
                    self.map_window.category_dropdown.configure(values=categories)
        except Exception as e:
            print(f"Error loading categories: {e}")

    def get_richards_categories(self):
        if not supabase:
            return []
        try:
            richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
            return [item["category"] for item in richards_response.data] if richards_response.data else []
        except:
            return []

    def test_system_category_info_permissions(self):
        """Test if we can read/write to the system_category_info table"""
        if not supabase:
            return False, "No supabase connection"

        try:
            # Test SELECT permission
            print("[DEBUG] Testing SELECT permission on system_category_info...")
            select_result = supabase.table("system_category_info").select("*").limit(1).execute()
            print(f"[DEBUG] SELECT test result: {len(select_result.data) if select_result.data else 0} rows")

            # Test INSERT permission with a dummy record
            print("[DEBUG] Testing INSERT permission on system_category_info...")
            test_data = {
                "system_name": "TEST_SYSTEM_PERMISSION_CHECK",
                "category": "TEST_CATEGORY",
                "system_info": "This is a test record to check permissions"
            }
            insert_result = supabase.table("system_category_info").insert(test_data).execute()
            print(f"[DEBUG] INSERT test successful: {insert_result}")

            # Clean up the test record
            print("[DEBUG] Cleaning up test record...")
            cleanup_result = supabase.table("system_category_info").delete().eq("system_name",
                                                                                "TEST_SYSTEM_PERMISSION_CHECK").execute()
            print(f"[DEBUG] Cleanup successful: {cleanup_result}")

            return True, "All permissions working"

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Permission test failed: {error_msg}")

            if "permission denied" in error_msg.lower():
                return False, f"Permission denied: {error_msg}"
            elif "relation does not exist" in error_msg.lower():
                return False, f"Table does not exist: {error_msg}"
            elif "rls" in error_msg.lower() or "policy" in error_msg.lower():
                return False, f"Row Level Security policy blocking access: {error_msg}"
            else:
                return False, f"Unknown error: {error_msg}"

    def save_category_table_data(self, system_name, category, info_string):
        """Save category-specific data to the system_category_info table"""
        if not supabase or not category or not info_string:
            print(
                f"[DEBUG] save_category_table_data early return: supabase={bool(supabase)}, category='{category}', info_string='{info_string[:50]}...'")
            return False

        print(
            f"[DEBUG] Attempting to save category data: system='{system_name}', category='{category}', info_length={len(info_string)}")

        # Try to save to system_category_info table directly (permissions are working)
        try:
            # Try to save to the new system_category_info table first
            print(f"[DEBUG] Checking for existing record in system_category_info...")
            existing = supabase.table("system_category_info").select("id").eq("system_name", system_name).eq("category",
                                                                                                             category).execute()
            print(f"[DEBUG] Existing records found: {len(existing.data) if existing.data else 0}")

            if existing.data:
                # Update existing record
                print(f"[DEBUG] Updating existing record...")
                result = supabase.table("system_category_info").update({"system_info": info_string}).eq("system_name",
                                                                                                        system_name).eq(
                    "category", category).execute()
                print(f"[SUCCESS] Updated system_category_info for {system_name} - {category}. Result: {result}")
            else:
                # Insert new record
                print(f"[DEBUG] Inserting new record...")
                insert_data = {
                    "system_name": system_name,
                    "category": category,
                    "system_info": info_string
                }
                print(f"[DEBUG] Insert data: {insert_data}")
                result = supabase.table("system_category_info").insert(insert_data).execute()
                print(f"[SUCCESS] Inserted new system_category_info for {system_name} - {category}. Result: {result}")

            # Verify the save worked
            verification = supabase.table("system_category_info").select("*").eq("system_name", system_name).eq(
                "category", category).execute()
            if verification.data:
                print(f"[VERIFY] ✓ Record confirmed in database: {verification.data[0]}")
                return True
            else:
                print(f"[ERROR] ✗ Record not found after save attempt!")
                return False

        except Exception as e:
            print(f"[ERROR] Exception saving to system_category_info: {e}")
            import traceback
            traceback.print_exc()
            # Continue to fallback method

        # Fallback: try the old category-specific table method
        print(f"[DEBUG] Attempting fallback to category table...")
        try:
            table_name = category.strip()
            response = supabase.table(table_name).select("*").limit(1).execute()
            if not response.data:
                print(f"[ERROR] No data in table {table_name}")
                return False
            available_columns = list(response.data[0].keys())
            data_dict = {}
            for line in info_string.split("\n"):
                if ": " in line:
                    key, value = line.split(": ", 1)
                    potential_keys = [
                        key.lower().replace(' ', '_'),
                        key.lower().replace(' ', ''),
                        key.replace(' ', '_'),
                        key.replace(' ', ''),
                        key.lower()
                    ]
                    for potential_key in potential_keys:
                        if potential_key in available_columns:
                            data_dict[potential_key] = value
                            break
            if not data_dict:
                print(f"[ERROR] No matching columns found for table {table_name}")
                return False
            system_col = None
            for col_name in ['system', 'System', 'SYSTEM', 'systems', 'Systems', 'SYSTEMS']:
                if col_name in available_columns:
                    system_col = col_name
                    break
            if not system_col:
                print(f"[ERROR] No system column found in table {table_name}")
                return False
            existing = supabase.table(table_name).select("id").eq(system_col, system_name).execute()
            if existing.data:
                supabase.table(table_name).update(data_dict).eq(system_col, system_name).execute()
            else:
                data_dict[system_col] = system_name
                supabase.table(table_name).insert(data_dict).execute()
            print(f"[SUCCESS] Saved to fallback table {table_name}")
            return True
        except Exception as e2:
            print(f"[ERROR] Fallback save failed: {e2}")
            return False

    def _safe_configure(self, widget, **kwargs):
        if hasattr(self, '_is_destroying') and self._is_destroying:
            return
        try:
            if widget.winfo_exists():
                widget.configure(**kwargs)
        except:
            pass

    def copy_to_clipboard(self, text):
        try:
            pyperclip.copy(text)
            notification = ctk.CTkToplevel(self)
            notification.overrideredirect(True)
            notification.configure(fg_color="#28a745")
            x = self.winfo_pointerx() + 10
            y = self.winfo_pointery() - 30
            notification.geometry(f"+{x}+{y}")
            ctk.CTkLabel(notification, text=f"Copied: {text}",
                         text_color="white",
                         fg_color="#28a745",
                         corner_radius=5).pack(padx=10, pady=5)
            notification.after(1500, notification.destroy)
        except Exception as e:
            print(f"Failed to copy to clipboard: {e}")

    def setup_main_tab(self, bold):
        main_container = ctk.CTkFrame(self.main_tab, fg_color=MAIN_BG_COLOR, corner_radius=0)
        main_container.pack(fill="both", expand=True)
        left_panel = ctk.CTkFrame(main_container, fg_color=MAIN_BG_COLOR, width=500)
        left_panel.pack(side="left", fill="y", padx=(20, 10), pady=20)
        left_panel.pack_propagate(False)
        info_card = ctk.CTkFrame(left_panel, fg_color=CARD_BG_COLOR,
                                 border_color=BORDER_COLOR, border_width=2, corner_radius=15)
        info_card.pack(fill="x", pady=(0, 20))
        cmdr_container = ctk.CTkFrame(info_card, fg_color="transparent")
        cmdr_container.pack(fill="x", padx=25, pady=(25, 15))
        title_frame = ctk.CTkFrame(cmdr_container, fg_color="transparent")
        title_frame.pack(anchor="w")
        ctk.CTkLabel(title_frame, text="⬢",
                     font=ctk.CTkFont(size=10), text_color=ACCENT_COLOR).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(title_frame, text="COMMANDER",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(side="left")
        self.cmdr_label = ctk.CTkLabel(cmdr_container, text=self.cmdr_name,
                                       font=ctk.CTkFont(size=24, weight="bold"),
                                       text_color=TEXT_COLOR)
        self.cmdr_label.pack(anchor="w", pady=(8, 0))
        separator = ctk.CTkFrame(info_card, height=2, fg_color=SECONDARY_BG_COLOR, corner_radius=1)
        separator.pack(fill="x", padx=25, pady=15)
        sys_container = ctk.CTkFrame(info_card, fg_color="transparent")
        sys_container.pack(fill="x", padx=25, pady=(15, 25))
        title_frame2 = ctk.CTkFrame(sys_container, fg_color="transparent")
        title_frame2.pack(anchor="w")
        ctk.CTkLabel(title_frame2, text="◈",
                     font=ctk.CTkFont(size=10), text_color=SUCCESS_COLOR).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(title_frame2, text="CURRENT SYSTEM",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(side="left")
        self.system_label = ctk.CTkLabel(sys_container, text=self.system_name,
                                         font=ctk.CTkFont(size=24, weight="bold"),
                                         text_color=TEXT_COLOR,
                                         cursor="hand2")
        self.system_label.pack(anchor="w", pady=(8, 0))
        self.system_label.bind("<Button-1>", lambda e: self.copy_to_clipboard(self.system_name))
        self.system_label.bind("<Enter>", lambda e: self.system_label.configure(text_color=ACCENT_COLOR))
        self.system_label.bind("<Leave>", lambda e: self.system_label.configure(text_color=TEXT_COLOR))
        actions_card = ctk.CTkFrame(left_panel, fg_color=CARD_BG_COLOR,
                                    border_color=BORDER_COLOR, border_width=2, corner_radius=15)
        actions_card.pack(fill="x", pady=(0, 20))
        header_frame = ctk.CTkFrame(actions_card, fg_color="transparent")
        header_frame.pack(anchor="w", padx=25, pady=(20, 15))
        ctk.CTkLabel(header_frame, text="▣",
                     font=ctk.CTkFont(size=12), text_color=INFO_COLOR).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(header_frame, text="QUICK ACTIONS",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_COLOR).pack(side="left")
        btn_frame = ctk.CTkFrame(actions_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="👁 View System",
                      command=self.view_current_system,
                      width=145, height=40,
                      fg_color=SECONDARY_BG_COLOR,
                      hover_color=TERTIARY_BG_COLOR,
                      border_color=BORDER_COLOR,
                      border_width=1,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=10).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="✦ Create POI",
                      command=self.current_system_settings,
                      width=145, height=40,
                      fg_color=SUCCESS_COLOR,
                      hover_color=SUCCESS_HOVER,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      text_color="#000000",
                      corner_radius=10).pack(side="left")
        unclaimed_card = ctk.CTkFrame(left_panel, fg_color=CARD_BG_COLOR,
                                      border_color=BORDER_COLOR, border_width=2, corner_radius=15)
        unclaimed_card.pack(fill="x", pady=(0, 20))
        header_frame2 = ctk.CTkFrame(unclaimed_card, fg_color="transparent")
        header_frame2.pack(anchor="w", padx=25, pady=(20, 15))
        ctk.CTkLabel(header_frame2, text="◎",
                     font=ctk.CTkFont(size=12), text_color=WARNING_COLOR).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(header_frame2, text="NEAREST UNCLAIMED",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_COLOR).pack(side="left")
        info_container = ctk.CTkFrame(unclaimed_card, fg_color=SECONDARY_BG_COLOR, corner_radius=10, height=100)
        info_container.pack(fill="x", padx=25, pady=(0, 15))
        info_container.pack_propagate(False)
        inner_container = ctk.CTkFrame(info_container, fg_color="transparent")
        inner_container.pack(fill="both", expand=True, padx=20, pady=15)

        # Top row with system name and distance
        top_row = ctk.CTkFrame(inner_container, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")

        self.closest_label = ctk.CTkLabel(top_row, text="None",
                                          font=ctk.CTkFont(size=18, weight="bold"),
                                          text_color=TEXT_COLOR)
        self.closest_label.pack(side="left", anchor="w")

        self.closest_distance_label = ctk.CTkLabel(top_row, text="",
                                                   font=ctk.CTkFont(size=14, weight="bold"),
                                                   text_color=ACCENT_COLOR)
        self.closest_distance_label.pack(side="right", anchor="e")

        self.closest_category_label = ctk.CTkLabel(inner_container, text="",
                                                   font=ctk.CTkFont(size=13),
                                                   text_color=TEXT_SECONDARY)
        self.closest_category_label.pack(anchor="w", pady=(6, 0))
        self.closest_poi_label = ctk.CTkLabel(inner_container, text="",
                                              font=ctk.CTkFont(size=12, weight="bold"),
                                              text_color=WARNING_COLOR)
        self.closest_poi_label.pack(anchor="w", pady=(4, 0))
        nav_frame = ctk.CTkFrame(unclaimed_card, fg_color="transparent")
        nav_frame.pack(fill="x", padx=25, pady=(0, 20))
        nav_controls = ctk.CTkFrame(nav_frame, fg_color="transparent")
        nav_controls.pack(side="left")
        self.btn_prev_unclaimed = ctk.CTkButton(nav_controls, text="◄", width=40, height=40,
                                                command=self.prev_unclaimed,
                                                fg_color=SECONDARY_BG_COLOR,
                                                hover_color=TERTIARY_BG_COLOR,
                                                border_color=BORDER_COLOR,
                                                border_width=1,
                                                font=ctk.CTkFont(size=14),
                                                corner_radius=8)
        self.btn_prev_unclaimed.pack(side="left", padx=(0, 8))
        self.unclaimed_position_label = ctk.CTkLabel(nav_controls, text="0/0",
                                                     font=ctk.CTkFont(size=13, weight="bold"),
                                                     text_color=TEXT_SECONDARY)
        self.unclaimed_position_label.pack(side="left", padx=10)
        self.btn_next_unclaimed = ctk.CTkButton(nav_controls, text="►", width=40, height=40,
                                                command=self.next_unclaimed,
                                                fg_color=SECONDARY_BG_COLOR,
                                                hover_color=TERTIARY_BG_COLOR,
                                                border_color=BORDER_COLOR,
                                                border_width=1,
                                                font=ctk.CTkFont(size=14),
                                                corner_radius=8)
        self.btn_next_unclaimed.pack(side="left", padx=(8, 0))
        action_buttons = ctk.CTkFrame(nav_frame, fg_color="transparent")
        action_buttons.pack(side="right")
        self.btn_view_closest = ctk.CTkButton(action_buttons, text="View",
                                              state="disabled", command=self.view_closest,
                                              width=90, height=42,
                                              fg_color=SECONDARY_BG_COLOR,
                                              hover_color=TERTIARY_BG_COLOR,
                                              border_color=BORDER_COLOR,
                                              border_width=1,
                                              font=ctk.CTkFont(size=14, weight="bold"),
                                              corner_radius=10)
        self.btn_view_closest.pack(side="left", padx=(0, 10))
        self.btn_claim_closest = ctk.CTkButton(action_buttons, text="Claim",
                                               state="disabled", command=self.claim_closest,
                                               width=90, height=42,
                                               fg_color=ACCENT_COLOR,
                                               hover_color=ACCENT_HOVER,
                                               font=ctk.CTkFont(size=14, weight="bold"),
                                               text_color="#FFFFFF",
                                               corner_radius=10)
        self.btn_claim_closest.pack(side="left")
        self.unclaimed_systems = []
        self.unclaimed_index = 0

        self.all_nearest_systems = []
        self.nearest_display_limit = 5
        right_panel = ctk.CTkFrame(main_container, fg_color=MAIN_BG_COLOR)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 20), pady=20)
        nearest_card = ctk.CTkFrame(right_panel, fg_color=CARD_BG_COLOR,
                                    border_color=BORDER_COLOR, border_width=2, corner_radius=15)
        nearest_card.pack(fill="both", expand=True)
        header_frame = ctk.CTkFrame(nearest_card, fg_color=SECONDARY_BG_COLOR,
                                    corner_radius=12, height=110)
        header_frame.pack(fill="x", padx=20, pady=20)
        header_frame.pack_propagate(False)
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.place(x=25, y=12)
        ctk.CTkLabel(title_container, text="◈",
                     font=ctk.CTkFont(size=14), text_color=ACCENT_COLOR).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(title_container, text="NEAREST SYSTEMS",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT_COLOR).pack(side="left")
        ctk.CTkLabel(header_frame, text="FILTERS",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_MUTED).place(x=25, y=48)
        self.category_dropdown = ctk.CTkComboBox(header_frame,
                                                 values=["All Categories"],
                                                 width=1, height=1)
        self.category_dropdown.place_forget()
        self.selected_categories_main = ["All Categories"]
        self.category_button_main = ctk.CTkButton(header_frame,
                                                  text="All Categories",
                                                  width=250,
                                                  height=32,
                                                  fg_color=TERTIARY_BG_COLOR,
                                                  hover_color="#363636",
                                                  text_color=TEXT_COLOR,
                                                  border_color=BORDER_COLOR,
                                                  border_width=1,
                                                  anchor="w",
                                                  font=ctk.CTkFont(size=12, weight="bold"),
                                                  corner_radius=8,
                                                  command=self.toggle_category_dropdown_main)
        self.category_button_main.place(x=25, y=70)
        self.category_dropdown_frame_main = ctk.CTkFrame(self.main_tab,
                                                         fg_color=CARD_BG_COLOR,
                                                         border_color=ACCENT_COLOR,
                                                         border_width=3,
                                                         corner_radius=15,
                                                         width=260,
                                                         height=380)
        self.category_checkboxes_main = []
        self._dropdown_visible_main = False
        self.nearest_filter = ctk.StringVar(value="All Systems")
        filter_dropdown = ctk.CTkComboBox(header_frame,
                                          values=["All Systems", "Unclaimed Only", "Your Claims", "Done Systems",
                                                  "POIs", "Potential POIs"],
                                          variable=self.nearest_filter,
                                          command=lambda x: self._on_filter_change(),
                                          width=160,
                                          height=32,
                                          state="readonly",
                                          fg_color=TERTIARY_BG_COLOR,
                                          border_color=BORDER_COLOR,
                                          button_color=ACCENT_COLOR,
                                          button_hover_color=ACCENT_HOVER,
                                          dropdown_fg_color=SECONDARY_BG_COLOR,
                                          dropdown_hover_color=TERTIARY_BG_COLOR,
                                          text_color=TEXT_COLOR,
                                          dropdown_text_color=TEXT_COLOR,
                                          font=ctk.CTkFont(size=12, weight="bold"),
                                          dropdown_font=ctk.CTkFont(size=12),
                                          corner_radius=8)
        filter_dropdown.place(x=285, y=70)
        self.load_categories()
        self.nearest_scroll = ctk.CTkScrollableFrame(nearest_card,
                                                     fg_color="#1a1a1a",
                                                     corner_radius=10,
                                                     scrollbar_button_color="#444444",
                                                     scrollbar_button_hover_color="#666666")
        self.nearest_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # FIX MOUSE WHEEL SCROLLING - This is the proper way to do it
        def _on_mousewheel(event):
            try:
                # Scroll with proper speed (3 units per wheel notch)
                self.nearest_scroll._parent_canvas.yview_scroll(int(-3 * (event.delta / 120)), "units")
            except:
                pass
            return "break"  # Prevent event propagation

        # Bind to ALL relevant widgets for comprehensive scrolling
        self.nearest_scroll.bind("<MouseWheel>", _on_mousewheel)
        self.nearest_scroll._parent_canvas.bind("<MouseWheel>", _on_mousewheel)

        # Also bind to the main window and nearby card for better coverage
        nearest_card.bind("<MouseWheel>", _on_mousewheel)

        # Store the scroll function for later rebinding if needed
        self._main_scroll_handler = _on_mousewheel

        # Rebind on focus to ensure scrolling always works
        def ensure_scroll_works(event=None):
            try:
                self.nearest_scroll.bind("<MouseWheel>", _on_mousewheel)
                self.nearest_scroll._parent_canvas.bind("<MouseWheel>", _on_mousewheel)
                nearest_card.bind("<MouseWheel>", _on_mousewheel)
            except:
                pass

        self.bind("<FocusIn>", ensure_scroll_works)
        self.bind("<Map>", ensure_scroll_works)

        # Also ensure scrolling works after a short delay (for startup)
        self.after(500, ensure_scroll_works)

        # Store original scroll binding
        self._original_scroll_bind = None
        if self.is_admin:
            admin_container = ctk.CTkFrame(main_container, fg_color=DANGER_COLOR, corner_radius=8)
            admin_container.place(relx=0.98, rely=0.02, anchor="ne")
            self.admin_label = ctk.CTkLabel(admin_container,
                                            text="⚡ ADMIN MODE",
                                            font=ctk.CTkFont(size=12, weight="bold"),
                                            text_color="#FFFFFF",
                                            fg_color=DANGER_COLOR)
            self.admin_label.pack(padx=12, pady=6)
            self.btn_admin_panel = ctk.CTkButton(main_container, text="🛡 Admin Panel",
                                                 command=self.show_admin_panel,
                                                 width=110, height=35,
                                                 fg_color=DANGER_COLOR,
                                                 hover_color=DANGER_HOVER,
                                                 font=ctk.CTkFont(size=12, weight="bold"),
                                                 corner_radius=8)
            self.btn_admin_panel.place(relx=0.84, rely=0.02, anchor="ne")
        refresh_x = 0.72 if self.is_admin else 0.86
        self.btn_refresh = ctk.CTkButton(main_container, text="↻ Refresh",
                                         command=self.refresh_all_data,
                                         width=100, height=35,
                                         fg_color=SECONDARY_BG_COLOR,
                                         hover_color=TERTIARY_BG_COLOR,
                                         border_width=1,
                                         border_color=BORDER_COLOR,
                                         text_color=TEXT_COLOR,
                                         font=ctk.CTkFont(size=12, weight="bold"),
                                         corner_radius=8)
        self.btn_refresh.place(relx=refresh_x, rely=0.02, anchor="ne")
        self.update_nearest_systems()

    def setup_bottom_selector(self):
        """Set up bottom category selector for multi-category systems"""
        # Initialize category selector state
        self.current_category_selection = None  # Currently selected category
        self.system_categories = []  # Available categories for current system
        self.current_system_popup = None  # Reference to current system popup

        # Note: Category selector is now created inside popup windows, not as a bottom selector

    def hide_category_selector(self):
        """Hide/cleanup category selector (legacy method for compatibility)"""
        self.system_categories = []
        self.current_category_selection = None
        self.current_system_popup = None

    def setup_compact_category_selector(self, info_frame, popup, system_name, categories):
        """Set up compact category selector inside System Info content"""
        if len(categories) > 1:
            self.system_categories = categories
            self.current_category_selection = categories[0]  # Default to first category
            self.current_system_popup = popup

            # Create compact category selector frame
            category_selector_frame = ctk.CTkFrame(info_frame,
                                                   fg_color=SECONDARY_BG_COLOR,
                                                   corner_radius=8,
                                                   border_width=1,
                                                   border_color=BORDER_COLOR,
                                                   height=40)
            category_selector_frame.pack(fill="x", pady=(0, 20), padx=0)
            category_selector_frame.pack_propagate(False)

            # Add compact title
            title_label = ctk.CTkLabel(category_selector_frame,
                                       text="Category:",
                                       font=ctk.CTkFont(size=11, weight="bold"),
                                       text_color=TEXT_COLOR)
            title_label.pack(side="left", padx=(10, 8), pady=10)

            # Create compact segmented button for category selection
            popup.category_selector = ctk.CTkSegmentedButton(category_selector_frame,
                                                             values=categories,
                                                             command=self.on_compact_category_selection_change,
                                                             fg_color=TERTIARY_BG_COLOR,
                                                             selected_color=ACCENT_COLOR,
                                                             selected_hover_color=ACCENT_HOVER,
                                                             unselected_color=CARD_BG_COLOR,
                                                             unselected_hover_color="#363636",
                                                             text_color=TEXT_COLOR,
                                                             font=ctk.CTkFont(size=10, weight="bold"),
                                                             corner_radius=6,
                                                             border_width=1,
                                                             height=30)
            popup.category_selector.pack(side="right", padx=(0, 10), pady=5, fill="x", expand=True)
            popup.category_selector.set(self.current_category_selection or categories[0])

            # Store reference to the selector frame
            popup.category_selector_frame = category_selector_frame

            # Load initial system info for the first category
            initial_category = self.current_category_selection or categories[0]
            self.current_category_selection = initial_category

            # Trigger initial system info load after popup is fully built
            popup.after(100, lambda: self.update_system_info_section(system_name, initial_category))

    # Removed old broken scroll handlers - using new proper scroll implementation

    def refresh_all_category_displays(self, system_name):
        """Refresh all UI elements that display categories after new categories are added"""
        print(f"[DEBUG] Refreshing all category displays for {system_name}")

        try:
            # 1. Refresh the nearest systems display to show updated categories
            print(f"[DEBUG] Refreshing nearest systems display...")
            self.update_nearest_systems()

            # 2. Refresh the compact category selector if open
            if hasattr(self, 'current_system_popup') and self.current_system_popup:
                print(f"[DEBUG] Refreshing compact category selector...")
                self.refresh_compact_category_selector(system_name)

            # 3. Update the unclaimed systems display which also shows categories
            print(f"[DEBUG] Refreshing unclaimed systems display...")
            self.find_nearest_unclaimed()

            # 4. If map window is open, refresh it too
            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                print(f"[DEBUG] Refreshing map window filters...")
                try:
                    # Force map to re-query categories by refreshing its filters
                    if hasattr(self.map_window, 'toggle_unvisited'):
                        self.map_window.toggle_unvisited()
                        self.map_window.toggle_unvisited()  # Toggle twice to refresh
                except Exception as map_e:
                    print(f"[DEBUG] Error refreshing map: {map_e}")

            print(f"[DEBUG] All category displays refreshed successfully")

        except Exception as e:
            print(f"[ERROR] Error refreshing category displays: {e}")

    def refresh_compact_category_selector(self, system_name):
        """Refresh the compact category selector with latest categories from database"""
        if not self.current_system_popup or not hasattr(self.current_system_popup, 'category_selector'):
            return

        try:
            # Get fresh category data from database (including system_category_info)
            fresh_systems_check = supabase.table("systems").select("*").eq("systems", system_name).execute()
            if fresh_systems_check.data:
                fresh_combined_data = combine_system_entries(fresh_systems_check.data, system_name)
                if fresh_combined_data and fresh_combined_data.get("_individual_categories"):
                    fresh_categories = fresh_combined_data["_individual_categories"]

                    print(
                        f"[DEBUG] Refreshing category selector with {len(fresh_categories)} categories: {fresh_categories}")

                    if len(fresh_categories) > 1:
                        # Update the selector with new categories
                        self.system_categories = fresh_categories
                        self.current_system_popup.category_selector.configure(values=fresh_categories)

                        # Update the header to show the new category count
                        if hasattr(self.current_system_popup, 'category_display_label'):
                            current_cat = self.current_category_selection or fresh_categories[0]
                            self.current_system_popup.category_display_label.configure(text=current_cat)

                    # Also refresh the nearest systems display to show updated categories
                    self.after(500, self.update_nearest_systems)

        except Exception as e:
            print(f"Error refreshing compact category selector: {e}")

    def on_compact_category_selection_change(self, value):
        """Handle category selection change in compact selector"""
        self.current_category_selection = value

        # Update just the system info section, not the entire popup
        if self.current_system_popup and hasattr(self.current_system_popup, '_system_name'):
            system_name = self.current_system_popup._system_name
            self.update_system_info_section(system_name, value)

    def update_system_info_section(self, system_name, category):
        """Update just the system info data section without rebuilding entire popup"""
        if not self.current_system_popup or not hasattr(self.current_system_popup, 'system_info_frame'):
            return

        try:
            # Update category display label if it exists
            if hasattr(self.current_system_popup, 'category_display_label'):
                self.current_system_popup.category_display_label.configure(text=category)

            # Get category-specific table data
            category_table_info = self.get_category_table_data(system_name, category)

            # Find and update the system info display
            info_frame = self.current_system_popup.system_info_frame

            # Clear existing system info content
            for widget in info_frame.winfo_children():
                widget.destroy()

            if category_table_info:
                # Create new system info content with same styling as original
                reg_font = ctk.CTkFont(family="Dosis", size=14) if "Dosis" in tkFont.families() else ctk.CTkFont(
                    size=14)

                # Add system info lines
                for line in category_table_info.split('\n'):
                    if line.strip():
                        info_label = ctk.CTkLabel(info_frame,
                                                  text=line.strip(),
                                                  font=reg_font,
                                                  text_color=TEXT_COLOR,
                                                  anchor="w")
                        info_label.pack(anchor="w", pady=1)
            else:
                # Show "no info available" message
                no_info_label = ctk.CTkLabel(info_frame,
                                             text=f"No information available for: {category}",
                                             font=ctk.CTkFont(size=12),
                                             text_color=TEXT_MUTED)
                no_info_label.pack(anchor="w", pady=5)

        except Exception as e:
            print(f"Error updating system info section: {e}")

    def setup_galaxy_tab(self):
        main_container = ctk.CTkFrame(self.galaxy_tab, fg_color=MAIN_BG_COLOR)
        main_container.pack(fill="both", expand=True)
        content_frame = ctk.CTkFrame(main_container, fg_color=MAIN_BG_COLOR)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        top_section = ctk.CTkFrame(content_frame, fg_color="transparent", height=400)
        top_section.pack(fill="x", pady=(0, 20))
        top_section.pack_propagate(False)
        left_panel = ctk.CTkFrame(top_section, fg_color=CARD_BG_COLOR,
                                  corner_radius=20, border_width=0, width=550)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        header_frame = ctk.CTkFrame(left_panel, fg_color=SECONDARY_BG_COLOR,
                                    corner_radius=15, height=80)
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        header_frame.pack_propagate(False)
        title_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_content.place(relx=0.5, rely=0.5, anchor="center")
        title_label = ctk.CTkLabel(title_content, text="Statistics",
                                   font=ctk.CTkFont(size=28, weight="bold"),
                                   text_color=ACCENT_COLOR)
        title_label.pack()
        stats_container = ctk.CTkFrame(left_panel, fg_color="transparent")
        stats_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        stats_grid = ctk.CTkFrame(stats_container, fg_color="transparent")
        stats_grid.pack(fill="both", expand=True)
        self.galaxy_stat_labels = {}
        row1 = ctk.CTkFrame(stats_grid, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 15))
        cmdr_card = self._create_stat_card(row1, "COMMANDER",
                                           self.cmdr_name if self.cmdr_name != "Unknown" else "Not Logged In",
                                           "", ACCENT_COLOR, side="left", expand=True)
        self.galaxy_stat_labels['commander'] = cmdr_card
        system_card = self._create_stat_card(row1, "CURRENT SYSTEM",
                                             self.system_name if self.system_name != "Unknown" else "Not Detected",
                                             "", SUCCESS_COLOR, side="right", expand=True)
        self.galaxy_stat_labels['system'] = system_card
        row2 = ctk.CTkFrame(stats_grid, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 15))
        session_time = self._calculate_session_time()
        time_card = self._create_stat_card(row2, "APP UPTIME", session_time,
                                           "", INFO_COLOR, side="left", expand=True)
        self.galaxy_stat_labels['session_time'] = time_card
        jump_count = getattr(self, 'jump_count', 0)
        jump_card = self._create_stat_card(row2, "JUMPS THIS SESSION", str(jump_count),
                                           "", WARNING_COLOR, side="right", expand=True)
        self.galaxy_stat_labels['jumps'] = jump_card
        row3 = ctk.CTkFrame(stats_grid, fg_color="transparent")
        row3.pack(fill="x")
        map_status = "Active" if self.map_window and hasattr(self.map_window,
                                                             'winfo_exists') and self.map_window.winfo_exists() else "Inactive"
        map_card = self._create_stat_card(row3, "MAP STATUS", map_status,
                                          "🗺", "#4CAF50" if "Active" in map_status else "#F44336", side="left",
                                          expand=True)
        self.galaxy_stat_labels['map_status'] = map_card
        claims_count = self._get_claims_count()
        claims_card = self._create_stat_card(row3, "YOUR CLAIMS", str(claims_count),
                                             "🏁", "#9C27B0", side="right", expand=True)
        self.galaxy_stat_labels['claims'] = claims_card
        right_panel = ctk.CTkFrame(top_section, fg_color="transparent", width=400)
        right_panel.pack(side="right", fill="both", padx=(10, 0))
        right_panel.pack_propagate(False)
        map_outer = ctk.CTkFrame(right_panel, fg_color=ACCENT_COLOR,
                                 corner_radius=25, border_width=0)
        map_outer.pack(fill="both", expand=True)
        map_container = ctk.CTkFrame(map_outer, fg_color=CARD_BG_COLOR, corner_radius=22)
        map_container.pack(fill="both", expand=True, padx=3, pady=3)
        preview_frame = ctk.CTkFrame(map_container, fg_color="#0a0a0a", corner_radius=20)
        preview_frame.pack(fill="both", expand=True, padx=20, pady=20)
        try:
            img = Image.open(resource("E47CDFX.png")).resize((340, 280), Resampling.LANCZOS)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.6)
            btn_img = CTkImage(dark_image=img, size=(340, 280))
            self.galaxy_launch_btn = ctk.CTkButton(preview_frame, image=btn_img, text="",
                                                   command=self.open_map,
                                                   fg_color="transparent",
                                                   hover_color="transparent",
                                                   cursor="hand2")
            self.galaxy_launch_btn.pack(fill="both", expand=True)
            overlay_frame = ctk.CTkFrame(preview_frame, fg_color="transparent", bg_color="transparent")
            overlay_frame.place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(overlay_frame, text="Open",
                         font=ctk.CTkFont(size=24, weight="bold"),
                         text_color="#FFFFFF").pack()
            ctk.CTkLabel(overlay_frame, text="Galaxy Map",
                         font=ctk.CTkFont(size=20),
                         text_color=TEXT_SECONDARY).pack()
            self.map_status_indicator = ctk.CTkLabel(overlay_frame, text="Click to open",
                                                     font=ctk.CTkFont(size=12),
                                                     text_color="#888888")
            self.map_status_indicator.pack(pady=(10, 0))
        except:
            self.galaxy_launch_btn = ctk.CTkButton(preview_frame, text="Open Galaxy Map",
                                                   command=self.open_map,
                                                   font=ctk.CTkFont(size=20, weight="bold"),
                                                   fg_color=SECONDARY_BG_COLOR,
                                                   hover_color=TERTIARY_BG_COLOR,
                                                   border_color=BORDER_COLOR,
                                                   border_width=1,
                                                   height=280)
            self.galaxy_launch_btn.pack(fill="both", expand=True, padx=20, pady=20)

        def on_enter_map(e):
            map_outer.configure(fg_color=ACCENT_HOVER)
            if hasattr(self, 'map_status_indicator'):
                self.map_status_indicator.configure(text_color="#FFFF00")

        def on_leave_map(e):
            map_outer.configure(fg_color=ACCENT_COLOR)
            if hasattr(self, 'map_status_indicator'):
                self.map_status_indicator.configure(text_color="#4CAF50")

        self.galaxy_launch_btn.bind("<Enter>", on_enter_map)
        self.galaxy_launch_btn.bind("<Leave>", on_leave_map)
        bottom_section = ctk.CTkFrame(content_frame, fg_color=SECONDARY_BG_COLOR,
                                      corner_radius=20, height=180)
        bottom_section.pack(fill="x", side="bottom")
        bottom_section.pack_propagate(False)
        actions_header = ctk.CTkFrame(bottom_section, fg_color="transparent")
        actions_header.pack(fill="x", padx=30, pady=(20, 15))
        ctk.CTkLabel(actions_header, text="QUICK ACTIONS",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TEXT_COLOR).pack(side="left")
        actions_grid = ctk.CTkFrame(bottom_section, fg_color="transparent")
        actions_grid.pack(fill="x", padx=30, pady=(0, 20))
        actions = [
            ("Find Nearest", lambda: self.galaxy_quick_find(), INFO_COLOR),
            ("View Current", lambda: self.view_current_system() if self.system_name != "Unknown" else None,
             SUCCESS_COLOR),
            ("Random Jump", lambda: self.suggest_random_system(), WARNING_COLOR),
            ("Statistics", lambda: self.show_detailed_stats(), "#9C27B0"),
        ]
        for i, (text, command, color) in enumerate(actions):
            btn = ctk.CTkButton(actions_grid, text=text, command=command,
                                fg_color=color, hover_color=color,
                                font=ctk.CTkFont(size=14, weight="bold"),
                                corner_radius=10, height=40, width=140)
            btn.grid(row=0, column=i, padx=5, sticky="ew")
            original_color = color
            lighter_color = self._lighten_color(color)
            btn.bind("<Enter>", lambda e, b=btn, c=lighter_color: b.configure(fg_color=c))
            btn.bind("<Leave>", lambda e, b=btn, c=original_color: b.configure(fg_color=c))
        actions_grid.columnconfigure((0, 1, 2, 3), weight=1)
        self._start_galaxy_stats_update()
        if not hasattr(self, 'session_start_time'):
            self.session_start_time = time.time()
        if not hasattr(self, 'jump_count'):
            self.jump_count = 0

    def _create_stat_card(self, parent, title, value, icon, color, side="left", expand=False):
        card = ctk.CTkFrame(parent, fg_color=SECONDARY_BG_COLOR, corner_radius=12, height=80)
        if side == "left":
            card.pack(side="left", fill="both" if expand else "x", expand=expand, padx=(0, 8))
        else:
            card.pack(side="right", fill="both" if expand else "x", expand=expand, padx=(8, 0))
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")
        title_row = ctk.CTkFrame(content, fg_color="transparent")
        title_row.pack()
        ctk.CTkLabel(title_row, text=icon, font=ctk.CTkFont(size=16),
                     text_color=color).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(title_row, text=title, font=ctk.CTkFont(size=12),
                     text_color=TEXT_MUTED).pack(side="left")
        value_label = ctk.CTkLabel(content, text=value,
                                   font=ctk.CTkFont(size=20, weight="bold"),
                                   text_color=TEXT_COLOR)
        value_label.pack(pady=(5, 0))
        return value_label

    def _calculate_session_time(self):
        if hasattr(self, 'session_start_time'):
            elapsed = time.time() - self.session_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"

    def _get_claims_count(self):
        if supabase and self.cmdr_name != "Unknown":
            try:
                result = supabase.table("taken").select("system", count="exact").eq("by_cmdr", self.cmdr_name).execute()
                return result.count if hasattr(result, 'count') else 0
            except:
                pass
        return 0

    def _lighten_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        r = min(255, int(r * 1.2))
        g = min(255, int(g * 1.2))
        b = min(255, int(b * 1.2))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _start_galaxy_stats_update(self):
        def update_stats():
            if hasattr(self, '_is_destroying') and self._is_destroying:
                return
            try:
                if 'session_time' in self.galaxy_stat_labels:
                    try:
                        self.galaxy_stat_labels['session_time'].configure(text=self._calculate_session_time())
                    except:
                        pass
                if 'commander' in self.galaxy_stat_labels:
                    try:
                        cmdr_text = self.cmdr_name if self.cmdr_name != "Unknown" else "Not Logged In"
                        self.galaxy_stat_labels['commander'].configure(text=cmdr_text)
                    except:
                        pass
                if 'system' in self.galaxy_stat_labels:
                    try:
                        sys_text = self.system_name if self.system_name != "Unknown" else "Not Detected"
                        self.galaxy_stat_labels['system'].configure(text=sys_text)
                    except:
                        pass
                if 'jumps' in self.galaxy_stat_labels:
                    try:
                        self.galaxy_stat_labels['jumps'].configure(text=str(getattr(self, 'jump_count', 0)))
                    except:
                        pass
                if 'map_status' in self.galaxy_stat_labels:
                    try:
                        map_active = self.map_window and hasattr(self.map_window,
                                                                 'winfo_exists') and self.map_window.winfo_exists()
                        status_text = "Active" if map_active else "Inactive"
                        self.galaxy_stat_labels['map_status'].configure(text=status_text)
                    except:
                        pass
                    if hasattr(self, 'map_status_indicator'):
                        try:
                            indicator_text = "● OPEN" if map_active else "● READY"
                            indicator_color = "#00FF00" if map_active else "#4CAF50"
                            self.map_status_indicator.configure(text=indicator_text, text_color=indicator_color)
                        except:
                            pass
                if 'claims' in self.galaxy_stat_labels:
                    try:
                        self.galaxy_stat_labels['claims'].configure(text=str(self._get_claims_count()))
                    except:
                        pass
            except Exception as e:
                print(f"Error updating galaxy stats: {e}")
            if not (hasattr(self, '_is_destroying') and self._is_destroying):
                self.after(1000, update_stats)

        update_stats()

    def galaxy_quick_find(self):
        if self.unclaimed_systems:
            popup = ctk.CTkToplevel(self)
            popup.title("Nearest Unclaimed")
            popup.geometry("400x250")
            popup.transient(self)
            popup.grab_set()
            popup.configure(fg_color=MAIN_BG_COLOR)
            popup.update_idletasks()
            x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
            y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
            popup.geometry(f"+{x}+{y}")
            content = ctk.CTkFrame(popup, fg_color=CARD_BG_COLOR, corner_radius=15)
            content.pack(fill="both", expand=True, padx=20, pady=20)
            nearest = self.unclaimed_systems[0]
            ctk.CTkLabel(content, text="Nearest Unclaimed System",
                         font=ctk.CTkFont(size=18, weight="bold"),
                         text_color=ACCENT_COLOR).pack(pady=(20, 10))
            ctk.CTkLabel(content, text=nearest['systems'],
                         font=ctk.CTkFont(size=24, weight="bold"),
                         text_color=TEXT_COLOR).pack()
            ctk.CTkLabel(content, text=nearest.get('category', 'Unknown'),
                         font=ctk.CTkFont(size=14),
                         text_color=TEXT_SECONDARY).pack(pady=(5, 0))
            ctk.CTkLabel(content, text=f"{nearest['distance']:.2f} LY away",
                         font=ctk.CTkFont(size=16),
                         text_color=SUCCESS_COLOR).pack(pady=(10, 20))
            btn_frame = ctk.CTkFrame(content, fg_color="transparent")
            btn_frame.pack()
            ctk.CTkButton(btn_frame, text="View Details",
                          command=lambda: (popup.destroy(),
                                           self.view_system(nearest['systems'], nearest.get('category'))),
                          fg_color=INFO_COLOR, width=120).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Close",
                          command=popup.destroy,
                          fg_color=SECONDARY_BG_COLOR, width=120).pack(side="left", padx=5)
        else:
            messagebox.showinfo("No Systems", "No unclaimed systems found in your filter!")

    def suggest_random_system(self):
        if not supabase:
            return
        try:
            systems = supabase.table("systems").select("systems,category,x,y,z").limit(1000).execute().data or []
            if systems and self.current_coords:
                cx, cy, cz = self.current_coords
                nearby = []
                for sys in systems:
                    dx = sys["x"] - cx
                    dy = sys["y"] - cy
                    dz = sys["z"] - cz
                    dist = (dx * dx + dy * dy + dz * dz) ** 0.5
                    if 50 < dist < 1000:
                        nearby.append((sys, dist))
                if nearby:
                    import random
                    chosen, distance = random.choice(nearby)
                    popup = ctk.CTkToplevel(self)
                    popup.title("Random Destination")
                    popup.geometry("400x250")
                    popup.transient(self)
                    popup.grab_set()
                    popup.configure(fg_color=MAIN_BG_COLOR)
                    popup.update_idletasks()
                    x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
                    y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
                    popup.geometry(f"+{x}+{y}")
                    content = ctk.CTkFrame(popup, fg_color=CARD_BG_COLOR, corner_radius=15)
                    content.pack(fill="both", expand=True, padx=20, pady=20)
                    ctk.CTkLabel(content, text="Alternative Destination",
                                 font=ctk.CTkFont(size=18, weight="bold"),
                                 text_color=WARNING_COLOR).pack(pady=(20, 10))
                    ctk.CTkLabel(content, text=chosen['systems'],
                                 font=ctk.CTkFont(size=24, weight="bold"),
                                 text_color=TEXT_COLOR).pack()
                    ctk.CTkLabel(content, text=chosen.get('category', 'Unknown'),
                                 font=ctk.CTkFont(size=14),
                                 text_color=TEXT_SECONDARY).pack(pady=(5, 0))
                    ctk.CTkLabel(content, text=f"{distance:.2f} LY away",
                                 font=ctk.CTkFont(size=16),
                                 text_color=INFO_COLOR).pack(pady=(10, 20))
                    btn_frame = ctk.CTkFrame(content, fg_color="transparent")
                    btn_frame.pack()
                    ctk.CTkButton(btn_frame, text="View System",
                                  command=lambda: (popup.destroy(),
                                                   self.view_system(chosen['systems'], chosen.get('category'))),
                                  fg_color=WARNING_COLOR, width=120).pack(side="left", padx=5)
                    ctk.CTkButton(btn_frame, text="Try Another",
                                  command=lambda: (popup.destroy(), self.suggest_random_system()),
                                  fg_color=SECONDARY_BG_COLOR, width=120).pack(side="left", padx=5)
        except:
            pass

    def show_detailed_stats(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Detailed Statistics")
        popup.geometry("600x500")
        popup.transient(self)
        popup.grab_set()
        popup.configure(fg_color=MAIN_BG_COLOR)
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        header = ctk.CTkFrame(scroll, fg_color=CARD_BG_COLOR, corner_radius=15)
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="EXPLORATION STATISTICS",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=ACCENT_COLOR).pack(pady=20)
        stats_sections = []
        if supabase:
            try:
                your_claims = supabase.table("taken").select("*", count="exact").eq("by_cmdr", self.cmdr_name).execute()
                your_visited = supabase.table("taken").select("*", count="exact").eq("by_cmdr", self.cmdr_name).eq(
                    "visited", True).execute()
                your_done = supabase.table("taken").select("*", count="exact").eq("by_cmdr", self.cmdr_name).eq("done",
                                                                                                                True).execute()
                stats_sections.append(("Your Activity", [
                    ("Total Claims", str(your_claims.count if hasattr(your_claims, 'count') else 0)),
                    ("Visited", str(your_visited.count if hasattr(your_visited, 'count') else 0)),
                    ("Completed", str(your_done.count if hasattr(your_done, 'count') else 0))
                ]))
                total_systems = supabase.table("systems").select("*", count="exact").execute()
                total_claimed = supabase.table("taken").select("*", count="exact").execute()
                total_pois = supabase.table("pois").select("*", count="exact").execute()
                stats_sections.append(("Global Statistics", [
                    ("Total Systems", str(total_systems.count if hasattr(total_systems, 'count') else 0)),
                    ("Systems Claimed", str(total_claimed.count if hasattr(total_claimed, 'count') else 0)),
                    ("POIs Marked", str(total_pois.count if hasattr(total_pois, 'count') else 0))
                ]))
            except:
                pass
        session_time = self._calculate_session_time()
        stats_sections.append(("Current Session", [
            ("Session Time", session_time),
            ("Jumps Made", str(getattr(self, 'jump_count', 0))),
            ("Current System", self.system_name if self.system_name != "Unknown" else "Not detected")
        ]))
        for section_title, stats in stats_sections:
            section_frame = ctk.CTkFrame(scroll, fg_color=SECONDARY_BG_COLOR, corner_radius=12)
            section_frame.pack(fill="x", pady=(0, 15))
            ctk.CTkLabel(section_frame, text=section_title,
                         font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=TEXT_COLOR).pack(pady=(15, 10))
            for stat_name, stat_value in stats:
                stat_row = ctk.CTkFrame(section_frame, fg_color="transparent")
                stat_row.pack(fill="x", padx=20, pady=5)
                ctk.CTkLabel(stat_row, text=stat_name,
                             font=ctk.CTkFont(size=14),
                             text_color=TEXT_MUTED).pack(side="left")
                ctk.CTkLabel(stat_row, text=stat_value,
                             font=ctk.CTkFont(size=14, weight="bold"),
                             text_color=ACCENT_COLOR).pack(side="right")
        ctk.CTkButton(scroll, text="Close", command=popup.destroy,
                      fg_color=SECONDARY_BG_COLOR, hover_color=TERTIARY_BG_COLOR,
                      width=200, height=40).pack(pady=20)

    def setup_info_tab(self):
        info_container = ctk.CTkFrame(self.info_tab, fg_color=MAIN_BG_COLOR)
        info_container.pack(fill="both", expand=True)
        info_frame = ctk.CTkScrollableFrame(info_container, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(info_frame, text="Elite Dangerous Records Helper",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=ACCENT_COLOR).pack(pady=(0, 20))
        sections = [
            ("About",
             "EDRH is a tool designed to help Elite Dangerous commanders track and manage system discoveries in specific regions of the galaxy."),
            ("Features",
             "• Real-time system tracking\n• POI management\n• Commander location sharing\n• System claiming\n• Interactive galaxy map\n• Nearest systems finder"),
            ("How to Use",
             "1. Select your Elite Dangerous journal folder\n2. The tool will automatically track your location\n3. Use the galaxy map to explore regions\n4. Claim systems you've discovered\n5. Mark systems as POIs"),
            ("Admin Features",
             "Admins have access to additional features:\n• View all commander locations\n• Manage system database\n• Access advanced filters"),
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
        tutorial_container = ctk.CTkFrame(self.tutorial_tab, fg_color=MAIN_BG_COLOR)
        tutorial_container.pack(fill="both", expand=True)
        tutorial_frame = ctk.CTkScrollableFrame(tutorial_container, fg_color="transparent")
        tutorial_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(tutorial_frame, text="Getting Started Tutorial",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=ACCENT_COLOR).pack(pady=(0, 20))
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

    def _on_filter_change(self):
        """Handle filter dropdown change"""
        self.nearest_display_limit = 5

        if hasattr(self, 'nearest_scroll') and hasattr(self.nearest_scroll, '_parent_canvas'):
            self.nearest_scroll._parent_canvas.yview_moveto(0)

        self.update_nearest_systems()

    def view_current_system(self):
        if self.current_coords and self.system_name != "Unknown":
            self.view_system(self.system_name, None)
        else:
            messagebox.showwarning("No System", "No system currently detected!")

    def current_system_settings(self):
        if not self.system_name or self.system_name == "Unknown":
            messagebox.showwarning("No System", "No system currently detected!")
            return
        if not supabase:
            messagebox.showerror("Error", "Database not available!")
            return
        existing = supabase.table("pois").select("*").eq("system_name", self.system_name).execute()
        if existing.data:
            messagebox.showinfo("Already Exists", f"{self.system_name} is already marked as a POI!")
            return
        try:
            poi_data = {
                "system_name": self.system_name,
                "name": self.system_name,
                "potential_or_poi": "Potential POI",
                "submitter": self.cmdr_name,
                "discoverer": self.cmdr_name
            }
            coords_added = False
            if self.current_coords:
                poi_data["coords_x"] = self.current_coords[0]
                poi_data["coords_y"] = self.current_coords[1]
                poi_data["coords_z"] = self.current_coords[2]
                coords_added = True
                print(f"Using journal coordinates for {self.system_name}: {self.current_coords}")
            if not coords_added:
                sys_check = supabase.table("systems").select("x,y,z").eq("systems", self.system_name).execute()
                if sys_check.data:
                    poi_data["coords_x"] = sys_check.data[0].get("x", 0)
                    poi_data["coords_y"] = sys_check.data[0].get("y", 0)
                    poi_data["coords_z"] = sys_check.data[0].get("z", 0)
                    coords_added = True
                    print(f"Using systems table coordinates for {self.system_name}")
            if not coords_added or (
                    poi_data.get("coords_x") == 0 and poi_data.get("coords_y") == 0 and poi_data.get("coords_z") == 0):
                messagebox.showwarning("No Coordinates",
                                       f"Cannot create POI for {self.system_name} - no valid coordinates found!")
                return
            supabase.table("pois").insert(poi_data).execute()
            messagebox.showinfo("Success", f"{self.system_name} added as Potential POI with coordinates!")
            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                self.map_window.toggle_potential_pois()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add POI: {e}")

    def update_nearest_systems(self):
        try:
            if hasattr(self, '_is_destroying') and self._is_destroying:
                return
            if not self.winfo_exists():
                return
        except:
            return
        if not supabase or not self.current_coords:
            return
        current_time = time.time()
        if current_time - self.last_update_time < self.update_cooldown:
            return
        self.last_update_time = current_time

        try:
            if not hasattr(self, 'nearest_scroll') or not self.nearest_scroll.winfo_exists():
                return
        except:
            return

        for widget in self.nearest_scroll.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        loading_label = ctk.CTkLabel(self.nearest_scroll, text="Loading systems...",
                                     font=ctk.CTkFont(size=14), text_color=TEXT_SECONDARY)
        loading_label.pack(pady=50)

        def load_systems():
            try:
                # Ensure current coordinates are floats
                cx, cy, cz = self.current_coords
                cx, cy, cz = float(cx), float(cy), float(cz)
                # Get systems from main systems table
                all_systems = supabase.table("systems").select("systems,category,x,y,z").execute().data or []

                # Bulk query system_category_info data for performance
                print(f"[DEBUG] Bulk querying system_category_info for {len(all_systems)} systems...")
                try:
                    # Get all category info data in one query
                    all_category_info = supabase.table("system_category_info").select(
                        "system_name,category").execute().data or []
                    category_info_by_system = {}
                    for cat_info in all_category_info:
                        system_name = cat_info["system_name"]
                        category = cat_info["category"]
                        if system_name not in category_info_by_system:
                            category_info_by_system[system_name] = []
                        category_info_by_system[system_name].append(category)

                    # Now enhance systems with category data in memory
                    enhanced_systems = []
                    for system in all_systems:
                        try:
                            system_name = system["systems"]

                            # Get additional categories from bulk data
                            additional_categories = category_info_by_system.get(system_name, [])

                            if additional_categories:
                                # Parse existing categories
                                existing_categories = parse_categories(system.get("category", ""))

                                # Combine with additional categories
                                all_categories = existing_categories.copy()
                                for cat in additional_categories:
                                    if cat not in all_categories:
                                        all_categories.append(cat)

                                # Update system with combined categories
                                enhanced_system = system.copy()
                                enhanced_system["category"] = format_categories_for_storage(all_categories)
                                enhanced_system["_individual_categories"] = all_categories
                                enhanced_systems.append(enhanced_system)
                            else:
                                # No additional categories, use original
                                enhanced_systems.append(system)

                        except Exception as e:
                            print(f"[ERROR] Error processing system {system.get('systems', 'Unknown')}: {e}")
                            enhanced_systems.append(system)  # Fallback to original data

                    all_systems = enhanced_systems
                    print(f"[DEBUG] Enhanced {len(all_systems)} systems with combined category data (bulk method)")
                except Exception as e:
                    print(f"[ERROR] Bulk category query failed: {e}")
                    # Continue with original systems if bulk query fails

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
                    print(f"Error loading new discoveries for nearest systems: {e}")

                richards_categories = []
                try:
                    richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                    richards_categories = [item["category"] for item in
                                           richards_response.data] if richards_response.data else []
                except:
                    pass
                if "All Categories" in self.selected_categories_main or not self.selected_categories_main:
                    # Filter out Richard's categories using multi-category logic
                    all_systems = [s for s in all_systems if
                                   not any(cat in richards_categories for cat in parse_categories(s.get("category")))]
                if "All Categories" not in self.selected_categories_main and self.selected_categories_main:
                    # Use multi-category filtering logic - check both combined categories and individual categories
                    filtered_systems = []
                    for s in all_systems:
                        # Check if system matches any selected category
                        system_matches = False

                        # Check main category field
                        if categories_match_filter(s.get("category"), self.selected_categories_main):
                            system_matches = True

                        # Also check individual categories if available
                        if not system_matches and s.get("_individual_categories"):
                            for selected_cat in self.selected_categories_main:
                                if selected_cat in s.get("_individual_categories", []):
                                    system_matches = True
                                    break

                        if system_matches:
                            filtered_systems.append(s)

                    all_systems = filtered_systems
                    print(
                        f"[DEBUG] After category filtering: {len(all_systems)} systems match {self.selected_categories_main}")
                filter_type = self.nearest_filter.get() if hasattr(self, 'nearest_filter') else "All Systems"
                if filter_type == "Unclaimed Only":
                    taken = {r["system"] for r in supabase.table("taken").select("system").execute().data or []}
                    pois = {p["system_name"] for p in supabase.table("pois").select("system_name").execute().data or []}
                    all_systems = [s for s in all_systems if s["systems"] not in taken and s["systems"] not in pois]
                elif filter_type == "Your Claims":
                    claims = supabase.table("taken").select("system,done").eq("by_cmdr",
                                                                              self.cmdr_name).execute().data or []
                    your_systems = {r["system"] for r in claims if not r.get("done", False)}
                    all_systems = [s for s in all_systems if s["systems"] in your_systems]
                elif filter_type == "Done Systems":
                    done = supabase.table("taken").select("system").eq("done", True).execute().data or []
                    done_systems = {r["system"] for r in done}
                    all_systems = [s for s in all_systems if s["systems"] in done_systems]
                elif filter_type == "POIs":
                    pois = supabase.table("pois").select("system_name").eq("potential_or_poi",
                                                                           "POI").execute().data or []
                    poi_names = {p["system_name"] for p in pois}
                    all_systems = [s for s in all_systems if s["systems"] in poi_names]
                elif filter_type == "Potential POIs":
                    pois = supabase.table("pois").select("system_name").eq("potential_or_poi",
                                                                           "Potential POI").execute().data or []
                    poi_names = {p["system_name"] for p in pois}
                    all_systems = [s for s in all_systems if s["systems"] in poi_names]
                systems_with_distance = []
                for sys in all_systems:
                    try:
                        # Ensure coordinates are converted to float
                        sys_x = float(sys["x"]) if sys["x"] is not None else 0.0
                        sys_y = float(sys["y"]) if sys["y"] is not None else 0.0
                        sys_z = float(sys["z"]) if sys["z"] is not None else 0.0

                        if sys["systems"] == self.system_name:
                            distance = 0.0
                        else:
                            dx = sys_x - cx
                            dy = sys_y - cy
                            dz = sys_z - cz
                            distance = (dx * dx + dy * dy + dz * dz) ** 0.5
                        systems_with_distance.append({
                            "name": sys["systems"],
                            "category": sys.get("category", "Unknown"),
                            "distance": distance,
                            "x": sys_x,
                            "y": sys_y,
                            "z": sys_z
                        })
                    except (ValueError, TypeError) as e:
                        print(f"Error processing coordinates for system {sys.get('systems', 'Unknown')}: {e}")
                        continue
                systems_with_distance.sort(key=lambda x: x["distance"])

                self.all_nearest_systems = systems_with_distance

                poi_data = {}
                done_data = set()
                category_images = get_category_images()
                system_images = {}

                if systems_with_distance:
                    pois = supabase.table("pois").select("system_name,potential_or_poi").execute().data or []
                    for poi in pois:
                        poi_data[poi["system_name"]] = poi["potential_or_poi"]
                    done = supabase.table("taken").select("system").eq("done", True).execute().data or []
                    done_data = {r["system"] for r in done}
                    sys_info = supabase.table("system_information").select("system,images").execute().data or []
                    for info in sys_info:
                        if info.get("images"):
                            system_images[info["system"]] = info["images"]

                for sys in systems_with_distance[:min(3, self.nearest_display_limit)]:
                    image_url = category_images.get(sys["category"]) or system_images.get(sys["name"])
                    if image_url:
                        cache_key = f"card_{image_url}_538x96"
                        if cache_key not in image_cache:
                            self._preload_image(image_url)

                self.after(0, lambda: self._display_systems_with_pagination(poi_data, done_data, category_images,
                                                                            system_images))
            except Exception as e:
                print(f"Error loading systems: {e}")
                error_msg = str(e).lower()
                if any(x in error_msg for x in
                       ["server disconnect", "connection reset", "connection aborted", "connection lost"]):
                    self.after(0, lambda: self._show_server_disconnect_error())
                    self.after(100, lambda: self.update_nearest_systems())
                else:
                    self.after(0, lambda: self._show_error())

        threading.Thread(target=load_systems, daemon=True).start()

    def _display_systems_with_pagination(self, poi_data, done_data, category_images, system_images):
        """Display systems with pagination support"""
        try:
            self._stored_poi_data = poi_data
            self._stored_done_data = done_data
            self._stored_category_images = category_images
            self._stored_system_images = system_images

            for widget in self.nearest_scroll.winfo_children():
                widget.destroy()

            if not self.all_nearest_systems:
                ctk.CTkLabel(self.nearest_scroll, text="No systems found",
                             font=ctk.CTkFont(size=14), text_color=TEXT_SECONDARY).pack(pady=50)
                return

            systems_to_display = self.all_nearest_systems[:self.nearest_display_limit]

            for sys in systems_to_display:
                self._create_system_card(sys, poi_data, done_data, category_images, system_images)

            if len(self.all_nearest_systems) > self.nearest_display_limit:
                show_more_frame = ctk.CTkFrame(self.nearest_scroll, fg_color="transparent")
                show_more_frame.pack(fill="x", pady=15, padx=5)

                remaining = len(self.all_nearest_systems) - self.nearest_display_limit
                button_text = f"Show More ({remaining} remaining)" if remaining > 15 else f"Show All ({remaining} remaining)"

                self.show_more_btn = ctk.CTkButton(
                    show_more_frame,
                    text=button_text,
                    command=self._show_more_systems,
                    width=200,
                    height=42,
                    fg_color=SECONDARY_BG_COLOR,
                    hover_color=TERTIARY_BG_COLOR,
                    border_color=ACCENT_COLOR,
                    border_width=2,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    corner_radius=10
                )
                self.show_more_btn.pack()


        except Exception as e:
            print(f"Error displaying systems with pagination: {e}")

    def _show_more_systems(self):
        """Load and display more systems without refreshing entire list"""
        try:
            current_shown = self.nearest_display_limit
            remaining = len(self.all_nearest_systems) - current_shown

            if current_shown >= 150:
                if hasattr(self, 'show_more_btn') and self.show_more_btn.winfo_exists():
                    self.show_more_btn.configure(
                        text=f"Max displayed (150). Use filters to narrow results.",
                        state="disabled",
                        fg_color="#666666"
                    )
                return

            if remaining > 15:
                new_limit = min(current_shown + 15, 150)
            else:
                new_limit = min(len(self.all_nearest_systems), 150)

            additional_systems = self.all_nearest_systems[current_shown:new_limit]

            if hasattr(self, 'show_more_btn') and self.show_more_btn.winfo_exists():
                self.show_more_btn.master.destroy()

            poi_data = getattr(self, '_stored_poi_data', {})
            done_data = getattr(self, '_stored_done_data', set())
            category_images = getattr(self, '_stored_category_images', {})
            system_images = getattr(self, '_stored_system_images', {})

            for sys in additional_systems:
                self._create_system_card(sys, poi_data, done_data, category_images, system_images)

            self.nearest_display_limit = new_limit

            if new_limit < len(self.all_nearest_systems):
                show_more_frame = ctk.CTkFrame(self.nearest_scroll, fg_color="transparent")
                show_more_frame.pack(fill="x", pady=15, padx=5)

                new_remaining = len(self.all_nearest_systems) - new_limit
                button_text = f"Show More ({new_remaining} remaining)" if new_remaining > 15 else f"Show All ({new_remaining} remaining)"

                self.show_more_btn = ctk.CTkButton(
                    show_more_frame,
                    text=button_text,
                    command=self._show_more_systems,
                    width=200,
                    height=42,
                    fg_color=SECONDARY_BG_COLOR,
                    hover_color=TERTIARY_BG_COLOR,
                    border_color=ACCENT_COLOR,
                    border_width=2,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    corner_radius=10
                )
                self.show_more_btn.pack()


        except Exception as e:
            print(f"Error showing more systems: {e}")

    def _display_systems(self, systems, poi_data, done_data, category_images, system_images):
        try:
            for widget in self.nearest_scroll.winfo_children():
                widget.destroy()
            if not systems:
                ctk.CTkLabel(self.nearest_scroll, text="No systems found",
                             font=ctk.CTkFont(size=14), text_color=TEXT_SECONDARY).pack(pady=50)
                return
            for sys in systems:
                self._create_system_card(sys, poi_data, done_data, category_images, system_images)
        except Exception as e:
            print(f"Error displaying systems: {e}")

    def _create_system_card(self, sys, poi_data, done_data, category_images, system_images):
        try:
            import tkinter as tk

            card = ctk.CTkFrame(self.nearest_scroll,
                                fg_color="#1a1a1a",
                                corner_radius=12, height=100,
                                border_color="#333333", border_width=1)
            card.pack(fill="x", padx=5, pady=5)
            card.pack_propagate(False)

            canvas = tk.Canvas(card, width=538, height=96,
                               bd=0, highlightthickness=0, bg="#1a1a1a")
            canvas.place(x=1, y=1)

            card._canvas = canvas
            card._system_name = sys['name']

            # Use primary category color for backward compatibility
            cat_color = get_category_color_for_multi(sys["category"]) if sys["category"] else "#666666"

            name_id = canvas.create_text(15, 25, text=sys['name'],
                                         font=("Arial", 18, "bold"),
                                         fill="white",
                                         anchor="w",
                                         tags=("system_name", "clickable"))

            # Display multiple categories with format_categories_for_display
            category_display = format_categories_for_display(sys['category'], max_length=45)
            canvas.create_text(15, 50, text=category_display,
                               font=("Arial", 11),
                               fill="#CCCCCC",
                               anchor="w")

            # Add category count indicator if multiple categories
            parsed_cats = parse_categories(sys['category'])
            if len(parsed_cats) > 1:
                count_text = f"({len(parsed_cats)} categories)"
                canvas.create_text(15, 65, text=count_text,
                                   font=("Arial", 9),
                                   fill="#888888",
                                   anchor="w")
                print(f"[DEBUG] Card for {sys['name']}: {len(parsed_cats)} categories - {parsed_cats}")

            distance_btn = ctk.CTkButton(card, text=f"{sys['distance']:.1f} LY",
                                         width=75, height=28,
                                         font=ctk.CTkFont(size=11, weight="bold"),
                                         fg_color="#2a2a2a",
                                         hover_color="#2a2a2a",
                                         text_color="#FFFFFF",
                                         border_width=0,
                                         corner_radius=6,
                                         state="disabled")
            distance_btn.place(x=390, rely=0.5, anchor="center")

            badge_x = 15

            if sys["name"] in done_data:
                done_btn = ctk.CTkButton(card, text="✓ DONE",
                                         width=60, height=22,
                                         font=ctk.CTkFont(size=10, weight="bold"),
                                         fg_color="#9f7aea",
                                         hover_color="#9f7aea",
                                         text_color="#FFFFFF",
                                         border_width=0,
                                         corner_radius=4,
                                         state="disabled")
                done_btn.place(x=badge_x, y=70)
                badge_x += 70

            if sys["name"] in poi_data:
                poi_type = poi_data[sys["name"]]
                if poi_type == "POI":
                    poi_btn = ctk.CTkButton(card, text="★ POI",
                                            width=50, height=22,
                                            font=ctk.CTkFont(size=10, weight="bold"),
                                            fg_color="#48bb78",
                                            hover_color="#48bb78",
                                            text_color="#FFFFFF",
                                            border_width=0,
                                            corner_radius=4,
                                            state="disabled")
                    poi_btn.place(x=badge_x, y=70)
                else:
                    pot_btn = ctk.CTkButton(card, text="◎ POTENTIAL",
                                            width=85, height=22,
                                            font=ctk.CTkFont(size=10, weight="bold"),
                                            fg_color="#f6ad55",
                                            hover_color="#f6ad55",
                                            text_color="#FFFFFF",
                                            border_width=0,
                                            corner_radius=4,
                                            state="disabled")
                    pot_btn.place(x=badge_x, y=70)

            view_btn = ctk.CTkButton(card, text="View",
                                     command=lambda: self.view_system(sys['name'], sys['category']),
                                     width=55, height=28,
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     fg_color="#17a2b8",
                                     hover_color="#138496",
                                     border_width=0,
                                     corner_radius=6)
            view_btn.place(x=460, rely=0.5, anchor="center")

            def on_name_click(event):
                bbox = canvas.bbox("system_name")
                if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
                    self.copy_to_clipboard(sys['name'])

            canvas.tag_bind("clickable", "<Button-1>", on_name_click)

            def on_name_enter(event):
                bbox = canvas.bbox("system_name")
                if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
                    canvas.config(cursor="hand2")
                    canvas.itemconfig("system_name", fill=ACCENT_COLOR)

            def on_name_leave(event):
                canvas.config(cursor="")
                canvas.itemconfig("system_name", fill="white")

            canvas.bind("<Motion>", on_name_enter)
            canvas.bind("<Leave>", on_name_leave)

            card._data = {
                'name': sys['name'],
                'category': sys['category'],
                'distance': f"{sys['distance']:.1f}",
                'done': sys["name"] in done_data,
                'poi': poi_data.get(sys["name"]),
                'cat_color': cat_color
            }

            card._canvas = canvas

            # Try to find image for category - handle multi-category systems
            image_url = None

            # First try exact match for the category string
            if sys["category"] in category_images:
                image_url = category_images[sys["category"]]
            else:
                # For multi-category systems, try each individual category
                parsed_cats = parse_categories(sys["category"])
                for cat in parsed_cats:
                    if cat in category_images:
                        image_url = category_images[cat]
                        print(f"[DEBUG] Found category image for '{cat}' in system {sys['name']}")
                        break

            # Fallback to system-specific image
            if not image_url:
                image_url = system_images.get(sys["name"])

            if image_url:
                self._load_card_background(card, image_url)


        except Exception as e:
            print(f"Error creating system card: {e}")

    def _load_card_background(self, card, image_url):
        """Load and apply the background image to the card"""

        def load_async():
            try:
                cache_key = f"card_{image_url}_538x96"
                if cache_key in image_cache and card.winfo_exists():
                    card.after(0, lambda: self._apply_card_background(card, image_cache[cache_key]))
                    return

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }

                if HAS_REQUESTS:
                    response = requests.get(image_url, headers=headers, timeout=3)
                    response.raise_for_status()
                    img = Image.open(BytesIO(response.content))
                else:
                    req = urllib.request.Request(image_url, headers=headers)
                    response = urllib.request.urlopen(req, timeout=3)
                    img = Image.open(BytesIO(response.read()))

                card_width = 538
                card_height = 96

                img_ratio = img.width / img.height
                card_ratio = card_width / card_height

                if img_ratio > card_ratio:
                    new_height = card_height
                    new_width = int(card_height * img_ratio)
                else:
                    new_width = card_width
                    new_height = int(card_width / img_ratio)

                img = img.resize((new_width, new_height), Resampling.LANCZOS)

                left = (new_width - card_width) // 2
                top = (new_height - card_height) // 2
                img = img.crop((left, top, left + card_width, top + card_height))

                img = img.convert('RGBA')
                overlay = Image.new('RGBA', (card_width, card_height), (0, 0, 0, 100))
                img = Image.alpha_composite(img, overlay)

                mask = Image.new('L', (card_width, card_height), 0)
                draw = ImageDraw.Draw(mask)
                radius = 12

                try:
                    draw.rounded_rectangle([(0, 0), (card_width - 1, card_height - 1)],
                                           radius=radius, fill=255)
                except AttributeError:
                    draw.rectangle([(radius, 0), (card_width - radius - 1, card_height - 1)], fill=255)
                    draw.rectangle([(0, radius), (card_width - 1, card_height - radius - 1)], fill=255)
                    draw.ellipse([(0, 0), (radius * 2, radius * 2)], fill=255)
                    draw.ellipse([(card_width - radius * 2 - 1, 0), (card_width - 1, radius * 2)], fill=255)
                    draw.ellipse([(0, card_height - radius * 2 - 1), (radius * 2, card_height - 1)], fill=255)
                    draw.ellipse([(card_width - radius * 2 - 1, card_height - radius * 2 - 1),
                                  (card_width - 1, card_height - 1)], fill=255)

                output = Image.new('RGBA', (card_width, card_height), (0, 0, 0, 0))
                output.paste(img, (0, 0))
                output.putalpha(mask)

                from PIL import ImageTk
                photo = ImageTk.PhotoImage(output)

                image_cache[cache_key] = photo

                if card.winfo_exists():
                    card.after(0, lambda: self._apply_card_background(card, photo))

            except Exception as e:
                print(f"Error loading card background: {e}")

        threading.Thread(target=load_async, daemon=True).start()

    def _apply_card_background(self, card, photo):
        """Apply the background image to the card's canvas"""
        try:
            if card.winfo_exists() and hasattr(card, '_canvas'):
                canvas = card._canvas

                canvas.delete("bg_image")
                canvas.create_image(0, 0, anchor="nw", image=photo, tags="bg_image")
                canvas.tag_lower("bg_image")

                card._bg_photo = photo

                canvas.delete("text")

                data = card._data

                name_id = canvas.create_text(15, 25, text=data['name'],
                                             font=("Arial", 18, "bold"),
                                             fill="white",
                                             anchor="w",
                                             tags=("system_name", "clickable", "text"))

                # Display multiple categories with format_categories_for_display
                category_display = format_categories_for_display(data['category'], max_length=45)
                canvas.create_text(15, 50, text=category_display,
                                   font=("Arial", 11),
                                   fill="#DDDDDD",
                                   anchor="w",
                                   tags="text")

                # Add category count indicator if multiple categories
                parsed_cats = parse_categories(data['category'])
                if len(parsed_cats) > 1:
                    canvas.create_text(15, 65, text=f"({len(parsed_cats)} categories)",
                                       font=("Arial", 9),
                                       fill="#AAAAAA",
                                       anchor="w",
                                       tags="text")

        except Exception as e:
            print(f"Error applying card background: {e}")

    def _preload_image(self, image_url):
        """Preload image into cache without card reference"""

        def load_async():
            try:
                cache_key = f"card_{image_url}_538x96"
                if cache_key in image_cache:
                    return

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }

                if HAS_REQUESTS:
                    response = requests.get(image_url, headers=headers, timeout=3)
                    response.raise_for_status()
                    img = Image.open(BytesIO(response.content))
                else:
                    req = urllib.request.Request(image_url, headers=headers)
                    response = urllib.request.urlopen(req, timeout=3)
                    img = Image.open(BytesIO(response.read()))

                card_width = 538
                card_height = 96

                img_ratio = img.width / img.height
                card_ratio = card_width / card_height

                if img_ratio > card_ratio:
                    new_height = card_height
                    new_width = int(card_height * img_ratio)
                else:
                    new_width = card_width
                    new_height = int(card_width / img_ratio)

                img = img.resize((new_width, new_height), Resampling.LANCZOS)

                left = (new_width - card_width) // 2
                top = (new_height - card_height) // 2
                img = img.crop((left, top, left + card_width, top + card_height))

                img = img.convert('RGBA')
                overlay = Image.new('RGBA', (card_width, card_height), (0, 0, 0, 100))
                img = Image.alpha_composite(img, overlay)

                mask = Image.new('L', (card_width, card_height), 0)
                draw = ImageDraw.Draw(mask)
                radius = 12

                try:
                    draw.rounded_rectangle([(0, 0), (card_width - 1, card_height - 1)],
                                           radius=radius, fill=255)
                except AttributeError:
                    draw.rectangle([(radius, 0), (card_width - radius - 1, card_height - 1)], fill=255)
                    draw.rectangle([(0, radius), (card_width - 1, card_height - radius - 1)], fill=255)
                    draw.ellipse([(0, 0), (radius * 2, radius * 2)], fill=255)
                    draw.ellipse([(card_width - radius * 2 - 1, 0), (card_width - 1, radius * 2)], fill=255)
                    draw.ellipse([(0, card_height - radius * 2 - 1), (radius * 2, card_height - 1)], fill=255)
                    draw.ellipse([(card_width - radius * 2 - 1, card_height - radius * 2 - 1),
                                  (card_width - 1, card_height - 1)], fill=255)

                output = Image.new('RGBA', (card_width, card_height), (0, 0, 0, 0))
                output.paste(img, (0, 0))
                output.putalpha(mask)

                from PIL import ImageTk
                photo = ImageTk.PhotoImage(output)
                image_cache[cache_key] = photo

            except Exception as e:
                print(f"Error preloading image: {e}")

        threading.Thread(target=load_async, daemon=True).start()

    def _show_error(self):
        for widget in self.nearest_scroll.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.nearest_scroll, text="Error loading systems",
                     font=ctk.CTkFont(size=14), text_color="#ff6b6b").pack(pady=50)

    def _show_server_disconnect_error(self):
        for widget in self.nearest_scroll.winfo_children():
            widget.destroy()

        error_frame = ctk.CTkFrame(self.nearest_scroll, fg_color="transparent")
        error_frame.pack(expand=True, pady=50)

        ctk.CTkLabel(error_frame, text="Server disconnected",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#ff6b6b").pack(pady=(0, 10))

        ctk.CTkLabel(error_frame, text="Please refresh",
                     font=ctk.CTkFont(size=14),
                     text_color="#ffaa55").pack()

        ctk.CTkLabel(error_frame, text="Auto-refreshing...",
                     font=ctk.CTkFont(size=12),
                     text_color="#888888").pack(pady=(10, 0))

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
        try:
            if hasattr(self, '_is_destroying') and self._is_destroying:
                return
            if not self.winfo_exists():
                return
        except:
            return
        if not supabase or not self.current_coords:
            return
        systems = []
        try:
            # Ensure current coordinates are floats
            cx, cy, cz = self.current_coords
            cx, cy, cz = float(cx), float(cy), float(cz)
            # Get systems from main systems table
            systems = supabase.table("systems").select("systems,category,x,y,z").execute().data or []

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
                        if not any(s["systems"] == discovery["system"] for s in systems):
                            systems.append(discovery_data)
            except Exception as e:
                print(f"Error loading new discoveries for nearest unclaimed: {e}")

            richards_categories = []
            try:
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                richards_categories = [item["category"] for item in
                                       richards_response.data] if richards_response.data else []
            except:
                pass
            if "All Categories" in self.selected_categories_main or not self.selected_categories_main:
                # Filter out Richard's categories using multi-category logic
                systems = [s for s in systems if
                           not any(cat in richards_categories for cat in parse_categories(s.get("category")))]
            else:
                pass
            if "All Categories" not in self.selected_categories_main and self.selected_categories_main:
                # Use multi-category filtering logic
                systems = [s for s in systems if
                           categories_match_filter(s.get("category"), self.selected_categories_main)]
            taken = {r["system"] for r in supabase.table("taken").select("system").execute().data or []}
            pois = supabase.table("pois").select("system_name").execute().data or []
            poi_systems = {poi["system_name"] for poi in pois}
            unclaimed = [s for s in systems if s["systems"] not in taken and s["systems"] not in poi_systems]
            self.unclaimed_systems = []
            for rec in unclaimed:
                try:
                    # Ensure coordinates are converted to float
                    rec_x = float(rec["x"]) if rec["x"] is not None else 0.0
                    rec_y = float(rec["y"]) if rec["y"] is not None else 0.0
                    rec_z = float(rec["z"]) if rec["z"] is not None else 0.0

                    dx, dy, dz = rec_x - cx, rec_y - cy, rec_z - cz
                    distance = (dx * dx + dy * dy + dz * dz) ** 0.5
                    self.unclaimed_systems.append({
                        **rec,
                        'distance': distance
                    })
                except (ValueError, TypeError) as e:
                    print(f"Error processing coordinates for system {rec.get('systems', 'Unknown')}: {e}")
                    continue
            self.unclaimed_systems.sort(key=lambda x: x['distance'])
            if self.unclaimed_systems:
                self.unclaimed_index = 0
                self.update_unclaimed_display()
            else:
                self.closest_label.configure(text="None")
                self.closest_distance_label.configure(text="")
                self.closest_category_label.configure(text="")
                self.closest_poi_label.configure(text="")
                self.unclaimed_position_label.configure(text="0/0")
                self.btn_view_closest.configure(state="disabled")
                self.btn_claim_closest.configure(state="disabled")
                self.btn_prev_unclaimed.configure(state="disabled")
                self.btn_next_unclaimed.configure(state="disabled")
        except Exception as e:
            print(f"Error in find_nearest_unclaimed: {e}")
            error_msg = str(e).lower()
            if any(x in error_msg for x in
                   ["server disconnect", "connection reset", "connection aborted", "connection lost"]):
                self.closest_label.configure(text="Server disconnected")
                self.after(500, self.find_nearest_unclaimed)
            else:
                self.closest_label.configure(text="Error")
            if hasattr(self, 'closest_distance_label'):
                self.closest_distance_label.configure(text="")
            if hasattr(self, 'closest_category_label'):
                self.closest_category_label.configure(text="")
            if hasattr(self, 'closest_poi_label'):
                self.closest_poi_label.configure(text="")
            if hasattr(self, 'unclaimed_position_label'):
                self.unclaimed_position_label.configure(text="0/0")
            self.btn_view_closest.configure(state="disabled")
            self.btn_claim_closest.configure(state="disabled")
            if hasattr(self, 'btn_prev_unclaimed'):
                self.btn_prev_unclaimed.configure(state="disabled")
            if hasattr(self, 'btn_next_unclaimed'):
                self.btn_next_unclaimed.configure(state="disabled")

    def open_map(self):
        if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
            self.map_window.lift()
            self.map_window.focus_force()
            self.map_window.attributes("-topmost", True)
            self.map_window.after(500, lambda: self.map_window.attributes("-topmost", False))
        else:
            self.map_window = ZoomableMap(self)

    def check_system_visited_in_journals(self, system_name):
        if not _cfg.get("journal_path"):
            return False
        try:
            journal_path = _cfg["journal_path"]
            for filename in os.listdir(journal_path):
                if filename.startswith("Journal.") and filename.endswith(".log"):
                    # Check if it matches either journal format
                    if (re.match(r"Journal\.\d{4}-\d{2}-\d{2}T\d{6}\.01\.log$", filename) or
                            re.match(r"Journal\.\d{12}\.01\.log$", filename)):
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
        if not system_name:
            return

        if hasattr(self, '_system_popup') and self._system_popup and self._system_popup.winfo_exists():
            self._refresh_system_popup(system_name, category)
            return

        popup = ctk.CTkToplevel(self)
        self._system_popup = popup
        self.current_system_popup = popup  # Store reference for category selector
        popup._system_name = system_name
        popup._category = category

        popup.title(f"POI: {system_name}")
        popup.geometry("800x650")
        popup.resizable(True, True)
        popup.transient(self)
        popup.grab_set()
        popup.configure(fg_color=MAIN_BG_COLOR)
        popup.attributes("-topmost", True)
        popup.lift()
        popup.focus_force()
        popup.after(300, lambda: popup.attributes("-topmost", False))

        def on_popup_close():
            self._system_popup = None
            self.current_system_popup = None
            self.system_categories = []
            self.current_category_selection = None
            self.hide_category_selector()  # Hide main category selector when popup closes
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", on_popup_close)

        try:
            popup.iconbitmap(resource("icon.ico"))
        except:
            pass

        popup._main_container = ctk.CTkFrame(popup, fg_color=MAIN_BG_COLOR)
        popup._main_container.pack(fill="both", expand=True)

        self._build_system_popup_content(popup, system_name, category)

        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")

    def _refresh_system_popup(self, system_name, category):
        """Refresh existing popup with new system data"""
        if not hasattr(self, '_system_popup') or not self._system_popup:
            return

        popup = self._system_popup
        popup._system_name = system_name
        popup._category = category
        popup.title(f"POI: {system_name}")

        # Clear all existing content
        for widget in popup._main_container.winfo_children():
            widget.destroy()

        # Reset category selector state to ensure fresh data
        self.system_categories = []
        self.current_category_selection = category

        # Force refresh of system data from database to get latest categories
        if supabase:
            try:
                fresh_systems_check = supabase.table("systems").select("*").eq("systems", system_name).execute()
                if fresh_systems_check.data:
                    fresh_combined_data = combine_system_entries(fresh_systems_check.data, system_name)
            except Exception as e:
                print(f"Error refreshing system data: {e}")

        # Rebuild everything with fresh data from database
        self._build_system_popup_content(popup, system_name, category)

    def _build_system_popup_content(self, popup, system_name, category):
        """Build the actual content of the system popup"""
        bold_font = ctk.CTkFont(family="Dosis", size=18,
                                weight="bold") if "Dosis" in tkFont.families() else ctk.CTkFont(size=18, weight="bold")
        reg_font = ctk.CTkFont(family="Dosis", size=14) if "Dosis" in tkFont.families() else ctk.CTkFont(size=14)

        # Use selected category from bottom selector if available, otherwise use original category
        display_category = self.current_category_selection if self.current_category_selection else category
        print(f"Building system popup content for {system_name} with display_category: {display_category}")

        tabview = ctk.CTkTabview(popup._main_container, width=780, height=610,
                                 fg_color=CARD_BG_COLOR,
                                 segmented_button_fg_color=SECONDARY_BG_COLOR,
                                 segmented_button_selected_color=ACCENT_COLOR,
                                 segmented_button_selected_hover_color=ACCENT_HOVER)
        tabview.pack(pady=10, padx=10, fill="both", expand=True)

        popup.tabview = tabview

        # Check if system has multiple categories - will be handled in info tab setup
        combined_system_data = None
        if supabase:
            try:
                systems_check = supabase.table("systems").select("*").eq("systems", system_name).execute()
                if systems_check.data:
                    combined_system_data = combine_system_entries(systems_check.data, system_name)
            except Exception as e:
                print(f"Error checking system categories: {e}")

        poi_data = None
        claim_data = None
        system_info = None
        is_visited = False
        journal_visited = False
        system_in_database = False
        systems_check = None
        if supabase:
            try:
                systems_check = supabase.table("systems").select("*").eq("systems", system_name).execute()
                system_in_database = bool(systems_check.data)

                # Combine multiple system entries with same name into single entry with merged categories
                combined_system_data = None
                if systems_check.data:
                    combined_system_data = combine_system_entries(systems_check.data, system_name)
                    print(
                        f"Combined system data for {system_name}: {combined_system_data.get('category') if combined_system_data else 'None'}")
                poi_response = supabase.table("pois").select("*").eq("system_name", system_name).execute()
                if poi_response.data:
                    poi_data = poi_response.data[0]
                    print(f"POI data found: {poi_data}")
                visited_check = supabase.table("taken").select("*").eq("system", system_name).eq("visited",
                                                                                                 True).execute()
                is_visited = bool(visited_check.data)
                journal_visited = self.check_system_visited_in_journals(system_name)

                if journal_visited and not is_visited and claim_data and claim_data.get("by_cmdr") == self.cmdr_name:
                    try:
                        supabase.table("taken").update({"visited": True}).eq("system", system_name).eq("by_cmdr",
                                                                                                       self.cmdr_name).execute()
                        is_visited = True
                        print(f"Auto-marked {system_name} as visited based on journal data")
                    except:
                        pass
                sys_info_response = supabase.table("system_information").select("*").eq("system", system_name).execute()
                if sys_info_response.data:
                    system_info = sys_info_response.data[0]
                    print(f"Found system_info for {system_name}: {system_info}")
                if sys_info_response.data:
                    system_info = sys_info_response.data[0]
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
                if not poi_data and not system_info and system_in_database and combined_system_data:
                    system_data = combined_system_data
                    poi_data = {
                        "system_name": system_data.get("systems"),
                        "coords_x": system_data.get("x"),
                        "coords_y": system_data.get("y"),
                        "coords_z": system_data.get("z"),
                        "description": system_data.get("category")
                    }
                claim_response = supabase.table("taken").select("*").eq("system", system_name).execute()
                if claim_response.data:
                    claim_data = claim_response.data[0]
            except Exception as e:
                print(f"Error fetching data: {e}")
                error_msg = str(e).lower()
                if any(x in error_msg for x in
                       ["server disconnect", "connection reset", "connection aborted", "connection lost"]):
                    messagebox.showwarning("Server Disconnected",
                                           "Server connection lost. Please try again.",
                                           parent=popup)
                    popup.after(1000, popup.destroy)
        info_tab = tabview.add("System Info")

        if is_visited or poi_data:
            poi_tab = tabview.add("POI")
        show_edit_tab = False
        if self.is_admin:
            show_edit_tab = True
        elif claim_data:
            if claim_data.get("by_cmdr") == self.cmdr_name:
                show_edit_tab = True
        # Also show edit tab for systems not in database if user is currently there
        elif not system_in_database and self.system_name == system_name:
            show_edit_tab = True
        if show_edit_tab:
            edit_tab = tabview.add("Edit Info")
        else:
            edit_tab = None
        info_frame = ctk.CTkScrollableFrame(info_tab, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)

        header_frame = ctk.CTkFrame(info_frame, fg_color=CARD_BG_COLOR,
                                    border_color=ACCENT_COLOR, border_width=2, corner_radius=10)
        header_frame.pack(fill="x", pady=(0, 20))
        img_frame = ctk.CTkFrame(header_frame, fg_color=MAIN_BG_COLOR,
                                 width=80, height=80, corner_radius=8)
        img_frame.pack(side="left", padx=15, pady=15)
        img_frame.pack_propagate(False)
        cat_color = "#666666"
        # Get category for proper multi-category support - use display_category if available
        if display_category and display_category != category:
            # Use the selected category for color
            cat_color = get_or_create_category_color(display_category)
        elif system_in_database and combined_system_data:
            category_data = combined_system_data.get("category", "")
            if category_data:
                # Use primary category for color but ensure we have the full data
                primary_category = get_primary_category(category_data)
                cat_color = get_or_create_category_color(primary_category)
        elif system_info and system_info.get("category"):
            # Check system_information table for multi-category data
            category_data = system_info.get("category")
            if category_data:
                primary_category = get_primary_category(category_data)
                cat_color = get_or_create_category_color(primary_category)
        elif poi_data:
            category = poi_data.get("description", "")
            cat_color = get_or_create_category_color(category) if category else "#666666"
        cat_indicator = ctk.CTkFrame(img_frame, fg_color=cat_color, corner_radius=6)
        cat_indicator.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.8)
        info_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_content.pack(side="left", fill="both", expand=True, padx=(0, 15), pady=15)
        system_name_label = ctk.CTkLabel(info_content, text=system_name,
                                         font=ctk.CTkFont(size=24, weight="bold"),
                                         text_color=ACCENT_COLOR,
                                         cursor="hand2")
        system_name_label.pack(anchor="w")
        system_name_label.bind("<Button-1>", lambda e: self.copy_to_clipboard(system_name))
        system_name_label.bind("<Enter>", lambda e: system_name_label.configure(text_color="#FFD700"))
        system_name_label.bind("<Leave>", lambda e: system_name_label.configure(text_color=ACCENT_COLOR))
        # Display category information - use display_category if available
        if display_category and display_category != category:
            # Show only the selected category when using category selector
            category_frame = ctk.CTkFrame(info_content, fg_color="transparent")
            category_frame.pack(anchor="w", pady=(5, 0), fill="x")

            # Store reference for updates
            popup.category_display_label = ctk.CTkLabel(category_frame, text=display_category,
                                                        font=ctk.CTkFont(size=14),
                                                        text_color=TEXT_SECONDARY)
            popup.category_display_label.pack(anchor="w")

            # Show category selector indicator
            if len(self.system_categories) > 1:
                count_text = f"({len(self.system_categories)} categories total - use selector above)"
                ctk.CTkLabel(category_frame, text=count_text,
                             font=ctk.CTkFont(size=11),
                             text_color="#888888").pack(anchor="w", pady=(2, 0))
        elif system_in_database and combined_system_data:
            category_data = combined_system_data.get("category", "Unknown Category")
            category_display = format_categories_for_display(category_data, max_length=60)

            # Create a frame for category information
            category_frame = ctk.CTkFrame(info_content, fg_color="transparent")
            category_frame.pack(anchor="w", pady=(5, 0), fill="x")

            ctk.CTkLabel(category_frame, text=category_display,
                         font=ctk.CTkFont(size=14),
                         text_color=TEXT_SECONDARY).pack(anchor="w")

            # Show category count if multiple categories
            parsed_cats = parse_categories(category_data)
            if len(parsed_cats) > 1:
                count_text = f"({len(parsed_cats)} categories total)"
                ctk.CTkLabel(category_frame, text=count_text,
                             font=ctk.CTkFont(size=11),
                             text_color="#888888").pack(anchor="w", pady=(2, 0))
        elif system_info and system_info.get("category"):
            # Handle multi-category display from system_information table
            category_data = system_info.get("category")
            category_display = format_categories_for_display(category_data, max_length=60)

            # Create a frame for category information
            category_frame = ctk.CTkFrame(info_content, fg_color="transparent")
            category_frame.pack(anchor="w", pady=(5, 0), fill="x")

            ctk.CTkLabel(category_frame, text=category_display,
                         font=ctk.CTkFont(size=14),
                         text_color=TEXT_SECONDARY).pack(anchor="w")

            # Show category count if multiple categories
            parsed_cats = parse_categories(category_data)
            if len(parsed_cats) > 1:
                count_text = f"({len(parsed_cats)} categories total)"
                ctk.CTkLabel(category_frame, text=count_text,
                             font=ctk.CTkFont(size=11),
                             text_color="#888888").pack(anchor="w", pady=(2, 0))
        elif poi_data and poi_data.get("category"):
            ctk.CTkLabel(info_content, text=poi_data.get("category", "Unknown Category"),
                         font=ctk.CTkFont(size=14),
                         text_color=TEXT_SECONDARY).pack(anchor="w", pady=(5, 0))
        elif not system_in_database:
            ctk.CTkLabel(info_content, text="System not in records database",
                         font=ctk.CTkFont(size=14),
                         text_color="#FF6B6B").pack(anchor="w", pady=(5, 0))

        # Add compact category selector after header, before system data
        if combined_system_data and combined_system_data.get("_individual_categories"):
            individual_categories = combined_system_data["_individual_categories"]
            # Also check if there are additional categories in the raw category string that weren't parsed
            raw_category_data = combined_system_data.get("category", "")
            if raw_category_data:
                raw_parsed_categories = parse_categories(raw_category_data)
                # Merge with individual categories, ensuring all categories are included
                all_categories = individual_categories.copy()
                for cat in raw_parsed_categories:
                    if cat not in all_categories:
                        all_categories.append(cat)
                individual_categories = all_categories

            if len(individual_categories) > 1:
                self.setup_compact_category_selector(info_frame, popup, system_name, individual_categories)

        if poi_data or system_info:
            data_to_show = poi_data if poi_data else system_info
            x_val = y_val = z_val = None
            distance_str = "N/A"
            try:
                if poi_data and poi_data.get("coords_x") is not None and poi_data.get("coords_x") != 0:
                    x_val = float(poi_data.get("coords_x"))
                    y_val = float(poi_data.get("coords_y"))
                    z_val = float(poi_data.get("coords_z"))
                    print(f"Got coords from POI coords_x/y/z: {x_val}, {y_val}, {z_val}")
                elif poi_data and poi_data.get("x") is not None and poi_data.get("x") != 0:
                    x_val = float(poi_data.get("x"))
                    y_val = float(poi_data.get("y"))
                    z_val = float(poi_data.get("z"))
                    print(f"Got coords from POI x/y/z: {x_val}, {y_val}, {z_val}")
                elif system_in_database and combined_system_data:
                    x_val = float(combined_system_data.get('x', 0))
                    y_val = float(combined_system_data.get('y', 0))
                    z_val = float(combined_system_data.get('z', 0))
                    print(f"Got coords from systems table: {x_val}, {y_val}, {z_val}")
                elif self.system_name == system_name and self.latest_starpos:
                    x_val, y_val, z_val = self.latest_starpos
                    print(f"Got coords from current position: {x_val}, {y_val}, {z_val}")
                else:
                    print(f"Fallback: Looking for {system_name} in all data sources...")
                    if supabase:
                        all_pois = supabase.table("pois").select("*").execute().data or []
                        for p in all_pois:
                            if p.get("system_name") == system_name:
                                print(f"Found POI in fallback: {p}")
                                for x_field, y_field, z_field in [("x", "y", "z"),
                                                                  ("coords_x", "coords_y", "coords_z")]:
                                    if x_field in p and p[x_field] is not None:
                                        test_x = float(p[x_field]) if p[x_field] else 0
                                        test_y = float(p[y_field]) if p[y_field] else 0
                                        test_z = float(p[z_field]) if p[z_field] else 0
                                        if test_x != 0 or test_y != 0 or test_z != 0:
                                            x_val, y_val, z_val = test_x, test_y, test_z
                                            print(f"Got coords from POI fallback: {x_val}, {y_val}, {z_val}")
                                            break
                                break
                if x_val is not None and y_val is not None and z_val is not None and (
                        x_val != 0 or y_val != 0 or z_val != 0):
                    distance = (x_val ** 2 + y_val ** 2 + z_val ** 2) ** 0.5
                    distance_str = f"{distance:.2f} LY"
                else:
                    x_val = y_val = z_val = 0
                    distance_str = "N/A"
            except Exception as e:
                print(f"Error in coordinate calculation: {e}")
                x_val = y_val = z_val = 0
                distance_str = "N/A"
            query_category = "No category available"
            category_table_info = None

            # Use display_category for specific category info if available
            if display_category and display_category != category:
                query_category = display_category
                category_table_info = self.get_category_table_data(system_name, display_category)
            elif system_info and system_info.get("category"):
                query_category = system_info.get("category")
            elif system_in_database and combined_system_data:
                query_category = combined_system_data.get("category", "Unknown")

            # Format category display for multi-category support
            if display_category and display_category != category:
                # Show only the selected category when using category selector
                query_category_display = display_category
            else:
                query_category_display = format_categories_for_display(query_category, max_length=80)

            if system_info and "system_info" in system_info:
                category_table_info = system_info.get("system_info")
            elif system_in_database and combined_system_data and combined_system_data.get(
                    "system_info") and not display_category:
                # Use combined system info from multiple database entries only if not using category selector
                category_table_info = combined_system_data.get("system_info")
            elif not category_table_info:
                # Get category-specific table data
                lookup_category = display_category if display_category else get_primary_category(query_category)
                category_table_info = self.get_category_table_data(system_name, lookup_category)
            info_items = [
                ("System Name:", data_to_show.get("system_name", system_name)),
                ("Coordinates:",
                 f"X: {x_val if x_val else 'N/A'}, Y: {y_val if y_val else 'N/A'}, Z: {z_val if z_val else 'N/A'}"),
                ("Distance from Sol:", distance_str),
                ("Categories:", query_category_display)
            ]
            if category_table_info:
                row_frame = ctk.CTkFrame(info_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=8)
                row_frame.pack(fill="x", pady=3)
                content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                content_frame.pack(fill="x", padx=15, pady=10)
                ctk.CTkLabel(content_frame, text="System Info:", font=reg_font,
                             text_color=ACCENT_COLOR, width=140, anchor="nw").pack(side="left", anchor="n")
                info_text_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                info_text_frame.pack(side="left", padx=(10, 0), fill="x", expand=True)

                # Store reference to the system info frame for updates
                popup.system_info_frame = info_text_frame

                for line in category_table_info.split('\n'):
                    if line.strip():
                        ctk.CTkLabel(info_text_frame, text=line, font=reg_font,
                                     text_color=TEXT_COLOR, anchor="w").pack(anchor="w", pady=1)
            else:
                # Create empty system info frame for later updates
                popup.system_info_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
                popup.system_info_frame.pack(fill="x", pady=3)
            if system_info and system_info.get("description"):
                info_items.append(("Description:", system_info.get("description")))

            for label, value in info_items:
                row_frame = ctk.CTkFrame(info_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=8)
                row_frame.pack(fill="x", pady=3)
                content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                content_frame.pack(fill="x", padx=15, pady=10)
                ctk.CTkLabel(content_frame, text=label, font=reg_font,
                             text_color=ACCENT_COLOR, width=140, anchor="w").pack(side="left",
                                                                                  anchor="n" if label == "Description:" else "center")
                ctk.CTkLabel(content_frame, text=str(value), font=reg_font,
                             text_color=TEXT_COLOR, anchor="w", wraplength=400).pack(side="left", padx=(10, 0),
                                                                                     anchor="n" if label == "Description:" else "center")

            # Create system info frame for category-specific data if not already created
            if not hasattr(popup, 'system_info_frame'):
                popup.system_info_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
                popup.system_info_frame.pack(fill="x", pady=3)
        elif not system_in_database:
            coords_text = "Unknown"
            if self.system_name == system_name and self.latest_starpos:
                x, y, z = self.latest_starpos
                coords_text = f"X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}"
                distance = (x ** 2 + y ** 2 + z ** 2) ** 0.5
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
        if (system_in_database and systems_check.data) or system_info:
            all_images = []

            # Get preset images - use display_category if available, otherwise use all categories
            if display_category and display_category != category:
                # Show only images for the selected category
                preset_images = get_preset_images_for_categories([display_category])
                all_images.extend(preset_images)
            elif system_in_database and combined_system_data:
                if combined_system_data.get("_individual_categories"):
                    preset_images = get_preset_images_for_categories(combined_system_data["_individual_categories"])
                    all_images.extend(preset_images)
                else:
                    # Fallback to old method for backward compatibility
                    category_name = combined_system_data.get("category", "")
                    preset_img_url = get_category_images().get(category_name)
                    if preset_img_url:
                        all_images.append(("Example Image", preset_img_url))

            # Add system-specific images
            if system_info:
                if system_info.get("images"):
                    all_images.append(("System Image", system_info.get("images")))
            if system_info and system_info.get("additional_images"):
                try:
                    additional_imgs = json.loads(system_info["additional_images"])
                    for idx, img_url in enumerate(additional_imgs):
                        all_images.append((f"Additional Image {idx + 1}", img_url))
                except Exception as e:
                    print(f"Error parsing additional images: {e}")
            if all_images:
                img_section = ctk.CTkFrame(info_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=8)
                img_section.pack(fill="x", pady=(10, 3))
                img_content = ctk.CTkFrame(img_section, fg_color="transparent")
                img_content.pack(fill="both", expand=True, padx=15, pady=10)
                ctk.CTkLabel(img_content, text="Images:", font=reg_font,
                             text_color=ACCENT_COLOR, width=140, anchor="w").pack(anchor="nw")
                imgs_scroll = ctk.CTkScrollableFrame(img_content, fg_color="#0f0f0f",
                                                     corner_radius=8, height=min(400, 250 * len(all_images)))
                imgs_scroll.pack(fill="both", expand=True, pady=(5, 0))

                popup._system_images_scroll = imgs_scroll
                for img_label, img_url in all_images:
                    single_img_frame = ctk.CTkFrame(imgs_scroll, fg_color="#1a1a1a", corner_radius=6)
                    single_img_frame.pack(fill="x", pady=5, padx=5)
                    header_frame = ctk.CTkFrame(single_img_frame, fg_color="transparent")
                    header_frame.pack(fill="x", padx=10, pady=(10, 5))
                    ctk.CTkLabel(header_frame, text=img_label,
                                 font=ctk.CTkFont(size=12, weight="bold"),
                                 text_color="#888888").pack(side="left")
                    img_container = ctk.CTkFrame(single_img_frame, fg_color="#0f0f0f",
                                                 corner_radius=4, height=220)
                    img_container.pack(fill="x", padx=10, pady=(0, 10))
                    img_container.pack_propagate(False)
                    loading_lbl = ctk.CTkLabel(img_container, text="Loading...",
                                               font=ctk.CTkFont(size=12),
                                               text_color="#666666")
                    loading_lbl.pack(expand=True)

                    def load_combined_img(url, container, lbl):
                        photo = load_image_from_url(url, size=(500, 200))
                        if photo and container.winfo_exists():
                            container.after(0, lambda photo=photo, container=container, lbl=lbl,
                                                      url=url: show_combined_img(container, photo, lbl, url))

                    def show_combined_img(container, photo, lbl, url):
                        if container.winfo_exists():
                            lbl.destroy()
                            img_lbl = ctk.CTkLabel(container, image=photo, text="")
                            img_lbl.pack(expand=True, pady=10)
                            img_lbl.photo = photo
                            display_text = "Image loaded successfully"
                            if "imgur.com" in url:
                                display_text = "Imgur image"
                            elif "supabase.co" in url:
                                display_text = "Supabase Storage image"
                            elif "discord" in url:
                                display_text = "Discord image"
                            elif url.startswith("data:"):
                                display_text = "Database stored image"

                            url_label = ctk.CTkLabel(container, text=display_text,
                                                     font=ctk.CTkFont(size=10),
                                                     text_color="lightblue",
                                                     cursor="hand2",
                                                     wraplength=480)
                            url_label.pack(pady=(0, 10))
                            import webbrowser
                            url_label.bind("<Button-1>", lambda e, url=url: webbrowser.open(url))

                    threading.Thread(target=load_combined_img,
                                     args=(img_url, img_container, loading_lbl),
                                     daemon=True).start()

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
                if poi_data.get("poi_description"):
                    poi_items.append(("Description:", poi_data.get("poi_description")))
                for label, value in poi_items:
                    row_frame = ctk.CTkFrame(poi_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=8)
                    row_frame.pack(fill="x", pady=3)
                    content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                    content_frame.pack(fill="x", padx=15, pady=10)
                    ctk.CTkLabel(content_frame, text=label, font=reg_font,
                                 text_color=ACCENT_COLOR, width=140, anchor="w").pack(side="left",
                                                                                      anchor="n" if label == "Description:" else "center")
                    ctk.CTkLabel(content_frame, text=str(value), font=reg_font,
                                 text_color=TEXT_COLOR, anchor="w", wraplength=400).pack(side="left", padx=(10, 0),
                                                                                         anchor="n" if label == "Description:" else "center")
                all_images = []

                # Add POI-specific images first
                if poi_data and poi_data.get("image_path"):
                    all_images.append(("POI Image", poi_data.get("image_path")))

                # Add system-specific images
                if system_info and system_info.get("images"):
                    all_images.append(("System Image", system_info.get("images")))

                # Get preset images - use display_category if available, otherwise use all categories (only if no POI data)
                if not poi_data:
                    if display_category and display_category != category:
                        # Show only images for the selected category
                        preset_images = get_preset_images_for_categories([display_category])
                        all_images.extend(preset_images)
                    elif system_in_database and combined_system_data:
                        if combined_system_data.get("_individual_categories"):
                            preset_images = get_preset_images_for_categories(
                                combined_system_data["_individual_categories"])
                            all_images.extend(preset_images)
                        else:
                            # Fallback to old method for backward compatibility
                            category_name = combined_system_data.get("category", "")
                            preset_img_url = get_category_images().get(category_name)
                            if preset_img_url:
                                all_images.append(("Example Image", preset_img_url))
                if system_info and system_info.get("additional_images"):
                    try:
                        additional_imgs = json.loads(system_info["additional_images"])
                        for idx, img_url in enumerate(additional_imgs):
                            all_images.append((f"Additional Image {idx + 1}", img_url))
                    except Exception as e:
                        print(f"Error parsing additional images: {e}")
                if all_images:
                    img_section = ctk.CTkFrame(poi_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=8)
                    img_section.pack(fill="x", pady=(10, 3))
                    img_content = ctk.CTkFrame(img_section, fg_color="transparent")
                    img_content.pack(fill="both", expand=True, padx=15, pady=10)
                    ctk.CTkLabel(img_content, text="Images:", font=reg_font,
                                 text_color=ACCENT_COLOR, width=140, anchor="w").pack(anchor="nw")
                    imgs_scroll = ctk.CTkScrollableFrame(img_content, fg_color="#0f0f0f",
                                                         corner_radius=8, height=min(400, 250 * len(all_images)))
                    imgs_scroll.pack(fill="both", expand=True, pady=(5, 0))

                    popup._poi_images_scroll = imgs_scroll
                    for img_label, img_url in all_images:
                        single_img_frame = ctk.CTkFrame(imgs_scroll, fg_color="#1a1a1a", corner_radius=6)
                        single_img_frame.pack(fill="x", pady=5, padx=5)
                        header_frame = ctk.CTkFrame(single_img_frame, fg_color="transparent")
                        header_frame.pack(fill="x", padx=10, pady=(10, 5))
                        ctk.CTkLabel(header_frame, text=img_label,
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color="#888888").pack(side="left")
                        img_container = ctk.CTkFrame(single_img_frame, fg_color="#0f0f0f",
                                                     corner_radius=4, height=220)
                        img_container.pack(fill="x", padx=10, pady=(0, 10))
                        img_container.pack_propagate(False)
                        loading_lbl = ctk.CTkLabel(img_container, text="Loading...",
                                                   font=ctk.CTkFont(size=12),
                                                   text_color="#666666")
                        loading_lbl.pack(expand=True)

                        def load_combined_img(url, container, lbl):
                            photo = load_image_from_url(url, size=(500, 200))
                            if photo and container.winfo_exists():
                                container.after(0, lambda photo=photo, container=container, lbl=lbl,
                                                          url=url: show_combined_img(container, photo, lbl, url))

                        def show_combined_img(container, photo, lbl, url):
                            if container.winfo_exists():
                                lbl.destroy()
                                img_lbl = ctk.CTkLabel(container, image=photo, text="")
                                img_lbl.pack(expand=True, pady=10)
                                img_lbl.photo = photo
                                display_text = "Image loaded successfully"
                                if "imgur.com" in url:
                                    display_text = "Imgur image"
                                elif "supabase.co" in url:
                                    display_text = "Supabase Storage image"
                                elif "discord" in url:
                                    display_text = "Discord image"
                                elif url.startswith("data:"):
                                    display_text = "Database stored image"

                                url_label = ctk.CTkLabel(container, text=display_text,
                                                         font=ctk.CTkFont(size=10),
                                                         text_color="lightblue",
                                                         cursor="hand2",
                                                         wraplength=480)
                                url_label.pack(pady=(0, 10))
                                import webbrowser
                                url_label.bind("<Button-1>", lambda e, url=url: webbrowser.open(url))

                        threading.Thread(target=load_combined_img,
                                         args=(img_url, img_container, loading_lbl),
                                         daemon=True).start()


            else:
                ctk.CTkLabel(poi_frame, text="No POI data available yet",
                             font=reg_font, text_color="gray").pack(pady=20)
        # Claim section - available for both database and non-database systems
        claim_frame = ctk.CTkFrame(info_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
        claim_frame.pack(fill="x", pady=(20, 10))
        ctk.CTkLabel(claim_frame, text="Claim Status",
                     font=bold_font, text_color=ACCENT_COLOR).pack(pady=(15, 10))

        if claim_data:
            visited_text = "Yes" if claim_data.get("visited", False) else "No"
            if claim_data.get("by_cmdr") == self.cmdr_name:
                if journal_visited and claim_data.get("visited", False):
                    visited_text = "Yes (Journal verified)"
                elif journal_visited and not claim_data.get("visited", False):
                    visited_text = "No (Found in journals!)"

            claim_items = [
                ("Status:", "CLAIMED"),
                ("Claimed by:", claim_data.get("by_cmdr", "Unknown")),
                ("Visited:", visited_text),
                ("Claim Date:",
                 claim_data.get("created_at", "Unknown")[:10] if claim_data.get("created_at") else "Unknown")
            ]
            for label, value in claim_items:
                row_frame = ctk.CTkFrame(claim_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2, padx=20)
                ctk.CTkLabel(row_frame, text=label, font=reg_font,
                             text_color=ACCENT_COLOR, width=120, anchor="w").pack(side="left")
                ctk.CTkLabel(row_frame, text=str(value), font=reg_font,
                             text_color=TEXT_COLOR, anchor="w").pack(side="left", padx=(10, 0))

            if journal_visited and not claim_data.get("visited", False) and claim_data.get("by_cmdr") == self.cmdr_name:
                auto_detect_frame = ctk.CTkFrame(claim_frame, fg_color="#2d5a2d", corner_radius=8)
                auto_detect_frame.pack(fill="x", pady=(10, 5), padx=20)
                ctk.CTkLabel(auto_detect_frame,
                             text="System found in your journals! Click 'Mark as Visited' to update.",
                             font=ctk.CTkFont(size=12), text_color="#90EE90").pack(pady=8, padx=10)

            if claim_data.get("by_cmdr") == self.cmdr_name:
                btn_frame = ctk.CTkFrame(claim_frame, fg_color="transparent")
                btn_frame.pack(pady=(10, 15))
                if not claim_data.get("done", False):
                    ctk.CTkButton(btn_frame, text="Unclaim System",
                                  command=lambda: self.unclaim_system(system_name, popup),
                                  fg_color="#dc3545", hover_color="#c82333").pack(side="left", padx=5)
                if not claim_data.get("visited", False):
                    ctk.CTkButton(btn_frame, text="Mark as Visited",
                                  command=lambda: self.mark_visited(system_name, popup),
                                  fg_color="#28a745", hover_color="#218838").pack(side="left", padx=5)
                else:
                    ctk.CTkButton(btn_frame, text="Unmark Visited",
                                  command=lambda: self.unmark_visited(system_name, popup),
                                  fg_color="#ffc107", hover_color="#e0a800").pack(side="left", padx=5)
                if not claim_data.get("done", False):
                    ctk.CTkButton(btn_frame, text="Mark as Done",
                                  command=lambda: self.mark_done(system_name, popup),
                                  fg_color="#6f42c1", hover_color="#5a32a3").pack(side="left", padx=5)
                else:
                    ctk.CTkLabel(btn_frame, text="Completed",
                                 font=ctk.CTkFont(size=14, weight="bold"),
                                 text_color="#6f42c1").pack(side="left", padx=5)
            else:
                ctk.CTkLabel(claim_frame, text="System claimed by another commander",
                             font=reg_font, text_color="orange").pack(pady=(10, 15))
        else:
            # System is unclaimed - show appropriate status and claim button
            if system_in_database:
                status_text = "UNCLAIMED"
                status_color = "green"
                info_text = "This system is in the records database and available to claim."
            else:
                status_text = "NEW DISCOVERY"
                status_color = "#FFD700"  # Gold color for new discoveries
                info_text = "This system is not in the records database. Claiming it will add it as a new discovery!"

            status_frame = ctk.CTkFrame(claim_frame, fg_color="transparent")
            status_frame.pack(fill="x", pady=10, padx=20)

            ctk.CTkLabel(status_frame, text=status_text,
                         font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=status_color).pack()

            ctk.CTkLabel(status_frame, text=info_text,
                         font=ctk.CTkFont(size=11),
                         text_color=TEXT_SECONDARY,
                         wraplength=400).pack(pady=(5, 0))

            # Check if we have coordinates for claiming
            has_coords = False
            if self.system_name == system_name and self.latest_starpos:
                has_coords = True
                coord_text = f"Will use current position: {self.latest_starpos[0]:.1f}, {self.latest_starpos[1]:.1f}, {self.latest_starpos[2]:.1f}"
            elif not system_in_database:
                coord_text = "⚠️ No coordinates available - visit this system first to claim it"
            else:
                has_coords = True
                coord_text = "Will use database coordinates"

            if not system_in_database:
                coord_info = ctk.CTkLabel(claim_frame, text=coord_text,
                                          font=ctk.CTkFont(size=10),
                                          text_color="#FFD700" if has_coords else "#FF6B6B")
                coord_info.pack(pady=(0, 10))

            if has_coords or system_in_database:
                ctk.CTkButton(claim_frame,
                              text="Claim System as Discovery" if not system_in_database else "Claim System",
                              command=lambda: self.claim_system_new_discovery(system_name,
                                                                              popup) if not system_in_database else self.claim_system(
                                  system_name, popup),
                              fg_color="#FFD700" if not system_in_database else "#28a745",
                              hover_color="#E6C200" if not system_in_database else "#218838",
                              text_color="#000000" if not system_in_database else "#FFFFFF",
                              font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0, 15))
            else:
                disabled_btn = ctk.CTkButton(claim_frame, text="Visit System First to Claim",
                                             state="disabled",
                                             fg_color="#666666",
                                             font=ctk.CTkFont(size=14, weight="bold"))
                disabled_btn.pack(pady=(0, 15))
        edit_frame = ctk.CTkScrollableFrame(edit_tab, fg_color="transparent")
        edit_frame.pack(fill="both", expand=True, padx=10, pady=10)
        header_frame = ctk.CTkFrame(edit_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text=f"Edit: {system_name}",
                     font=bold_font, text_color=ACCENT_COLOR).pack(pady=15)
        ctk.CTkFrame(edit_frame, height=2, fg_color="#333333").pack(fill="x", pady=10)

        def open_system_editor():
            sys_window = ctk.CTkToplevel(popup)
            sys_window.title("System Information Editor")
            sys_window.geometry("800x700")
            sys_window.transient(popup)
            sys_window.grab_set()
            sys_window.configure(fg_color=MAIN_BG_COLOR)
            sys_window.attributes("-topmost", True)
            sys_window.lift()
            sys_window.focus_force()
            sys_window.after(300, lambda: sys_window.attributes("-topmost", False))
            sys_frame = ctk.CTkScrollableFrame(sys_window, fg_color="transparent")
            sys_frame.pack(fill="both", expand=True, padx=20, pady=20)
            header = ctk.CTkFrame(sys_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
            header.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(header, text="System Information Editor",
                         font=bold_font, text_color=ACCENT_COLOR).pack(pady=15)
            fields_frame = ctk.CTkFrame(sys_frame, fg_color=CARD_BG_COLOR, corner_radius=10)
            fields_frame.pack(fill="x", pady=10)
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
            cat_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            cat_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(cat_frame, text="Categories:",
                         font=reg_font, width=120, anchor="w",
                         text_color=TEXT_COLOR).pack(side="left")

            # Add multi-category entry field
            category_entry_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            category_entry_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(category_entry_frame, text="Edit Categories:",
                         font=reg_font, width=120, anchor="w",
                         text_color=TEXT_COLOR).pack(side="left", anchor="n")

            category_entry = ctk.CTkEntry(category_entry_frame, width=400, height=40,
                                          fg_color=SECONDARY_BG_COLOR, border_color="#444444",
                                          text_color=TEXT_COLOR,
                                          placeholder_text="Use dropdown below to edit categories",
                                          state="readonly")
            category_entry.pack(side="left", padx=(10, 0))

            # Pre-populate with existing categories
            if system_in_database and systems_check and systems_check.data:
                existing_categories = combined_system_data.get("category", "") if combined_system_data else ""
                if existing_categories:
                    parsed_cats = parse_categories(existing_categories)
                    category_entry.insert(0, ", ".join(parsed_cats))

            ctk.CTkLabel(category_entry_frame, text="Separate multiple categories with commas",
                         font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w", pady=(5, 0))
            # Multi-category system info editor
            system_categories = []
            if system_in_database and systems_check and systems_check.data:
                if combined_system_data and combined_system_data.get("_individual_categories"):
                    system_categories = combined_system_data["_individual_categories"]
                else:
                    # Single category system
                    single_cat = combined_system_data.get("category", None) if combined_system_data else None
                    if single_cat:
                        system_categories = [single_cat]

            # Multi-category system info editing section
            multi_cat_info_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            multi_cat_info_frame.pack(fill="x", pady=10, padx=20)

            # Category dropdown for system info editing
            ctk.CTkLabel(multi_cat_info_frame, text="Edit System Info:",
                         font=reg_font, width=120, anchor="n",
                         text_color=TEXT_COLOR).pack(side="left", anchor="n")

            cat_info_container = ctk.CTkFrame(multi_cat_info_frame, fg_color="transparent")
            cat_info_container.pack(side="left", padx=(10, 0), fill="x", expand=True)

            # Category selector dropdown
            cat_selector_frame = ctk.CTkFrame(cat_info_container, fg_color="transparent")
            cat_selector_frame.pack(fill="x", pady=(0, 10))

            ctk.CTkLabel(cat_selector_frame, text="Select Category:",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT_COLOR).pack(side="left")

            # Build category options
            category_options = []
            if system_categories:
                category_options.extend(system_categories)
            category_options.append("Create New Category...")

            selected_category = ctk.StringVar(
                value=category_options[0] if category_options else "Create New Category...")

            category_dropdown = ctk.CTkComboBox(cat_selector_frame,
                                                values=category_options,
                                                variable=selected_category,
                                                width=200,
                                                fg_color=SECONDARY_BG_COLOR,
                                                border_color="#444444",
                                                button_color="#444444",
                                                button_hover_color="#555555",
                                                dropdown_fg_color=SECONDARY_BG_COLOR,
                                                dropdown_text_color=TEXT_COLOR,
                                                text_color=TEXT_COLOR)
            category_dropdown.pack(side="left", padx=(10, 0))

            # Delete category button
            delete_cat_btn = ctk.CTkButton(cat_selector_frame, text="Delete Category",
                                           width=120, height=32,
                                           fg_color="#dc3545", hover_color="#c82333",
                                           text_color="#FFFFFF",
                                           font=ctk.CTkFont(size=11, weight="bold"))
            delete_cat_btn.pack(side="left", padx=(10, 0))

            # Custom category name entry (initially hidden)
            custom_cat_frame = ctk.CTkFrame(cat_info_container, fg_color="transparent")
            custom_cat_entry = ctk.CTkEntry(custom_cat_frame,
                                            placeholder_text="Enter new category name...",
                                            width=200,
                                            fg_color=SECONDARY_BG_COLOR,
                                            border_color="#444444",
                                            text_color=TEXT_COLOR)
            custom_cat_entry.pack(side="left")

            # System info textbox
            cat_info_text = ctk.CTkTextbox(cat_info_container, width=400, height=100,
                                           fg_color=SECONDARY_BG_COLOR,
                                           border_color="#444444", text_color=TEXT_COLOR)
            cat_info_text.pack(fill="x", pady=(10, 0))

            # Load initial system info data
            def load_category_info(category_name):
                """Load system info for the selected category"""
                cat_info_text.delete("1.0", "end")
                if category_name and category_name != "Create New Category...":
                    # Get category-specific table data
                    current_cat_info = self.get_category_table_data(system_name, category_name)
                    if current_cat_info:
                        cat_info_text.insert("1.0", current_cat_info)

            def on_category_change(*args):
                """Handle category dropdown change"""
                selected = selected_category.get()
                if selected == "Create New Category...":
                    custom_cat_frame.pack(fill="x", pady=(5, 0))
                    custom_cat_entry.focus()
                    cat_info_text.delete("1.0", "end")
                else:
                    custom_cat_frame.pack_forget()
                    load_category_info(selected)

            selected_category.trace('w', on_category_change)

            # Load initial data
            if category_options and category_options[0] != "Create New Category...":
                load_category_info(category_options[0])

            def get_selected_category_name():
                """Get the currently selected or custom category name"""
                if selected_category.get() == "Create New Category...":
                    custom_name = custom_cat_entry.get().strip()
                    if custom_name:
                        print(f"[DEBUG] Using custom category name: '{custom_name}'")
                        return custom_name
                    else:
                        print(f"[WARNING] No custom category name entered, using default")
                        return "New Category"
                selected = selected_category.get()
                print(f"[DEBUG] Using selected category: '{selected}'")
                return selected

            def get_system_info_text():
                """Get the current system info text"""
                return cat_info_text.get("1.0", "end-1c").strip()

            def refresh_category_dropdown():
                """Refresh the category dropdown with latest categories"""
                try:
                    # Get fresh category data from database
                    fresh_systems_check = supabase.table("systems").select("*").eq("systems", system_name).execute()
                    if fresh_systems_check.data:
                        fresh_combined_data = combine_system_entries(fresh_systems_check.data, system_name)
                        if fresh_combined_data and fresh_combined_data.get("_individual_categories"):
                            fresh_categories = fresh_combined_data["_individual_categories"]
                            fresh_options = fresh_categories + ["Create New Category..."]
                            category_dropdown.configure(values=fresh_options)

                            # Update the category entry field to show all categories
                            category_entry.configure(state="normal")
                            category_entry.delete(0, 'end')
                            category_entry.insert(0, ", ".join(fresh_categories))
                            category_entry.configure(state="readonly")

                            # Update the current selection if needed
                            current_selection = selected_category.get()
                            if current_selection not in fresh_options:
                                selected_category.set(fresh_options[0] if fresh_options else "Create New Category...")

                except Exception as e:
                    pass  # Error handling for refresh

            def delete_category():
                """Delete the currently selected category"""
                current_cat = selected_category.get()
                if current_cat and current_cat != "Create New Category...":
                    # Confirm deletion
                    result = messagebox.askyesno("Delete Category",
                                                 f"Are you sure you want to remove '{current_cat}' from this system?\n\nThis will remove it from the category list and delete all associated category data.",
                                                 parent=sys_window)
                    if result:
                        try:
                            print(f"[DEBUG] Deleting category '{current_cat}' from system '{system_name}'")

                            # Get current categories
                            current_categories = []
                            if system_in_database and systems_check.data:
                                if combined_system_data and combined_system_data.get("_individual_categories"):
                                    current_categories = combined_system_data["_individual_categories"].copy()
                                elif combined_system_data and combined_system_data.get("category"):
                                    current_categories = parse_categories(combined_system_data["category"])

                            # Remove the category
                            if current_cat in current_categories:
                                current_categories.remove(current_cat)
                                print(f"[DEBUG] Remaining categories after removal: {current_categories}")

                                # STEP 1: Remove from system_category_info table
                                try:
                                    cat_info_result = supabase.table("system_category_info").delete().eq("system_name",
                                                                                                         system_name).eq(
                                        "category", current_cat).execute()
                                    print(
                                        f"[DEBUG] Removed {len(cat_info_result.data) if cat_info_result.data else 0} category info records")
                                except Exception as cat_e:
                                    print(f"[DEBUG] Error removing from system_category_info: {cat_e}")

                                # STEP 2: Update the systems table
                                if len(current_categories) > 1:
                                    formatted_categories = format_categories_for_storage(current_categories)
                                elif len(current_categories) == 1:
                                    formatted_categories = current_categories[0]
                                else:
                                    formatted_categories = None

                                if formatted_categories:
                                    systems_result = supabase.table("systems").update(
                                        {"category": formatted_categories}).eq("systems", system_name).execute()
                                    print(
                                        f"[DEBUG] Updated systems table: {len(systems_result.data) if systems_result.data else 0} records")

                                    # Refresh the dropdown and UI
                                    refresh_category_dropdown()

                                    # Refresh the main popup to update category count
                                    if hasattr(self, 'current_system_popup') and self.current_system_popup:
                                        self._refresh_system_popup(system_name, current_categories[
                                            0] if current_categories else None)

                                    # Refresh all category displays
                                    self.refresh_all_category_displays(system_name)

                                    messagebox.showinfo("Success", f"Category '{current_cat}' deleted successfully!",
                                                        parent=sys_window)
                                else:
                                    messagebox.showwarning("Cannot Delete",
                                                           "Cannot delete the last category from a system.",
                                                           parent=sys_window)
                            else:
                                print(
                                    f"[DEBUG] Category '{current_cat}' not found in current categories: {current_categories}")
                                messagebox.showwarning("Category Not Found",
                                                       f"Category '{current_cat}' was not found in the system's category list.",
                                                       parent=sys_window)

                        except Exception as e:
                            print(f"[ERROR] Failed to delete category '{current_cat}': {e}")
                            import traceback
                            traceback.print_exc()
                            messagebox.showerror("Error", f"Failed to delete category: {e}", parent=sys_window)

            # Connect delete button
            delete_cat_btn.configure(command=delete_category)

            # Store references for save function
            cat_info_widgets = {
                'dropdown': category_dropdown,
                'custom_entry': custom_cat_entry,
                'textbox': cat_info_text,
                'get_category': get_selected_category_name,
                'get_info': get_system_info_text,
                'refresh_dropdown': refresh_category_dropdown
            }
            preset_image_url = None
            if system_in_database:
                category_text = "Unknown"
                if systems_check.data:
                    category_text = combined_system_data.get("category",
                                                             "Unknown") if combined_system_data else "Unknown"
                    if category_text in get_category_images():
                        preset_image_url = get_category_images()[category_text]
                cat_label = ctk.CTkLabel(cat_frame, text=category_text,
                                         font=reg_font, fg_color=SECONDARY_BG_COLOR,
                                         corner_radius=5, width=400, anchor="w",
                                         text_color="#888888")
                cat_label.pack(side="left", padx=(10, 0), ipady=5, ipadx=10)
                cat_dropdown = None
            else:
                categories = []
                if supabase:
                    try:
                        cat_response = supabase.table("systems").select("category").execute()
                        if cat_response.data:
                            categories = sorted(
                                list(set(item["category"] for item in cat_response.data if item["category"])))
                    except:
                        categories = []
                if not categories:
                    categories = ["No categories available"]
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
                if system_info and system_info.get("category") and not system_in_database:
                    if cat_dropdown:
                        cat_dropdown.set(system_info["category"])
                ctk.CTkLabel(cat_frame, text="(Editable for unrecorded systems)",
                             font=ctk.CTkFont(size=10), text_color="#666666").pack(side="left", padx=(10, 0))
            img_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            img_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(img_frame, text="Image URL:",
                         font=reg_font, width=120, anchor="w",
                         text_color=TEXT_COLOR).pack(side="left")

            img_input_frame = ctk.CTkFrame(img_frame, fg_color="transparent")
            img_input_frame.pack(side="left", padx=(10, 0))

            # Add explanation for new discoveries
            if not system_in_database:
                img_info_frame = ctk.CTkFrame(fields_frame, fg_color="#2d4a2d", corner_radius=8)
                img_info_frame.pack(fill="x", pady=(5, 10), padx=20)
                ctk.CTkLabel(img_info_frame, text="💡 New Discovery Tip:",
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color="#90EE90").pack(anchor="w", padx=10, pady=(8, 2))
                ctk.CTkLabel(img_info_frame,
                             text="The first image will be displayed as the background in 'Nearest Systems' cards.",
                             font=ctk.CTkFont(size=10),
                             text_color="#CCCCCC",
                             wraplength=600).pack(anchor="w", padx=10, pady=(0, 8))

            image_entry = ctk.CTkEntry(img_input_frame, width=300,
                                       placeholder_text="e.g., https://i.imgur.com/example.jpg",
                                       fg_color=SECONDARY_BG_COLOR, border_color="#444444",
                                       text_color=TEXT_COLOR)
            image_entry.pack(side="left")

            def upload_image():
                file_path = filedialog.askopenfilename(
                    parent=sys_window,
                    title="Select Image to Upload",
                    filetypes=[
                        ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                        ("All files", "*.*")
                    ]
                )
                if file_path:
                    upload_btn.configure(text="Uploading...", state="disabled")
                    sys_window.update()

                    def do_upload():
                        try:
                            url = upload_to_imgur(file_path)
                            if url:
                                sys_window.after(0, lambda: image_entry.delete(0, 'end'))
                                sys_window.after(0, lambda: image_entry.insert(0, url))
                                sys_window.after(0, lambda: upload_btn.configure(text="Uploaded", state="normal",
                                                                                 fg_color="#4CAF50"))
                                sys_window.after(2000, lambda: upload_btn.configure(text="Upload", fg_color="#17a2b8"))
                            else:
                                sys_window.after(0, lambda: upload_btn.configure(text="Upload Failed", state="normal",
                                                                                 fg_color="#dc3545"))
                                sys_window.after(3000, lambda: upload_btn.configure(text="Upload", fg_color="#17a2b8"))

                                def show_upload_help():
                                    help_popup = ctk.CTkToplevel(sys_window)
                                    help_popup.title("Upload Failed - Manual Options")
                                    help_popup.geometry("400x300")
                                    help_popup.transient(sys_window)
                                    help_popup.configure(fg_color=MAIN_BG_COLOR)

                                    ctk.CTkLabel(help_popup, text="Upload Failed",
                                                 font=ctk.CTkFont(size=16, weight="bold"),
                                                 text_color="#dc3545").pack(pady=10)

                                    help_text = """Your system may have SSL connectivity issues.

Try these manual options:

1. Upload to Imgur manually:
   Go to imgur.com/upload
   Upload your image
   Copy the image URL and paste it

2. Use Discord:
   Upload to any Discord channel
   Right-click and Copy link
   Paste the URL"""

                                    ctk.CTkLabel(help_popup, text=help_text,
                                                 font=ctk.CTkFont(size=12),
                                                 text_color=TEXT_COLOR,
                                                 justify="left").pack(padx=20, pady=10)

                                    ctk.CTkButton(help_popup, text="Open Imgur",
                                                  command=lambda: os.system("start https://imgur.com/upload"),
                                                  fg_color="#4CAF50").pack(pady=5)

                                    ctk.CTkButton(help_popup, text="Close",
                                                  command=help_popup.destroy,
                                                  fg_color="#6c757d").pack(pady=5)

                                sys_window.after(100, show_upload_help)
                        except Exception as e:
                            print(f"Upload error: {e}")
                            sys_window.after(0, lambda: upload_btn.configure(text="Upload Failed", state="normal",
                                                                             fg_color="#dc3545"))
                            sys_window.after(3000, lambda: upload_btn.configure(text="Upload", fg_color="#17a2b8"))

                    threading.Thread(target=do_upload, daemon=True).start()

            upload_btn = ctk.CTkButton(img_input_frame, text="Upload", width=90,
                                       command=upload_image,
                                       fg_color="#17a2b8", hover_color="#138496")
            upload_btn.pack(side="left", padx=(5, 0))

            def open_upload_help():
                help_window = ctk.CTkToplevel(sys_window)
                help_window.title("Image Upload Help")
                help_window.geometry("500x400")
                help_window.transient(sys_window)
                help_window.configure(fg_color=MAIN_BG_COLOR)

                ctk.CTkLabel(help_window, text="Image Upload Options",
                             font=ctk.CTkFont(size=18, weight="bold"),
                             text_color=ACCENT_COLOR).pack(pady=20)

                help_text = """RECOMMENDED: Use Upload Button
• Click Upload to upload - tries external services first
• Images uploaded this way are visible to ALL users
• Fallback to database storage if external services fail

Manual Upload Options:

Option 1: Manual Upload to Imgur
1. Go to https://imgur.com/upload
2. Upload your image there
3. Right-click the image and "Copy image address"
4. Paste the URL in the Image URL field

Option 2: Use Discord
1. Upload image to any Discord channel
2. Right-click the image and "Copy link"
3. Paste the URL in the Image URL field

Note: Only images uploaded through the app
or via public URLs will be visible to other users."""

                ctk.CTkLabel(help_window, text=help_text,
                             font=ctk.CTkFont(size=12),
                             text_color=TEXT_COLOR,
                             justify="left").pack(padx=20, pady=20)

                ctk.CTkButton(help_window, text="Open Imgur Upload",
                              command=lambda: os.system("start https://imgur.com/upload"),
                              fg_color="#4CAF50").pack(pady=10)

                ctk.CTkButton(help_window, text="Close",
                              command=help_window.destroy,
                              fg_color="#6c757d").pack(pady=5)

            help_btn = ctk.CTkButton(img_input_frame, text="?", width=30,
                                     command=open_upload_help,
                                     fg_color="#6c757d", hover_color="#5a6268")
            help_btn.pack(side="left", padx=(5, 0))

            if system_info and "images" in system_info:
                if system_info.get("images"):
                    image_entry.insert(0, system_info["images"])
            elif preset_image_url and not system_info:
                image_entry.insert(0, preset_image_url)
            additional_imgs_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            additional_imgs_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(additional_imgs_frame, text="Additional Images:",
                         font=reg_font, width=120, anchor="w",
                         text_color=TEXT_COLOR).pack(side="left", anchor="n")
            imgs_container = ctk.CTkFrame(additional_imgs_frame, fg_color="transparent")
            imgs_container.pack(side="left", fill="x", expand=True, padx=(10, 0))
            additional_entries = []
            existing_additional = []
            if system_info and system_info.get("additional_images"):
                try:
                    existing_additional = json.loads(system_info["additional_images"])
                except:
                    existing_additional = []

            def add_image_entry(initial_value=""):
                entry_frame = ctk.CTkFrame(imgs_container, fg_color="transparent")
                entry_frame.pack(fill="x", pady=2)
                entry = ctk.CTkEntry(entry_frame, width=250, placeholder_text="https://i.imgur.com/...",
                                     fg_color=SECONDARY_BG_COLOR, border_color="#444444",
                                     text_color=TEXT_COLOR)
                entry.pack(side="left")
                if initial_value:
                    entry.insert(0, initial_value)

                def upload_additional():
                    file_path = filedialog.askopenfilename(
                        parent=sys_window,
                        title="Select Image to Upload",
                        filetypes=[
                            ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                            ("All files", "*.*")
                        ]
                    )
                    if file_path:
                        upload_mini_btn.configure(text="...", state="disabled")

                        def do_upload():
                            try:
                                url = upload_to_imgur(file_path)
                                if url:
                                    sys_window.after(0, lambda: entry.delete(0, 'end'))
                                    sys_window.after(0, lambda: entry.insert(0, url))
                                    sys_window.after(0, lambda: upload_mini_btn.configure(text="UP", state="normal"))
                                else:
                                    sys_window.after(0, lambda: upload_mini_btn.configure(text="X", state="normal"))
                                    sys_window.after(2000, lambda: upload_mini_btn.configure(text="UP"))
                            except Exception as e:
                                print(f"Additional upload error: {e}")
                                sys_window.after(0, lambda: upload_mini_btn.configure(text="X", state="normal"))
                                sys_window.after(2000, lambda: upload_mini_btn.configure(text="UP"))

                        threading.Thread(target=do_upload, daemon=True).start()

                upload_mini_btn = ctk.CTkButton(entry_frame, text="UP", width=30,
                                                command=upload_additional,
                                                fg_color="#17a2b8", hover_color="#138496")
                upload_mini_btn.pack(side="left", padx=(5, 0))

                remove_btn = ctk.CTkButton(entry_frame, text="X", width=30,
                                           fg_color="#dc3545", hover_color="#c82333",
                                           command=lambda: remove_entry(entry_frame, entry))
                remove_btn.pack(side="left", padx=(5, 0))
                additional_entries.append(entry)

            def remove_entry(frame, entry):
                additional_entries.remove(entry)
                frame.destroy()

            for img_url in existing_additional:
                add_image_entry(img_url)
            add_img_btn = ctk.CTkButton(imgs_container, text="+ Add Another Image",
                                        fg_color="#28a745", hover_color="#218838",
                                        command=lambda: add_image_entry())
            add_img_btn.pack(pady=5)

            def save_system_info():
                if not supabase:
                    messagebox.showerror("Error", "Database not available", parent=sys_window)
                    return
                try:
                    updates = {}
                    name_value = name_entry.get().strip()
                    updates["name"] = name_value if name_value else None
                    sys_desc_value = sys_desc_text.get("1.0", "end-1c").strip()
                    updates["description"] = sys_desc_value if sys_desc_value else None

                    # Handle multi-category system info
                    category_save_success = False
                    new_category_added = False
                    final_selected_category = None

                    if 'cat_info_widgets' in locals():
                        selected_cat = cat_info_widgets['get_category']()
                        cat_info_value = cat_info_widgets['get_info']()

                        print(
                            f"[DEBUG] System info save - selected_cat: '{selected_cat}', cat_info_value length: {len(cat_info_value) if cat_info_value else 0}")

                        # Validate new category name
                        if selected_category.get() == "Create New Category...":
                            custom_name = custom_cat_entry.get().strip()
                            if not custom_name:
                                messagebox.showwarning("Invalid Category", "Please enter a name for the new category!",
                                                       parent=sys_window)
                                return
                            if len(custom_name) < 3:
                                messagebox.showwarning("Invalid Category",
                                                       "Category name must be at least 3 characters long!",
                                                       parent=sys_window)
                                return

                        if selected_cat and cat_info_value:
                            final_selected_category = selected_cat
                            print(f"[DEBUG] Processing category: '{selected_cat}'")
                            print(f"[DEBUG] Full category info being saved:\n{cat_info_value}")

                            # STEP 1: Check if this is a new category (don't modify systems table)
                            existing_categories = []
                            if system_in_database and systems_check.data:
                                if combined_system_data and combined_system_data.get("_individual_categories"):
                                    existing_categories = combined_system_data["_individual_categories"].copy()
                                elif combined_system_data and combined_system_data.get("category"):
                                    existing_categories = parse_categories(combined_system_data["category"])

                            # Check if this is a new category (not in systems table)
                            print(f"[DEBUG] Saving category '{selected_cat}' to system_category_info table...")

                            # Save the category-specific data to system_category_info table ONLY
                            category_save_success = self.save_category_table_data(system_name, selected_cat,
                                                                                  cat_info_value)

                            if category_save_success:
                                print(f"[SUCCESS] Category '{selected_cat}' saved successfully")
                                new_category_added = True
                                final_selected_category = selected_cat
                            else:
                                print(f"[ERROR] Failed to save category '{selected_cat}'")

                            # Also save to system_information table for general access
                            updates["system_info"] = cat_info_value

                    if not system_in_database and cat_dropdown:
                        selected_cat = cat_dropdown.get()
                        if selected_cat and selected_cat != "Custom/Unknown":
                            updates["category"] = selected_cat
                        elif selected_cat == "Custom/Unknown":
                            updates["category"] = "POI System"

                        if self.system_name == system_name and self.latest_starpos:
                            x, y, z = self.latest_starpos

                            # For new systems, also consider any new categories from the system info editor
                            final_categories = []
                            if 'cat_info_widgets' in locals():
                                new_category = cat_info_widgets['get_category']()
                                if new_category and new_category != updates.get("category", "POI System"):
                                    final_categories = [updates.get("category", "POI System"), new_category]
                                else:
                                    final_categories = [updates.get("category", "POI System")]
                            else:
                                final_categories = [updates.get("category", "POI System")]

                            # Format categories for storage
                            formatted_category = format_categories_for_storage(final_categories) if len(
                                final_categories) > 1 else final_categories[0]

                            new_system = {
                                "systems": system_name,
                                "x": x,
                                "y": y,
                                "z": z,
                                "category": formatted_category
                            }
                            try:
                                supabase.table("systems").insert(new_system).execute()
                            except Exception as e:
                                pass  # Error handling for system creation
                    elif system_in_database:
                        # Handle category updates for systems in database
                        if systems_check.data:
                            # Note: Category entry is now read-only and managed via dropdown
                            # Category updates are handled through the multi-category system info editor above
                            # Keep existing category if nothing changed
                            current_category = combined_system_data.get("category",
                                                                        "Unknown") if combined_system_data else "Unknown"
                            updates["category"] = current_category

                    img_url = image_entry.get().strip()
                    updates["images"] = img_url if img_url else None
                    additional_urls = []
                    for entry in additional_entries:
                        url = entry.get().strip()
                        if url:
                            additional_urls.append(url)
                    updates["additional_images"] = json.dumps(additional_urls) if additional_urls else None
                    updates["system"] = system_name

                    # Save to system_information table
                    print(f"[DEBUG] Saving to system_information table...")
                    existing = supabase.table("system_information").select("*").eq("system", system_name).execute()
                    if existing.data:
                        result = supabase.table("system_information").update(updates).eq("system",
                                                                                         system_name).execute()
                        print(f"[DEBUG] Updated system_information: {result}")
                    else:
                        result = supabase.table("system_information").insert(updates).execute()
                        print(f"[DEBUG] Inserted into system_information: {result}")

                    # STEP 3: Refresh everything if changes were made
                    if new_category_added or category_save_success:
                        print(f"[DEBUG] Refreshing UI elements after successful save...")

                        # Refresh the global category list to include the new category
                        self.load_categories()

                        # Refresh the category dropdown in the editor
                        if 'cat_info_widgets' in locals() and 'refresh_dropdown' in cat_info_widgets:
                            cat_info_widgets['refresh_dropdown']()

                        # Refresh all category displays
                        self.refresh_all_category_displays(system_name)

                        # Refresh the main popup to update category count and selector
                        if hasattr(self, 'current_system_popup') and self.current_system_popup:
                            self._refresh_system_popup(system_name, final_selected_category)

                    # Create detailed success message based on what actually happened
                    success_message = "System information saved successfully!"

                    if final_selected_category:
                        success_message += f"\n\nCategory: {final_selected_category}"

                        if new_category_added:
                            success_message += " (NEW CATEGORY ADDED TO SYSTEM)"

                        if category_save_success:
                            success_message += f"\n✓ Category-specific system info saved successfully!"
                        else:
                            success_message += f"\n⚠ Category-specific system info failed to save"
                            success_message += f"\n  (Check console for details)"

                    print(f"[SUCCESS] Save operation completed!")
                    messagebox.showinfo("Success", success_message, parent=sys_window)
                    sys_window.destroy()

                    # Close and reopen the system popup to ensure fresh data if new category was added
                    if new_category_added and final_selected_category:
                        popup.destroy()
                        self.after(100, lambda: self.view_system(system_name, final_selected_category))
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save changes: {e}", parent=sys_window)

            # Test button for debugging
            def test_permissions():
                permissions_ok, msg = self.test_system_category_info_permissions()
                if permissions_ok:
                    messagebox.showinfo("Permission Test", f"✓ SUCCESS: {msg}", parent=sys_window)
                else:
                    messagebox.showerror("Permission Test", f"✗ FAILED: {msg}", parent=sys_window)

            test_btn = ctk.CTkButton(sys_frame, text="Test Database Permissions",
                                     command=test_permissions,
                                     fg_color="#6c757d", hover_color="#5a6268",
                                     height=30)
            test_btn.pack(pady=(0, 10))

            ctk.CTkButton(sys_frame, text="Save System Information",
                          command=save_system_info,
                          fg_color="#007bff", hover_color="#0056b3",
                          height=40).pack(pady=20)

        ctk.CTkButton(edit_frame, text="Edit System Information",
                      command=open_system_editor,
                      fg_color="#6c757d", hover_color="#5a6268",
                      height=40).pack(pady=10)

        def open_poi_editor():
            poi_window = ctk.CTkToplevel(popup)
            poi_window.title("POI Editor")
            poi_window.geometry("700x600")
            poi_window.transient(popup)
            poi_window.grab_set()
            poi_window.configure(fg_color=MAIN_BG_COLOR)
            poi_window.attributes("-topmost", True)
            poi_window.lift()
            poi_window.focus_force()
            poi_window.after(300, lambda: poi_window.attributes("-topmost", False))
            poi_frame = ctk.CTkScrollableFrame(poi_window, fg_color="transparent")
            poi_frame.pack(fill="both", expand=True, padx=20, pady=20)
            header = ctk.CTkFrame(poi_frame, fg_color=SECONDARY_BG_COLOR, corner_radius=10)
            header.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(header, text="POI Editor",
                         font=bold_font, text_color=ACCENT_COLOR).pack(pady=15)
            fields_frame = ctk.CTkFrame(poi_frame, fg_color=CARD_BG_COLOR, corner_radius=10)
            fields_frame.pack(fill="x", pady=10)
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
                if field_key == "system_name":
                    entry = ctk.CTkEntry(row_frame, width=400, fg_color="#1a1a1a",
                                         border_color="#333333", text_color="#888888",
                                         state="readonly")
                    entry.pack(side="left", padx=(10, 0))
                    entry.configure(state="normal")
                    entry.insert(0, system_name)
                    entry.configure(state="readonly")
                else:
                    entry = ctk.CTkEntry(row_frame, width=400, fg_color=SECONDARY_BG_COLOR,
                                         border_color="#444444", text_color=TEXT_COLOR)
                    entry.pack(side="left", padx=(10, 0))
                    if poi_data and field_key in poi_data and poi_data[field_key] is not None:
                        entry.insert(0, str(poi_data[field_key]))
                edit_fields[field_key] = entry
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
            poi_type_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            poi_type_frame.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(poi_type_frame, text="POI Type:",
                         font=reg_font, width=120, anchor="w",
                         text_color=TEXT_COLOR).pack(side="left")
            poi_type_var = ctk.StringVar(
                value=poi_data.get("potential_or_poi", "Potential POI") if poi_data else "Potential POI")
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

            def save_poi_info():
                if not supabase:
                    messagebox.showerror("Error", "Database not available", parent=poi_window)
                    return
                try:
                    updates = {}
                    for field_key, widget in edit_fields.items():
                        value = widget.get().strip()
                        if value:
                            updates[field_key] = value
                    coords_fields = ['coords_x', 'coords_y', 'coords_z', 'x', 'y', 'z']
                    for coord_field in coords_fields:
                        if coord_field in updates:
                            del updates[coord_field]
                    updates["potential_or_poi"] = poi_type_var.get()
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
                        self._refresh_system_popup(system_name, category)
                        if hasattr(popup, 'tabview'):
                            popup.tabview.set("System Info")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save changes: {e}", parent=poi_window)

            btn_frame = ctk.CTkFrame(poi_frame, fg_color="transparent")
            btn_frame.pack(pady=20)
            ctk.CTkButton(btn_frame, text="Save POI Information",
                          command=save_poi_info,
                          fg_color="#007bff", hover_color="#0056b3",
                          height=40).pack(side="left", padx=5)
            if poi_data:
                def undo_poi():
                    if messagebox.askyesno("Confirm", "Remove all POI data for this system?", parent=poi_window):
                        try:
                            supabase.table("pois").delete().eq("system_name", system_name).execute()
                            messagebox.showinfo("Success", "POI data removed!", parent=poi_window)
                            poi_window.destroy()
                            self._refresh_system_popup(system_name, category)
                            if hasattr(popup, 'tabview'):
                                popup.tabview.set("System Info")
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to remove POI: {e}", parent=poi_window)

                ctk.CTkButton(btn_frame, text="Remove POI",
                              command=undo_poi,
                              fg_color="#dc3545", hover_color="#c82333",
                              height=40).pack(side="left", padx=5)

        ctk.CTkButton(edit_frame, text="Edit POI Information",
                      command=open_poi_editor,
                      fg_color="#28a745", hover_color="#218838",
                      height=40).pack(pady=10)

        def global_wheel_handler(event):
            try:
                x, y = popup.winfo_pointerx(), popup.winfo_pointery()
                widget_under_mouse = popup.winfo_containing(x, y)

                # Handle system images scrolling with faster speed
                if hasattr(popup, '_system_images_scroll') and widget_under_mouse:
                    if _is_widget_in_area(widget_under_mouse, popup._system_images_scroll):
                        if hasattr(popup._system_images_scroll, '_parent_canvas'):
                            popup._system_images_scroll._parent_canvas.yview_scroll(int(-6 * (event.delta / 120)),
                                                                                    "units")
                        return "break"

                # Handle POI images scrolling with faster speed
                if hasattr(popup, '_poi_images_scroll') and widget_under_mouse:
                    if _is_widget_in_area(widget_under_mouse, popup._poi_images_scroll):
                        if hasattr(popup._poi_images_scroll, '_parent_canvas'):
                            popup._poi_images_scroll._parent_canvas.yview_scroll(int(-6 * (event.delta / 120)), "units")
                        return "break"

                # If not over specific areas, allow normal scrolling at standard speed
                # This will be handled by the default CustomTkinter scrolling
                return

            except Exception as e:
                return

        def _is_widget_in_area(widget, area):
            try:
                current = widget
                while current:
                    if current == area:
                        return True
                    current = current.master
                return False
            except:
                return False

        popup.bind("<MouseWheel>", global_wheel_handler)

    def claim_system_new_discovery(self, system_name, popup_window):
        """Claim a system that's not in the records database - adds it as a new discovery first"""
        if not supabase:
            messagebox.showerror("Error", "Database not available", parent=popup_window)
            return

        try:
            # Set current commander for RLS policies
            self.set_current_commander()
            # Check if system is already claimed
            existing = supabase.table("taken").select("*").eq("system", system_name).execute()
            if existing.data:
                messagebox.showwarning("Warning", "System is already claimed!", parent=popup_window)
                return

            # Check if we have coordinates (should be current system)
            if not (self.system_name == system_name and self.latest_starpos):
                messagebox.showwarning("Warning", "You must be in this system to claim it as a new discovery!",
                                       parent=popup_window)
                return

            x, y, z = self.latest_starpos

            # Store discovery information in system_information table (user accessible)
            # This preserves the discovery without requiring admin access to systems table
            discovery_data = {
                "system": system_name,
                "name": system_name,
                "description": f"New discovery by CMDR {self.cmdr_name}",
                "category": "New Discovery",
                "x": x,
                "y": y,
                "z": z
            }

            # Check if discovery info already exists
            existing_info = supabase.table("system_information").select("*").eq("system", system_name).execute()
            if not existing_info.data:
                supabase.table("system_information").insert(discovery_data).execute()
                print(f"Stored discovery information for {system_name}")
            else:
                # Update with coordinates if missing
                existing = existing_info.data[0]
                if not existing.get("x") or not existing.get("y") or not existing.get("z"):
                    supabase.table("system_information").update({
                        "x": x, "y": y, "z": z,
                        "category": "New Discovery"
                    }).eq("system", system_name).execute()
                    print(f"Updated coordinates for {system_name}")

            # Now claim the system
            visited = True  # They're currently in the system

            supabase.table("taken").insert({
                "system": system_name,
                "by_cmdr": self.cmdr_name,
                "visited": visited
            }).execute()

            success_label = ctk.CTkLabel(popup_window, text="✓ Discovery claimed & documented!",
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color="#FFD700")
            success_label.place(relx=0.5, rely=0.95, anchor="center")
            popup_window.after(2000, lambda: success_label.destroy())

            self._refresh_system_popup(system_name, None)

            self.find_nearest_unclaimed()
            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                self.map_window.toggle_unvisited()
                self.map_window.toggle_your_claims()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to claim new discovery: {e}", parent=popup_window)

    def claim_system(self, system_name, popup_window):
        if not supabase:
            messagebox.showerror("Error", "Database not available", parent=popup_window)
            return
        try:
            # Set current commander for RLS policies
            self.set_current_commander()
            existing = supabase.table("taken").select("*").eq("system", system_name).execute()
            if existing.data:
                messagebox.showwarning("Warning", "System is already claimed!", parent=popup_window)
                return

            visited = self.check_system_visited_in_journals(system_name) or (self.system_name == system_name)

            supabase.table("taken").insert({
                "system": system_name,
                "by_cmdr": self.cmdr_name,
                "visited": visited
            }).execute()

            success_label = ctk.CTkLabel(popup_window, text="✓ System claimed!",
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color="#4CAF50")
            success_label.place(relx=0.5, rely=0.95, anchor="center")
            popup_window.after(2000, lambda: success_label.destroy())

            self._refresh_system_popup(system_name, None)

            self.find_nearest_unclaimed()
            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                self.map_window.toggle_unvisited()
                self.map_window.toggle_your_claims()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to claim system: {e}", parent=popup_window)

    def mark_visited(self, system_name, popup_window):
        if not supabase:
            messagebox.showerror("Error", "Database not available", parent=popup_window)
            return
        try:
            # Set current commander for RLS policies
            self.set_current_commander()
            supabase.table("taken").update({"visited": True}).eq("system", system_name).eq("by_cmdr",
                                                                                           self.cmdr_name).execute()

            success_label = ctk.CTkLabel(popup_window, text="✓ Marked as visited!",
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color="#4CAF50")
            success_label.place(relx=0.5, rely=0.95, anchor="center")
            popup_window.after(2000, lambda: success_label.destroy())

            self._refresh_system_popup(system_name, None)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark as visited: {e}", parent=popup_window)

    def unmark_visited(self, system_name, popup_window):
        if not supabase:
            messagebox.showerror("Error", "Database not available", parent=popup_window)
            return
        try:
            # Set current commander for RLS policies
            self.set_current_commander()
            supabase.table("taken").update({"visited": False}).eq("system", system_name).eq("by_cmdr",
                                                                                            self.cmdr_name).execute()

            success_label = ctk.CTkLabel(popup_window, text="✓ Unmarked as visited!",
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color="#ffc107")
            success_label.place(relx=0.5, rely=0.95, anchor="center")
            popup_window.after(2000, lambda: success_label.destroy())

            self._refresh_system_popup(system_name, None)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to unmark as visited: {e}", parent=popup_window)

    def mark_done(self, system_name, popup_window):
        if not supabase:
            messagebox.showerror("Error", "Database not available", parent=popup_window)
            return
        try:
            # Set current commander for RLS policies
            self.set_current_commander()
            supabase.table("taken").update({
                "visited": True,
                "done": True
            }).eq("system", system_name).eq("by_cmdr", self.cmdr_name).execute()

            success_label = ctk.CTkLabel(popup_window, text="✓ Marked as done!",
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color="#9C27B0")
            success_label.place(relx=0.5, rely=0.95, anchor="center")
            popup_window.after(2000, lambda: success_label.destroy())

            self._refresh_system_popup(system_name, None)

            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                self.map_window.toggle_your_claims()
                self.map_window.toggle_done_systems()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark as done: {e}", parent=popup_window)

    def verify_system_data(self, system_name):
        """Show exactly what data exists for this system across all tables"""
        if not supabase:
            return {}
        try:
            system_name = system_name.strip()
            print(f"[VERIFY] Checking all data for system: '{system_name}'")

            # Check all relevant tables
            taken_data = supabase.table("taken").select("*").eq("system", system_name).execute()
            info_data = supabase.table("system_information").select("*").eq("system", system_name).execute()
            poi_data = supabase.table("pois").select("*").eq("system_name", system_name).execute()
            systems_data = supabase.table("systems").select("*").eq("systems", system_name).execute()

            results = {
                "taken": taken_data.data if taken_data.data else [],
                "system_information": info_data.data if info_data.data else [],
                "pois": poi_data.data if poi_data.data else [],
                "systems": systems_data.data if systems_data.data else []
            }

            print(f"[VERIFY] Data found:")
            for table, data in results.items():
                print(f"  {table}: {len(data)} records")
                if data:
                    for record in data:
                        relevant_fields = {}
                        if table == "taken":
                            relevant_fields = {k: v for k, v in record.items() if
                                               k in ["id", "system", "by_cmdr", "visited", "done"]}
                        elif table == "system_information":
                            relevant_fields = {k: v for k, v in record.items() if
                                               k in ["id", "system", "name", "category"]}
                        elif table == "pois":
                            relevant_fields = {k: v for k, v in record.items() if
                                               k in ["id", "system_name", "name", "potential_or_poi"]}
                        elif table == "systems":
                            relevant_fields = {k: v for k, v in record.items() if
                                               k in ["systems", "category", "x", "y", "z"]}
                        print(f"    {relevant_fields}")

            return results
        except Exception as e:
            print(f"[ERROR] Failed to verify system data: {e}")
            return {}

    def set_current_commander(self):
        """Set the current commander in the database session for RLS policies"""
        if not supabase or not self.cmdr_name or self.cmdr_name == "Unknown":
            return False
        try:
            # Set the current commander for Row Level Security policies
            supabase.rpc('set_config', {
                'parameter': 'app.current_commander',
                'value': self.cmdr_name
            }).execute()
            print(f"[DEBUG] Set current commander to: '{self.cmdr_name}'")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to set current commander: {e}")
            return False

    def purge_new_discovery(self, system_name):
        """Safely remove all traces of a new discovery from all tables"""
        if not supabase:
            return False
        try:
            # Set current commander for RLS policies
            self.set_current_commander()

            # Clean the system name
            system_name = system_name.strip()
            print(f"[DEBUG] Safely purging data for new discovery: '{system_name}'")

            # First, verify what we're about to delete by querying first
            taken_check = supabase.table("taken").select("*").eq("system", system_name).eq("by_cmdr",
                                                                                           self.cmdr_name).execute()
            info_check = supabase.table("system_information").select("*").eq("system", system_name).execute()
            poi_check = supabase.table("pois").select("*").eq("system_name", system_name).execute()

            print(
                f"[DEBUG] Found for deletion - taken: {len(taken_check.data) if taken_check.data else 0}, info: {len(info_check.data) if info_check.data else 0}, poi: {len(poi_check.data) if poi_check.data else 0}")

            # Delete in the correct order to avoid RLS policy conflicts
            # Delete from system_information and pois FIRST (while taken record still exists for RLS)
            if info_check.data:
                # Remove from system_information table (exact system name match)
                info_result = supabase.table("system_information").delete().eq("system", system_name).execute()
                print(
                    f"[DEBUG] Removed from system_information table: {len(info_result.data) if info_result.data else 0} rows")

            if poi_check.data:
                # Remove from pois table (exact system name match)
                poi_result = supabase.table("pois").delete().eq("system_name", system_name).execute()
                print(f"[DEBUG] Removed from pois table: {len(poi_result.data) if poi_result.data else 0} rows")

            # Delete from taken table LAST (after other tables are cleaned up)
            if taken_check.data:
                # Remove from taken table (only YOUR claim)
                taken_result = supabase.table("taken").delete().eq("system", system_name).eq("by_cmdr",
                                                                                             self.cmdr_name).execute()
                print(f"[DEBUG] Removed from taken table: {len(taken_result.data) if taken_result.data else 0} rows")

            return True
        except Exception as e:
            print(f"[ERROR] Failed to purge new discovery '{system_name}': {e}")
            return False

    def unclaim_system(self, system_name, popup_window):
        if not supabase:
            messagebox.showerror("Error", "Database not available", parent=popup_window)
            return
        try:
            # Set current commander for RLS policies
            self.set_current_commander()

            # Ensure system name is clean (no extra whitespace)
            system_name = system_name.strip()
            print(f"[DEBUG] Processing unclaim for system: '{system_name}'")

            # First, verify what data exists for this system
            system_data = self.verify_system_data(system_name)

            # Check if system is in records database
            system_in_database = bool(system_data.get("systems", []))
            print(f"[DEBUG] System in main database: {system_in_database}")

            if system_in_database:
                # Regular unclaim for systems in database
                if not messagebox.askyesno("Confirm", f"Unclaim system {system_name}?", parent=popup_window):
                    return
                action_text = "unclaimed"
            else:
                # Delete entirely for new discoveries
                if not messagebox.askyesno("Confirm",
                                           f"Delete discovery {system_name}?\n\nThis will completely remove your discovery record.",
                                           parent=popup_window):
                    return
                action_text = "deleted"

            if not system_in_database:
                # Use thorough purge for new discoveries
                print(f"[DEBUG] Attempting to purge new discovery: '{system_name}' (not in main database)")
                if self.purge_new_discovery(system_name):
                    print(f"[SUCCESS] Successfully purged new discovery: '{system_name}'")
                else:
                    print(f"[ERROR] Failed to purge new discovery: '{system_name}'")
            else:
                # Regular unclaim for systems in database - only remove YOUR claim
                print(f"[DEBUG] Unclaiming regular system: '{system_name}' for CMDR: '{self.cmdr_name}'")
                result = supabase.table("taken").delete().eq("system", system_name).eq("by_cmdr",
                                                                                       self.cmdr_name).execute()
                print(f"[DEBUG] Unclaimed {len(result.data) if result.data else 0} claims from taken table")

            success_label = ctk.CTkLabel(popup_window, text=f"✓ Discovery {action_text}!",
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color="#dc3545")
            success_label.place(relx=0.5, rely=0.95, anchor="center")
            popup_window.after(2000, lambda: success_label.destroy())

            # Close the popup since the system no longer exists for new discoveries
            if not system_in_database:
                popup_window.after(2000, popup_window.destroy)
            else:
                self._refresh_system_popup(system_name, None)

            # Refresh data with error handling
            try:
                self.find_nearest_unclaimed()
            except Exception as refresh_e:
                print(f"Error refreshing nearest unclaimed after deletion: {refresh_e}")

            try:
                self.update_nearest_systems()
            except Exception as update_e:
                print(f"Error updating nearest systems after deletion: {update_e}")

            if self.map_window and hasattr(self.map_window, 'winfo_exists') and self.map_window.winfo_exists():
                try:
                    self.map_window.toggle_unvisited()
                    self.map_window.toggle_your_claims()
                except Exception as map_e:
                    print(f"Error refreshing map after deletion: {map_e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to unclaim system: {e}", parent=popup_window)

    def show_admin_panel(self):
        admin_window = ctk.CTkToplevel(self)
        admin_window.title("Admin Panel - Security Management")
        admin_window.geometry("450x500")
        admin_window.configure(fg_color=MAIN_BG_COLOR)
        admin_window.transient(self)
        admin_window.grab_set()
        admin_window.attributes("-topmost", True)
        admin_window.lift()
        admin_window.focus_force()
        admin_window.after(300, lambda: admin_window.attributes("-topmost", False))
        ctk.CTkLabel(admin_window, text="Commander Security Management",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#dc3545").pack(pady=10)
        info_frame = ctk.CTkFrame(admin_window, fg_color=TERTIARY_BG_COLOR, corner_radius=8)
        info_frame.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(info_frame, text="ℹ Security Info:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=INFO_COLOR).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(info_frame,
                     text="• New users are automatically added as BLOCKED\n• Detects renames from banned accounts via journal history\n• Rename attempts are logged to Discord",
                     font=ctk.CTkFont(size=10),
                     text_color=TEXT_SECONDARY,
                     justify="left").pack(anchor="w", padx=10, pady=(0, 8))
        cmdr_entry = ctk.CTkEntry(admin_window, placeholder_text="Enter CMDR name",
                                  width=300, fg_color=SECONDARY_BG_COLOR,
                                  border_color="#444444", text_color=TEXT_COLOR)
        cmdr_entry.pack(pady=10)
        ctk.CTkLabel(admin_window, text="All Commanders in Security Table:",
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_COLOR).pack(pady=(20, 5))
        cmdr_list_frame = ctk.CTkScrollableFrame(admin_window, width=350, height=150,
                                                 fg_color=SECONDARY_BG_COLOR)
        cmdr_list_frame.pack(pady=5)

        def refresh_blocked_list():
            for widget in cmdr_list_frame.winfo_children():
                widget.destroy()
            try:
                all_cmdrs = supabase.table("security").select("name,blocked").execute()
                if all_cmdrs.data:
                    blocked_count = sum(1 for c in all_cmdrs.data if c.get("blocked", True))
                    allowed_count = len(all_cmdrs.data) - blocked_count
                    count_frame = ctk.CTkFrame(cmdr_list_frame, fg_color=TERTIARY_BG_COLOR, corner_radius=8)
                    count_frame.pack(fill="x", pady=(0, 10), padx=5)
                    ctk.CTkLabel(count_frame, text=f"Total: {len(all_cmdrs.data)} | ",
                                 font=ctk.CTkFont(size=11, weight="bold"),
                                 text_color=TEXT_COLOR).pack(side="left", padx=(10, 0))
                    ctk.CTkLabel(count_frame, text=f"Allowed: {allowed_count} | ",
                                 font=ctk.CTkFont(size=11, weight="bold"),
                                 text_color="#4ecdc4").pack(side="left")
                    ctk.CTkLabel(count_frame, text=f"Blocked: {blocked_count}",
                                 font=ctk.CTkFont(size=11, weight="bold"),
                                 text_color="#ff6b6b").pack(side="left", padx=(0, 10))
                    sorted_cmdrs = sorted(all_cmdrs.data, key=lambda x: (not x.get("blocked", True), x["name"]))
                    for cmdr in sorted_cmdrs:
                        frame = ctk.CTkFrame(cmdr_list_frame, fg_color="transparent")
                        frame.pack(fill="x", pady=2, padx=5)
                        name_label = ctk.CTkLabel(frame, text=cmdr["name"],
                                                  text_color="#ff6b6b" if cmdr.get("blocked", True) else "#4ecdc4",
                                                  anchor="w", width=200)
                        name_label.pack(side="left")
                        status_text = "BLOCKED" if cmdr.get("blocked", True) else "ALLOWED"
                        status_label = ctk.CTkLabel(frame, text=status_text,
                                                    font=ctk.CTkFont(size=10, weight="bold"),
                                                    text_color="#ff6b6b" if cmdr.get("blocked", True) else "#4ecdc4")
                        status_label.pack(side="right")
                else:
                    ctk.CTkLabel(cmdr_list_frame, text="No commanders in security table",
                                 text_color="#666666").pack()
            except Exception as e:
                ctk.CTkLabel(cmdr_list_frame, text=f"Error loading list: {e}",
                             text_color="#ff0000").pack()

        def block_cmdr():
            cmdr_to_block = cmdr_entry.get().strip()
            if not cmdr_to_block:
                messagebox.showwarning("Warning", "Enter a CMDR name", parent=admin_window)
                return
            try:
                existing = supabase.table("security").select("name").eq("name", cmdr_to_block).maybe_single().execute()
                if existing and existing.data:
                    supabase.table("security").update({"blocked": True}).eq("name", cmdr_to_block).execute()
                else:
                    supabase.table("security").insert({
                        "name": cmdr_to_block,
                        "blocked": True
                    }).execute()
                messagebox.showinfo("Success", f"CMDR {cmdr_to_block} has been blocked", parent=admin_window)
                cmdr_entry.delete(0, 'end')
                refresh_blocked_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to block CMDR: {e}", parent=admin_window)

        def unblock_cmdr():
            cmdr_to_unblock = cmdr_entry.get().strip()
            if not cmdr_to_unblock:
                messagebox.showwarning("Warning", "Enter a CMDR name", parent=admin_window)
                return
            try:
                supabase.table("security").update({"blocked": False}).eq("name", cmdr_to_unblock).execute()
                messagebox.showinfo("Success", f"CMDR {cmdr_to_unblock} has been unblocked", parent=admin_window)
                cmdr_entry.delete(0, 'end')
                refresh_blocked_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to unblock CMDR: {e}", parent=admin_window)

        btn_frame = ctk.CTkFrame(admin_window, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Block CMDR", command=block_cmdr,
                      fg_color="#dc3545", hover_color="#c82333", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Unblock CMDR", command=unblock_cmdr,
                      fg_color="#28a745", hover_color="#218838", width=120).pack(side="left", padx=5)
        refresh_blocked_list()
        ctk.CTkButton(admin_window, text="Refresh List", command=refresh_blocked_list,
                      fg_color="#6c757d", hover_color="#5a6268", width=100).pack(pady=5)

    def check_admin_status(self):
        """Check if the current commander has admin privileges"""
        if not supabase or self.cmdr_name == "Unknown":
            return False
        try:
            # Check admin access table
            admin_check = supabase.table("admin_access").select("id").eq("name", self.cmdr_name).execute()
            if admin_check.data:
                self.is_admin = True
                print(f"[DEBUG] Commander {self.cmdr_name} has admin privileges")
                return True
            else:
                self.is_admin = False
                return False
        except Exception as e:
            print(f"[ERROR] Failed to check admin status: {e}")
            self.is_admin = False
            return False

    def update_commander_location(self):
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
            return
        current_journal = get_current_journal_path()
        if not current_journal or not os.path.exists(current_journal):
            print(f"Current journal not found or doesn't exist: {current_journal}")
            if _cfg.get("journal_path"):
                initial_journal = find_latest_journal_with_fsdjump(_cfg["journal_path"])
                if not initial_journal:
                    initial_journal = get_latest_journal_file(_cfg["journal_path"])
                if initial_journal:
                    save_current_journal_path(initial_journal)
                    print(f"Set current journal: {initial_journal}")
        self.start_monitoring()

    def ask_for_journal_folder(self):
        while True:
            fld = filedialog.askdirectory(title="Select Elite Dangerous journal folder")
            if not fld:
                os._exit(0)

            # Look for both journal formats
            journal_files = []
            for file in os.listdir(fld):
                if file.startswith("Journal.") and file.endswith(".log"):
                    # Check if it matches either format
                    if (re.match(r"Journal\.\d{4}-\d{2}-\d{2}T\d{6}\.01\.log$", file) or
                            re.match(r"Journal\.\d{12}\.01\.log$", file)):
                        journal_files.append(file)

            if journal_files:
                _cfg["journal_path"] = fld
                _cfg["journal_verified"] = True
                save_config(_cfg)

                if hasattr(self, '_from_splash_failure') and self._from_splash_failure:
                    self.initialize_app()
                else:
                    self.start_monitoring()
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

    def start_monitoring(self):
        def monitor():
            last_journal = None
            last_size = 0
            last_mtime = 0
            initial_journal = get_current_journal_path()
            if not initial_journal or not os.path.exists(initial_journal):
                initial_journal = find_latest_journal_with_valid_data(_cfg["journal_path"])
                if not initial_journal:
                    initial_journal = find_latest_journal_with_fsdjump(_cfg["journal_path"])
                if not initial_journal:
                    initial_journal = get_latest_journal_file(_cfg["journal_path"])
            if initial_journal:
                last_journal = initial_journal
                save_current_journal_path(initial_journal)
                self.cmdr_name = extract_commander_name(initial_journal)
                print(f"[DEBUG] Extracted commander name: '{self.cmdr_name}' from journal: {initial_journal}")
                if supabase:
                    if self.cmdr_name == "Unknown":
                        print("[WARNING] No commander found in journal - waiting for login...")
                    else:
                        try:
                            auto_block_list = ["Arcanic", "Julian Ford"]
                            if self.cmdr_name in auto_block_list:
                                print(f"[WARNING] Auto-blocking commander: {self.cmdr_name}")
                                try:
                                    supabase.table("security").upsert({
                                        "name": self.cmdr_name,
                                        "blocked": True,
                                        "notes": "Auto-blocked commander"
                                    }).execute()
                                except:
                                    pass
                                messagebox.showerror("Access Denied", "You are not authorized to use this application.")
                                os._exit(1)

                            all_commanders = detect_commander_renames(_cfg.get("journal_path", ""))
                            banned_commander = None

                            if len(all_commanders) > 1:
                                print(f"[DEBUG] Multiple commanders detected in journals: {all_commanders}")
                                print(f"[DEBUG] Current commander: {self.cmdr_name}")
                                print(f"[DEBUG] Checking each commander for blocks...")

                                for cmdr in all_commanders:
                                    if cmdr != self.cmdr_name:
                                        try:
                                            check = supabase.table("security").select("name,blocked").ilike("name",
                                                                                                            cmdr).eq(
                                                "blocked", True).execute()
                                            if check and check.data and len(check.data) > 0:
                                                banned_commander = check.data[0]["name"]
                                                print(
                                                    f"[WARNING] Blocked commander '{banned_commander}' (searched as '{cmdr}') found in same journal folder as '{self.cmdr_name}'")
                                                break
                                        except Exception as e:
                                            print(f"[DEBUG] Error checking commander '{cmdr}': {e}")
                                            continue

                                if banned_commander:
                                    print(
                                        f"[SECURITY] Rename attempt detected: {self.cmdr_name} linked to banned commander {banned_commander}")
                                    try:
                                        if login_events_client:
                                            from datetime import datetime, timezone
                                            login_events_client.table('login_events').insert({
                                                'commander': f"{self.cmdr_name} (linked to {banned_commander})",
                                                'is_admin': False,
                                                'login_time': datetime.now(timezone.utc).isoformat(),
                                                'app_version': VERSION_TEXT,
                                                'event_type': 'rename_attempt',
                                                'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'
                                            }).execute()
                                            print(f"[DEBUG] Logged rename attempt to Discord")
                                            time.sleep(1)
                                    except Exception as e:
                                        print(f"[ERROR] Failed to log rename attempt: {e}")
                                    messagebox.showerror("Access Denied",
                                                         f"Rename detected! {banned_commander} is banned.\nSpeak to the plugin owner in Discord to gain access.")
                                    os._exit(1)
                                else:
                                    print(
                                        f"[DEBUG] Multiple commanders detected but none are banned - allowing access for {self.cmdr_name}")

                            security_check = None
                            try:
                                print(f"[DEBUG] Checking security for commander: {self.cmdr_name}")
                                result = supabase.table("security").select("*").eq("name", self.cmdr_name).execute()
                                print(f"[DEBUG] Security query returned: {len(result.data)} rows")
                                if result.data and len(result.data) > 1:
                                    print(f"[WARNING] Multiple security entries found for {self.cmdr_name}:")
                                    for entry in result.data:
                                        print(f"  - ID: {entry['id']}, Blocked: {entry.get('blocked', 'N/A')}")
                                security_check = result.data[0] if result.data else None
                            except Exception as query_e:
                                print(f"[ERROR] Security query failed: {query_e}")
                                security_check = None
                            if not security_check:
                                print(f"[DEBUG] {self.cmdr_name} not in security table - adding as allowed (new user)")
                                try:
                                    from datetime import datetime, timezone
                                    all_commanders = detect_commander_renames(_cfg.get("journal_path", ""))
                                    rename_info = None
                                    if len(all_commanders) > 1:
                                        rename_info = f"Multiple names detected: {', '.join(all_commanders)}"
                                    security_data = {
                                        "name": self.cmdr_name,
                                        "blocked": False,
                                        "first_seen": datetime.now(timezone.utc).isoformat(),
                                        "journal_path": _cfg.get("journal_path", "Unknown")
                                    }
                                    if rename_info:
                                        security_data["notes"] = rename_info
                                    supabase.table("security").insert(security_data).execute()
                                    print(f"[DEBUG] Added {self.cmdr_name} to security table as allowed")
                                    if login_events_client:
                                        try:
                                            event_type = 'new_user_with_rename' if rename_info else 'new_user'
                                            login_events_client.table('login_events').insert({
                                                'commander': self.cmdr_name,
                                                'is_admin': False,
                                                'login_time': datetime.now(timezone.utc).isoformat(),
                                                'app_version': VERSION_TEXT,
                                                'event_type': event_type,
                                                'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'}).execute()
                                            print(f"[DEBUG] Logged {event_type} event for {self.cmdr_name} to Discord")
                                            time.sleep(1)
                                        except Exception as log_e:
                                            print(f"[ERROR] Failed to log new user event: {log_e}")
                                except Exception as sec_e:
                                    print(f"[ERROR] Error adding to security table: {sec_e}")

                            is_blocked = False if not security_check else security_check.get("blocked", True)

                            if is_blocked:
                                is_alt_account = False
                                main_account = None

                                if all_commanders and len(all_commanders) > 1:
                                    print(f"[DEBUG] Checking if {self.cmdr_name} is an alt account...")
                                    for other_cmdr in all_commanders:
                                        if other_cmdr != self.cmdr_name:
                                            try:
                                                other_check = supabase.table("security").select("name,blocked").eq(
                                                    "name", other_cmdr).maybe_single().execute()
                                                if other_check and other_check.data and not other_check.data.get(
                                                        "blocked", True):
                                                    is_alt_account = True
                                                    main_account = other_cmdr
                                                    print(
                                                        f"[DEBUG] {self.cmdr_name} is an alt account of authenticated user {main_account}")

                                                    supabase.table("security").update({"blocked": False,
                                                                                       "notes": f"Alt account of {main_account}"}).eq(
                                                        "name", self.cmdr_name).execute()

                                                    if login_events_client:
                                                        try:
                                                            from datetime import datetime, timezone
                                                            login_events_client.table('login_events').insert({
                                                                'commander': f"{self.cmdr_name} (alt of {main_account})",
                                                                'is_admin': False,
                                                                'login_time': datetime.now(timezone.utc).isoformat(),
                                                                'app_version': VERSION_TEXT,
                                                                'event_type': 'alt_account_authenticated',
                                                                'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'
                                                            }).execute()
                                                            print(
                                                                f"[DEBUG] Logged alt account authentication to Discord")
                                                        except Exception as e:
                                                            print(f"[ERROR] Failed to log alt account: {e}")
                                                    break
                                            except:
                                                continue

                                if not is_alt_account:
                                    print(f"[DEBUG] User {self.cmdr_name} is explicitly blocked")
                                    print(
                                        f"[DEBUG] About to log blocked attempt. login_events_client available: {login_events_client is not None}")
                                    try:
                                        if login_events_client:
                                            print(f"[DEBUG] Inserting into login_events table...")
                                            from datetime import datetime, timezone
                                            result = login_events_client.table('login_events').insert({
                                                'commander': self.cmdr_name,
                                                'is_admin': False,
                                                'login_time': datetime.now(timezone.utc).isoformat(),
                                                'app_version': VERSION_TEXT,
                                                'event_type': 'blocked_attempt',
                                                'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'}).execute()
                                            print(f"[DEBUG] Logged blocked attempt to Discord")
                                            time.sleep(1)
                                        else:
                                            print(f"[ERROR] login_events_client is None!")
                                    except Exception as e:
                                        print(f"[ERROR] Failed to log blocked attempt: {e}")
                                    messagebox.showerror("Access Denied",
                                                         "You are unauthenticated. Speak to the plugin owner in Discord to gain access.")
                                    os._exit(1)
                            print(f"[DEBUG] User {self.cmdr_name} is authenticated")
                            print(f"[DEBUG] Logging successful login event for {self.cmdr_name}")
                            try:
                                from datetime import datetime, timezone
                                if login_events_client:
                                    result = login_events_client.table('login_events').insert({
                                        'commander': self.cmdr_name,
                                        'is_admin': self.is_admin,
                                        'login_time': datetime.now(timezone.utc).isoformat(),
                                        'app_version': VERSION_TEXT,
                                        'event_type': 'login',
                                        'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'}).execute()
                                    print(f"[DEBUG] Successfully logged login event to Discord")
                                else:
                                    print("[ERROR] login_events_client not available")
                            except Exception as login_e:
                                print(f"[ERROR] Failed to log login event: {login_e}")
                                import traceback
                                traceback.print_exc()
                            if self.is_admin:
                                try:
                                    from datetime import datetime, timezone
                                    admin_data = {
                                        "name": self.cmdr_name,
                                        "passed_check": True,
                                        "date_of_login": datetime.now(timezone.utc).isoformat()
                                    }
                                    supabase.table("all_admins").insert(admin_data).execute()
                                    print(f"[DEBUG] Logged admin access for {self.cmdr_name}")
                                except Exception as admin_e:
                                    print(f"[ERROR] Error logging admin access: {admin_e}")
                        except Exception as e:
                            print(f"[ERROR] Security check error: {e}")
                            import traceback
                            traceback.print_exc()
                self.cmdr_label.configure(text=f"CMDR: {self.cmdr_name}")
                sysnm, pos = self.find_latest_journal_and_pos(initial_journal)
                if sysnm:
                    self.system_name = sysnm
                    self.system_label.configure(text=sysnm)
                if pos:
                    self.latest_starpos = pos
                    self.current_coords = pos
                else:
                    if sysnm and supabase:
                        try:
                            sys_data = supabase.table("systems").select("x,y,z").eq("systems",
                                                                                    sysnm).maybe_single().execute()
                            if sys_data and sys_data.data:
                                x = sys_data.data.get("x", 0)
                                y = sys_data.data.get("y", 0)
                                z = sys_data.data.get("z", 0)
                                if x or y or z:
                                    self.latest_starpos = (x, y, z)
                                    self.current_coords = (x, y, z)
                                    print(f"Got coordinates from database for {sysnm}")
                        except:
                            pass
                if self.current_coords:
                    self.find_nearest_unclaimed()
                    self.update_nearest_systems()
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

                        # Always check for commander changes to handle account switching
                        detected_cmdr = extract_commander_name(latest)
                        if detected_cmdr != "Unknown" and detected_cmdr != self.cmdr_name:
                            print(f"[DEBUG] Commander change detected: {self.cmdr_name} -> {detected_cmdr}")
                            old_cmdr = self.cmdr_name
                            self.cmdr_name = detected_cmdr
                            self.cmdr_label.configure(text=f"CMDR: {self.cmdr_name}")

                            # Perform security check for the new commander
                            if supabase and self.cmdr_name != "Unknown":
                                print(f"[DEBUG] Security check for new commander: {self.cmdr_name}")
                                try:
                                    security_check_result = supabase.table("security").select("name,blocked").eq("name",
                                                                                                                 self.cmdr_name).maybe_single().execute()
                                    is_blocked = False

                                    if not security_check_result or not security_check_result.data:
                                        print(
                                            f"[DEBUG] New commander {self.cmdr_name} not in security table - adding as allowed")
                                        try:
                                            from datetime import datetime, timezone
                                            security_data = {
                                                "name": self.cmdr_name,
                                                "blocked": False,
                                                "first_seen": datetime.now(timezone.utc).isoformat(),
                                                "journal_path": _cfg.get("journal_path", "Unknown"),
                                                "notes": f"Account switch from {old_cmdr}"
                                            }
                                            supabase.table("security").insert(security_data).execute()
                                            print(f"[DEBUG] Added {self.cmdr_name} to security table as allowed")
                                        except Exception as add_e:
                                            print(f"[ERROR] Failed to add new commander to security table: {add_e}")
                                    else:
                                        is_blocked = security_check_result.data.get("blocked", False)
                                        print(
                                            f"[DEBUG] Commander {self.cmdr_name} found in security table - blocked: {is_blocked}")

                                    if is_blocked:
                                        print(f"[WARNING] New commander {self.cmdr_name} is blocked")
                                        if login_events_client:
                                            try:
                                                from datetime import datetime, timezone
                                                login_events_client.table('login_events').insert({
                                                    'commander': f"{self.cmdr_name} (account switch from {old_cmdr})",
                                                    'is_admin': False,
                                                    'login_time': datetime.now(timezone.utc).isoformat(),
                                                    'app_version': VERSION_TEXT,
                                                    'event_type': 'blocked_account_switch',
                                                    'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'
                                                }).execute()
                                                print(f"[DEBUG] Logged blocked account switch to Discord")
                                            except Exception as e:
                                                print(f"[ERROR] Failed to log blocked account switch: {e}")
                                        messagebox.showerror("Access Denied",
                                                             f"Commander {self.cmdr_name} is not authorized. Speak to the plugin owner in Discord to gain access.")
                                        os._exit(1)
                                    else:
                                        print(f"[DEBUG] Account switch approved for {self.cmdr_name}")

                                        # Check admin status for the new commander
                                        old_admin_status = self.is_admin
                                        self.check_admin_status()
                                        if old_admin_status != self.is_admin:
                                            print(
                                                f"[DEBUG] Admin status changed: {old_admin_status} -> {self.is_admin}")

                                        if login_events_client:
                                            try:
                                                from datetime import datetime, timezone
                                                login_events_client.table('login_events').insert({
                                                    'commander': f"{self.cmdr_name} (account switch from {old_cmdr})",
                                                    'is_admin': self.is_admin,
                                                    'login_time': datetime.now(timezone.utc).isoformat(),
                                                    'app_version': VERSION_TEXT,
                                                    'event_type': 'account_switch',
                                                    'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'
                                                }).execute()
                                                print(f"[DEBUG] Logged account switch to Discord")
                                            except Exception as e:
                                                print(f"[ERROR] Failed to log account switch: {e}")
                                except Exception as e:
                                    print(f"[ERROR] Security check failed for new commander: {e}")

                        sysnm, pos = self.find_latest_journal_and_pos(latest)
                        if pos:
                            self.latest_starpos = pos
                            self.current_coords = pos
                        if sysnm and sysnm != self.system_name:
                            self.system_name = sysnm
                            self.system_label.configure(text=sysnm)
                            if hasattr(self, 'jump_count'):
                                self.jump_count += 1
                            else:
                                self.jump_count = 1
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
        """Find latest system and position - prioritizes CURRENT journal, reads from BOTTOM to TOP"""

        try:
            current_journal_name = os.path.basename(fp)
            print(f"[DEBUG] Starting location extraction from: {current_journal_name}")

            # PRIORITY 1: Scan the CURRENT journal from BOTTOM to TOP (latest entries first)
            print(f"[DEBUG] Reading current journal for location: {current_journal_name}")
            try:
                with open(fp, encoding="utf-8", errors='ignore') as f:
                    lines = f.readlines()

                print(f"[DEBUG] Current journal has {len(lines)} lines, scanning for location...")

                # Read from bottom to top (latest entries first)
                for i, line in enumerate(reversed(lines)):
                    line = line.strip()
                    if not line:
                        continue

                    # Look for location events
                    if '"event":"FSDJump"' in line or '"event":"Location"' in line or '"event":"CarrierJump"' in line:
                        print(f"[DEBUG] Found potential location event at line {len(lines) - i}: {line[:150]}...")

                        try:
                            d = json.loads(line)
                            system_name = d.get("StarSystem")
                            star_pos = d.get("StarPos")
                            event_type = d.get("event")

                            if system_name and star_pos and isinstance(star_pos, list) and len(star_pos) == 3:
                                print(
                                    f"[DEBUG] ✓ FOUND {event_type} location in current journal: '{system_name}' at {star_pos}")
                                return system_name, tuple(star_pos)

                        except json.JSONDecodeError as je:
                            print(f"[DEBUG] JSON decode error, trying regex: {je}")
                            # Fallback regex parsing
                            if '"StarSystem"' in line and '"StarPos"' in line:
                                sys_match = re.search(r'"StarSystem"\s*:\s*"([^"]+)"', line)
                                pos_match = re.search(
                                    r'"StarPos"\s*:\s*\[\s*([+-]?\d*\.?\d+)\s*,\s*([+-]?\d*\.?\d+)\s*,\s*([+-]?\d*\.?\d+)\s*\]',
                                    line)
                                if sys_match and pos_match:
                                    system_name = sys_match.group(1)
                                    coordinates = (float(pos_match.group(1)), float(pos_match.group(2)),
                                                   float(pos_match.group(3)))
                                    print(
                                        f"[DEBUG] ✓ FOUND location via regex in current journal: '{system_name}' at {coordinates}")
                                    return system_name, coordinates

            except Exception as file_e:
                print(f"[ERROR] Could not read current journal {current_journal_name}: {file_e}")

            # PRIORITY 2: If NO location found in current journal, check recent journals with proper sorting
            print(f"[WARNING] No location found in current journal {current_journal_name}, checking recent journals...")

            journal_dir = os.path.dirname(fp)
            all_journals = list_sorted_journals(journal_dir)  # This now handles both formats correctly

            print(f"[DEBUG] Found {len(all_journals)} total journals to check for location")

            # Check the most recent journals (excluding current one we already checked)
            for journal_path in all_journals[:5]:  # Check only 5 most recent for location
                journal_name = os.path.basename(journal_path)
                if journal_path == fp:  # Skip current journal as we already processed it
                    print(f"[DEBUG] Skipping current journal: {journal_name}")
                    continue

                print(f"[DEBUG] Checking recent journal for location: {journal_name}")
                try:
                    with open(journal_path, encoding="utf-8", errors='ignore') as f:
                        lines = f.readlines()

                    # Read from bottom to top (latest entries first)
                    for line in reversed(lines):
                        line = line.strip()
                        if not line:
                            continue

                        if '"event":"FSDJump"' in line or '"event":"Location"' in line or '"event":"CarrierJump"' in line:
                            try:
                                d = json.loads(line)
                                system_name = d.get("StarSystem")
                                star_pos = d.get("StarPos")
                                event_type = d.get("event")

                                if system_name and star_pos and isinstance(star_pos, list) and len(star_pos) == 3:
                                    print(
                                        f"[DEBUG] ✓ FOUND {event_type} location in recent journal {journal_name}: '{system_name}'")
                                    return system_name, tuple(star_pos)

                            except json.JSONDecodeError:
                                # Fallback regex parsing
                                if '"StarSystem"' in line and '"StarPos"' in line:
                                    sys_match = re.search(r'"StarSystem"\s*:\s*"([^"]+)"', line)
                                    pos_match = re.search(
                                        r'"StarPos"\s*:\s*\[\s*([+-]?\d*\.?\d+)\s*,\s*([+-]?\d*\.?\d+)\s*,\s*([+-]?\d*\.?\d+)\s*\]',
                                        line)
                                    if sys_match and pos_match:
                                        system_name = sys_match.group(1)
                                        coordinates = (float(pos_match.group(1)), float(pos_match.group(2)),
                                                       float(pos_match.group(3)))
                                        print(
                                            f"[DEBUG] ✓ FOUND location via regex in recent journal {journal_name}: '{system_name}'")
                                        return system_name, coordinates

                except Exception as e:
                    print(f"[DEBUG] Error reading recent journal {journal_name}: {e}")
                    continue

            print(f"[WARNING] No location found in any recent journals")
            return None, None

        except Exception as e:
            print(f"[ERROR] Fatal error in location extraction: {e}")
            import traceback
            traceback.print_exc()
        return None, None

    def setup_category_dropdown_main(self):
        for widget in self.category_dropdown_frame_main.winfo_children():
            widget.destroy()
        self.category_checkboxes_main = []
        header_frame = ctk.CTkFrame(self.category_dropdown_frame_main,
                                    fg_color=SECONDARY_BG_COLOR,
                                    height=40,
                                    corner_radius=12)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        header_label = ctk.CTkLabel(header_frame,
                                    text="SELECT CATEGORIES",
                                    font=ctk.CTkFont(size=13, weight="bold"),
                                    text_color=TEXT_COLOR)
        header_label.place(relx=0.5, rely=0.5, anchor="center")
        instructions = ctk.CTkLabel(self.category_dropdown_frame_main,
                                    text="Click to toggle • ESC to cancel",
                                    font=ctk.CTkFont(size=11, slant="italic"),
                                    text_color=TEXT_MUTED)
        instructions.pack(pady=(0, 5))
        scroll_frame = ctk.CTkScrollableFrame(self.category_dropdown_frame_main,
                                              fg_color=SECONDARY_BG_COLOR,
                                              width=240,
                                              height=280,
                                              corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # FIX SCROLLING for category dropdown
        def _category_scroll_handler(event):
            try:
                scroll_frame._parent_canvas.yview_scroll(int(-3 * (event.delta / 120)), "units")
            except:
                pass
            return "break"

        # Bind scroll events to category dropdown
        scroll_frame.bind("<MouseWheel>", _category_scroll_handler)
        if hasattr(scroll_frame, '_parent_canvas'):
            scroll_frame._parent_canvas.bind("<MouseWheel>", _category_scroll_handler)
        all_frame = ctk.CTkFrame(scroll_frame, fg_color=TERTIARY_BG_COLOR, corner_radius=8)
        all_frame.pack(fill="x", padx=5, pady=(5, 10))
        all_cb = ctk.CTkCheckBox(all_frame,
                                 text="All Categories",
                                 font=ctk.CTkFont(size=13, weight="bold"),
                                 text_color=ACCENT_COLOR,
                                 fg_color=ACCENT_COLOR,
                                 hover_color=ACCENT_HOVER,
                                 border_color=ACCENT_COLOR,
                                 checkbox_width=22,
                                 checkbox_height=22,
                                 corner_radius=6,
                                 command=lambda: self.toggle_all_categories_main())
        all_cb.pack(anchor="w", padx=15, pady=10)
        all_cb.select()
        self.all_categories_cb_main = all_cb
        categories = self.category_dropdown.cget("values")
        if "All Categories" in categories:
            categories = [c for c in categories if c != "All Categories"]
        cat_style = {
            "font": ctk.CTkFont(size=12, weight="bold"),
            "text_color": TEXT_COLOR,
            "fg_color": SUCCESS_COLOR,
            "hover_color": SUCCESS_HOVER,
            "border_color": "#444444",
            "checkbox_width": 20,
            "checkbox_height": 20,
            "corner_radius": 5
        }
        for i, category in enumerate(categories):
            cat_frame = ctk.CTkFrame(scroll_frame,
                                     fg_color="transparent",
                                     corner_radius=8,
                                     height=35)
            cat_frame.pack(fill="x", padx=5, pady=2)
            cat_frame.pack_propagate(False)
            cat_color = get_or_create_category_color(category)
            color_strip = ctk.CTkFrame(cat_frame, width=4, fg_color=cat_color, corner_radius=2)
            color_strip.place(x=5, y=5, relheight=0.7)
            cb = ctk.CTkCheckBox(cat_frame,
                                 text=category[:50] + "..." if len(category) > 50 else category,
                                 command=self.update_selected_categories_main,
                                 **cat_style)
            cb.pack(anchor="w", padx=(15, 10), pady=5)
            self.category_checkboxes_main.append((category, cb))

            def on_enter(e, frame=cat_frame):
                frame.configure(fg_color=TERTIARY_BG_COLOR)

            def on_leave(e, frame=cat_frame):
                frame.configure(fg_color="transparent")

            cat_frame.bind("<Enter>", on_enter)
            cat_frame.bind("<Leave>", on_leave)
        self.richards_categories_main = []
        if supabase:
            try:
                all_systems_response = supabase.table("systems").select("category").execute()
                all_categories_in_systems = set()
                if all_systems_response.data:
                    all_categories_in_systems = {item["category"] for item in all_systems_response.data if
                                                 item["category"]}
                richards_response = supabase.table("preset_images").select("category").eq("Richard", True).execute()
                if richards_response.data:
                    richards_cats = [item["category"] for item in richards_response.data]
                    richards_cats = [cat for cat in richards_cats if cat in all_categories_in_systems]
                    if richards_cats:
                        self.richards_categories_main = richards_cats
                        separator_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent", height=30)
                        separator_frame.pack(fill="x", pady=(10, 5))
                        separator_label = ctk.CTkLabel(separator_frame,
                                                       text="———— Richard's Stuff ————",
                                                       font=ctk.CTkFont(size=12, weight="bold"),
                                                       text_color="#666666")
                        separator_label.pack()
                        for category in richards_cats:
                            cb = ctk.CTkCheckBox(scroll_frame,
                                                 text=category[:50] + "..." if len(category) > 50 else category,
                                                 font=ctk.CTkFont(size=12),
                                                 text_color="#ff6b6b",
                                                 fg_color="#666666",
                                                 hover_color="#777777",
                                                 border_color="#888888",
                                                 checkbox_width=20,
                                                 checkbox_height=20,
                                                 command=self.update_selected_categories_main)
                            cb.pack(anchor="w", padx=10, pady=3)
                            self.category_checkboxes_main.append((category, cb))
            except Exception as e:
                print(f"Error loading Richard's categories: {e}")

    def toggle_all_categories_main(self):
        if self.all_categories_cb_main.get():
            self.selected_categories_main = ["All Categories"]
            for cat, cb in self.category_checkboxes_main:
                if cat not in getattr(self, 'richards_categories_main', []):
                    cb.deselect()
                else:
                    cb.deselect()
            self.category_button_main.configure(text="All Categories")
        else:
            self.selected_categories_main = []
            for cat, cb in self.category_checkboxes_main:
                cb.deselect()
            self.category_button_main.configure(text="No categories selected")

        self.nearest_display_limit = 5

        if hasattr(self, 'nearest_scroll') and hasattr(self.nearest_scroll, '_parent_canvas'):
            self.nearest_scroll._parent_canvas.yview_moveto(0)

        self.update_nearest_systems()
        self.find_nearest_unclaimed()

    def prev_unclaimed(self):
        if self.unclaimed_systems and self.unclaimed_index > 0:
            self.unclaimed_index -= 1
            self.update_unclaimed_display()

    def toggle_category_dropdown_main(self):
        if self._dropdown_visible_main:
            self.category_dropdown_frame_main.place_forget()
            self._dropdown_visible_main = False
        else:
            self.category_dropdown_frame_main.place(
                in_=self.category_button_main.master,
                x=self.category_button_main.winfo_x(),
                y=self.category_button_main.winfo_y() + self.category_button_main.winfo_height() + 2
            )
            self._dropdown_visible_main = True
            self.category_dropdown_frame_main.lift()

    def next_unclaimed(self):
        if self.unclaimed_systems and self.unclaimed_index < len(self.unclaimed_systems) - 1:
            self.unclaimed_index += 1
            self.update_unclaimed_display()

    def update_unclaimed_display(self):
        if not self.unclaimed_systems:
            return
        system = self.unclaimed_systems[self.unclaimed_index]
        self.closest = system
        self.closest_label.configure(text=system['systems'])
        self.closest_distance_label.configure(text=f"{system['distance']:.2f} LY")

        # Format category display for multi-category support
        category_display = format_categories_for_display(system.get('category', 'Unknown Category'), max_length=40)
        self.closest_category_label.configure(text=category_display)

        if supabase:
            poi_check = supabase.table("pois").select("potential_or_poi").eq("system_name", system['systems']).execute()
            if poi_check.data:
                poi_status = poi_check.data[0]['potential_or_poi']
                self.closest_poi_label.configure(text=f"★ {poi_status}")
            else:
                self.closest_poi_label.configure(text="")
        self.unclaimed_position_label.configure(text=f"{self.unclaimed_index + 1}/{len(self.unclaimed_systems)}")
        self.btn_prev_unclaimed.configure(state="normal" if self.unclaimed_index > 0 else "disabled")
        self.btn_next_unclaimed.configure(
            state="normal" if self.unclaimed_index < len(self.unclaimed_systems) - 1 else "disabled")
        self.btn_view_closest.configure(state="normal")
        self.btn_claim_closest.configure(state="normal")

    def update_selected_categories_main(self):
        self.selected_categories_main = []
        self.all_categories_cb_main.deselect()
        for cat, cb in self.category_checkboxes_main:
            if cb.get():
                self.selected_categories_main.append(cat)
        if not self.selected_categories_main:
            self.category_button_main.configure(text="No categories selected")
        elif len(self.selected_categories_main) == 1:
            text = self.selected_categories_main[0][:28] + "..." if len(self.selected_categories_main[0]) > 28 else \
            self.selected_categories_main[0]
            self.category_button_main.configure(text=text)
        else:
            self.category_button_main.configure(text=f"{len(self.selected_categories_main)} categories selected")

        self.nearest_display_limit = 5

        if hasattr(self, 'nearest_scroll') and hasattr(self.nearest_scroll, '_parent_canvas'):
            self.nearest_scroll._parent_canvas.yview_moveto(0)

        self.update_nearest_systems()
        self.find_nearest_unclaimed()

    def on_closing(self):
        try:
            self._is_destroying = True
            self.stop_event.set()
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
            self.withdraw()
            self.update_idletasks()
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
            if hasattr(self, '_instance_lock') and self._instance_lock:
                try:
                    if sys.platform == 'win32':
                        import ctypes
                        ctypes.windll.kernel32.CloseHandle(self._instance_lock)
                except:
                    pass
            if hasattr(self, 'map_window') and self.map_window:
                try:
                    self.map_window.destroy()
                except:
                    pass

            def destroy_children(widget):
                children = list(widget.winfo_children())
                for child in children:
                    destroy_children(child)
                    try:
                        child.destroy()
                    except:
                        pass

            destroy_children(self)
            try:
                self.quit()
            except:
                pass
        except Exception as e:
            pass
        finally:
            os._exit(0)


if __name__ == "__main__":
    import tkinter as tk

    if sys.platform == 'win32':
        try:
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)
        except:
            try:
                windll.user32.SetProcessDPIAware()
            except:
                pass

    ctk.set_appearance_mode("dark")
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)

    _is_shutting_down = False


    def custom_tk_error_handler(exc, val, tb):
        global _is_shutting_down
        error_msg = str(val).lower()
        if _is_shutting_down or any(phrase in error_msg for phrase in
                                    ['invalid command name', 'application has been destroyed', 'bad window',
                                     'ctkcanvas']):
            return
        import traceback
        traceback.print_exception(exc, val, tb)
        instance_lock = check_single_instance()
        if instance_lock is None:
            sys.exit(0)
        app = App()
        app._instance_lock = instance_lock
        original_on_closing = app.on_closing

        def wrapped_on_closing():
            global _is_shutting_down
            _is_shutting_down = True
            original_on_closing()

        app.on_closing = wrapped_on_closing
        app.protocol("WM_DELETE_WINDOW", wrapped_on_closing)
        app.report_callback_exception = custom_tk_error_handler
        app.mainloop()


    instance_lock = check_single_instance()

    app = App()
    app._instance_lock = instance_lock

    original_on_closing = app.on_closing


    def wrapped_on_closing():
        global _is_shutting_down
        _is_shutting_down = True
        original_on_closing()


    app.on_closing = wrapped_on_closing
    app.protocol("WM_DELETE_WINDOW", wrapped_on_closing)
    app.report_callback_exception = custom_tk_error_handler
    app.mainloop()
