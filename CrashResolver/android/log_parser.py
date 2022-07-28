'''从log中提取tumbstone文件，可能不完备'''

from asyncio.log import logger
import enum
import re

from ..base_parser import BaseCrashParser


PAT_TUMBSTONE = '*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***'
PAT_PREFIX = re.compile(r'^[^\(:]+ [^\( ]+ *([^\(]+\([0-9 ]+\):)')
# line='06-13 07:05:56.322 E/CRASH   ( 1990): *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***'
# line = '06-23 22:12:50.967 E/AndroidRuntime(31768): java.lang.Error: *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***'
# print(PAT_PREFIX.search(line).group(1))


class ParseState(enum.Enum):
    PARSE_NIL = 0
    PARSE_START = 1


def parse_tumbstone_from_log(text: str):
    '''从文本中提取tumbstone的内容'''
    lines = text.splitlines()
    parse_state = ParseState.PARSE_NIL
    reading_lines = []
    logs = []
    for index, line in enumerate(lines):
        if ParseState.PARSE_NIL == parse_state:
            if PAT_TUMBSTONE in line:
                parse_state = ParseState.PARSE_START
                reading_lines = []
                pattern = PAT_PREFIX.search(line).group(1)
                reading_lines.append(line.split('): ', maxsplit=1)[1])
        elif ParseState.PARSE_START == parse_state:
            if pattern in line:
                reading_lines.append(line.split('): ', maxsplit=1)[1])
            else:
                parse_state = ParseState.PARSE_NIL
                logs.append('\n'.join(reading_lines))
    return logs


class AndroidParseState(enum.Enum):
    '''解析状态'''
    INIT = 0
    HEADER = 1
    '''解析header'''
    WAIT_BACKTRACE = 2
    '''解析原因'''
    BACKTRACE = 3
    '''解析crash堆栈'''
    LOG = 4
    '''解析日志'''


class CrashLogParser(BaseCrashParser):
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
                parts[-1] = CrashLogParser._normalize_path(
                    parts[-1], 'com.longtugame.yjfb')
            else:
                # 非游戏的so符号地址不确定
                parts[2] = '(MAY_CHANGE_PER_OS)'
            lines.append(' '.join(parts))

        return '\n'.join(lines)

    def parse_crash(self, text: str, filename) -> dict:
        '''从文本解析crash信息，保存结果为字典'''
        stacks = []
        reason_lines = []
        crash = {}
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
                    match = re.match('pid: ([^,]+), tid: ([^,]+)', line)
                    if match:
                        crash['crash_pid'] = match.groups()[0]
                        crash['crash_tid'] = match.groups()[1]

                    state = AndroidParseState.WAIT_BACKTRACE

            elif state == AndroidParseState.WAIT_BACKTRACE:
                if line == 'backtrace:':
                    state = AndroidParseState.BACKTRACE

            elif state == AndroidParseState.BACKTRACE:
                if line == '':
                    state = AndroidParseState.LOG
                else:
                    stacks.append(line)

        crash['stacks'] = '\n'.join(stacks)
        crash['thread_logs'] = 'NO NEED'
        crash['full_text'] = text

        if len(stacks) == 0:
            crash['reason'] = 'NO_BACKTRACE'
            crash['stack_key'] = 'NO_BACKTRACE'
        else:
            crash['reason'] = '\n'.join(reason_lines)
            crash['stack_key'] = CrashLogParser.stack_fingerprint(stacks)
        return crash


def _parse_header(headers: dict, text: str):
    '''提取键值对'''
    if text == '':
        return
    arr = text.split(':', maxsplit=1)
    if len(arr) < 2:
        logger.error('unknown header %s', text)
        return
    headers[arr[0]] = arr[1].strip()
