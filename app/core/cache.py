import redis
import json
import hashlib
import time
from typing import Any, Optional, Dict
import os
import pickle

class CacheManager:
    def __init__(self):
        # Redis connection for caching
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=2,
            decode_responses=True
        )
        
        # Cache TTL settings (in seconds)
        self.cache_ttl = {
            'scam_detection': 3600,  # 1 hour
            'agent_reply': 1800,      # 30 minutes
            'model_predictions': 7200, # 2 hours
            'analytics': 300,         # 5 minutes
            'intelligence': 86400,    # 24 hours
            'user_sessions': 1800     # 30 minutes
        }
        
        # Local memory cache for frequently accessed items
        self.local_cache = {}
        self.local_cache_size = 1000
        self.local_cache_ttl = 300  # 5 minutes
    
    def _generate_cache_key(self, prefix: str, data: Any) -> str:
        """Generate cache key from prefix and data"""
        if isinstance(data, (str, int, float, bool)):
            content = str(data)
        else:
            content = json.dumps(data, sort_keys=True)
        
        hash_key = hashlib.md5(content.encode()).hexdigest()
        return f"{prefix}:{hash_key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (local first, then Redis)"""
        # Check local cache first
        if key in self.local_cache:
            cache_item = self.local_cache[key]
            if time.time() - cache_item['timestamp'] < self.local_cache_ttl:
                return cache_item['value']
            else:
                del self.local_cache[key]
        
        # Check Redis cache
        try:
            cached_value = self.redis_client.get(key)
            if cached_value:
                # Deserialize and store in local cache
                try:
                    value = json.loads(cached_value)
                except json.JSONDecodeError:
                    # Try pickle as fallback
                    try:
                        value = pickle.loads(cached_value.encode('latin1'))
                    except:
                        return cached_value
                
                # Store in local cache
                self._store_local(key, value)
                return value
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache (both local and Redis)"""
        try:
            # Store in local cache
            self._store_local(key, value)
            
            # Serialize and store in Redis
            try:
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                # Use pickle for complex objects
                serialized_value = pickle.dumps(value).decode('latin1')
            
            # Set TTL
            if ttl is None:
                # Determine TTL from key prefix
                for prefix, default_ttl in self.cache_ttl.items():
                    if key.startswith(prefix):
                        ttl = default_ttl
                        break
                else:
                    ttl = 3600  # Default 1 hour
            
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            # Remove from local cache
            if key in self.local_cache:
                del self.local_cache[key]
            
            # Remove from Redis
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            # Clear from local cache
            keys_to_delete = [key for key in self.local_cache.keys() if pattern in key]
            for key in keys_to_delete:
                del self.local_cache[key]
            
            # Clear from Redis
            redis_keys = self.redis_client.keys(pattern)
            if redis_keys:
                return self.redis_client.delete(*redis_keys)
            return 0
        except Exception as e:
            print(f"Cache clear pattern error: {e}")
            return 0
    
    def _store_local(self, key: str, value: Any):
        """Store value in local cache with LRU eviction"""
        # Remove oldest item if cache is full
        if len(self.local_cache) >= self.local_cache_size:
            oldest_key = min(self.local_cache.keys(), 
                           key=lambda k: self.local_cache[k]['timestamp'])
            del self.local_cache[oldest_key]
        
        self.local_cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            redis_info = self.redis_client.info()
            redis_keys = self.redis_client.dbsize()
            
            return {
                'local_cache_size': len(self.local_cache),
                'redis_keys_count': redis_keys,
                'redis_memory_used': redis_info.get('used_memory_human', 'N/A'),
                'redis_hit_rate': redis_info.get('keyspace_hits', 0),
                'redis_miss_rate': redis_info.get('keyspace_misses', 0)
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {
                'local_cache_size': len(self.local_cache),
                'redis_keys_count': 0,
                'redis_memory_used': 'Error',
                'redis_hit_rate': 0,
                'redis_miss_rate': 0
            }

class SmartCache:
    """Smart cache with intelligent invalidation"""
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.dependency_graph = {}  # Track cache dependencies
    
    def get_cached_result(self, operation: str, params: Dict, compute_func, ttl: Optional[int] = None):
        """Get cached result or compute and cache"""
        cache_key = self.cache._generate_cache_key(operation, params)
        
        # Try to get from cache
        result = self.cache.get(cache_key)
        if result is not None:
            return result
        
        # Compute result
        result = compute_func()
        
        # Cache the result
        self.cache.set(cache_key, result, ttl)
        
        return result
    
    def invalidate_dependencies(self, operation: str):
        """Invalidate all caches that depend on this operation"""
        if operation in self.dependency_graph:
            for dependent in self.dependency_graph[operation]:
                self.cache.clear_pattern(f"*{dependent}*")
    
    def add_dependency(self, operation: str, depends_on: str):
        """Add dependency relationship"""
        if depends_on not in self.dependency_graph:
            self.dependency_graph[depends_on] = []
        self.dependency_graph[depends_on].append(operation)

# Global cache instances
cache_manager = CacheManager()
smart_cache = SmartCache(cache_manager)

def cached_result(operation: str, ttl: Optional[int] = None):
    """Decorator for caching function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            params = {
                'args': args,
                'kwargs': kwargs
            }
            
            def compute():
                return func(*args, **kwargs)
            
            return smart_cache.get_cached_result(operation, params, compute, ttl)
        return wrapper
    return decorator

def get_cached_scam_detection(message: str) -> Optional[Dict]:
    """Get cached scam detection result"""
    cache_key = cache_manager._generate_cache_key('scam_detection', message)
    return cache_manager.get(cache_key)

def cache_scam_detection(message: str, result: Dict):
    """Cache scam detection result"""
    cache_key = cache_manager._generate_cache_key('scam_detection', message)
    cache_manager.set(cache_key, result, cache_manager.cache_ttl['scam_detection'])

def get_cached_agent_reply(context: str, message: str) -> Optional[str]:
    """Get cached agent reply"""
    cache_key = cache_manager._generate_cache_key('agent_reply', {'context': context, 'message': message})
    return cache_manager.get(cache_key)

def cache_agent_reply(context: str, message: str, reply: str):
    """Cache agent reply"""
    cache_key = cache_manager._generate_cache_key('agent_reply', {'context': context, 'message': message})
    cache_manager.set(cache_key, reply, cache_manager.cache_ttl['agent_reply'])

def invalidate_user_cache(user_identifier: str):
    """Invalidate all cache entries for a specific user"""
    patterns = [
        f"*{user_identifier}*",
        f"*session:{user_identifier}*"
    ]
    
    for pattern in patterns:
        cache_manager.clear_pattern(pattern)
