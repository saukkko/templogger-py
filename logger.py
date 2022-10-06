import logging


def level_matcher(level: str):
    match level.upper():
        case "DEBUG":
            return logging.DEBUG
        case "INFO":
            return logging.INFO
        case "WARN":
            return logging.WARN
        case _:
            raise ValueError("Invalid loglevel. Currently only DEBUG, INFO and WARN are supported")


def setup_logger(level: str) -> logging.Logger:
    logger = logging.getLogger()
    frmt = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(frmt)
    logger.setLevel(level_matcher(level))
    ch.setLevel(level_matcher(level))
    logger.addHandler(ch)
    return logger


def init_logger(loglevel: str = "WARN"):
    if loglevel not in ["DEBUG", "INFO", "WARN", "ERROR"]:
        raise ValueError("Invalid loglevel provided")
    logger = setup_logger(loglevel)
    logger.debug(f"Logger module initialized")
    logger.info(f"Loglevel set to '{loglevel}'")

    return logger

