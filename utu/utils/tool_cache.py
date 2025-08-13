import os
import json
import time
import hashlib
import pathlib
import functools
from typing import Optional, Literal
from datetime import datetime

from sqlmodel import create_engine, Session, select

from .path import DIR_ROOT
from ..db import ToolCacheModel
from ..utils import get_logger

logger = get_logger(__name__)

DIR_CACHE = DIR_ROOT / ".cache"
DIR_CACHE.mkdir(exist_ok=True)

engine = create_engine(
    os.getenv("DB_URL"), pool_size=300, max_overflow=500, pool_timeout=30
)  # set a larger pool size to avoid connection pool overflow


def async_file_cache(
    cache_dir: str | pathlib.Path = DIR_CACHE, expire_time: Optional[int] = None, mode: Literal["db", "file"] = "db"
):
    """Decorator to cache async function results to local files.
    Args:
        cache_dir (str|pathlib.Path): Directory to store cache files
        expire_time (Optional[int]): Cache expiration time in seconds, None means no expiration
    """
    # TODO: only cache successful results!
    cache_path = pathlib.Path(cache_dir)
    cache_path.mkdir(exist_ok=True, parents=True)

    def decorator_file(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            cache_args = args[1:] if args and hasattr(args[0], func.__name__) else args  # remove `self`
            args_str = str(cache_args) + str(sorted(kwargs.items()))
            cache_key = hashlib.md5(args_str.encode()).hexdigest()
            cache_file = cache_path / f"{func_name}" / f"{func_name}_{cache_key}.json"
            cache_file.parent.mkdir(exist_ok=True, parents=True)

            if cache_file.exists():
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                if expire_time is None or (time.time() - cache_data["metadata"]["timestamp"]) < expire_time:
                    logger.debug(f"🔄 Using cached result for {func_name} from {cache_file}")
                    return cache_data["result"]

            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            metadata = {
                "function": func_name,
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                "args": str(cache_args),
                "kwargs": str(kwargs),
                "execution_time": execution_time,
            }

            cache_data = {"result": result, "metadata": metadata}

            with open(cache_file, "w") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"💾 Cached result for {func_name} to {cache_file}")
            return result

        return wrapper

    def decorator_db(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            cache_args = args[1:] if args and hasattr(args[0], func.__name__) else args  # remove `self`
            args_str = str(cache_args) + str(sorted(kwargs.items()))
            cache_key = hashlib.md5(args_str.encode()).hexdigest()

            with Session(engine) as session:
                stmt = select(ToolCacheModel).where(
                    ToolCacheModel.function == func_name, ToolCacheModel.cache_key == cache_key
                )
                if_exist = session.exec(stmt).first()  # one_or_none
                if if_exist and (expire_time is None or (time.time() - if_exist.timestamp) < expire_time):
                    logger.debug(f"🔄 Using cached result for {func_name} from db")
                    return if_exist.result
                else:
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    data = ToolCacheModel(
                        function=func_name,
                        args=args_str,
                        kwargs=str(kwargs),
                        result=result,
                        cache_key=cache_key,
                        execution_time=execution_time,
                        timestamp=time.time(),
                        datetime=datetime.now().isoformat(),
                    )
                    session.add(data)
                    session.commit()
                    logger.debug(f"💾 Cached result for {func_name} to db")
                    return result

        return wrapper

    if mode == "db":
        return decorator_db
    elif mode == "file":
        return decorator_file
    else:
        raise ValueError(f"Invalid mode: {mode}")
