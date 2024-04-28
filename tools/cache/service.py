'''
This file contains the cache service for the application. It is responsible for storing and retrieving data from the cache.
'''
import redis
import logging
import functools

class Cache:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.redis = redis.Redis()

    def set(self, key, value):
        try:
            self.redis.set(key, value)
            return True
        except Exception as e:
            self.logger.error(f"Error setting value in cache: {e}")
            return False

    def get(self, key):
        try:
            value = self.redis.get(key)
            if value is not None:
                return value.decode('utf-8')  # Assuming value is stored as a string
            return None
        except Exception as e:
            self.logger.error(f"Error getting value from cache: {e}")
            return None

    def with_caching(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{args}_{kwargs}"
            cached_result = self.get(cache_key)
            if cached_result is not None:
                self.logger.info(f"Cache hit for {cache_key}")
                return cached_result
            else:
                result = func(*args, **kwargs)
                self.set(cache_key, result)
                return result
        return wrapper
