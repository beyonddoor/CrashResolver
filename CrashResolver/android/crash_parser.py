'''
解析ios和android的crash文件，结构化为一个dict
'''

from enum import Enum
from pathlib import Path
import os
import re
import csv

from ..core.base_parser import BaseCrashParser


class AndroidParseState(Enum):
    '''解析状态'''
    INIT = 0
    HEADER = 1
    '''解析header'''
    REASON = 2
    '''解析原因'''
    BACKTRACE = 3
    '''解析crash堆栈'''
    LOG = 4
    '''解析日志'''


class AndroidCrashParser(BaseCrashParser):
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
                parts[-1] = AndroidCrashParser._normalize_path(
                    parts[-1], 'com.longtugame.yjfb')
            else:
                # 非游戏的so符号地址不确定
                parts[2] = '(MAY_CHANGE_PER_OS)'
            lines.append(' '.join(parts))

        return '\n'.join(lines)

    def parse_crash(self, text: str) -> dict:
        '''从文本解析crash信息，保存结果为字典'''
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
                        log_line = f" {crash['crash_pid']} {crash['crash_tid']} " if int(
                            crash['crash_tid']) >= 10000 else f" {crash['crash_pid']}  {crash['crash_tid']} "

                    state = AndroidParseState.REASON

                    if not lines[index + 1].startswith('signal ') or not lines[index + 2].startswith('    '):
                        # 没有traceback，提取log
                        state = AndroidParseState.LOG

            elif state == AndroidParseState.REASON:
                # TODO 解析reason
                if line == '':
                    state = AndroidParseState.BACKTRACE
                else:
                    reason_lines.append(line)

            elif state == AndroidParseState.BACKTRACE:
                if line == '':
                    state = AndroidParseState.LOG
                else:
                    stacks.append(line)

            elif state == AndroidParseState.LOG:
                if log_line_pattern is None:
                    break
                if len(line) > 0 and line[0] >= '0' and line[0] <= '9' and re.match(log_line_pattern, line) is not None:
                    logs.append(line)
                # if log_line is None:
                #     break
                # if len(line)>0 and line[0]>='0' and line[0]<='9' and log_line in line:
                #     logs.append(line)

        crash['stacks'] = stacks
        crash['thread_logs'] = '\n'.join(logs)

        if len(stacks) == 0:
            crash['reason'] = 'NO_BACKTRACE'
            crash['stack_key'] = 'NO_BACKTRACE'
        else:
            crash['reason'] = '\n'.join(reason_lines)
            crash['stack_key'] = AndroidCrashParser.stack_fingerprint(stacks)
        return crash


def _parse_header(headers: dict, text: str):
    '''提取键值对'''
    if text == '':
        return
    arr = text.split(':')
    headers[arr[0]] = arr[1].strip()
