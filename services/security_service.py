"""
Security service for Elite Dangerous Records Helper.
Handles authentication, authorization, and security checks.
"""

import os
import hashlib
import winreg
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any


class SecurityService:
    """Manages authentication, authorization, and security checks"""
    
    def __init__(self, config_manager, database_service, commander_manager=None):
        """Initialize the security service.
        
        Args:
            config_manager: The configuration manager instance.
            database_service: The database service instance.
            commander_manager: The commander manager instance.
        """
        self.config = config_manager
        self.db = database_service
        self.commander_manager = commander_manager
    
    def verify_commander(self, commander_name: str, journal_path: str = None) -> Dict[str, Any]:
        """Verify a commander's security status.
        
        Args:
            commander_name (str): The commander name to verify.
            journal_path (str, optional): Path to the journal directory.
        
        Returns:
            Dict[str, Any]: Verification result with status and message.
        """
        if not self.db.is_connected():
            return {"status": "unknown", "message": "No database connection"}
        
        if commander_name == "Unknown":
            return {"status": "unknown", "message": "Commander name unknown"}
        
        # Check auto-block list
        auto_block_list = ["Arcanic", "Julian Ford"]
        if commander_name in auto_block_list:
            self._block_commander(commander_name, "Auto-blocked commander")
            return {
                "status": "blocked",
                "message": f"Commander {commander_name} is auto-blocked"
            }
        
        # Check for commander renames if journal path is provided
        banned_commander = None
        if journal_path and os.path.exists(journal_path):
            all_commanders = self._detect_commander_renames(journal_path)
            if len(all_commanders) > 1:
                print(f"[DEBUG] Multiple commanders detected: {all_commanders}")
                
                for cmdr in all_commanders:
                    if cmdr != commander_name:
                        is_blocked = self._check_if_blocked(cmdr)
                        if is_blocked:
                            banned_commander = cmdr
                            break
        
        if banned_commander:
            self._log_rename_attempt(commander_name, banned_commander)
            return {
                "status": "blocked",
                "message": f"Rename detected! {banned_commander} is banned."
            }
        
        # Check if the current commander is blocked
        is_blocked = self._check_if_blocked(commander_name)
        if is_blocked:
            return {
                "status": "blocked",
                "message": f"Commander {commander_name} is blocked"
            }
        
        # If commander is not in the security table, add them
        security_check = self._get_security_entry(commander_name)
        if not security_check:
            rename_info = None
            if journal_path and os.path.exists(journal_path):
                all_commanders = self._detect_commander_renames(journal_path)
                if len(all_commanders) > 1:
                    rename_info = f"Multiple names detected: {', '.join(all_commanders)}"
            
            self._add_new_commander(commander_name, journal_path, rename_info)
            return {
                "status": "allowed",
                "message": f"Commander {commander_name} is allowed (new user)"
            }
        
        return {
            "status": "allowed",
            "message": f"Commander {commander_name} is allowed"
        }
    
    def check_admin_status(self, commander_name: str) -> bool:
        """Check if a commander has admin status.
        
        Args:
            commander_name (str): The commander name.
        
        Returns:
            bool: True if admin, False otherwise.
        """
        if not self.db.is_connected():
            return False
        
        return self.db.check_admin_status(commander_name)
    
    def get_blocked_commanders(self) -> List[Dict[str, Any]]:
        """Get a list of blocked commanders.
        
        Returns:
            List[Dict[str, Any]]: List of blocked commanders.
        """
        if not self.db.is_connected():
            return []
        
        return self.db.get_blocked_commanders()
    
    def block_commander(self, commander_name: str, reason: str = "") -> bool:
        """Block a commander.
        
        Args:
            commander_name (str): The commander name.
            reason (str, optional): The reason for blocking.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.db.is_connected():
            return False
        
        return self.db.block_commander(commander_name, reason)
    
    def unblock_commander(self, commander_name: str) -> bool:
        """Unblock a commander.
        
        Args:
            commander_name (str): The commander name.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.db.is_connected():
            return False
        
        return self.db.unblock_commander(commander_name)
    
    def create_hidden_lock_file(self, commander_name: str) -> bool:
        """Create a hidden lock file for a commander.
        
        Args:
            commander_name (str): The commander name.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if commander_name == "Unknown":
            return False
        
        try:
            # Create a registry key to lock the commander
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\EDRH")
            winreg.SetValueEx(
                key,
                f"lock_{hashlib.md5(commander_name.encode()).hexdigest()}",
                0,
                winreg.REG_SZ,
                "LOCKED"
            )
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[ERROR] Error creating hidden lock file: {e}")
            return False
    
    def check_if_locked(self, commander_name: str) -> bool:
        """Check if a commander is locked.
        
        Args:
            commander_name (str): The commander name.
        
        Returns:
            bool: True if locked, False otherwise.
        """
        if commander_name == "Unknown":
            return False
        
        try:
            # Check if the registry key exists
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\EDRH",
                0,
                winreg.KEY_READ
            )
            
            lock_value = f"lock_{hashlib.md5(commander_name.encode()).hexdigest()}"
            try:
                value, _ = winreg.QueryValueEx(key, lock_value)
                winreg.CloseKey(key)
                return value == "LOCKED"
            except:
                winreg.CloseKey(key)
                return False
        except:
            return False
    
    def _check_if_blocked(self, commander_name: str) -> bool:
        """Check if a commander is blocked.
        
        Args:
            commander_name (str): The commander name.
        
        Returns:
            bool: True if blocked, False otherwise.
        """
        try:
            security_entry = self._get_security_entry(commander_name)
            return security_entry.get("blocked", False) if security_entry else False
        except Exception as e:
            print(f"[ERROR] Error checking if commander is blocked: {e}")
            return False
    
    def _get_security_entry(self, commander_name: str) -> Optional[Dict[str, Any]]:
        """Get a commander's security entry.
        
        Args:
            commander_name (str): The commander name.
        
        Returns:
            Optional[Dict[str, Any]]: The security entry, or None if not found.
        """
        try:
            return self.db.get_security_entry(commander_name)
        except Exception as e:
            print(f"[ERROR] Error getting security entry: {e}")
            return None
    
    def _add_new_commander(self, commander_name: str, journal_path: str = None, rename_info: str = None) -> bool:
        """Add a new commander to the security table.
        
        Args:
            commander_name (str): The commander name.
            journal_path (str, optional): Path to the journal directory.
            rename_info (str, optional): Information about commander renames.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            security_data = {
                "name": commander_name,
                "blocked": False,
                "first_seen": datetime.now(timezone.utc).isoformat(),
                "journal_path": journal_path or self.config.get("journal_path", "Unknown")
            }
            
            if rename_info:
                security_data["notes"] = rename_info
            
            return self.db.add_security_entry(security_data)
        except Exception as e:
            print(f"[ERROR] Error adding new commander: {e}")
            return False
    
    def _log_rename_attempt(self, commander_name: str, banned_commander: str) -> bool:
        """Log a rename attempt.
        
        Args:
            commander_name (str): The commander name.
            banned_commander (str): The banned commander name.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            return self.db.log_rename_attempt(commander_name, banned_commander)
        except Exception as e:
            print(f"[ERROR] Error logging rename attempt: {e}")
            return False
    
    def _detect_commander_renames(self, journal_path: str) -> List[str]:
        """Detect commander renames by checking journal files.
        
        Args:
            journal_path (str): Path to the journal directory.
        
        Returns:
            List[str]: List of commander names found in the journal files.
        """
        if self.commander_manager:
            # Use the commander manager if available
            return self.commander_manager.detect_commander_renames()
        
        # Otherwise, implement a simplified version
        commanders = set()
        
        if not os.path.exists(journal_path):
            return list(commanders)
        
        # Find journal files
        journal_files = []
        for filename in os.listdir(journal_path):
            if filename.startswith("Journal.") and filename.endswith(".log"):
                journal_files.append(os.path.join(journal_path, filename))
        
        # Extract commander names from journal files
        for journal_file in journal_files:
            try:
                with open(journal_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            import json
                            event = json.loads(line)
                            if event.get("event") == "Commander" and "Name" in event:
                                commanders.add(event["Name"])
                            elif event.get("event") == "LoadGame" and "Commander" in event:
                                commanders.add(event["Commander"])
                        except:
                            continue
            except:
                continue
        
        return list(commanders)