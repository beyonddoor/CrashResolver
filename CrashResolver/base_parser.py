from abc import abstractmethod
from asyncio.log import logger
import logging
import os

from pathlib import Path

from .config import get_config

logger = logging.getLogger(__name__)


class ParseError(Exception):
    '''parser失败'''


class BaseCrashParser:
    '''解析crash的base class'''

    @abstractmethod
    def parse_crash(self, text: str, filename=None) -> dict:
        '''解析crash'''

    def read_crash(self, filename: str) -> dict:
        '''从文件中提取crash'''
        try:
            with open(filename, 'r', encoding='utf8', errors="ignore") as file:
                crash = self.parse_crash(file.read(), filename)
                return crash
        except ParseError as err:
            logger.error('invalid android crash %s, %s', filename, err)
            return None

    def read_crash_list(self, crash_dir: str) -> list:
        '''从目录中提取crash的列表'''
        crashes = []
        for root, _, filenames in os.walk(crash_dir):
            for filename in filenames:
                if not filename.endswith(get_config().CrashExt):
                    continue

                crash = self.read_crash(Path(root)/filename)
                if crash is None:
                    continue

                crash['filename'] = filename
                crashes.append(crash)
        return crashes
