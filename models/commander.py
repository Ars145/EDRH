"""
Data models for commanders in EDRH
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime

@dataclass
class Commander:
    """
    Represents a commander in Elite Dangerous
    """
    name: str
    current_system: str = "Unknown"
    position: Tuple[float, float, float] = None
    is_admin: bool = False
    blocked: bool = False
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    claimed_systems: List[str] = field(default_factory=list)
    visited_systems: List[str] = field(default_factory=list)
    notes: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Commander':
        """Create a Commander from a dictionary"""
        position = None
        if 'x' in data and 'y' in data and 'z' in data:
            position = (data.get('x', 0.0), data.get('y', 0.0), data.get('z', 0.0))
            
        first_seen = None
        if 'first_seen' in data:
            try:
                if isinstance(data['first_seen'], str):
                    first_seen = datetime.fromisoformat(data['first_seen'])
                elif isinstance(data['first_seen'], datetime):
                    first_seen = data['first_seen']
            except:
                pass
                
        last_seen = None
        if 'last_seen' in data:
            try:
                if isinstance(data['last_seen'], str):
                    last_seen = datetime.fromisoformat(data['last_seen'])
                elif isinstance(data['last_seen'], datetime):
                    last_seen = data['last_seen']
            except:
                pass
                
        return cls(
            name=data.get('name', ''),
            current_system=data.get('current_system', 'Unknown'),
            position=position,
            is_admin=data.get('is_admin', False),
            blocked=data.get('blocked', False),
            first_seen=first_seen,
            last_seen=last_seen,
            claimed_systems=data.get('claimed_systems', []),
            visited_systems=data.get('visited_systems', []),
            notes=data.get('notes', '')
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary"""
        result = {
            'name': self.name,
            'current_system': self.current_system,
            'is_admin': self.is_admin,
            'blocked': self.blocked,
            'claimed_systems': self.claimed_systems,
            'visited_systems': self.visited_systems,
            'notes': self.notes
        }
        
        if self.position:
            result['x'] = self.position[0]
            result['y'] = self.position[1]
            result['z'] = self.position[2]
            
        if self.first_seen:
            result['first_seen'] = self.first_seen.isoformat()
            
        if self.last_seen:
            result['last_seen'] = self.last_seen.isoformat()
            
        return result
        
    def update_position(self, system_name: str, position: Optional[Tuple[float, float, float]] = None) -> None:
        """Update the commander's position"""
        self.current_system = system_name
        if position:
            self.position = position
            
        self.last_seen = datetime.now()
        
        # Add to visited systems if not already there
        if system_name not in self.visited_systems:
            self.visited_systems.append(system_name)
            
    def claim_system(self, system_name: str) -> None:
        """Claim a system"""
        if system_name not in self.claimed_systems:
            self.claimed_systems.append(system_name)
            
    def unclaim_system(self, system_name: str) -> None:
        """Unclaim a system"""
        if system_name in self.claimed_systems:
            self.claimed_systems.remove(system_name)


class CommanderManager:
    """
    Manages commanders
    """
    def __init__(self):
        self.commanders: Dict[str, Commander] = {}
        self.current_commander: Optional[Commander] = None
        
    def add_commander(self, commander: Commander) -> None:
        """Add or update a commander"""
        self.commanders[commander.name] = commander
        
    def get_commander(self, name: str) -> Optional[Commander]:
        """Get a commander by name"""
        return self.commanders.get(name)
        
    def set_current_commander(self, name: str) -> None:
        """Set the current commander"""
        commander = self.get_commander(name)
        if commander:
            self.current_commander = commander
        else:
            # Create a new commander
            self.current_commander = Commander(name=name)
            self.add_commander(self.current_commander)
            
    def get_blocked_commanders(self) -> List[Commander]:
        """Get all blocked commanders"""
        return [c for c in self.commanders.values() if c.blocked]
        
    def get_admin_commanders(self) -> List[Commander]:
        """Get all admin commanders"""
        return [c for c in self.commanders.values() if c.is_admin]
        
    def clear(self) -> None:
        """Clear all commanders"""
        self.commanders.clear()
        self.current_commander = None


# Global commander manager
_commander_manager = CommanderManager()

def get_commander_manager() -> CommanderManager:
    """Get the global commander manager"""
    return _commander_manager