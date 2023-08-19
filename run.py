import config
from layers import main
from layers.logger import init_logger

if __name__ == "__main__":
    logger = init_logger(level=config.LOG_LEVEL)

    main(
        streets=config.STREETS,
        buildings=config.BUILDINGS,
        morphometrics=config.MORPHOMETRICS,
        csv_out=config.CSV_OUT,
    )
