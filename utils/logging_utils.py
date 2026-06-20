import logging

logger = logging.getLogger("eduflow")


def log_event(message):
    logger.info(message)


def log_warning(message):
    logger.warning(message)


def log_error(message, exc_info=False):
    logger.error(
        message,
        exc_info=exc_info
    )
