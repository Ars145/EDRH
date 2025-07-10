"""
Supabase client service for EDRH
"""

import time
import threading
import json
from collections import OrderedDict
from datetime import datetime, timezone
from supabase import create_client

# Default retry settings
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds
DEFAULT_RETRY_BACKOFF = 2.0  # multiplier

class LRUCache:
    """
    Least Recently Used (LRU) cache with size limit and TTL
    """
    def __init__(self, max_size=100, ttl=60):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self.timestamps = {}
        self.lock = threading.Lock()
        
    def get(self, key):
        """Get an item from the cache"""
        with self.lock:
            # Check if key exists and is not expired
            if key in self.cache:
                if self.ttl > 0:
                    timestamp = self.timestamps.get(key, 0)
                    if time.time() - timestamp > self.ttl:
                        # Expired
                        self.cache.pop(key)
                        self.timestamps.pop(key, None)
                        return None
                
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None
        
    def put(self, key, value):
        """Add an item to the cache"""
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # Remove oldest item
                oldest = next(iter(self.cache))
                self.cache.pop(oldest)
                self.timestamps.pop(oldest, None)
                
            self.cache[key] = value
            self.timestamps[key] = time.time()
        
    def clear(self):
        """Clear the cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
        
    def __contains__(self, key):
        """Check if key is in cache and not expired"""
        with self.lock:
            if key in self.cache:
                if self.ttl > 0:
                    timestamp = self.timestamps.get(key, 0)
                    if time.time() - timestamp > self.ttl:
                        # Expired
                        self.cache.pop(key)
                        self.timestamps.pop(key, None)
                        return False
                return True
            return False
        
    def __len__(self):
        """Get cache size"""
        with self.lock:
            return len(self.cache)


class SupabaseClient:
    """
    Enhanced Supabase client with caching and retry logic
    """
    def __init__(self, url, key, options=None):
        """
        Initialize the Supabase client
        
        Args:
            url: Supabase URL
            key: Supabase API key
            options: Additional options
        """
        self.url = url
        self.key = key
        self.options = options or {}
        self.client = create_client(url, key, **self.options)
        self.query_cache = LRUCache(max_size=100, ttl=60)  # 1 minute TTL
        self.lock = threading.Lock()
        
    def table(self, table_name):
        """Get a table query builder with enhanced features"""
        return TableQuery(self, table_name)
        
    def rpc(self, fn, params=None):
        """Call a Postgres function"""
        return RPCQuery(self, fn, params)
        
    def storage(self):
        """Get the storage client"""
        return self.client.storage
        
    def auth(self):
        """Get the auth client"""
        return self.client.auth
        
    def _execute_with_retry(self, query_fn, retry_count=DEFAULT_RETRY_COUNT, 
                           retry_delay=DEFAULT_RETRY_DELAY, 
                           retry_backoff=DEFAULT_RETRY_BACKOFF):
        """
        Execute a query with retry logic
        
        Args:
            query_fn: Function that returns a query to execute
            retry_count: Number of retries
            retry_delay: Initial delay between retries (seconds)
            retry_backoff: Multiplier for delay after each retry
            
        Returns:
            Query result
        """
        last_error = None
        current_delay = retry_delay
        
        for attempt in range(retry_count + 1):
            try:
                return query_fn().execute()
            except Exception as e:
                last_error = e
                
                # Don't sleep on the last attempt
                if attempt < retry_count:
                    time.sleep(current_delay)
                    current_delay *= retry_backoff
                    
        # If we get here, all retries failed
        raise last_error
        
    def clear_cache(self):
        """Clear the query cache"""
        self.query_cache.clear()


class TableQuery:
    """
    Enhanced table query builder with caching and retry logic
    """
    def __init__(self, client, table_name):
        """
        Initialize the table query
        
        Args:
            client: SupabaseClient instance
            table_name: Name of the table
        """
        self.client = client
        self.table_name = table_name
        self.query = client.client.table(table_name)
        self.cache_key_parts = [table_name]
        self.use_cache = True
        
    def select(self, columns="*"):
        """Select columns"""
        self.query = self.query.select(columns)
        self.cache_key_parts.append(f"select:{columns}")
        return self
        
    def insert(self, values, returning="representation"):
        """Insert values"""
        self.query = self.query.insert(values, returning=returning)
        self.use_cache = False  # Don't cache inserts
        return self
        
    def update(self, values, returning="representation"):
        """Update values"""
        self.query = self.query.update(values, returning=returning)
        self.use_cache = False  # Don't cache updates
        return self
        
    def upsert(self, values, returning="representation", ignore_duplicates=False):
        """Upsert values"""
        self.query = self.query.upsert(values, returning=returning, ignore_duplicates=ignore_duplicates)
        self.use_cache = False  # Don't cache upserts
        return self
        
    def delete(self, returning="representation"):
        """Delete rows"""
        self.query = self.query.delete(returning=returning)
        self.use_cache = False  # Don't cache deletes
        return self
        
    def eq(self, column, value):
        """Equal filter"""
        self.query = self.query.eq(column, value)
        self.cache_key_parts.append(f"eq:{column}:{value}")
        return self
        
    def neq(self, column, value):
        """Not equal filter"""
        self.query = self.query.neq(column, value)
        self.cache_key_parts.append(f"neq:{column}:{value}")
        return self
        
    def gt(self, column, value):
        """Greater than filter"""
        self.query = self.query.gt(column, value)
        self.cache_key_parts.append(f"gt:{column}:{value}")
        return self
        
    def gte(self, column, value):
        """Greater than or equal filter"""
        self.query = self.query.gte(column, value)
        self.cache_key_parts.append(f"gte:{column}:{value}")
        return self
        
    def lt(self, column, value):
        """Less than filter"""
        self.query = self.query.lt(column, value)
        self.cache_key_parts.append(f"lt:{column}:{value}")
        return self
        
    def lte(self, column, value):
        """Less than or equal filter"""
        self.query = self.query.lte(column, value)
        self.cache_key_parts.append(f"lte:{column}:{value}")
        return self
        
    def like(self, column, pattern):
        """LIKE filter"""
        self.query = self.query.like(column, pattern)
        self.cache_key_parts.append(f"like:{column}:{pattern}")
        return self
        
    def ilike(self, column, pattern):
        """ILIKE filter"""
        self.query = self.query.ilike(column, pattern)
        self.cache_key_parts.append(f"ilike:{column}:{pattern}")
        return self
        
    def is_(self, column, value):
        """IS filter"""
        self.query = self.query.is_(column, value)
        self.cache_key_parts.append(f"is:{column}:{value}")
        return self
        
    def in_(self, column, values):
        """IN filter"""
        self.query = self.query.in_(column, values)
        self.cache_key_parts.append(f"in:{column}:{','.join(map(str, values))}")
        return self
        
    def order(self, column, desc=False, nullsfirst=False):
        """Order results"""
        self.query = self.query.order(column, desc=desc, nullsfirst=nullsfirst)
        self.cache_key_parts.append(f"order:{column}:{desc}:{nullsfirst}")
        return self
        
    def limit(self, count):
        """Limit results"""
        self.query = self.query.limit(count)
        self.cache_key_parts.append(f"limit:{count}")
        return self
        
    def offset(self, count):
        """Offset results"""
        self.query = self.query.offset(count)
        self.cache_key_parts.append(f"offset:{count}")
        return self
        
    def range(self, start, end):
        """Range of results"""
        self.query = self.query.range(start, end)
        self.cache_key_parts.append(f"range:{start}:{end}")
        return self
        
    def single(self):
        """Expect a single result"""
        self.query = self.query.single()
        self.cache_key_parts.append("single")
        return self
        
    def maybe_single(self):
        """Maybe expect a single result"""
        self.query = self.query.maybe_single()
        self.cache_key_parts.append("maybe_single")
        return self
        
    def execute(self):
        """Execute the query"""
        # Generate cache key
        if self.use_cache:
            cache_key = ":".join(self.cache_key_parts)
            
            # Check cache
            cached_result = self.client.query_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Execute query with retry
            result = self.client._execute_with_retry(lambda: self.query)
            
            # Cache result
            self.client.query_cache.put(cache_key, result)
            return result
        else:
            # Execute query with retry (no caching)
            return self.client._execute_with_retry(lambda: self.query)


class RPCQuery:
    """
    Enhanced RPC query builder with retry logic
    """
    def __init__(self, client, fn, params=None):
        """
        Initialize the RPC query
        
        Args:
            client: SupabaseClient instance
            fn: Function name
            params: Function parameters
        """
        self.client = client
        self.fn = fn
        self.params = params or {}
        self.query = client.client.rpc(fn, params)
        
    def execute(self):
        """Execute the RPC query"""
        # Execute query with retry
        return self.client._execute_with_retry(lambda: self.query)


# Global client instance
_client = None

def init_supabase(url, key, options=None):
    """Initialize the global Supabase client"""
    global _client
    _client = SupabaseClient(url, key, options)
    return _client
    
def get_client():
    """Get the global Supabase client"""
    if _client is None:
        raise ValueError("Supabase client not initialized. Call init_supabase first.")
    return _client
    
def table(table_name):
    """Get a table query builder"""
    return get_client().table(table_name)
    
def rpc(fn, params=None):
    """Call a Postgres function"""
    return get_client().rpc(fn, params)
    
def storage():
    """Get the storage client"""
    return get_client().storage()
    
def auth():
    """Get the auth client"""
    return get_client().auth()
    
def clear_cache():
    """Clear the query cache"""
    get_client().clear_cache()