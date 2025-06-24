import json
import sys
import pathlib
import logging

DIR_LOGS = pathlib.Path(__file__).parent.parent.parent / "logs"
DIR_LOGS.mkdir(exist_ok=True)

LOGGING_LEVEL = logging.INFO

def set_log_level(level: str | int) -> None:
    """ Setup logging level """
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    global LOGGING_LEVEL
    LOGGING_LEVEL = level
    logger = logging.getLogger("utu")
    logger.setLevel(level)

def setup_logging() -> None:
    log_format = "%(asctime)s - %(name)s - %(pathname)s:%(lineno)d - %(levelname)s - %(message)s"
    logging.basicConfig(
        format=log_format,
    )

    logger = logging.getLogger("utu")
    logger.setLevel(LOGGING_LEVEL)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(stdout_handler)

    file_handler = logging.FileHandler(DIR_LOGS / "utu.log")
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)

def oneline_object(obj: object, limit: int = 100) -> str:
    try:
        s = json.dumps(obj, ensure_ascii=False)
    except:
        s = json.dumps(str(obj), ensure_ascii=False)
    return f"{s[:limit]}..." if len(s) > limit else s

setup_logging()
