import logging

from . import cnf


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("autoalerter")
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger

    handler = logging.FileHandler(cnf.LOG_FILE, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)
    return logger
