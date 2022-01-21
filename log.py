import logging
import sys
from os import path

DEFAULT = "\033[0m"
BLACK = "\033[1;30m"
RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
MAGENTA = "\033[1;35m"
CYAN = "\033[1;36m"
WHITE = "\033[1;37m"

LOGGERNAME = "pidell"

IMPORTS = ()
logger = logging.getLogger(LOGGERNAME)
dir = path.dirname(__file__)


def get_ready():
    for h in logger.handlers:
        logger.removeHandler(h)

    outhandler = logging.StreamHandler(sys.stdout)
    formatter = LogFormatter(
        fmt="%(asctime)s [%(levelname)s][%(filename)s] %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    outhandler.setFormatter(formatter)
    logger.addHandler(outhandler)
    logger.setLevel(logging.INFO)


class LogFormatter(logging.Formatter):
    def __init__(
        self, fmt: str, datefmt: str, style: str = "%", validate: bool = ...
    ) -> None:

        self.debug_formatter = logging.Formatter(
            fmt=BLUE + fmt + DEFAULT, datefmt=datefmt
        )
        self.info_formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        self.warning_formatter = logging.Formatter(
            fmt=YELLOW + fmt + DEFAULT, datefmt=datefmt
        )
        self.error_formatter = logging.Formatter(
            fmt=MAGENTA + fmt + DEFAULT, datefmt=datefmt
        )
        self.crit_formatter = logging.Formatter(
            fmt=RED + fmt + DEFAULT, datefmt=datefmt
        )
        self.formatters = (
            None,
            self.debug_formatter,
            self.info_formatter,
            self.warning_formatter,
            self.error_formatter,
            self.crit_formatter,
        )

    def format(self, record: logging.LogRecord) -> str:
        return logging.Formatter.format(
            self.formatters[int(record.levelno / 10)], record
        )
