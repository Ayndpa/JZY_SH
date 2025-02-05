import time
import asyncio
import json
from functools import lru_cache
from typing import Callable, Any
from collections import deque

class RequestPool:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, rpm_limit: int = 10, cache_size: int = 100):
        if not hasattr(self, 'initialized'):
            self.rpm_limit = rpm_limit
            self.interval = 60.0 / rpm_limit
            self.last_request_time = 0.0
            self.request_queue = deque()
            self.cache_size = cache_size
            self._cache = {}
            self.initialized = True

    @staticmethod
    def _get_cache_key(func, *args, **kwargs) -> str:
        """生成可哈希的缓存键"""
        cache_data = {
            'func_name': func.__name__,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }
        return json.dumps(cache_data, sort_keys=True)

    async def _cached_execute(self, func: Callable, *args, **kwargs) -> Any:
        """使用字符串作为缓存键"""
        cache_key = self._get_cache_key(func, *args, **kwargs)
        if cache_key not in self._cache:
            self._cache[cache_key] = await self._execute(func, *args, **kwargs)
        return self._cache[cache_key]

    async def _execute(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            
            if time_since_last_request < self.interval:
                await asyncio.sleep(self.interval - time_since_last_request)
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await asyncio.to_thread(func, *args, **kwargs)
                self.last_request_time = time.time()
                return result
            except Exception as e:
                raise Exception(f"Error executing request: {str(e)}")

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """支持缓存的异步执行"""
        use_cache = kwargs.pop('use_cache', True)
        if use_cache:
            return await self._cached_execute(func, *args, **kwargs)
        return await self._execute(func, *args, **kwargs)

# 创建全局请求池实例
global_request_pool = RequestPool(rpm_limit=10)

async def execute_request(func: Callable, *args, **kwargs) -> Any:
    """异步执行请求的便捷函数"""
    return await global_request_pool.execute(func, *args, **kwargs)

def sync_execute_request(func: Callable, *args, **kwargs) -> Any:
    """同步执行请求的便捷函数"""
    return asyncio.run(execute_request(func, *args, **kwargs))

def set_rpm_limit(rpm: int):
    global_request_pool.rpm_limit = rpm
    global_request_pool.interval = 60.0 / rpm