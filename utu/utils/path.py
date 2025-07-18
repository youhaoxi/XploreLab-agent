import pathlib
import hashlib
import tempfile
import requests
from urllib.parse import urlparse


def get_package_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent.parent

DIR_ROOT = get_package_path()


class FileUtils:
    @staticmethod
    def is_web_url(url: str) -> bool:
        parsed_url = urlparse(url)
        return all([parsed_url.scheme, parsed_url.netloc])

    @staticmethod
    def get_file_ext(file_path: str) -> str:
        if FileUtils.is_web_url(file_path):
            return pathlib.Path(urlparse(file_path).path).suffix
        return pathlib.Path(file_path).suffix

    @staticmethod
    def download_file(url: str, save_path: str=None) -> str:
        """Download file from web. Return the saved path"""
        # if not save_path, use tempfile
        if not save_path:
            save_path = tempfile.NamedTemporaryFile(
                suffix=FileUtils.get_file_ext(url),
                delete=False,
            ).name
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        return save_path

    @staticmethod
    def get_file_md5(file_path: str) -> str:
        hash_md5 = hashlib.md5()
        if FileUtils.is_web_url(file_path):
            file_path = FileUtils.download_file(file_path)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
