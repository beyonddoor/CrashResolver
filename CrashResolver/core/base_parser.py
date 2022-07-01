import os
from pathlib import Path

from .. import config


class ParseError(Exception):
    pass


class BaseCrashParser:
    def parse_crash(self, text: str) -> dict:
        raise NotImplementedError()

    def read_crash(self, filename: str) -> dict:
        '''从文件中提取crash'''
        try:
            with open(filename, 'r', encoding='utf8', errors="ignore") as file:
                crash = self.parse_crash(file.read())
                return crash
        except ParseError as err:
            print(f'invalid android crash {filename}, {err}')
            return None

    def read_crash_list(self, crash_dir: str) -> list:
        '''从目录中提取crash的列表'''
        crashes = []
        for root, _, filenames in os.walk(crash_dir):
            for filename in filenames:
                if not filename.endswith(config.CrashExt):
                    continue

                crash = self.read_crash(Path(root)/filename)
                if crash is None:
                    continue

                crash['filename'] = filename
                crashes.append(crash)
        return crashes
