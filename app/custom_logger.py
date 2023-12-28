import logging
from colorlog import ColoredFormatter


class CustomColoredFormatter(ColoredFormatter):
    LOG_COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bg_red',
    }

    def __init__(self, *args, **kwargs):
        # Set the format for the message
        fmt = "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s " "%(white)s%(message)s"

        # Initialize the ColoredFormatter with the format and colors
        super().__init__(fmt, log_colors=self.LOG_COLORS, *args, **kwargs)


def setup_logger(name):
    # Create a handler with a stream output (console)
    handler = logging.StreamHandler()

    # Set the formatter to our custom colored formatter
    handler.setFormatter(CustomColoredFormatter())

    # Get the logger instance
    logger = logging.getLogger(name)

    # Add the handler to the logger
    logger.addHandler(handler)

    # Set the logging level (DEBUG to capture all messages)
    logger.setLevel(logging.DEBUG)

    # Return the logger instance
    return logger


# Example usage
if __name__ == "__main__":
    logger = setup_logger('my_logger')
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')
