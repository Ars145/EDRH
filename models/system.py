"""
Data models for star systems in EDRH
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime

@dataclass
class StarSystem:
    """
    Represents a star system in Elite Dangerous
    """
    name: str
    position: Tuple[float, float, float] = None
    category: str = ""
    visited: bool = False
    claimed_by: str = ""
    claimed_date: Optional[datetime] = None
    is_done: bool = False
    images: List[str] = field(default_factory=list)
    info: str = ""
    distance: float = 0.0  # Distance from current system
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StarSystem':
        """Create a StarSystem from a dictionary"""
        position = None
        if 'x' in data and 'y' in data and 'z' in data:
            position = (data.get('x', 0.0), data.get('y', 0.0), data.get('z', 0.0))
            
        claimed_date = None
        if 'claimed_date' in data:
            try:
                if isinstance(data['claimed_date'], str):
                    claimed_date = datetime.fromisoformat(data['claimed_date'])
                elif isinstance(data['claimed_date'], datetime):
                    claimed_date = data['claimed_date']
            except:
                pass
                
        return cls(
            name=data.get('name', data.get('systems', '')),
            position=position,
            category=data.get('category', ''),
            visited=data.get('visited', False),
            claimed_by=data.get('claimed_by', data.get('by_cmdr', '')),
            claimed_date=claimed_date,
            is_done=data.get('is_done', False),
            images=data.get('images', []),
            info=data.get('info', ''),
            distance=data.get('distance', 0.0)
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary"""
        result = {
            'name': self.name,
            'category': self.category,
            'visited': self.visited,
            'claimed_by': self.claimed_by,
            'is_done': self.is_done,
            'images': self.images,
            'info': self.info,
            'distance': self.distance
        }
        
        if self.position:
            result['x'] = self.position[0]
            result['y'] = self.position[1]
            result['z'] = self.position[2]
            
        if self.claimed_date:
            result['claimed_date'] = self.claimed_date.isoformat()
            
        return result
        
    def calculate_distance(self, other_position: Tuple[float, float, float]) -> float:
        """Calculate distance to another position"""
        if not self.position or not other_position:
            return float('inf')
            
        return ((self.position[0] - other_position[0]) ** 2 +
                (self.position[1] - other_position[1]) ** 2 +
                (self.position[2] - other_position[2]) ** 2) ** 0.5


@dataclass
class SystemCategory:
    """
    Represents a category of star systems
    """
    name: str
    color: str = "#FFFFFF"
    image: str = ""
    count: int = 0
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'SystemCategory':
        """Create a SystemCategory from a name and dictionary"""
        return cls(
            name=name,
            color=data.get('color', "#FFFFFF"),
            image=data.get('image', ""),
            count=data.get('count', 0)
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary"""
        return {
            'name': self.name,
            'color': self.color,
            'image': self.image,
            'count': self.count
        }


class SystemManager:
    """
    Manages star systems and categories
    """
    def __init__(self):
        self.systems: Dict[str, StarSystem] = {}
        self.categories: Dict[str, SystemCategory] = {}
        self.current_system: Optional[StarSystem] = None
        self.current_position: Optional[Tuple[float, float, float]] = None
        
    def add_system(self, system: StarSystem) -> None:
        """Add or update a system"""
        self.systems[system.name] = system
        
        # Update category count
        if system.category and system.category in self.categories:
            self.categories[system.category].count += 1
            
    def add_category(self, category: SystemCategory) -> None:
        """Add or update a category"""
        self.categories[category.name] = category
        
    def get_system(self, name: str) -> Optional[StarSystem]:
        """Get a system by name"""
        return self.systems.get(name)
        
    def get_category(self, name: str) -> Optional[SystemCategory]:
        """Get a category by name"""
        return self.categories.get(name)
        
    def set_current_system(self, system_name: str, position: Optional[Tuple[float, float, float]] = None) -> None:
        """Set the current system"""
        system = self.get_system(system_name)
        if system:
            self.current_system = system
            if position:
                self.current_position = position
                system.position = position
        else:
            # Create a new system
            self.current_system = StarSystem(name=system_name, position=position)
            self.add_system(self.current_system)
            
        self.current_position = position or (self.current_system.position if self.current_system else None)
        
    def get_systems_by_category(self, category: str) -> List[StarSystem]:
        """Get all systems in a category"""
        return [s for s in self.systems.values() if s.category == category]
        
    def get_nearest_systems(self, count: int = 10, categories: List[str] = None, 
                           exclude_visited: bool = False, exclude_claimed: bool = False) -> List[StarSystem]:
        """
        Get the nearest systems to the current position
        
        Args:
            count: Maximum number of systems to return
            categories: List of categories to include (None for all)
            exclude_visited: Whether to exclude visited systems
            exclude_claimed: Whether to exclude claimed systems
            
        Returns:
            List of systems sorted by distance
        """
        if not self.current_position:
            return []
            
        # Filter systems
        filtered_systems = []
        for system in self.systems.values():
            if not system.position:
                continue
                
            if categories and system.category not in categories:
                continue
                
            if exclude_visited and system.visited:
                continue
                
            if exclude_claimed and system.claimed_by:
                continue
                
            # Calculate distance
            distance = system.calculate_distance(self.current_position)
            system.distance = distance
            filtered_systems.append(system)
            
        # Sort by distance
        filtered_systems.sort(key=lambda s: s.distance)
        
        # Return the nearest systems
        return filtered_systems[:count]
        
    def clear(self) -> None:
        """Clear all systems and categories"""
        self.systems.clear()
        self.categories.clear()
        self.current_system = None
        self.current_position = None


# Global system manager
_system_manager = SystemManager()

def get_system_manager() -> SystemManager:
    """Get the global system manager"""
    return _system_manager