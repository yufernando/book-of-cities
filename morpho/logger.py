import logging
import sys
from pathlib import Path


def get_logger(level="INFO", filename=None):
    if not filename:
        log_folder = Path("logs")
        filename = log_folder / (Path(sys.argv[0]).stem + ".log")

    # Configure logging
    logger = logging.getLogger("log")

    level_dict = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    logger.setLevel(level_dict[level.upper()])

    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if log_folder.exists():
        fh = logging.FileHandler(filename, mode="w")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info(f"Saving logs to {filename}")
    else:
        logger.warning(
            f"Logs will only be printed to screen. Could not find log folder: {log_folder.absolute()}"
        )

    return logger
