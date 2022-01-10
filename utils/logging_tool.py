"""
Module for logging simplicity.
Can be used same as vanilla logging module.
"""

import logging
import secrets

from utils import constants as c



def get_logger():
    logger_id = secrets.token_urlsafe(16)

    logging.basicConfig(
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        filename=c.LOGGER_FILENAME,
        encoding='utf-8',
        level=logging.DEBUG
    )

    logger = logging.getLogger(logger_id)

    return logger
