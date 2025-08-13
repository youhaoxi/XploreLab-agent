import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(raise_error_if_not_found=True), verbose=True, override=True)


def get_env(key: str) -> str:
    return os.getenv(key)

def assert_env(key: str) -> None:
    if not os.getenv(key):
        raise ValueError(f"Environment variable {key} is not set")
