import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(raise_error_if_not_found=True), verbose=True, override=True)


class EnvUtils:
    @staticmethod
    def get_env(key: str) -> str | None:
        return os.getenv(key)

    @staticmethod
    def assert_env(key: str) -> None:
        if not os.getenv(key):
            raise ValueError(f"Environment variable {key} is not set")
