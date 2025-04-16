import logging
import sys

def create_simple_logger(level: str, filename: str):
    """
    :param sout: Option that indicates where we want to show the infor if in a file or directly
    through the terminal System output are only availabe for file or direc system output.
    :param level: Level of the logger, DEBUG, INFO, ERROR, CRITICAL
    :param filename: Option file was chosen, this parameter is for the location where the file will be saved.
    :return: The logger with the config.
    """
    log_format: str = '%(asctime)s %(levelname)s %(message)s'
    logger = logging.getLogger(__name__)
    if filename != "":
        logging.basicConfig(level=level,
                            filename=filename,
                            filemode='a',
                            format=log_format)
    else:
        logging.basicConfig(level=level,
                            format=log_format,
                            stream=sys.stdout)
    return logger
