"""
Database service for Elite Dangerous Records Helper.
Handles Supabase interactions and database operations.
"""

import sys
import httpx
from supabase import create_client
from datetime import datetime, timezone


class DatabaseService:
    """Manages database interactions with Supabase"""
    
    def __init__(self, config_manager):
        """Initialize the database service.
        
        Args:
            config_manager: The configuration manager instance.
        """
        self.config = config_manager
        self.supabase = None
        self.login_events_client = None
        self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialize Supabase client with error handling."""
        url = self.config.get("supabase_url", "")
        key = self.config.get("supabase_key", "")
        auth_key = self.config.get("supabase_auth_confirmation", "")
        
        if not url or not key:
            print("[ERROR] Missing Supabase URL or key in configuration")
            return
        
        # Try to initialize with auth confirmation key if available
        if isinstance(auth_key, str) and auth_key:
            try:
                self.supabase = create_client(url, auth_key)
                # Test the connection
                self.supabase.table("admin_access").select("id").limit(1).execute()
                print("[DEBUG] Supabase initialized with auth confirmation key")
                return
            except Exception as e:
                print(f"[ERROR] Failed to initialize Supabase with auth key: {e}")
        
        # Fall back to regular key
        try:
            if getattr(sys, 'frozen', False):
                # Create a custom HTTP client for better performance in frozen mode
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
            
            self.supabase = create_client(url, key)
            print("[DEBUG] Supabase initialized with regular key")
            
            # Initialize login events client
            try:
                self.login_events_client = create_client(url, key)
                self.login_events_client.table('login_events').select('*').limit(1).execute()
                print("[DEBUG] Login events client initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize login events client: {e}")
                self.login_events_client = None
                
        except Exception as e:
            print(f"[ERROR] Failed to initialize Supabase: {e}")
            self.supabase = None
    
    def is_connected(self):
        """Check if connected to Supabase.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        return self.supabase is not None
    
    def get_systems(self, filters=None):
        """Get systems with optional filtering.
        
        Args:
            filters (dict, optional): Filters to apply to the query.
        
        Returns:
            list: List of systems matching the filters.
        """
        if not self.is_connected():
            return []
        
        try:
            query = self.supabase.table("systems").select("*")
            
            if filters:
                if "name" in filters:
                    query = query.ilike("name", f"%{filters['name']}%")
                if "category" in filters:
                    query = query.ilike("category", f"%{filters['category']}%")
                if "commander" in filters:
                    query = query.eq("commander", filters["commander"])
                if "claimed" in filters:
                    if filters["claimed"]:
                        query = query.not_.is_("commander", "null")
                    else:
                        query = query.is_("commander", "null")
                if "visited" in filters:
                    query = query.eq("visited", filters["visited"])
                if "done" in filters:
                    query = query.eq("done", filters["done"])
            
            result = query.execute()
            return result.data
        except Exception as e:
            print(f"[ERROR] Error getting systems: {e}")
            return []
    
    def add_system(self, system_data):
        """Add a new system.
        
        Args:
            system_data (dict): System data to add.
        
        Returns:
            dict: The added system data, or None if failed.
        """
        if not self.is_connected():
            return None
        
        try:
            result = self.supabase.table("systems").insert(system_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"[ERROR] Error adding system: {e}")
            return None
    
    def update_system(self, system_id, system_data):
        """Update an existing system.
        
        Args:
            system_id (int): The system ID.
            system_data (dict): System data to update.
        
        Returns:
            dict: The updated system data, or None if failed.
        """
        if not self.is_connected():
            return None
        
        try:
            result = self.supabase.table("systems").update(system_data).eq("id", system_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"[ERROR] Error updating system: {e}")
            return None
    
    def delete_system(self, system_id):
        """Delete a system.
        
        Args:
            system_id (int): The system ID.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.is_connected():
            return False
        
        try:
            result = self.supabase.table("systems").delete().eq("id", system_id).execute()
            return bool(result.data)
        except Exception as e:
            print(f"[ERROR] Error deleting system: {e}")
            return False
    
    def get_category_images(self):
        """Get category images.
        
        Returns:
            dict: Dictionary of category images.
        """
        if not self.is_connected():
            return {}
        
        try:
            result = self.supabase.table("category_images").select("*").execute()
            
            category_images = {}
            for item in result.data:
                category = item.get("category", "")
                image_url = item.get("image_url", "")
                if category and image_url:
                    category_images[category] = image_url
            
            return category_images
        except Exception as e:
            print(f"[ERROR] Error getting category images: {e}")
            return {}
    
    def get_security_status(self, commander_name):
        """Get a commander's security status.
        
        Args:
            commander_name (str): The commander name.
        
        Returns:
            dict: The security status, or None if not found.
        """
        if not self.is_connected():
            return None
        
        try:
            result = self.supabase.table("security").select("*").eq("name", commander_name).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"[ERROR] Error getting security status: {e}")
            return None
    
    def get_security_entry(self, commander_name):
        """Get a commander's security entry.
        
        Args:
            commander_name (str): The commander name.
        
        Returns:
            dict: The security entry, or None if not found.
        """
        return self.get_security_status(commander_name)
    
    def block_commander(self, commander_name, reason=""):
        """Block a commander.
        
        Args:
            commander_name (str): The commander name.
            reason (str, optional): The reason for blocking.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.is_connected():
            return False
        
        try:
            security_data = {
                "name": commander_name,
                "blocked": True
            }
            
            if reason:
                security_data["notes"] = reason
            
            result = self.supabase.table("security").upsert(security_data).execute()
            return bool(result.data)
        except Exception as e:
            print(f"[ERROR] Error blocking commander: {e}")
            return False
    
    def add_security_entry(self, security_data):
        """Add a new security entry.
        
        Args:
            security_data (dict): Security data to add.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.is_connected():
            return False
        
        try:
            result = self.supabase.table("security").insert(security_data).execute()
            
            # Log new user event
            if self.login_events_client:
                try:
                    event_type = 'new_user'
                    if security_data.get("notes") and "Multiple names detected" in security_data["notes"]:
                        event_type = 'new_user_with_alts'
                    
                    self.login_events_client.table('login_events').insert({
                        'commander': security_data["name"],
                        'is_admin': False,
                        'login_time': datetime.now(timezone.utc).isoformat(),
                        'app_version': self.config.get("app_version", "Unknown"),
                        'event_type': event_type,
                        'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'
                    }).execute()
                except Exception as e:
                    print(f"[ERROR] Failed to log new user event: {e}")
            
            return bool(result.data)
        except Exception as e:
            print(f"[ERROR] Error adding security entry: {e}")
            return False
    
    def log_rename_attempt(self, commander_name, banned_commander):
        """Log a rename attempt.
        
        Args:
            commander_name (str): The commander name.
            banned_commander (str): The banned commander name.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.login_events_client:
            return False
        
        try:
            result = self.login_events_client.table('login_events').insert({
                'commander': f"{commander_name} (linked to {banned_commander})",
                'is_admin': False,
                'login_time': datetime.now(timezone.utc).isoformat(),
                'app_version': self.config.get("app_version", "Unknown"),
                'event_type': 'rename_attempt',
                'webhook_id': 'https://discord.com/api/webhooks/1386234211928903681/uQB4XGehER9Bq4kRtJvcPuZq5nFeaQzlcjyVPVLrsaFwITpd9tYdEzL7AqkBBts6sdV2'
            }).execute()
            return bool(result.data)
        except Exception as e:
            print(f"[ERROR] Error logging rename attempt: {e}")
            return False
    
    def check_admin_status(self, commander_name):
        """Check if a commander has admin status.
        
        Args:
            commander_name (str): The commander name.
        
        Returns:
            bool: True if admin, False otherwise.
        """
        if not self.is_connected():
            return False
        
        try:
            result = self.supabase.table("admin_access").select("*").eq("commander", commander_name).execute()
            return bool(result.data)
        except Exception as e:
            print(f"[ERROR] Error checking admin status: {e}")
            return False
    
    def get_blocked_commanders(self):
        """Get a list of blocked commanders.
        
        Returns:
            list: List of blocked commanders.
        """
        if not self.is_connected():
            return []
        
        try:
            result = self.supabase.table("security").select("*").eq("blocked", True).execute()
            return result.data
        except Exception as e:
            print(f"[ERROR] Error getting blocked commanders: {e}")
            return []
    
    def unblock_commander(self, commander_name):
        """Unblock a commander.
        
        Args:
            commander_name (str): The commander name.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.is_connected():
            return False
        
        try:
            result = self.supabase.table("security").update({"blocked": False}).eq("name", commander_name).execute()
            return bool(result.data)
        except Exception as e:
            print(f"[ERROR] Error unblocking commander: {e}")
            return False