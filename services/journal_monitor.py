"""
Journal file monitoring service for Elite Dangerous
"""

import os
import json
import time
import threading
import re
import winreg
import hashlib
from datetime import datetime, timezone
from config.settings import _cfg, save_config

# Constants
FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4

class JournalMonitor:
    """Monitor Elite Dangerous journal files for changes"""
    
    def __init__(self, journal_path, callback):
        """
        Initialize the journal monitor
        
        Args:
            journal_path: Path to the journal directory
            callback: Function to call when a new event is detected
                      Signature: callback(event_type, event_data)
        """
        self.journal_path = journal_path
        self.callback = callback
        self.current_file = None
        self.current_position = 0
        self.stop_event = threading.Event()
        self.commander_name = "Unknown"
        self.system_name = "Unknown"
        self.star_pos = None
        
    def start(self):
        """Start monitoring journal files"""
        self.stop_event.clear()
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        
    def stop(self):
        """Stop monitoring journal files"""
        self.stop_event.set()
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        last_journal = None
        last_size = 0
        last_mtime = 0
        
        # Find initial journal file
        initial_journal = self._find_latest_journal()
        if initial_journal:
            last_journal = initial_journal
            self.current_file = initial_journal
            self.commander_name = self._extract_commander_name(initial_journal)
            system_name, star_pos = self._extract_system_info(initial_journal)
            if system_name:
                self.system_name = system_name
            if star_pos:
                self.star_pos = star_pos
                
            # Notify about initial state
            self.callback("commander", {"name": self.commander_name})
            self.callback("system", {"name": self.system_name, "position": self.star_pos})
            
            # Set current position to end of file for incremental reading
            try:
                self.current_position = os.path.getsize(initial_journal)
            except:
                self.current_position = 0
        
        # Main monitoring loop
        while not self.stop_event.is_set():
            try:
                # Find latest journal file
                latest = self._find_latest_journal()
                if not latest:
                    time.sleep(1)
                    continue
                    
                # Check if file has changed
                try:
                    stat = os.stat(latest)
                    current_size = stat.st_size
                    current_mtime = stat.st_mtime
                except:
                    time.sleep(1)
                    continue
                
                # If new file or file has changed
                if latest != last_journal or current_size != last_size or current_mtime != last_mtime:
                    # If new file
                    if latest != last_journal:
                        last_journal = latest
                        self.current_file = latest
                        self.current_position = 0
                        
                        # Extract commander name if unknown
                        if self.commander_name == "Unknown":
                            self.commander_name = self._extract_commander_name(latest)
                            self.callback("commander", {"name": self.commander_name})
                    
                    # Update file stats
                    last_size = current_size
                    last_mtime = current_mtime
                    
                    # Read new content incrementally
                    self._read_new_content()
                
                # Sleep to reduce CPU usage
                time.sleep(1)
                
            except Exception as e:
                print(f"Error in journal monitor: {e}")
                time.sleep(5)
    
    def _read_new_content(self):
        """Read new content from the current journal file"""
        if not self.current_file or not os.path.exists(self.current_file):
            return
            
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                # Seek to last read position
                f.seek(self.current_position)
                
                # Read new lines
                new_lines = f.readlines()
                
                # Update position
                self.current_position = f.tell()
                
                # Process new lines
                for line in new_lines:
                    self._process_journal_line(line)
                    
        except Exception as e:
            print(f"Error reading journal file: {e}")
    
    def _process_journal_line(self, line):
        """Process a single journal line"""
        try:
            # Skip empty lines
            if not line.strip():
                return
                
            # Parse JSON
            event = json.loads(line)
            
            # Extract event type
            event_type = event.get("event")
            if not event_type:
                return
                
            # Process specific events
            if event_type in ["FSDJump", "Location", "CarrierJump"]:
                # Extract system information
                if "StarSystem" in event:
                    self.system_name = event["StarSystem"]
                    
                if "StarPos" in event:
                    coords = event["StarPos"]
                    if isinstance(coords, list) and len(coords) == 3:
                        self.star_pos = tuple(coords)
                        
                # Notify about system change
                self.callback("system", {
                    "name": self.system_name,
                    "position": self.star_pos,
                    "event": event_type
                })
                
            # Notify about all events
            self.callback("event", {"type": event_type, "data": event})
                
        except json.JSONDecodeError:
            # Ignore invalid JSON
            pass
        except Exception as e:
            print(f"Error processing journal line: {e}")
    
    def _find_latest_journal(self):
        """Find the latest journal file in the journal directory"""
        if not self.journal_path or not os.path.exists(self.journal_path):
            return None
            
        try:
            # Get all journal files
            journal_files = [
                os.path.join(self.journal_path, f) 
                for f in os.listdir(self.journal_path) 
                if f.startswith("Journal.") and f.endswith(".log")
            ]
            
            if not journal_files:
                return None
                
            # Sort by modification time (newest first)
            journal_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            return journal_files[0]
            
        except Exception as e:
            print(f"Error finding latest journal: {e}")
            return None
    
    def _extract_commander_name(self, journal_file):
        """Extract commander name from journal file"""
        try:
            with open(journal_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '"event":"Commander"' in line or '"event":"LoadGame"' in line:
                        data = json.loads(line)
                        if "Commander" in data:
                            return data["Commander"]
                        elif "Name" in data:
                            return data["Name"]
        except Exception as e:
            print(f"Error extracting commander name: {e}")
        
        return "Unknown"
    
    def _extract_system_info(self, journal_file):
        """Extract system name and position from journal file"""
        system_name = None
        star_pos = None
        
        try:
            with open(journal_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '"event":"FSDJump"' in line or '"event":"Location"' in line or '"event":"CarrierJump"' in line:
                        data = json.loads(line)
                        if "StarSystem" in data:
                            system_name = data["StarSystem"]
                        if "StarPos" in data:
                            coords = data["StarPos"]
                            if isinstance(coords, list) and len(coords) == 3:
                                star_pos = tuple(coords)
        except Exception as e:
            print(f"Error extracting system info: {e}")
        
        return system_name, star_pos


def auto_detect_journal_folder():
    """Auto-detect the Elite Dangerous journal folder"""
    # Common locations
    possible_locations = [
        os.path.expanduser("~/Saved Games/Frontier Developments/Elite Dangerous"),
        "C:/Users/*/Saved Games/Frontier Developments/Elite Dangerous",
        "D:/Users/*/Saved Games/Frontier Developments/Elite Dangerous"
    ]
    
    # Try registry key first
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Frontier Developments\Elite Dangerous\Options")
        value, _ = winreg.QueryValueEx(key, "AppDataPath")
        if value:
            journal_path = os.path.join(value, "Logs")
            if os.path.exists(journal_path):
                return journal_path
    except:
        pass
    
    # Try common locations
    for location in possible_locations:
        if "*" in location:
            # Handle wildcards
            parts = location.split("*")
            base = parts[0]
            if os.path.exists(os.path.dirname(base)):
                for item in os.listdir(os.path.dirname(base)):
                    full_path = base + item + parts[1]
                    if os.path.exists(full_path):
                        return full_path
        elif os.path.exists(location):
            return location
    
    return None


def analyze_journal_folder(folder_path):
    """Analyze a journal folder to extract commander information"""
    if not folder_path or not os.path.exists(folder_path):
        return None
        
    result = {
        "folder_path": folder_path,
        "commanders": {},
        "journal_count": 0,
        "latest_journal": None,
        "latest_date": None
    }
    
    try:
        # Get all journal files
        journal_files = [
            os.path.join(folder_path, f) 
            for f in os.listdir(folder_path) 
            if f.startswith("Journal.") and f.endswith(".log")
        ]
        
        result["journal_count"] = len(journal_files)
        
        if not journal_files:
            return result
            
        # Sort by modification time (newest first)
        journal_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        result["latest_journal"] = journal_files[0]
        result["latest_date"] = datetime.fromtimestamp(os.path.getmtime(journal_files[0])).strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract commander information from each file
        for journal_file in journal_files:
            try:
                with open(journal_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '"event":"Commander"' in line or '"event":"LoadGame"' in line:
                            data = json.loads(line)
                            cmdr_name = data.get("Commander", data.get("Name", "Unknown"))
                            
                            if cmdr_name not in result["commanders"]:
                                result["commanders"][cmdr_name] = {
                                    "first_seen": os.path.getmtime(journal_file),
                                    "last_seen": os.path.getmtime(journal_file),
                                    "journal_count": 1,
                                    "latest_journal": journal_file
                                }
                            else:
                                cmdr_data = result["commanders"][cmdr_name]
                                cmdr_data["journal_count"] += 1
                                
                                if os.path.getmtime(journal_file) > cmdr_data["last_seen"]:
                                    cmdr_data["last_seen"] = os.path.getmtime(journal_file)
                                    cmdr_data["latest_journal"] = journal_file
                                    
                                if os.path.getmtime(journal_file) < cmdr_data["first_seen"]:
                                    cmdr_data["first_seen"] = os.path.getmtime(journal_file)
                            
                            # Format dates
                            for cmdr in result["commanders"]:
                                cmdr_data = result["commanders"][cmdr]
                                cmdr_data["first_seen_date"] = datetime.fromtimestamp(cmdr_data["first_seen"]).strftime("%Y-%m-%d %H:%M:%S")
                                cmdr_data["last_seen_date"] = datetime.fromtimestamp(cmdr_data["last_seen"]).strftime("%Y-%m-%d %H:%M:%S")
            except:
                continue
                
        return result
        
    except Exception as e:
        print(f"Error analyzing journal folder: {e}")
        return None


def detect_commander_renames(journal_path):
    """Detect commander renames by analyzing journal files"""
    if not journal_path or not os.path.exists(journal_path):
        return []
        
    commanders = []
    
    try:
        # Get all journal files
        journal_files = [
            os.path.join(journal_path, f) 
            for f in os.listdir(journal_path) 
            if f.startswith("Journal.") and f.endswith(".log")
        ]
        
        if not journal_files:
            return commanders
            
        # Extract commander names from each file
        for journal_file in journal_files:
            try:
                with open(journal_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '"event":"Commander"' in line or '"event":"LoadGame"' in line:
                            data = json.loads(line)
                            cmdr_name = data.get("Commander", data.get("Name", "Unknown"))
                            
                            if cmdr_name != "Unknown" and cmdr_name not in commanders:
                                commanders.append(cmdr_name)
            except:
                continue
                
        return commanders
        
    except Exception as e:
        print(f"Error detecting commander renames: {e}")
        return []


def check_if_locked(cmdr_name):
    """Check if a commander is locked (already running in another instance)"""
    if not cmdr_name or cmdr_name == "Unknown":
        return False
        
    try:
        # Check registry lock
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\EDRH")
        value, _ = winreg.QueryValueEx(key, f"lock_{hashlib.md5(cmdr_name.encode()).hexdigest()}")
        if value == "LOCKED":
            return True
    except:
        pass
        
    # Check file lock
    try:
        appdata = os.getenv('APPDATA')
        lock_dir = os.path.join(appdata, "EDRH", "locks")
        os.makedirs(lock_dir, exist_ok=True)
        
        lock_path = os.path.join(lock_dir, f"{hashlib.md5(cmdr_name.encode()).hexdigest()}.lock")
        
        if os.path.exists(lock_path):
            # Check if lock is stale (older than 5 minutes)
            if time.time() - os.path.getmtime(lock_path) < 300:
                return True
            else:
                # Remove stale lock
                try:
                    os.remove(lock_path)
                except:
                    pass
    except:
        pass
        
    return False


def create_hidden_lock_file(cmdr_name):
    """Create a hidden lock file for a commander"""
    if not cmdr_name or cmdr_name == "Unknown":
        return False
        
    try:
        import ctypes
        
        appdata = os.getenv('APPDATA')
        lock_dir = os.path.join(appdata, "EDRH", "locks")
        os.makedirs(lock_dir, exist_ok=True)
        
        lock_path = os.path.join(lock_dir, f"{hashlib.md5(cmdr_name.encode()).hexdigest()}.lock")
        
        with open(lock_path, 'w') as f:
            f.write(f"LOCKED:{cmdr_name}:{int(time.time())}")
            
        # Make file hidden and system
        ctypes.windll.kernel32.SetFileAttributesW(lock_path, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
        
        # Also set registry lock
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\EDRH")
            winreg.SetValueEx(key, f"lock_{hashlib.md5(cmdr_name.encode()).hexdigest()}", 0, winreg.REG_SZ, "LOCKED")
            winreg.CloseKey(key)
        except:
            pass
            
        return True
        
    except:
        return False