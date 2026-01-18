import logging
import sys

from quantlib_st.logging.adaptor import *

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

_logging_configured = False


def get_logger(name, attributes=None):
    """
    # set up a logger with a name
    log = get_logger("my_logger")

    # create a log message with a logging level
    log.debug("debug message")
    log.info("info message")
    log.warning("warning message")
    log.error("error message")
    log.critical("critical message")

    # parameterise the message
    log.info("Hello %s", "world")
    log.info("Goodbye %s %s", "cruel", "world")

    # setting attributes on initialisation
    log = get_logger("attributes", {"stage": "first"})

    # setting attributes on message creation
    log.info("logging call attributes", instrument_code="GOLD")

    # merging attributes: method 'overwrite' (default if no method supplied)
    overwrite = get_logger("Overwrite", {"type": "first"})
    overwrite.info("overwrite, type 'first'")
    overwrite.info(
        "overwrite, type 'second', stage 'one'",
        method="overwrite",
        type="second",
        stage="one",
    )

    # merging attributes: method 'preserve'
    preserve = get_logger("Preserve", {"type": "first"})
    preserve.info("preserve, type 'first'")
    preserve.info(
        "preserve, type 'first', stage 'one'", method="preserve", type="second", stage="one"
    )

    # merging attributes: method 'clear'
    clear = get_logger("Clear", {"type": "first", "stage": "one"})
    clear.info("clear, type 'first', stage 'one'")
    clear.info("clear, type 'second', no stage", method="clear", type="second")
    clear.info("clear, no attributes", method="clear")

    :param name: logger name
    :type name: str
    :param attributes: log attributes
    :type attributes: dict
    :return: logger instance
    :rtype: DynamicAttributeLogger
    """
    _configure_logging()
    if not name:
        if attributes and "type" in attributes:
            name = attributes["type"]
    return DynamicAttributeLogger(logging.getLogger(name), attributes)


def _configure_logging():
    global _logging_configured
    if _logging_configured:
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(logging.INFO)
    logging.getLogger("ib_insync").setLevel(logging.WARNING)
    logging.getLogger("arctic").setLevel(logging.INFO)
    logging.getLogger("matplotlib").setLevel(logging.INFO)
    logging.basicConfig(
        handlers=[handler],
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG,
    )
    _logging_configured = True
