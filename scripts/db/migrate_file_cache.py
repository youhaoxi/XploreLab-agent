import os
import json
import hashlib

from sqlmodel import create_engine, Session

from utu.db import ToolCacheModel
from utu.utils.tool_cache import DIR_CACHE


engine = create_engine(os.getenv("DB_URL"), echo=True)


def convert_data(data: dict) -> ToolCacheModel:
    meta = data["metadata"]
    cache_key = hashlib.md5(meta["args"].encode()).hexdigest()
    return ToolCacheModel(
        result=data["result"],
        function=meta["function"],
        args=meta["args"],
        kwargs=meta["kwargs"],
        cache_key=cache_key,
        execution_time=meta["execution_time"],
        timestamp=meta["timestamp"],
        datetime=meta["datetime"],
    )


# walk through DIR_CACHE
total = 0
for root, dirs, files in os.walk(DIR_CACHE):
    for file in files:
        if file.endswith(".json"):
            cached_data = json.load(open(os.path.join(root, file)))
            # TODO check duplication
            with Session(engine) as session:
                session.add(convert_data(cached_data))
                session.commit()
            total += 1
            if total % 100 == 0:
                print(f"total: {total}")
print(f"total: {total}")