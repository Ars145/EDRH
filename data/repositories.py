"""
Repository classes for Elite Dangerous Records Helper.
Provides a layer of abstraction between the database and the application.
"""

from typing import List, Dict, Optional, Any, Union
from .models import System, Commander, CategoryImage, JournalEvent


class SystemRepository:
    """Repository for star system data."""

    def __init__(self, database_service):
        """Initialize the system repository.

        Args:
            database_service: The database service instance.
        """
        self.db = database_service

    def get_all(self) -> List[System]:
        """Get all systems.

        Returns:
            List[System]: List of all systems.
        """
        systems_data = self.db.get_systems()
        return [System.from_dict(data) for data in systems_data]

    def get_by_name(self, name: str) -> Optional[System]:
        """Get a system by name.

        Args:
            name (str): The system name.

        Returns:
            Optional[System]: The system, or None if not found.
        """
        systems_data = self.db.get_systems({"name": name})
        if not systems_data:
            return None
        return System.from_dict(systems_data[0])

    def get_by_filter(self, filters: Dict[str, Any]) -> List[System]:
        """Get systems by filter.

        Args:
            filters (Dict[str, Any]): Filters to apply.

        Returns:
            List[System]: List of systems matching the filter.
        """
        systems_data = self.db.get_systems(filters)
        return [System.from_dict(data) for data in systems_data]

    def add(self, system: System) -> Optional[System]:
        """Add a new system.

        Args:
            system (System): The system to add.

        Returns:
            Optional[System]: The added system with ID, or None if failed.
        """
        system_data = system.to_dict()
        result = self.db.add_system(system_data)
        if not result:
            return None
        return System.from_dict(result)

    def update(self, system: System) -> Optional[System]:
        """Update an existing system.

        Args:
            system (System): The system to update.

        Returns:
            Optional[System]: The updated system, or None if failed.
        """
        if system.id is None:
            return None

        system_data = system.to_dict()
        result = self.db.update_system(system.id, system_data)
        if not result:
            return None
        return System.from_dict(result)

    def delete(self, system_id: int) -> bool:
        """Delete a system.

        Args:
            system_id (int): The system ID.

        Returns:
            bool: True if successful, False otherwise.
        """
        return self.db.delete_system(system_id)

    def claim(self, system_name: str, commander_name: str) -> bool:
        """Claim a system for a commander.

        Args:
            system_name (str): The system name.
            commander_name (str): The commander name.

        Returns:
            bool: True if successful, False otherwise.
        """
        system = self.get_by_name(system_name)
        if not system:
            return False

        system.commander = commander_name
        return self.update(system) is not None

    def unclaim(self, system_name: str) -> bool:
        """Unclaim a system.

        Args:
            system_name (str): The system name.

        Returns:
            bool: True if successful, False otherwise.
        """
        system = self.get_by_name(system_name)
        if not system:
            return False

        system.commander = None
        return self.update(system) is not None

    def mark_visited(self, system_name: str) -> bool:
        """Mark a system as visited.

        Args:
            system_name (str): The system name.

        Returns:
            bool: True if successful, False otherwise.
        """
        system = self.get_by_name(system_name)
        if not system:
            return False

        system.visited = True
        return self.update(system) is not None

    def mark_done(self, system_name: str) -> bool:
        """Mark a system as done.

        Args:
            system_name (str): The system name.

        Returns:
            bool: True if successful, False otherwise.
        """
        system = self.get_by_name(system_name)
        if not system:
            return False

        system.done = True
        return self.update(system) is not None

    def get_nearest_systems(self, current_x: float, current_y: float, current_z: float, 
                           limit: int = 20, category_filter: List[str] = None) -> List[System]:
        """Get systems nearest to the specified coordinates.

        Args:
            current_x (float): Current X coordinate
            current_y (float): Current Y coordinate
            current_z (float): Current Z coordinate
            limit (int, optional): Maximum number of systems to return
            category_filter (List[str], optional): List of categories to filter by

        Returns:
            List[System]: List of nearest systems
        """
        if not self.db.is_connected():
            return []

        try:
            # Get all systems
            systems_data = self.db.get_systems()

            # Calculate distances
            systems_with_distance = []
            for system_data in systems_data:
                try:
                    system = System.from_dict(system_data)

                    # Apply category filter if specified
                    if category_filter and "All Categories" not in category_filter:
                        # Skip if system categories don't match filter
                        if not any(cat in system.categories for cat in category_filter):
                            continue

                    # Calculate distance
                    dx = system.x - current_x
                    dy = system.y - current_y
                    dz = system.z - current_z
                    distance = (dx * dx + dy * dy + dz * dz) ** 0.5

                    systems_with_distance.append((system, distance))
                except Exception as e:
                    print(f"[ERROR] Error processing system {system_data.get('name', 'Unknown')}: {e}")
                    continue

            # Sort by distance
            systems_with_distance.sort(key=lambda x: x[1])

            # Return limited number of systems
            return [system for system, _ in systems_with_distance[:limit]]
        except Exception as e:
            print(f"[ERROR] Error getting nearest systems: {e}")
            return []

    def get_unclaimed_systems(self, current_x: float, current_y: float, current_z: float,
                             category_filter: List[str] = None) -> List[Dict[str, Any]]:
        """Get unclaimed systems sorted by distance.

        Args:
            current_x (float): Current X coordinate
            current_y (float): Current Y coordinate
            current_z (float): Current Z coordinate
            category_filter (List[str], optional): List of categories to filter by

        Returns:
            List[Dict[str, Any]]: List of unclaimed systems with distance
        """
        if not self.db.is_connected():
            return []

        try:
            # Get all systems
            systems_data = self.db.get_systems()

            # Get taken systems
            taken_systems = set()
            try:
                taken_data = self.db.supabase.table("taken").select("system").execute().data
                taken_systems = {item["system"] for item in taken_data}
            except Exception as e:
                print(f"[ERROR] Error getting taken systems: {e}")

            # Get POI systems
            poi_systems = set()
            try:
                poi_data = self.db.supabase.table("pois").select("system_name").execute().data
                poi_systems = {item["system_name"] for item in poi_data}
            except Exception as e:
                print(f"[ERROR] Error getting POI systems: {e}")

            # Filter and calculate distances
            unclaimed_systems = []
            for system_data in systems_data:
                try:
                    system_name = system_data.get("name", "")
                    if not system_name or system_name in taken_systems or system_name in poi_systems:
                        continue

                    # Get categories
                    categories = system_data.get('category', [])
                    if isinstance(categories, str):
                        if categories.startswith('[') and categories.endswith(']'):
                            try:
                                import json
                                categories = json.loads(categories)
                            except:
                                categories = [categories]
                        else:
                            categories = [categories]

                    # Apply category filter if specified
                    if category_filter and "All Categories" not in category_filter:
                        # Skip if system categories don't match filter
                        if not any(cat in categories for cat in category_filter):
                            continue

                    # Calculate distance
                    try:
                        x = float(system_data.get("x", 0))
                        y = float(system_data.get("y", 0))
                        z = float(system_data.get("z", 0))

                        dx = x - current_x
                        dy = y - current_y
                        dz = z - current_z
                        distance = (dx * dx + dy * dy + dz * dz) ** 0.5

                        unclaimed_systems.append({
                            "systems": system_name,  # Match UI_main.py field name
                            "category": system_data.get("category", ""),
                            "x": x,
                            "y": y,
                            "z": z,
                            "distance": distance
                        })
                    except (ValueError, TypeError) as e:
                        print(f"[ERROR] Error processing coordinates for system {system_name}: {e}")
                        continue
                except Exception as e:
                    print(f"[ERROR] Error processing system: {e}")
                    continue

            # Sort by distance
            unclaimed_systems.sort(key=lambda x: x["distance"])
            return unclaimed_systems
        except Exception as e:
            print(f"[ERROR] Error getting unclaimed systems: {e}")
            return []


