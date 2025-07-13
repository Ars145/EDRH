"""
Category service for Elite Dangerous Records Helper.
Handles category management, formatting, and filtering.
"""

import json
import random
import colorsys
from typing import List, Dict, Optional, Any, Union


class CategoryService:
    """Manages categories, their formatting, and filtering"""
    
    def __init__(self, config_manager, category_repository=None):
        """Initialize the category service.
        
        Args:
            config_manager: The configuration manager instance.
            category_repository: The category repository instance.
        """
        self.config = config_manager
        self.repository = category_repository
    
    def parse_categories(self, category_data: Any) -> List[str]:
        """Parse categories from various formats.
        
        Args:
            category_data: Category data in various formats (string, list, JSON string).
        
        Returns:
            List[str]: List of categories.
        """
        if not category_data:
            return []
        
        # If already a list, return it
        if isinstance(category_data, list):
            return category_data
        
        # If a string, try to parse as JSON if it looks like a list
        if isinstance(category_data, str):
            if category_data.startswith('[') and category_data.endswith(']'):
                try:
                    return json.loads(category_data)
                except:
                    # If parsing fails, treat as comma-separated string
                    return [c.strip() for c in category_data.split(',') if c.strip()]
            else:
                # Single category as string or comma-separated list
                return [c.strip() for c in category_data.split(',') if c.strip()]
        
        # If we get here, return an empty list
        return []
    
    def format_categories_for_storage(self, categories: List[str]) -> Union[str, List[str]]:
        """Format categories for storage in the database.
        
        Args:
            categories (List[str]): List of categories.
        
        Returns:
            Union[str, List[str]]: Formatted categories for storage.
        """
        if not categories:
            return ""
        
        # If only one category, store as string for backward compatibility
        if len(categories) == 1:
            return categories[0]
        
        # Otherwise, store as JSON array
        return json.dumps(categories)
    
    def format_categories_for_display(self, categories: List[str], max_length: int = 50, separator: str = " • ") -> str:
        """Format categories for display in the UI.
        
        Args:
            categories (List[str]): List of categories.
            max_length (int, optional): Maximum length of the formatted string.
            separator (str, optional): Separator between categories.
        
        Returns:
            str: Formatted categories for display.
        """
        if not categories:
            return ""
        
        # If only one category, return it
        if len(categories) == 1:
            return categories[0]
        
        # Format with separator
        formatted = separator.join(categories)
        
        # Truncate if too long
        if len(formatted) > max_length:
            # Try to find a good truncation point
            truncate_index = formatted.rfind(separator, 0, max_length - 3)
            if truncate_index == -1:
                # If no separator found, just truncate
                return formatted[:max_length - 3] + "..."
            else:
                # Truncate at separator
                return formatted[:truncate_index] + "..."
        
        return formatted
    
    def get_primary_category(self, categories: List[str]) -> str:
        """Get the primary category (first in the list).
        
        Args:
            categories (List[str]): List of categories.
        
        Returns:
            str: The primary category, or empty string if none.
        """
        return categories[0] if categories else ""
    
    def categories_match_filter(self, categories: List[str], selected_filters: List[str]) -> bool:
        """Check if categories match selected filters.
        
        Args:
            categories (List[str]): List of categories.
            selected_filters (List[str]): List of selected filter categories.
        
        Returns:
            bool: True if categories match filters, False otherwise.
        """
        if not selected_filters:
            return True
        
        # Check if any category matches any filter
        for category in categories:
            if category in selected_filters:
                return True
        
        return False
    
    def get_category_color(self, category: str) -> str:
        """Get the color for a category.
        
        Args:
            category (str): The category name.
        
        Returns:
            str: The category color in hex format.
        """
        colors = self.config.get("category_colors", {})
        return colors.get(category, self.generate_unique_color(colors.values()))
    
    def get_category_color_for_multi(self, categories: List[str]) -> str:
        """Get a color for multiple categories.
        
        Args:
            categories (List[str]): List of categories.
        
        Returns:
            str: The category color in hex format.
        """
        if not categories:
            return "#808080"  # Default gray
        
        # If only one category, use its color
        if len(categories) == 1:
            return self.get_category_color(categories[0])
        
        # Otherwise, use the primary category's color
        return self.get_category_color(self.get_primary_category(categories))
    
    def get_or_create_category_color(self, category: str) -> str:
        """Get or create a color for a category.
        
        Args:
            category (str): The category name.
        
        Returns:
            str: The category color in hex format.
        """
        colors = self.config.get("category_colors", {})
        if category in colors:
            return colors[category]
        
        # Generate a new color
        new_color = self.generate_unique_color(colors.values())
        colors[category] = new_color
        self.config.set("category_colors", colors)
        return new_color
    
    def generate_unique_color(self, existing_colors: List[str]) -> str:
        """Generate a unique color not similar to existing ones.
        
        Args:
            existing_colors (List[str]): List of existing colors in hex format.
        
        Returns:
            str: A new unique color in hex format.
        """
        # Convert existing colors to HSV for better comparison
        existing_hsv = []
        for color in existing_colors:
            try:
                # Skip invalid colors
                if not color.startswith('#') or len(color) != 7:
                    continue
                
                # Convert hex to RGB
                r = int(color[1:3], 16) / 255.0
                g = int(color[3:5], 16) / 255.0
                b = int(color[5:7], 16) / 255.0
                
                # Convert RGB to HSV
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                existing_hsv.append((h, s, v))
            except:
                continue
        
        # Generate random colors until we find one that's not too similar
        for _ in range(100):  # Limit attempts
            # Generate random HSV with good saturation and value
            h = random.random()
            s = random.uniform(0.5, 0.9)
            v = random.uniform(0.5, 0.9)
            
            # Check if it's too similar to existing colors
            too_similar = False
            for eh, es, ev in existing_hsv:
                # Check hue similarity (considering the circular nature of hue)
                h_diff = min(abs(h - eh), 1 - abs(h - eh))
                if h_diff < 0.1 and abs(s - es) < 0.1 and abs(v - ev) < 0.1:
                    too_similar = True
                    break
            
            if not too_similar:
                # Convert back to RGB and then to hex
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        
        # If we couldn't find a unique color, just return a random one
        r, g, b = colorsys.hsv_to_rgb(random.random(), 0.7, 0.7)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    
    def get_category_images(self) -> Dict[str, str]:
        """Get category images.
        
        Returns:
            Dict[str, str]: Dictionary of category images.
        """
        if self.repository:
            return self.repository.get_category_images()
        return {}
    
    def get_preset_images_for_categories(self, categories: List[str]) -> List[str]:
        """Get preset images for categories.
        
        Args:
            categories (List[str]): List of categories.
        
        Returns:
            List[str]: List of image URLs.
        """
        category_images = self.get_category_images()
        result = []
        
        for category in categories:
            if category in category_images:
                result.append(category_images[category])
        
        return result