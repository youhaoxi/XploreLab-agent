import asyncio
from jinja2 import Environment, FileSystemLoader


def get_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def get_jinja_env(directory: str) -> Environment:
    return Environment(loader=FileSystemLoader(directory))
