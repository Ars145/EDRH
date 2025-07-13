"""
Image service for Elite Dangerous Records Helper.
Handles image uploading, caching, and processing.
"""

import os
import base64
import urllib.request
import urllib.parse
import ssl
import json
import time
from io import BytesIO
from typing import Optional, Dict, List, Callable
from PIL import Image, ImageTk
from collections import OrderedDict


class LRUCache:
    """Least Recently Used Cache with size limit"""
    
    def __init__(self, max_size=100):
        """Initialize the LRU cache.
        
        Args:
            max_size (int, optional): Maximum number of items in the cache.
        """
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key):
        """Get an item from the cache.
        
        Args:
            key: The cache key.
        
        Returns:
            The cached value, or None if not found.
        """
        if key in self.cache:
            # Move to end (most recently used)
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        return None
    
    def put(self, key, value):
        """Put an item in the cache.
        
        Args:
            key: The cache key.
            value: The value to cache.
        """
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used item
            self.cache.popitem(last=False)
        self.cache[key] = value


class ImageUploadStrategy:
    """Base class for image upload strategies."""
    
    def upload(self, image_path: str) -> Optional[str]:
        """Upload an image.
        
        Args:
            image_path (str): Path to the image file.
        
        Returns:
            Optional[str]: URL of the uploaded image, or None if failed.
        """
        raise NotImplementedError("Subclasses must implement upload method")


