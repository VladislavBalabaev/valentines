import re
import asyncio
import logging
from queue import Queue
from logging import StreamHandler
from colorlog import ColoredFormatter
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

from .env_reader import BOT_DIR


logs_path = BOT_DIR / "data" / "logs" / "coffee.log"

logs_path.parent.mkdir(parents=True, exist_ok=True)


class AiogramFilter(logging.Filter):
    """
    Filter to block 'aiogram' INFO-level logs from being displayed in the console, but allows others.
    """
    def filter(self, record):
        if record.levelname == 'INFO' and record.name.startswith('aiogram'):
            return False
        return True


class RemoveColorCodesFilter(logging.Filter):
    """
    Filter that removes color codes from log messages before writing them to the log file.
    """
    def filter(self, record):
        record.msg = self.remove_color_codes(record.msg)
        return True

    @staticmethod
    def remove_color_codes(text):
        return re.sub(r'\x1b\[[0-9;]*m', '', text)


colored_console_format = ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s :: %(asctime)s.%(msecs)03d :: %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    },
)


file_format = logging.Formatter("%(levelname)-8s :: %(name)-25s :: %(asctime)s :: %(message)s :: (%(filename)s:%(lineno)d)")


async def init_logger():
    """
    Initializes the logging system with console and file handlers.
    Uses a QueueListener to asynchronously handle log messages.
    """
    que = Queue()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(QueueHandler(que))

    aiogram_logger = logging.getLogger('aiogram')
    aiogram_logger.setLevel(logging.INFO)

    pymongo_logger = logging.getLogger('pymongo')
    pymongo_logger.setLevel(logging.INFO)

    console_handler = StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(colored_console_format)
    console_handler.addFilter(AiogramFilter())

    file_handler = RotatingFileHandler(logs_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_format)
    file_handler.addFilter(RemoveColorCodesFilter())

    listener = QueueListener(que, console_handler, file_handler, respect_handler_level=True)

    try:
        listener.start()
        logging.info(f'### Logger has started working! ###')

        while True:
            await asyncio.sleep(60)
    finally:
        logging.info(f'### Logger has finished working! ###')
        listener.stop()
