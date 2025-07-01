import json
import time
import hashlib
import pathlib
import logging
import functools
from typing import Optional
from datetime import datetime

from .path import DIR_ROOT

logger = logging.getLogger("utu")

DIR_CACHE = DIR_ROOT / ".cache"
DIR_CACHE.mkdir(exist_ok=True)


def async_file_cache(cache_dir: str|pathlib.Path = DIR_CACHE, expire_time: Optional[int] = None):
    """Decorator to cache async function results to local files.
    Args:
        cache_dir (str|pathlib.Path): Directory to store cache files
        expire_time (Optional[int]): Cache expiration time in seconds, None means no expiration
    """
    # TODO: only cache successful results!
    cache_path = pathlib.Path(cache_dir)
    cache_path.mkdir(exist_ok=True, parents=True)
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            cache_args = args[1:] if args and hasattr(args[0], func.__name__) else args  # remove `self`
            args_str = str(cache_args) + str(sorted(kwargs.items()))
            cache_key = hashlib.md5(args_str.encode()).hexdigest()
            cache_file = cache_path / f"{func_name}_{cache_key}.json"
            
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                if expire_time is None or (time.time() - cache_data['metadata']['timestamp']) < expire_time:
                    logger.info(f"🔄 Using cached result for {func_name} from {cache_file}")
                    return cache_data['result']
            
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            metadata = {
                'function': func_name,
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'args': str(cache_args),
                'kwargs': str(kwargs),
                'execution_time': execution_time
            }
            
            cache_data = {
                'result': result,
                'metadata': metadata
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Cached result for {func_name} to {cache_file}")
            return result
        
        return wrapper
    
    return decorator