class ImgBBUploadStrategy(ImageUploadStrategy):
    """Strategy for uploading images to ImgBB."""
    
    def __init__(self, api_key: str):
        """Initialize the ImgBB upload strategy.
        
        Args:
            api_key (str): ImgBB API key.
        """
        self.api_key = api_key
    
    def upload(self, image_path: str) -> Optional[str]:
        """Upload an image to ImgBB.
        
        Args:
            image_path (str): Path to the image file.
        
        Returns:
            Optional[str]: URL of the uploaded image, or None if failed.
        """
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            if len(image_data) > 32 * 1024 * 1024:
                print(f"ImgBB: Image too large ({len(image_data)} bytes), max 32MB")
                return None
            
            b64_image = base64.b64encode(image_data).decode()
            
            # Try with requests if available
            try:
                import requests
                import urllib3
                urllib3.disable_warnings()
                
                data = {
                    'key': self.api_key,
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
            
            except (ImportError, Exception) as e:
                print(f"ImgBB requests method failed: {e}")
            
            # Fall back to urllib
            try:
                data = urllib.parse.urlencode({
                    'key': self.api_key,
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
            
            return None
        
        except Exception as e:
            print(f"ImgBB upload error: {e}")
            return None


class ImgurUploadStrategy(ImageUploadStrategy):
    """Strategy for uploading images to Imgur."""
    
    def __init__(self, client_id: str):
        """Initialize the Imgur upload strategy.
        
        Args:
            client_id (str): Imgur client ID.
        """
        self.client_id = client_id
    
    def upload(self, image_path: str) -> Optional[str]:
        """Upload an image to Imgur.
        
        Args:
            image_path (str): Path to the image file.
        
        Returns:
            Optional[str]: URL of the uploaded image, or None if failed.
        """
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Try with requests if available
            try:
                import requests
                
                headers = {'Authorization': f'Client-ID {self.client_id}'}
                files = {'image': image_data}
                
                response = requests.post(
                    'https://api.imgur.com/3/image',
                    headers=headers,
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"Imgur upload successful")
                        return result['data']['link']
                    else:
                        print(f"Imgur API error: {result}")
            
            except (ImportError, Exception) as e:
                print(f"Imgur requests method failed: {e}")
            
            # Fall back to urllib
            try:
                b64_image = base64.b64encode(image_data).decode()
                
                headers = {
                    'Authorization': f'Client-ID {self.client_id}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                
                data = urllib.parse.urlencode({
                    'image': b64_image,
                    'type': 'base64'
                }).encode()
                
                req = urllib.request.Request(
                    'https://api.imgur.com/3/image',
                    data=data,
                    headers=headers
                )
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    result = json.loads(response.read().decode())
                    if result.get('success'):
                        print(f"Imgur urllib upload successful")
                        return result['data']['link']
                    else:
                        print(f"Imgur urllib API error: {result}")
            
            except Exception as e:
                print(f"Imgur urllib method failed: {e}")
            
            return None
        
        except Exception as e:
            print(f"Imgur upload error: {e}")
            return None


class SupabaseBase64UploadStrategy(ImageUploadStrategy):
    """Strategy for uploading images to Supabase as base64."""
    
    def __init__(self, database_service):
        """Initialize the Supabase base64 upload strategy.
        
        Args:
            database_service: The database service instance.
        """
        self.db = database_service
    
    def upload(self, image_path: str) -> Optional[str]:
        """Upload an image to Supabase as base64.
        
        Args:
            image_path (str): Path to the image file.
        
        Returns:
            Optional[str]: URL of the uploaded image, or None if failed.
        """
        try:
            if not self.db.is_connected():
                return None
            
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            b64_image = base64.b64encode(image_data).decode()
            
            # Generate a unique ID for the image
            import hashlib
            import time
            image_id = hashlib.md5(f"{image_path}_{time.time()}".encode()).hexdigest()
            
            # Insert the image into the database
            result = self.db.supabase.table("images").insert({
                "id": image_id,
                "data": b64_image,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }).execute()
            
            if result.data:
                # Return a URL that can be used to retrieve the image
                return f"supabase://images/{image_id}"
            
            return None
        
        except Exception as e:
            print(f"Supabase base64 upload error: {e}")
            return None


class SupabaseStorageUploadStrategy(ImageUploadStrategy):
    """Strategy for uploading images to Supabase Storage."""
    
    def __init__(self, database_service):
        """Initialize the Supabase Storage upload strategy.
        
        Args:
            database_service: The database service instance.
        """
        self.db = database_service
    
    def upload(self, image_path: str) -> Optional[str]:
        """Upload an image to Supabase Storage.
        
        Args:
            image_path (str): Path to the image file.
        
        Returns:
            Optional[str]: URL of the uploaded image, or None if failed.
        """
        try:
            if not self.db.is_connected():
                return None
            
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Generate a unique filename
            import hashlib
            import time
            filename = f"{hashlib.md5(f'{image_path}_{time.time()}'.encode()).hexdigest()}.jpg"
            
            # Upload the file to Supabase Storage
            result = self.db.supabase.storage.from_("images").upload(
                filename,
                image_data,
                {"content-type": "image/jpeg"}
            )
            
            if result:
                # Get the public URL
                public_url = self.db.supabase.storage.from_("images").get_public_url(filename)
                return public_url
            
            return None
        
        except Exception as e:
            print(f"Supabase Storage upload error: {e}")
            return None


class ImageService:
    """Manages image uploading, caching, and processing"""
    
    def __init__(self, config_manager, database_service=None):
        """Initialize the image service.
        
        Args:
            config_manager: The configuration manager instance.
            database_service: The database service instance.
        """
        self.config = config_manager
        self.db = database_service
        self.image_cache = LRUCache(max_size=100)
        
        # Initialize upload strategies
        self.upload_strategies = []
        
        # ImgBB strategy
        imgbb_api_key = "8df93308e43e8a90de4b3a1219f07956"  # Default key
        self.upload_strategies.append(ImgBBUploadStrategy(imgbb_api_key))
        
        # Imgur strategy
        imgur_client_id = "8b0158e0f64f692"  # Default client ID
        self.upload_strategies.append(ImgurUploadStrategy(imgur_client_id))
        
        # Supabase strategies (if database service is provided)
        if database_service:
            self.upload_strategies.append(SupabaseBase64UploadStrategy(database_service))
            self.upload_strategies.append(SupabaseStorageUploadStrategy(database_service))
    
    def upload_image(self, image_path: str) -> Optional[str]:
        """Upload an image using multiple strategies with fallback.
        
        Args:
            image_path (str): Path to the image file.
        
        Returns:
            Optional[str]: URL of the uploaded image, or None if all strategies failed.
        """
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return None
        
        for strategy in self.upload_strategies:
            try:
                url = strategy.upload(image_path)
                if url:
                    return url
            except Exception as e:
                print(f"{strategy.__class__.__name__} failed: {e}")
        
        print("All image upload strategies failed")
        return None
    
    def load_image_from_url(self, url: str, size=(100, 100)) -> Optional[ImageTk.PhotoImage]:
        """Load and cache an image from a URL.
        
        Args:
            url (str): The image URL.
            size (tuple, optional): The desired image size.
        
        Returns:
            Optional[ImageTk.PhotoImage]: The loaded image, or None if failed.
        """
        if not url:
            return None
        
        # Check cache first
        cache_key = f"{url}_{size[0]}x{size[1]}"
        cached_image = self.image_cache.get(cache_key)
        if cached_image:
            return cached_image
        
        try:
            # Try with requests if available
            try:
                import requests
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    image_data = response.content
                    img = Image.open(BytesIO(image_data))
                    img = img.resize(size, Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.image_cache.put(cache_key, photo)
                    return photo
            except (ImportError, Exception) as e:
                print(f"Requests image loading failed: {e}")
            
            # Fall back to urllib
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    image_data = response.read()
                    img = Image.open(BytesIO(image_data))
                    img = img.resize(size, Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.image_cache.put(cache_key, photo)
                    return photo
            except Exception as e:
                print(f"Urllib image loading failed: {e}")
            
            return None
        
        except Exception as e:
            print(f"Error loading image from URL: {e}")
            return None
    
    def preload_images(self, urls: List[str], size=(100, 100), callback: Optional[Callable] = None):
        """Preload multiple images in the background.
        
        Args:
            urls (List[str]): List of image URLs to preload.
            size (tuple, optional): The desired image size.
            callback (Callable, optional): Callback function to call when all images are loaded.
        """
        import threading
        
        def load_images():
            for url in urls:
                if url:
                    self.load_image_from_url(url, size)
            
            if callback:
                callback()
        
        thread = threading.Thread(target=load_images, daemon=True)
        thread.start()