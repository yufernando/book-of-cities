"""
Main Entrypoint
"""
import sys

import config
from boundaries.boundaries import get_boundaries
from layers import main
from layers.logger import init_logger

if __name__ == "__main__":
    logger = init_logger(level=config.LOG_LEVEL)

    logger.info("City list:      %s", ", ".join(config.CITY_LIST))

    if len(sys.argv) == 2 and sys.argv[1] == "boundaries":
        get_boundaries(config.CITY_LIST)
        sys.exit(0)

    logger.info("Parameters:")
    logger.info(" Streets:       %s", config.STREETS)
    logger.info(" Buildings:     %s", config.BUILDINGS)
    logger.info(" Morphometrics: %s", config.MORPHOMETRICS)
    logger.info(" Full vars:     %s", config.FULL_VARIABLES)
    logger.info(" CSV out:       %s", config.CSV_OUT)
    logger.info(" Log level:     %s", config.LOG_LEVEL)

    main(
        city_list=config.CITY_LIST,
        streets=config.STREETS,
        buildings=config.BUILDINGS,
        morphometrics=config.MORPHOMETRICS,
        full=config.FULL_VARIABLES,
        csv_out=config.CSV_OUT,
    )
