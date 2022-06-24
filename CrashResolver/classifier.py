
from enum import Enum
from pathlib import Path
import sys
import os
import argparse
import re

from . import setup
from . import config

'''
对已经fetch的所有crash，进行汇总。
初步的汇总比较简单，将stack生成指纹（fingerprint），根据指纹汇总。
'''

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
    def _parse_header(dict:dict, text:str):
        '''提取键值对'''
        if text == '': return
        arr = text.split(':')
        dict[arr[0]] = arr[1].strip()

    @staticmethod
    def stack_fingerprint(stacks:list, is_rough)->str:
        '''从stack计算一个指纹'''

        list = []
        if not is_rough:
            for stack in stacks:
                match = re.match('[0-9]+ +([^ ]+) +0x[0-9a-f]+ 0x[0-9a-f]+ \\+ ([0-9]+)', stack)
                if match:
                    list.append('%s:%s' % (match.groups()[0], match.groups()[1]))
        else:
            for stack in stacks:
                match = re.match('[0-9]+ +([^ ]+)', stack)
                if match:
                    list.append(match.groups()[0])
        return '\n'.join(list)

    @staticmethod
    def parse_stack_frameworks(stacks:list)->dict:
        '''解析stack中的framework'''
        frameworks = {}
        for stack in stacks:
            match = re.match('[0-9]+ +([^ ]+) +0x.+', stack)
            if match:
                framework_name = match.groups()[0]
                frameworks[framework_name] = True

        return frameworks

    def parse_crash(self, text:str)->dict:
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
                    stack_frameworks = CrashParser.parse_stack_frameworks(stacks)

            elif state == ParseState.BinaryImage:
                # 0x102b14000 -        0x102b1ffff  libobjc-trampolines.dylib arm64e  <c4eb3fea90983e00a8b00b468bd6701d> /usr/lib/libobjc-trampolines.dylib
                match = re.match('.*(0x[0-9a-f]+) - +(0x[0-9a-f]+) +([^ ]+) +([^ ]+) +<([^>]+)>', line)
                if match:
                    framework_name = match.groups()[2]
                    if framework_name in stack_frameworks:
                        stack_frameworks[framework_name] = {
                            'uuid': match.groups()[4],
                            'offset': match.groups()[0]
                        }

        crash['stacks'] = stacks
        crash['is_arm64e'] = text.find('CoreFoundation arm64e') >= 0
        crash['stack_key'] = CrashParser.stack_fingerprint(stacks, self._is_rough)
        return crash

def read_crash(filename:str, is_rough)->dict:
    '''从文件中提取crash'''
    with open(filename, 'r') as file:
        text = file.read()
        parser = CrashParser(is_rough)
        crash = parser.parse_crash(text)
        return crash

def read_crash_list(crash_dir:str, is_rough)->list:
    '''从目录中提取crash的列表'''
    crashes = []
    for root,_,filenames in os.walk(crash_dir):
        for filename in filenames:
            crash = read_crash(Path(root)/filename, is_rough)
            crash['filename'] = filename
            crashes.append(crash)
    return crashes

def classify_by_stack(crash_list:list)->dict:
    crashes = {}
    for crash in crash_list:
        fingerprint = crash['stack_key']
        if fingerprint not in crashes:
            crashes[fingerprint] = []

        crashes[fingerprint].append(crash)

    return crashes

def stringify_crash(crash):
    return str(crash)

def dump(crash_list, filename:str):
    with open(filename, 'w') as file:
        for crashes_pair in crash_list:
            file.write(f'\n------ {crashes_pair[1]} in total ------\n')

            for crash in crashes_pair[1]:
                file.write(str(crash))
                file.write("\n")

def is_os_available(crash:dict, os_names:set)->bool:
    '''os的符号是否可用'''
    arm64e = 'arm64e' if crash['is_arm64e'] else 'arm64'
    return (crash['OS Version'] + ' ' + arm64e) in os_names

def read_os_names(filename)->set:
    '''读取已经下载就绪的os名字，比如 iPhone OS 13.6 (17G68) arm64e'''
    lines = []
    with open(filename, 'r') as file:
        lines = file.read().split('\n')
    return set(line for line in lines if line.strip() != '')

def _do_classify(args):
    '''统计stack指纹'''
    crash_list = read_crash_list(args.crash_dir, args.is_rough)
    os_names = set()
    if args.os_file:
        os_names = read_os_names(args.os_file)

    for crash in crash_list:
        crash['os_symbol_ready'] = is_os_available(crash, os_names)

    crashes = classify_by_stack(crash_list)

    crashes_sort =  list(crashes.items())
    crashes_sort.sort(key=lambda x: len(x[1]), reverse=True)
    dump(crashes_sort, args.out_file)

def _do_stat_os(args):
    '''统计os'''
    crash_list = read_crash_list(args.crash_dir, False)
    crash_dict = {}
    for crash in crash_list:
        arm64e = '(arm64e)' if crash['is_arm64e'] else ''
        os_version = crash['Code Type'] + arm64e + ":" + crash['OS Version']
        if os_version not in crash_dict:
            crash_dict[os_version] = 0
        crash_dict[os_version] += 1

    sort_list = list(crash_dict.items())
    sort_list.sort(key=lambda x: x[1], reverse=True)
    with open(args.out_file, 'w') as file:
        for os_version, count in sort_list:
            file.write(f'{count}\t{os_version}\n')

def _do_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--setting_file', help='a ini setting file', default='setting.ini')
    
    sub_parsers = parser.add_subparsers()

    sub_parser = sub_parsers.add_parser('classify', help='classify crashes by stack fingerprint')
    sub_parser.add_argument('--is_rough', help='is rough stack fingerprint', action='store_true', dest='is_rough')
    sub_parser.add_argument('--os_file', help='downloaded os names')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('out_file', help='output file')
    sub_parser.set_defaults(func=_do_classify)

    sub_parser = sub_parsers.add_parser('stat_os', help='statistics crashed iOS platforms')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('out_file', help='output file')
    sub_parser.set_defaults(func=_do_stat_os)

    args = parser.parse_args()
    setup.setup(args.setting_file)
    args.func(args)

if __name__ == '__main__':
    _do_parse_args()
