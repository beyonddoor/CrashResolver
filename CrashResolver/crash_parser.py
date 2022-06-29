'''
对已经fetch的所有crash，进行汇总。
初步的汇总比较简单，将stack生成指纹（fingerprint），根据指纹汇总。
'''

from enum import Enum
from pathlib import Path
import os
import re
import csv

from . import config

class ParseError(Exception):
    pass

class BaseCrashParser:
    def parse_crash(self, text: str) -> dict:
        raise NotImplementedError()

    def read_crash(self, filename: str) -> dict:
        '''从文件中提取crash'''
        try:
            with open(filename, 'r', encoding='utf8', errors="ignore") as file:
                text = file.read()
                crash = self.parse_crash(text)
                return crash
        except ParseError as e:
            print(f'invalid android crash {filename}, {e}')
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
        self._is_rough = False

    @staticmethod
    def stack_fingerprint(stacks: list[str], is_rough) -> str:
        '''从stack计算一个指纹'''
        # #00 pc 0006b6d8  /system/lib/arm711/nb/libc.so (pthread_kill+0)
        lines = []
        for stack in stacks:
            if stack.startswith('backtrace:'):
                continue
            parts = stack.strip().split(' ', 4)
            del parts[2]
            lines.append(' '.join(parts))
        return '\n'.join(lines)

    def parse_crash(self, text: str) -> dict:
        '''从文本解析crash信息，保存结果为字典'''
        lines = text.split('\n')
        stacks = []
        reason_lines = []
        crash = {}
        state = AndroidParseState.INIT
        for index, line in enumerate(lines):
            if state == AndroidParseState.INIT:
                if line.startswith("***"):
                    state = AndroidParseState.HEADER
            elif state == AndroidParseState.HEADER:
                if line.startswith("**"):
                    continue
                _parse_header(crash, line)
                if line.startswith('pid: '):
                    state = AndroidParseState.REASON
                    if not lines[index + 1].startswith('signal ') or not lines[index + 2].startswith('    r0'):
                        raise ParseError('invalid android crash')

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
                break

        crash['stacks'] = stacks
        crash['reason'] = '\n'.join(reason_lines)
        crash['stack_key'] = AndroidCrashParser.stack_fingerprint(
            stacks, self._is_rough)
        return crash


class IosParseState(Enum):
    '''ios解析状态'''
    INIT = 0
    HEADER = 1
    HEADER_FINISH = 2
    CRASH_STACK = 3
    CRASH_STACK_FINISH = 4
    BINARY_IMAGE = 5


