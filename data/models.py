"""
Data models for Elite Dangerous Records Helper.
Defines data structures used throughout the application.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class System:
    """Represents a star system in the Elite Dangerous universe."""
    
    name: str
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    categories: List[str] = field(default_factory=list)
    commander: Optional[str] = None
    visited: bool = False
    done: bool = False
    images: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    discovery_date: Optional[datetime] = None
    id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'System':
        """Create a System instance from a dictionary.
        
        Args:
            data: Dictionary containing system data.
            
        Returns:
            System: A new System instance.
        """
        # Handle categories which might be a string, list, or JSON string
        categories = data.get('category', [])
        if isinstance(categories, str):
            # Try to parse as JSON if it looks like a list
            if categories.startswith('[') and categories.endswith(']'):
                try:
                    import json
                    categories = json.loads(categories)
                except:
                    # If parsing fails, treat as comma-separated string
                    categories = [c.strip() for c in categories.split(',') if c.strip()]
            else:
                # Single category as string
                categories = [categories]
        
        # Parse discovery date if present
        discovery_date = None
        if 'discovery_date' in data and data['discovery_date']:
            try:
                if isinstance(data['discovery_date'], str):
                    discovery_date = datetime.fromisoformat(data['discovery_date'].replace('Z', '+00:00'))
                else:
                    discovery_date = data['discovery_date']
            except:
                pass
        
        # Create system instance
        return cls(
            name=data.get('name', ''),
            x=float(data.get('x', 0.0)),
            y=float(data.get('y', 0.0)),
            z=float(data.get('z', 0.0)),
            categories=categories,
            commander=data.get('commander'),
            visited=bool(data.get('visited', False)),
            done=bool(data.get('done', False)),
            images=data.get('images', []),
            notes=data.get('notes'),
            discovery_date=discovery_date,
            id=data.get('id')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the System instance to a dictionary.
        
        Returns:
            Dict: Dictionary representation of the system.
        """
        result = {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'visited': self.visited,
            'done': self.done
        }
        
        # Only include non-empty values
        if self.categories:
            import json
            result['category'] = json.dumps(self.categories)
        
        if self.commander:
            result['commander'] = self.commander
            
        if self.images:
            result['images'] = self.images
            
        if self.notes:
            result['notes'] = self.notes
            
        if self.discovery_date:
            result['discovery_date'] = self.discovery_date.isoformat()
            
        if self.id is not None:
            result['id'] = self.id
            
        return result


@dataclass
class Commander:
    """Represents a commander in Elite Dangerous."""
    
    name: str
    blocked: bool = False
    first_seen: Optional[datetime] = None
    journal_path: Optional[str] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Commander':
        """Create a Commander instance from a dictionary.
        
        Args:
            data: Dictionary containing commander data.
            
        Returns:
            Commander: A new Commander instance.
        """
        # Parse first_seen date if present
        first_seen = None
        if 'first_seen' in data and data['first_seen']:
            try:
                if isinstance(data['first_seen'], str):
                    first_seen = datetime.fromisoformat(data['first_seen'].replace('Z', '+00:00'))
                else:
                    first_seen = data['first_seen']
            except:
                pass
        
        # Create commander instance
        return cls(
            name=data.get('name', ''),
            blocked=bool(data.get('blocked', False)),
            first_seen=first_seen,
            journal_path=data.get('journal_path'),
            notes=data.get('notes'),
            id=data.get('id')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the Commander instance to a dictionary.
        
        Returns:
            Dict: Dictionary representation of the commander.
        """
        result = {
            'name': self.name,
            'blocked': self.blocked
        }
        
        # Only include non-empty values
        if self.first_seen:
            result['first_seen'] = self.first_seen.isoformat()
            
        if self.journal_path:
            result['journal_path'] = self.journal_path
            
        if self.notes:
            result['notes'] = self.notes
            
        if self.id is not None:
            result['id'] = self.id
            
        return result


@dataclass
class CategoryImage:
    """Represents an image for a category."""
    
    category: str
    image_url: str
    id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CategoryImage':
        """Create a CategoryImage instance from a dictionary.
        
        Args:
            data: Dictionary containing category image data.
            
        Returns:
            CategoryImage: A new CategoryImage instance.
        """
        return cls(
            category=data.get('category', ''),
            image_url=data.get('image_url', ''),
            id=data.get('id')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the CategoryImage instance to a dictionary.
        
        Returns:
            Dict: Dictionary representation of the category image.
        """
        result = {
            'category': self.category,
            'image_url': self.image_url
        }
        
        if self.id is not None:
            result['id'] = self.id
            
        return result


@dataclass
class JournalEvent:
    """Represents an event from the Elite Dangerous journal."""
    
    event: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JournalEvent':
        """Create a JournalEvent instance from a dictionary.
        
        Args:
            data: Dictionary containing journal event data.
            
        Returns:
            JournalEvent: A new JournalEvent instance.
        """
        # Parse timestamp
        timestamp = datetime.now()
        if 'timestamp' in data:
            try:
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            except:
                pass
        
        # Create event instance
        return cls(
            event=data.get('event', ''),
            timestamp=timestamp,
            data=data
        )