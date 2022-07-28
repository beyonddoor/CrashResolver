'''
解析ios和android的crash文件，结构化为一个dict
'''

from asyncio.log import logger
from enum import Enum
from pathlib import Path
import os
import re
import csv
import logging

from ..base_parser import BaseCrashParser

logger = logging.getLogger(__name__)

PAT_SO = re.compile('.*/lib/([^/]+)/\w+\.so', re.MULTILINE | re.DOTALL)
'''提取abi'''


PAT_BLOCK_HEADER = re.compile('^(\w[^:]+):$')
'''提取块名'''


class AndroidParseState(Enum):
    '''解析状态'''
    INIT = 0
    HEADER = 1
    '''解析header'''
    SIGNAL = 2
    '''解析原因'''
    BACKTRACE = 3
    '''解析crash堆栈'''
    LOG = 4
    '''解析日志'''
    BLOCK = 5
    '''解析块，每行为"Xxx:"是特征 '''


def get_abi_name(stacks):
    '''提取abi'''
    pattern = PAT_SO.match(stacks)
    if pattern:
        return pattern.groups()[0]


class TumbstoneParser(BaseCrashParser):
    '''从text中解析android crash信息'''

    def __init__(self) -> None:
        pass

    @staticmethod
    def _normalize_path(path: str, default: str) -> str:
        '''app的路径可能会变化，标准化'''
        parts = path.split('/')
        parts[3] = default
        return '/'.join(parts)

    @staticmethod
    def stack_fingerprint(stacks: list[str]) -> str:
        '''从stack计算一个指纹'''
        # #00 pc 0006b6d8  /system/lib/arm711/nb/libc.so (pthread_kill+0)
        lines = []

        for stack in stacks:
            if stack.startswith('backtrace:'):
                continue
            parts = stack.strip().split(' ', 4)
            if parts[-1].startswith('/data/app/com.longtugame.yjfb'):
                # 游戏的so符号地址应该是相同的
                parts[-1] = TumbstoneParser._normalize_path(
                    parts[-1], 'com.longtugame.yjfb')
            else:
                # 非游戏的so符号地址不确定
                parts[2] = '(MAY_CHANGE_PER_OS)'
            lines.append(' '.join(parts))

        return '\n'.join(lines)

    def parse_crash(self, text: str, filename) -> dict:
        '''从文本解析crash信息，保存结果为字典'''
        # logger.info('parse_crash %s', filename)
        stacks = []
        reason_lines = []
        crash = {}
        logs = []
        log_line_pattern = None
        state = AndroidParseState.INIT
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if state == AndroidParseState.INIT:
                if line.startswith("***"):
                    state = AndroidParseState.HEADER

            elif state == AndroidParseState.HEADER:
                if line.startswith("**"):
                    continue

                _parse_header(crash, line)

                if line.startswith('pid: '):
                    # pid: 20433, tid: 20625
                    match = re.match('pid: ([^,]+), tid: ([^,]+)', line)
                    if match:
                        crash['crash_pid'] = match.groups()[0]
                        crash['crash_tid'] = match.groups()[1]
                        log_line_pattern = re.compile(
                            f"[0-9]+.* {crash['crash_pid']} +{crash['crash_tid']} .*")

                    state = AndroidParseState.BLOCK

            elif state == AndroidParseState.BLOCK:
                block_match = PAT_BLOCK_HEADER.match(line)
                if block_match:
                    name = block_match.groups()[0]
                    # logger.debug('block name %s', name)

                    if 'backtrace' == name:
                        state = AndroidParseState.BACKTRACE
                    elif 'logcat' == name:
                        state = AndroidParseState.LOG

            elif state == AndroidParseState.BACKTRACE:
                if line == '':
                    state = AndroidParseState.BLOCK
                else:
                    stacks.append(line)

            elif state == AndroidParseState.LOG:
                if len(line) > 0 and line[0] >= '0' and line[0] <= '9' and log_line_pattern.match(line) is not None:
                    logs.append(line)
                if line == '':
                    state = AndroidParseState.BLOCK

        crash['stacks'] = '\n'.join(stacks)
        crash['thread_logs'] = '\n'.join(logs)
        crash['abi_name'] = get_abi_name(crash['stacks'])
        # logger.info('abi_name %s %s', filename, crash['abi_name'])
        if not crash['abi_name']:
            logger.error('abi_name not found for %s', filename)
            # logger.debug(crash['stacks'])

        if len(stacks) == 0:
            crash['reason'] = 'NO_BACKTRACE'
            crash['stack_key'] = 'NO_BACKTRACE'
        else:
            crash['reason'] = '\n'.join(reason_lines)
            crash['stack_key'] = TumbstoneParser.stack_fingerprint(stacks)
        return crash


def _parse_header(headers: dict, text: str):
    '''提取键值对'''
    if text == '':
        return
    arr = text.split(':', maxsplit=1)
    headers[arr[0]] = arr[1].strip()