class CommanderRepository:
    """Repository for commander data."""

    def __init__(self, database_service):
        """Initialize the commander repository.

        Args:
            database_service: The database service instance.
        """
        self.db = database_service

    def get_by_name(self, name: str) -> Optional[Commander]:
        """Get a commander by name.

        Args:
            name (str): The commander name.

        Returns:
            Optional[Commander]: The commander, or None if not found.
        """
        commander_data = self.db.get_security_entry(name)
        if not commander_data:
            return None
        return Commander.from_dict(commander_data)

    def add(self, commander: Commander) -> bool:
        """Add a new commander.

        Args:
            commander (Commander): The commander to add.

        Returns:
            bool: True if successful, False otherwise.
        """
        commander_data = commander.to_dict()
        return self.db.add_security_entry(commander_data)

    def block(self, name: str, reason: str = "") -> bool:
        """Block a commander.

        Args:
            name (str): The commander name.
            reason (str, optional): The reason for blocking.

        Returns:
            bool: True if successful, False otherwise.
        """
        return self.db.block_commander(name, reason)

    def unblock(self, name: str) -> bool:
        """Unblock a commander.

        Args:
            name (str): The commander name.

        Returns:
            bool: True if successful, False otherwise.
        """
        return self.db.unblock_commander(name)

    def get_blocked(self) -> List[Commander]:
        """Get all blocked commanders.

        Returns:
            List[Commander]: List of blocked commanders.
        """
        commanders_data = self.db.get_blocked_commanders()
        return [Commander.from_dict(data) for data in commanders_data]

    def is_admin(self, name: str) -> bool:
        """Check if a commander is an admin.

        Args:
            name (str): The commander name.

        Returns:
            bool: True if admin, False otherwise.
        """
        return self.db.check_admin_status(name)


class CategoryRepository:
    """Repository for category data."""

    def __init__(self, database_service):
        """Initialize the category repository.

        Args:
            database_service: The database service instance.
        """
        self.db = database_service

    def get_category_images(self) -> Dict[str, str]:
        """Get category images.

        Returns:
            Dict[str, str]: Dictionary of category images.
        """
        return self.db.get_category_images()

    def get_category_colors(self, config_manager) -> Dict[str, str]:
        """Get category colors from configuration.

        Args:
            config_manager: The configuration manager instance.

        Returns:
            Dict[str, str]: Dictionary of category colors.
        """
        return config_manager.get("category_colors", {})

    def set_category_color(self, config_manager, category: str, color: str) -> bool:
        """Set a category color in configuration.

        Args:
            config_manager: The configuration manager instance.
            category (str): The category name.
            color (str): The color value.

        Returns:
            bool: True if successful, False otherwise.
        """
        colors = config_manager.get("category_colors", {})
        colors[category] = color
        return config_manager.set("category_colors", colors)