class IosCrashParser(BaseCrashParser):
    '''ios crash的解析'''

    # 0   UnityFramework                      0x000000010c975748 0x10c0d8000 + 9033544
    PATTERN_DETAIL_STACK = re.compile(
        '[0-9]+ +([^ ]+) +0x[0-9a-f]+ 0x[0-9a-f]+ \\+ ([0-9]+)')

    # 0   UnityFramework                      0x000000010c975748 0x10c0d8000 + 9033544
    PATTERN_ROUGH_STACK = re.compile('[0-9]+ +([^ ]+)')

    PATTERN_FRAMEWORK_NAME = re.compile('[0-9]+ +([^ ]+) +0x.+')

    # 0x102b14000 -        0x102b1ffff  libobjc-trampolines.dylib arm64e  <c4eb3fea90983e00a8b00b468bd6701d> /usr/lib/libobjc-trampolines.dylib
    PATTERN_BINARY_IMAGE = re.compile(
        '.*(0x[0-9a-f]+) - +(0x[0-9a-f]+) +([^ ]+) +([^ ]+) +<([^>]+)>')

    def __init__(self, is_rough) -> None:
        self._is_rough = is_rough

    @staticmethod
    def stack_fingerprint(stacks: list, is_rough) -> str:
        '''从stack计算一个指纹'''

        stack_list = []
        if not is_rough:
            for stack in stacks:
                match = re.match(IosCrashParser.PATTERN_DETAIL_STACK, stack)
                if match:
                    stack_list.append(
                        f'{match.groups()[0]}:{match.groups()[1]}')
        else:
            for stack in stacks:
                match = re.match(IosCrashParser.PATTERN_ROUGH_STACK, stack)
                if match:
                    stack_list.append(match.groups()[0])
        return '\n'.join(stack_list)

    @staticmethod
    def parse_stack_frameworks(stacks: list) -> dict:
        '''解析stack中的framework'''
        frameworks = {}
        for stack in stacks:
            match = re.match(IosCrashParser.PATTERN_FRAMEWORK_NAME, stack)
            if match:
                framework_name = match.groups()[0]
                frameworks[framework_name] = True

        return frameworks

    def parse_crash(self, text: str) -> dict:
        '''从文本解析crash信息，保存结果为字典'''
        lines = text.split('\n')
        stacks = []
        crash = {}
        state = IosParseState.HEADER
        stack_frameworks = {}

        for line in lines:
            if state == IosParseState.HEADER:
                _parse_header(crash, line)
                if line.startswith('Crashed Thread:'):
                    state = IosParseState.HEADER_FINISH

            elif state == IosParseState.HEADER_FINISH:
                if line.endswith('Crashed:'):
                    state = IosParseState.CRASH_STACK

            elif state == IosParseState.CRASH_STACK:
                if line == "":
                    state = IosParseState.CRASH_STACK_FINISH
                    break
                else:
                    stacks.append(line)

            elif state == IosParseState.CRASH_STACK_FINISH:
                if line.startswith('Binary Images:'):
                    state = IosParseState.BINARY_IMAGE
                    stack_frameworks = IosCrashParser.parse_stack_frameworks(
                        stacks)

            elif state == IosParseState.BINARY_IMAGE:
                match = re.match(IosCrashParser.PATTERN_BINARY_IMAGE, line)
                if match:
                    framework_name = match.groups()[2]
                    if framework_name in stack_frameworks:
                        stack_frameworks[framework_name] = {
                            'uuid': match.groups()[4],
                            'offset': match.groups()[0]
                        }

        crash['stacks'] = stacks
        crash['is_arm64e'] = text.find('CoreFoundation arm64e') >= 0
        crash['stack_key'] = IosCrashParser.stack_fingerprint(
            stacks, self._is_rough)
        return crash


def _parse_header(headers: dict, text: str):
    '''提取键值对'''
    if text == '':
        return
    arr = text.split(':')
    headers[arr[0]] = arr[1].strip()


def save_crashes_to_csv_file(crash_list: list[dict], csv_file: str):
    '''保存crash到csv文件'''
    with open(csv_file, 'w', encoding='utf8') as file:
        writer = csv.writer(file, 'excel')
        writer.writerow(crash_list[0].keys())

        for crash in crash_list:
            writer.writerow(crash.values())


def classify_by_stack(crash_list: list[dict]) -> dict[str, dict]:
    '''根据stack的指纹分类crash'''
    crashes = {}
    for crash in crash_list:
        fingerprint = crash['stack_key']
        if fingerprint not in crashes:
            crashes[fingerprint] = []

        crashes[fingerprint].append(crash)

    return crashes


def stringify_crash(crash: dict) -> str:
    return str(crash)


def save_crashes_to_file(crash_list, filename: str):
    '''将crash的写入文件'''
    with open(filename, 'w', encoding='utf8') as file:
        for crashes_pair in crash_list:
            file.write(f'\n------ {len(crashes_pair[1])} in total ------\n')

            for crash in crashes_pair[1]:
                file.write(str(crash))
                file.write("\n")


def is_os_available(crash: dict, os_names: set) -> bool:
    '''os的符号是否可用'''
    arm64e = 'arm64e' if crash['is_arm64e'] else 'arm64'
    return (crash['OS Version'] + ' ' + arm64e) in os_names


def read_os_names(filename) -> set:
    '''读取已经下载就绪的os名字，比如 iPhone OS 13.6 (17G68) arm64e'''
    lines = []
    with open(filename, 'r', encoding='utf8') as file:
        lines = file.read().split('\n')
    return set(line for line in lines if line.strip() != '')
