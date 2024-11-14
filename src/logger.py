import logging
from logging.handlers import RotatingFileHandler


class Logger:
    def __init__(self, name: str, log_file: str = "app.log", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        file_handler = RotatingFileHandler(log_file, maxBytes=10 ** 6)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
