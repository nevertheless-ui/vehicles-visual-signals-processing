"""
Module for logging simplicity.
Can be used same as vanilla logging module.
"""

import logging
import secrets
from typing_extensions import OrderedDict

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



def log_writer_report(logger, writer_report):
    """Writes to log file report from writer. Report is useful for
    understanding behaviour of writer and catching broken chunks.

    Args:
        writer_report (OrderedDict): Any key
    """
    assert isinstance(writer_report, OrderedDict()), 'Writer report type is incorrect'
    for name, value in writer_report.items():
        if name == 'Broken chunks list' and len(value) > 0:
            for record in value:
                logger.debug(f"Report: {name}: {record}")
        else:
            logger.debug(f"Report: {name}: {value}")
