'''对crash的stack进行符号化，同时对crash的原因进行归因'''

import logging
import os
from pathlib import Path
import subprocess

from .. import config
from . import crash_parser

logger = logging.getLogger(__name__)


def parse_reason(crash, reasons) -> str:
    '''从crash中推断原因'''
    stacks = '\n'.join(crash['stacks'])
    for reason in reasons:
        if stacks.find(reason) >= 0:
            return reason
    return None


def symbolicate(filename):
    '''进行符号化'''
    subprocess.run(['bash', config.SymbolicatePath, filename], check=False)


class Symbolicator:
    '''
    尝试符号化有代表性的crash
    '''

    def __init__(self, symbol_func, parse_reason_func, parser: crash_parser.BaseCrashParser) -> None:
        self._symbol_func = symbol_func
        self._parse_reason_func = parse_reason_func
        self._crash_parser = parser

        if self._symbol_func is None:
            self._symbol_func = symbolicate

    def symbolicate_same_crashes(self, crash_list: enumerate, crash_dir: str, symbolicate_crashes: list):
        '''将同一种crash指定原因和符号化的stack'''
        crash_dir_obj = Path(crash_dir)
        found_crash = None

        for crash in crash_list:
            if crash['filename'][0:-len(config.CrashExt)] in symbolicate_crashes:
                found_crash = crash
                logger.info(
                    '--- already symbolicated: {filename}', filename=found_crash["filename"])
                break

        # 没有符号化，则先符号化有代表性的crash，解析符号化之后的文件
        if found_crash is None:
            found_crash = crash_list[0]
            logger.info(
                '--- try symbolicate file: {filename}', filename=found_crash["filename"])
            self._symbol_func(crash_dir_obj / found_crash['filename'])

        result_filename = found_crash['filename'][0:-
                                                  len(config.CrashExt)] + config.SymbolExt
        final_crash = self._crash_parser.read_crash(
            crash_dir_obj / result_filename)

        reason = self._parse_reason_func(final_crash)
        # print(config.SymbolExt, result_filename, reason)
        for crash in crash_list:
            crash['crash_reason'] = reason
            crash['symbol_stacks'] = final_crash['stacks']
