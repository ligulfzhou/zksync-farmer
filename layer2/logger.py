import logging


def get_logger(level=logging.INFO) -> logging.Logger:
    # formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(threadName)-10s] %(message)s')
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger


global_logger = get_logger()
