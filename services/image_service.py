"""
Image loading and caching service for EDRH
"""

import os
import time
import threading
import base64
from io import BytesIO
from collections import OrderedDict
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageEnhance
from PIL.Image import Resampling
import customtkinter as ctk
from customtkinter import CTkImage

# Try to import requests, fall back to urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.parse
    HAS_REQUESTS = False

# Global supabase client (will be set by the application)
supabase = None

class LRUCache:
    """
    Least Recently Used (LRU) cache with size limit
    """
    def __init__(self, max_size=100):
        self.cache = OrderedDict()
        self.max_size = max_size
        
    def get(self, key):
        """Get an item from the cache"""
        if key in self.cache:
            # Move to end (most recently used)
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        return None
        
    def put(self, key, value):
        """Add an item to the cache"""
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # Remove oldest item
            self.cache.popitem(last=False)
        self.cache[key] = value
        
    def clear(self):
        """Clear the cache"""
        self.cache.clear()
        
    def __contains__(self, key):
        """Check if key is in cache"""
        return key in self.cache
        
    def __len__(self):
        """Get cache size"""
        return len(self.cache)


class ImageService:
    """
    Service for loading and caching images
    """
    def __init__(self, cache_size=100):
        """Initialize the image service"""
        self.cache = LRUCache(max_size=cache_size)
        self.card_cache = LRUCache(max_size=cache_size)
        self.lock = threading.Lock()
        
    def load_image(self, url, size=None, format=None, callback=None):
        """
        Load an image from a URL with caching
        
        Args:
            url: URL or path to the image
            size: Tuple of (width, height) to resize the image to
            format: Optional format for special processing (e.g., "card")
            callback: Function to call when the image is loaded
                     Signature: callback(photo_image)
                     
        Returns:
            PhotoImage if cached, None if loading asynchronously
        """
        # Generate cache key
        cache_key = self._generate_cache_key(url, size, format)
        
        # Check cache
        with self.lock:
            if format == "card":
                cached = self.card_cache.get(cache_key)
            else:
                cached = self.cache.get(cache_key)
                
            if cached:
                if callback:
                    callback(cached)
                return cached
        
        # Start async loading
        self._load_async(url, size, format, callback)
        return None
        
    def preload_image(self, url, size=None, format=None):
        """
        Preload an image into the cache without returning it
        
        Args:
            url: URL or path to the image
            size: Tuple of (width, height) to resize the image to
            format: Optional format for special processing (e.g., "card")
        """
        self.load_image(url, size, format)
        
    def clear_cache(self):
        """Clear all image caches"""
        with self.lock:
            self.cache.clear()
            self.card_cache.clear()
            
    def _generate_cache_key(self, url, size, format):
        """Generate a cache key for an image"""
        if format == "card":
            return f"card_{url}_{size[0]}x{size[1]}" if size else f"card_{url}"
        else:
            return f"{url}_{size[0]}x{size[1]}" if size else url
            
    def _load_async(self, url, size, format, callback):
        """Load an image asynchronously"""
        def load_thread():
            try:
                # Fetch image data
                img_data = self._fetch_image_data(url)
                if not img_data:
                    print(f"Failed to fetch image data from {url}")
                    return
                    
                # Process image
                img = self._process_image(img_data, size, format)
                if not img:
                    print(f"Failed to process image from {url}")
                    return
                    
                # Create photo image
                photo = self._create_photo_image(img, format)
                if not photo:
                    print(f"Failed to create photo image from {url}")
                    return
                    
                # Cache the result
                cache_key = self._generate_cache_key(url, size, format)
                with self.lock:
                    if format == "card":
                        self.card_cache.put(cache_key, photo)
                    else:
                        self.cache.put(cache_key, photo)
                        
                # Call callback if provided
                if callback:
                    callback(photo)
                    
            except Exception as e:
                print(f"Error loading image from {url}: {e}")
                
        # Start loading thread
        threading.Thread(target=load_thread, daemon=True).start()
        
    def _fetch_image_data(self, url):
        """Fetch image data from a URL"""
        try:
            # Handle Supabase storage URLs
            if url.startswith("supabase://uploaded_images/"):
                return self._fetch_from_supabase(url)
                
            # Handle base64 encoded images
            elif url.startswith("data:image"):
                return self._fetch_from_base64(url)
                
            # Handle regular URLs
            else:
                return self._fetch_from_url(url)
                
        except Exception as e:
            print(f"Error fetching image data: {e}")
            return None
            
    def _fetch_from_supabase(self, url):
        """Fetch image data from Supabase storage"""
        if not supabase:
            return None
            
        try:
            image_id = url.split("/")[-1]
            result = supabase.table("uploaded_images").select("data").eq("id", image_id).single().execute()
            
            if result and result.data:
                b64_data = result.data["data"]
                return base64.b64decode(b64_data)
                
        except Exception as e:
            print(f"Failed to load Supabase image: {e}")
            
        return None
        
    def _fetch_from_base64(self, url):
        """Fetch image data from a base64 encoded URL"""
        try:
            header, data = url.split(",", 1)
            return base64.b64decode(data)
        except Exception as e:
            print(f"Failed to load base64 image: {e}")
            return None
            
    def _fetch_from_url(self, url):
        """Fetch image data from a regular URL"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            if HAS_REQUESTS:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.content
            else:
                req = urllib.request.Request(url, headers=headers)
                response = urllib.request.urlopen(req, timeout=10)
                return response.read()
        except Exception as e:
            print(f"Failed to fetch URL {url}: {e}")
            return None
            
    def _process_image(self, img_data, size, format):
        """Process image data based on size and format"""
        try:
            # Open image
            img = Image.open(BytesIO(img_data))
            
            # Apply card format
            if format == "card":
                return self._process_card_image(img, size)
                
            # Apply regular format
            elif size:
                img.thumbnail(size, Resampling.LANCZOS)
                
            return img
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return None
            
    def _process_card_image(self, img, size):
        """Process an image for card format"""
        try:
            # Default card size
            card_width = 538
            card_height = 96
            
            # Use provided size if available
            if size:
                card_width, card_height = size
                
            # Calculate aspect ratio
            img_ratio = img.width / img.height
            card_ratio = card_width / card_height
            
            # Resize to cover the card
            if img_ratio > card_ratio:
                new_height = card_height
                new_width = int(card_height * img_ratio)
            else:
                new_width = card_width
                new_height = int(card_width / img_ratio)
                
            img = img.resize((new_width, new_height), Resampling.LANCZOS)
            
            # Crop to card size
            left = (new_width - card_width) // 2
            top = (new_height - card_height) // 2
            img = img.crop((left, top, left + card_width, top + card_height))
            
            # Add semi-transparent overlay
            img = img.convert('RGBA')
            overlay = Image.new('RGBA', (card_width, card_height), (0, 0, 0, 100))
            img = Image.alpha_composite(img, overlay)
            
            # Create rounded corners mask
            mask = Image.new('L', (card_width, card_height), 0)
            draw = ImageDraw.Draw(mask)
            radius = 12
            
            try:
                # Try to use rounded_rectangle (PIL 8.0.0+)
                draw.rounded_rectangle([(0, 0), (card_width-1, card_height-1)],
                                     radius=radius, fill=255)
            except AttributeError:
                # Fallback for older PIL versions
                draw.rectangle([(radius, 0), (card_width-radius-1, card_height-1)], fill=255)
                draw.rectangle([(0, radius), (card_width-1, card_height-radius-1)], fill=255)
                draw.ellipse([(0, 0), (radius*2, radius*2)], fill=255)
                draw.ellipse([(card_width-radius*2-1, 0), (card_width-1, radius*2)], fill=255)
                draw.ellipse([(0, card_height-radius*2-1), (radius*2, card_height-1)], fill=255)
                draw.ellipse([(card_width-radius*2-1, card_height-radius*2-1), (card_width-1, card_height-1)], fill=255)
                
            # Apply mask
            output = Image.new('RGBA', (card_width, card_height), (0, 0, 0, 0))
            output.paste(img, (0, 0))
            output.putalpha(mask)
            
            return output
            
        except Exception as e:
            print(f"Error processing card image: {e}")
            return None
            
    def _create_photo_image(self, img, format):
        """Create a photo image from a PIL image"""
        try:
            if format == "card":
                # For cards, use Tkinter's PhotoImage
                return ImageTk.PhotoImage(img)
            else:
                # For regular images, use CTkImage
                return CTkImage(dark_image=img, size=(img.width, img.height))
                
        except Exception as e:
            print(f"Error creating photo image: {e}")
            return None


# Create a global instance
image_service = ImageService(cache_size=200)

# Convenience functions
def load_image(url, size=None, format=None, callback=None):
    """Load an image from a URL with caching"""
    return image_service.load_image(url, size, format, callback)
    
def preload_image(url, size=None, format=None):
    """Preload an image into the cache"""
    image_service.preload_image(url, size, format)
    
def clear_image_cache():
    """Clear the image cache"""
    image_service.clear_cache()
    
def set_supabase_client(client):
    """Set the global Supabase client"""
    global supabase
    supabase = client