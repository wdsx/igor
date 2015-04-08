import unittest
import logging
from mock import Mock
from wds.logging import log_writer


class LoggingTest (unittest.TestCase):

    def test_it_can_log_info(self):
        logging.info = Mock()
        log_writer.info("My info")
        logging.info.assert_called_with("My info")

    def test_it_can_log_warning(self):
        logging.warning = Mock()
        log_writer.warning("My info")
        logging.warning.assert_called_with("My info")

    def test_it_can_log_errors(self):
        logging.error = Mock()
        log_writer.error("My info")
        logging.error.assert_called_with("My info")

    def test_it_can_log_critical(self):
        logging.critical = Mock()
        log_writer.critical("My info")
        logging.critical.assert_called_with("My info")

    def test_it_can_log_exception(self):
        logging.exception = Mock()
        e = Exception("Lol")
        log_writer.exception("My info", e)
        logging.exception.assert_called_with("My info", e)