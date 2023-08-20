import config
from layers import main
from layers.logger import init_logger

if __name__ == "__main__":
    logger = init_logger(level=config.LOG_LEVEL)

    logger.info("Parameters:")
    logger.info("Streets:       %s", config.STREETS)
    logger.info("Buildings:     %s", config.BUILDINGS)
    logger.info("Morphometrics: %s", config.MORPHOMETRICS)
    logger.info("log level:     %s", config.LOG_LEVEL)
    logger.info("CSV out:       %s", config.CSV_OUT)

    main(
        streets=config.STREETS,
        buildings=config.BUILDINGS,
        morphometrics=config.MORPHOMETRICS,
        csv_out=config.CSV_OUT,
    )
