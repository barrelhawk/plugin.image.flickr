# -*- coding: utf-8 -*-
"""
Caching system for Flickr Add-on
Provides memory and disk-based caching for API responses
"""

import json
import time
import hashlib
import os
from typing import Dict, Any, Optional, Union
from threading import Lock


class CacheManager:
    """Cache manager for API responses and metadata"""
    
    def __init__(self, config, logger, cache_dir: Optional[str] = None):
        """Initialize cache manager"""
        
        self.config = config
        self.logger = logger
        self.cache_dir = cache_dir
        
        # Memory cache
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = Lock()
        
        # Cache settings
        self.enabled = self.config.get_bool('cache_enabled', True)
        self.memory_cache_size = self.config.get_int('memory_cache_size', 100)
        self.default_ttl = self.config.get_int('cache_duration', 300)  # 5 minutes
        self.disk_cache_enabled = self.config.get_bool('disk_cache_enabled', True)
        
        # Initialize disk cache directory
        if self.disk_cache_enabled and cache_dir:
            self._ensure_cache_dir()
        
        self.logger.debug(f"Cache manager initialized - enabled: {self.enabled}")
    
    def _ensure_cache_dir(self) -> bool:
        """Ensure cache directory exists"""
        
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
                self.logger.debug(f"Created cache directory: {self.cache_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create cache directory: {e}")
            self.disk_cache_enabled = False
            return False
    
    def _generate_cache_key(self, namespace: str, identifier: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key from namespace, identifier and parameters"""
        
        key_parts = [namespace, identifier]
        
        if params:
            # Sort parameters for consistent key generation
            param_str = json.dumps(params, sort_keys=True, separators=(',', ':'))
            key_parts.append(param_str)
        
        # Create hash of the combined key
        key_string = '|'.join(key_parts)
        cache_key = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        
        return f"{namespace}_{cache_key}"
    
    def get(self, namespace: str, identifier: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Get item from cache"""
        
        if not self.enabled:
            return None
        
        cache_key = self._generate_cache_key(namespace, identifier, params)
        
        # Check memory cache first
        memory_result = self._get_from_memory(cache_key)
        if memory_result is not None:
            self.logger.debug(f"Memory cache hit: {cache_key}")
            return memory_result
        
        # Check disk cache
        if self.disk_cache_enabled:
            disk_result = self._get_from_disk(cache_key)
            if disk_result is not None:
                self.logger.debug(f"Disk cache hit: {cache_key}")
                # Store in memory for faster access
                self._store_in_memory(cache_key, disk_result, ttl=self.default_ttl)
                return disk_result
        
        self.logger.debug(f"Cache miss: {cache_key}")
        return None
    
    def set(
        self,
        namespace: str,
        identifier: str,
        data: Any,
        ttl: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store item in cache"""
        
        if not self.enabled:
            return False
        
        cache_key = self._generate_cache_key(namespace, identifier, params)
        ttl = ttl or self.default_ttl
        
        try:
            # Store in memory cache
            self._store_in_memory(cache_key, data, ttl)
            
            # Store in disk cache if enabled
            if self.disk_cache_enabled:
                self._store_in_disk(cache_key, data, ttl)
            
            self.logger.debug(f"Cached item: {cache_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache item {cache_key}: {e}")
            return False
    
    def _get_from_memory(self, cache_key: str) -> Optional[Any]:
        """Get item from memory cache"""
        
        with self._cache_lock:
            if cache_key in self._memory_cache:
                cache_entry = self._memory_cache[cache_key]
                
                # Check if expired
                if time.time() > cache_entry['expires_at']:
                    del self._memory_cache[cache_key]
                    return None
                
                return cache_entry['data']
        
        return None
    
    def _store_in_memory(self, cache_key: str, data: Any, ttl: int) -> None:
        """Store item in memory cache"""
        
        with self._cache_lock:
            # Clean up expired entries and enforce size limit
            self._cleanup_memory_cache()
            
            # Store new entry
            self._memory_cache[cache_key] = {
                'data': data,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
    
    def _cleanup_memory_cache(self) -> None:
        """Clean up expired entries and enforce size limit"""
        
        current_time = time.time()
        
        # Remove expired entries
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._memory_cache[key]
        
        # Enforce size limit (remove oldest entries)
        if len(self._memory_cache) > self.memory_cache_size:
            # Sort by creation time and remove oldest
            sorted_entries = sorted(
                self._memory_cache.items(),
                key=lambda x: x[1]['created_at']
            )
            
            entries_to_remove = len(self._memory_cache) - self.memory_cache_size
            for i in range(entries_to_remove):
                key = sorted_entries[i][0]
                del self._memory_cache[key]
    
    def _get_from_disk(self, cache_key: str) -> Optional[Any]:
        """Get item from disk cache"""
        
        if not self.cache_dir:
            return None
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if expired
            if time.time() > cache_data.get('expires_at', 0):
                try:
                    os.remove(cache_file)
                except:
                    pass  # Ignore cleanup errors
                return None
            
            return cache_data.get('data')
            
        except Exception as e:
            self.logger.debug(f"Error reading disk cache {cache_key}: {e}")
            return None
    
    def _store_in_disk(self, cache_key: str, data: Any, ttl: int) -> None:
        """Store item in disk cache"""
        
        if not self.cache_dir:
            return
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            cache_data = {
                'data': data,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, separators=(',', ':'))
                
        except Exception as e:
            self.logger.debug(f"Error writing disk cache {cache_key}: {e}")
    
    def invalidate(self, namespace: str, identifier: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Invalidate specific cache entry"""
        
        cache_key = self._generate_cache_key(namespace, identifier, params)
        
        try:
            # Remove from memory cache
            with self._cache_lock:
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
            
            # Remove from disk cache
            if self.disk_cache_enabled and self.cache_dir:
                cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            
            self.logger.debug(f"Invalidated cache entry: {cache_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to invalidate cache entry {cache_key}: {e}")
            return False
    
    def invalidate_namespace(self, namespace: str) -> bool:
        """Invalidate all entries in a namespace"""
        
        try:
            count = 0
            
            # Clean memory cache
            with self._cache_lock:
                keys_to_remove = [
                    key for key in self._memory_cache.keys()
                    if key.startswith(f"{namespace}_")
                ]
                
                for key in keys_to_remove:
                    del self._memory_cache[key]
                    count += 1
            
            # Clean disk cache
            if self.disk_cache_enabled and self.cache_dir:
                try:
                    for filename in os.listdir(self.cache_dir):
                        if filename.startswith(f"{namespace}_") and filename.endswith('.json'):
                            os.remove(os.path.join(self.cache_dir, filename))
                            count += 1
                except:
                    pass  # Ignore disk cleanup errors
            
            self.logger.info(f"Invalidated {count} cache entries in namespace: {namespace}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to invalidate namespace {namespace}: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cache entries"""
        
        try:
            count = 0
            
            # Clear memory cache
            with self._cache_lock:
                count = len(self._memory_cache)
                self._memory_cache.clear()
            
            # Clear disk cache
            if self.disk_cache_enabled and self.cache_dir:
                try:
                    for filename in os.listdir(self.cache_dir):
                        if filename.endswith('.json'):
                            os.remove(os.path.join(self.cache_dir, filename))
                except:
                    pass  # Ignore cleanup errors
            
            self.logger.info(f"Cleared all cache entries ({count} from memory)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        
        with self._cache_lock:
            memory_entries = len(self._memory_cache)
        
        disk_entries = 0
        if self.disk_cache_enabled and self.cache_dir:
            try:
                disk_entries = len([
                    f for f in os.listdir(self.cache_dir)
                    if f.endswith('.json')
                ])
            except:
                pass
        
        return {
            'enabled': self.enabled,
            'memory_cache_size': self.memory_cache_size,
            'memory_entries': memory_entries,
            'disk_cache_enabled': self.disk_cache_enabled,
            'disk_entries': disk_entries,
            'default_ttl': self.default_ttl
        }


# Specialized cache helpers
class APICache:
    """Specialized cache for API responses"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.namespace = 'api'
    
    def get_photos(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached photo list"""
        return self.cache.get(self.namespace, f"photos_{method}", params)
    
    def set_photos(self, method: str, params: Dict[str, Any], data: Dict[str, Any], ttl: int = 300) -> bool:
        """Cache photo list"""
        return self.cache.set(self.namespace, f"photos_{method}", data, ttl, params)
    
    def get_photo_info(self, photo_id: str) -> Optional[Dict[str, Any]]:
        """Get cached photo info"""
        return self.cache.get(self.namespace, f"photo_info", {'photo_id': photo_id})
    
    def set_photo_info(self, photo_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache photo info"""
        return self.cache.set(self.namespace, f"photo_info", data, ttl, {'photo_id': photo_id})
    
    def get_photosets(self, user_id: str = 'me') -> Optional[Dict[str, Any]]:
        """Get cached photosets"""
        return self.cache.get(self.namespace, f"photosets", {'user_id': user_id})
    
    def set_photosets(self, data: Dict[str, Any], user_id: str = 'me', ttl: int = 600) -> bool:
        """Cache photosets"""
        return self.cache.set(self.namespace, f"photosets", data, ttl, {'user_id': user_id})
    
    def invalidate_user_data(self, user_id: str = 'me') -> None:
        """Invalidate all cached data for a user"""
        # This is a simplified approach - in practice, you'd want more granular invalidation
        self.cache.invalidate_namespace(self.namespace)