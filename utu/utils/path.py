import pathlib

def get_package_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent.parent

DIR_ROOT = get_package_path()