import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(raise_error_if_not_found=True), verbose=True, override=True)


class EnvUtils:
    @staticmethod
    def get_env(key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)

    @staticmethod
    def assert_env(key: str | list[str]) -> None:
        if isinstance(key, list):
            for k in key:
                EnvUtils.assert_env(k)
        if not os.getenv(key):
            raise ValueError(f"Environment variable {key} is not set")
