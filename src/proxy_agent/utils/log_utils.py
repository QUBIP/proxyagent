import logging
import sys

from proxy_agent.model.config import LoggingConfig


def create_simple_logger(log_config: LoggingConfig) -> None:
    """
    :param sout: Option that indicates where we want to show the infor if in a file or directly
    through the terminal System output are only availabe for file or direc system output.
    :param level: Level of the logger, DEBUG, INFO, ERROR, CRITICAL
    :param filename: Option file was chosen, this parameter is for the location where the file will be saved.
    :return: The logger with the config.
    """
    log_format: str = '%(asctime)s %(levelname)s (%(threadName)s) %(message)s'

    if log_config.file != "":
        logging.basicConfig(level=log_config.level,
                            filename=log_config.file,
                            filemode='a',
                            format=log_format)
    else:
        logging.basicConfig(level=log_config.level,
                            format=log_format,
                            stream=sys.stdout)