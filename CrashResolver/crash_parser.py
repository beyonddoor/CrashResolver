'''
对已经fetch的所有crash，进行汇总。
初步的汇总比较简单，将stack生成指纹（fingerprint），根据指纹汇总。
'''

from enum import Enum
from pathlib import Path
import os
import re

import csv


class ParseState(Enum):
    Init = 0,
    Header = 1,
    HeaderFinish = 2,
    CrashStack = 3,
    CrashStackFinish = 4,
    BinaryImage = 5,


class CrashParser:
    def __init__(self, is_rough) -> None:
        self._is_rough = is_rough

    @staticmethod
    def _parse_header(headers: dict, text: str):
        '''提取键值对'''
        if text == '':
            return
        arr = text.split(':')
        headers[arr[0]] = arr[1].strip()

    @staticmethod
    def stack_fingerprint(stacks: list, is_rough) -> str:
        '''从stack计算一个指纹'''

        stack_list = []
        if not is_rough:
            for stack in stacks:
                match = re.match(
                    '[0-9]+ +([^ ]+) +0x[0-9a-f]+ 0x[0-9a-f]+ \\+ ([0-9]+)', stack)
                if match:
                    stack_list.append('%s:%s' %
                                      (match.groups()[0], match.groups()[1]))
        else:
            for stack in stacks:
                match = re.match('[0-9]+ +([^ ]+)', stack)
                if match:
                    stack_list.append(match.groups()[0])
        return '\n'.join(stack_list)

    @staticmethod
    def parse_stack_frameworks(stacks: list) -> dict:
        '''解析stack中的framework'''
        frameworks = {}
        for stack in stacks:
            match = re.match('[0-9]+ +([^ ]+) +0x.+', stack)
            if match:
                framework_name = match.groups()[0]
                frameworks[framework_name] = True

        return frameworks

    def parse_crash(self, text: str) -> dict:
        '''从文本解析crash信息，保存结果为字典'''
        lines = text.split('\n')
        stacks = []
        crash = {}
        state = ParseState.Header
        stack_frameworks = {}

        for line in lines:
            if state == ParseState.Header:
                if line.startswith('Crashed Thread:'):
                    CrashParser._parse_header(crash, line)
                    state = ParseState.HeaderFinish
                else:
                    CrashParser._parse_header(crash, line)

            elif state == ParseState.HeaderFinish:
                if line.endswith('Crashed:'):
                    state = ParseState.CrashStack

            elif state == ParseState.CrashStack:
                if line == "":
                    state = ParseState.CrashStackFinish
                    break
                else:
                    stacks.append(line)

            elif state == ParseState.CrashStackFinish:
                if line.startswith('Binary Images:'):
                    state = ParseState.BinaryImage
                    stack_frameworks = CrashParser.parse_stack_frameworks(
                        stacks)

            elif state == ParseState.BinaryImage:
                # 0x102b14000 -        0x102b1ffff  libobjc-trampolines.dylib arm64e  <c4eb3fea90983e00a8b00b468bd6701d> /usr/lib/libobjc-trampolines.dylib
                match = re.match(
                    '.*(0x[0-9a-f]+) - +(0x[0-9a-f]+) +([^ ]+) +([^ ]+) +<([^>]+)>', line)
                if match:
                    framework_name = match.groups()[2]
                    if framework_name in stack_frameworks:
                        stack_frameworks[framework_name] = {
                            'uuid': match.groups()[4],
                            'offset': match.groups()[0]
                        }

        crash['stacks'] = stacks
        crash['is_arm64e'] = text.find('CoreFoundation arm64e') >= 0
        crash['stack_key'] = CrashParser.stack_fingerprint(
            stacks, self._is_rough)
        return crash


def read_crash(filename: str, is_rough) -> dict:
    '''从文件中提取crash'''
    with open(filename, 'r', encoding='utf8') as file:
        text = file.read()
        parser = CrashParser(is_rough)
        crash = parser.parse_crash(text)
        return crash


def read_crash_list(crash_dir: str, is_rough) -> list:
    '''从目录中提取crash的列表'''
    crashes = []
    for root, _, filenames in os.walk(crash_dir):
        for filename in filenames:
            crash = read_crash(Path(root)/filename, is_rough)
            crash['filename'] = filename
            crashes.append(crash)
    return crashes


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
