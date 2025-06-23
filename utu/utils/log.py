import pathlib
import logging

DIR_LOGS = pathlib.Path(__file__).parent.parent.parent / "logs"
DIR_LOGS.mkdir(exist_ok=True)


def setup_logging():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format=log_format,
    # )

    logger = logging.getLogger("utu")
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(DIR_LOGS / "utu.log")
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)
    return logger


logger = setup_logging()
