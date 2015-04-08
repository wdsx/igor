import logging


def info(msg):
    logging.info(msg)

def warning(msg):
    logging.warning(msg)

def error(msg):
    logging.error(msg)

def exception(msg, exception):
    logging.exception(msg, exception)

def critical(msg):
    logging.critical(msg)