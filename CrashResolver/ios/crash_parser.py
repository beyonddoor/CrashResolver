'''
解析ios和android的crash文件，结构化为一个dict
'''

from enum import Enum
import re

from ..base_parser import BaseCrashParser


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

    def parse_crash(self, text: str, filename) -> dict:
        '''从文本解析crash信息，保存结果为字典'''
        stacks = []
        crash = {}
        state = IosParseState.HEADER
        stack_frameworks = {}
        lines = text.splitlines()

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

        crash['stacks'] = '\n'.join(stacks)
        crash['is_arm64e'] = text.find('CoreFoundation arm64e') >= 0
        crash['stack_key'] = IosCrashParser.stack_fingerprint(
            stacks, self._is_rough)
        return crash


def _parse_header(headers: dict, text: str):
    '''提取键值对'''
    if text == '':
        return
    arr = text.split(':', maxsplit=1)
    headers[arr[0]] = arr[1].strip()
