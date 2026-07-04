import logging
import sys


class JsonLikeFormatter(logging.Formatter):
    """Small dependency-free structured log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        return (
            f'ts="{self.formatTime(record, self.datefmt)}" '
            f'level="{record.levelname}" '
            f'logger="{record.name}" '
            f'message="{message.replace(chr(34), chr(39))}"'
        )


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLikeFormatter("%(message)s"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
