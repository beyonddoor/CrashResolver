'''提供一些命令行功能'''

import argparse
from asyncio.log import logger
import sys
from time import time
from itertools import groupby
import operator
from pathlib import Path
import subprocess

from CrashResolver import database_csv
from . import crash_parser
from .. import setup
from .. import util
from ..util import group_count, group_detail
from ..config import get_config

def get_os_version(crash):
    '''codetype和版本组成的更有区分性的信息'''
    arm64e = '(arm64e)' if crash['is_arm64e'] else ''
    os_version = crash['Code Type'] + arm64e + ":" + crash['OS Version']
    return os_version
    
def symbolicate(filename, crash_dir)->dict:
    '''符号化，返回符号化之后的dict'''
    crash_fullpath = Path(crash_dir) / filename
    sym_path = crash_fullpath.with_suffix(get_config().SymbolExt)
    if not sym_path.exists():
        logger.info("processing %s", crash_fullpath)
        subprocess.run(['bash', get_config().SymbolicatePath, crash_fullpath], check=False)
    return crash_parser.IosCrashParser(False).read_crash(sym_path)

def symbolicate_groups(crash_groups, do_symbolicate):
    '''符号化分组的crash'''
    for group in crash_groups:
        first_crash = group[1][0]
        final_crash = do_symbolicate(first_crash['filename'])
        for crash in group[1]:
            crash['symbol_stacks'] = final_crash['stacks']

def _do_symbolicate(args):
    '''符号化，保存结果到db'''
    dict_list = database_csv.load(args.db_file)
    def key(crash):
        return crash['stack_key']
        
    dict_list.sort(key=key, reverse=True)
    group_obj = groupby(dict_list, key)
    groups = [(key, list(lists)) for (key, lists) in group_obj]
    groups.sort(key=lambda x: len(x[1]), reverse=True)
    symbolicate_groups(groups, lambda filename: symbolicate(filename, args.crash_dir))
    database_csv.save(args.db_file, dict_list)


def _do_update_os_names(args):
    crash_list = database_csv.load(args.db_file)
    os_names = set(util.read_lines(args.os_file))

    for crash in crash_list:
        crash['os_symbol_ready'] = util.is_os_available(
            crash, os_names)

    database_csv.save(args.db_file, crash_list)


def _do_save_csv(args):
    '''save csv'''
    crash_list = crash_parser.IosCrashParser(
        False).read_crash_list(args.crash_dir)
    database_csv.save(args.out_file, crash_list)


def _do_group_by_stack_key(args):
    crash_list = database_csv.load(args.db_file)
    group_detail(crash_list, lambda crash: crash['stack_key'], 'stack_key', 100)


def _do_stat_os(args):
    '''统计os'''
    crash_list = database_csv.load(args.db_file)
    group_detail(crash_list, get_os_version, 'os version', 10)

def _do_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--setting_file', help='a ini setting file', default='setting.ini')

    sub_parsers = parser.add_subparsers()

    # ios相关的命令
    sub_parser = sub_parsers.add_parser(
        'save_csv', help='save ios crashes to csv files')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('out_file', help='output file')
    sub_parser.set_defaults(func=_do_save_csv)

    sub_parser = sub_parsers.add_parser(
        'classify', help='classify crashes by stack fingerprint')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_do_group_by_stack_key)

    sub_parser = sub_parsers.add_parser(
        'stat_os', help='statistics crashed iOS platforms')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_do_stat_os)
    
    sub_parser = sub_parsers.add_parser(
        'update_os', help='update "os_symbol_ready" field')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('os_file', help='os file')
    sub_parser.set_defaults(func=_do_update_os_names)

    sub_parser = sub_parsers.add_parser('symbolicate', help='symbolicate all crashes in csv')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('crash_dir', help='clash report dir')
    sub_parser.set_defaults(func=_do_symbolicate)
    
    args = parser.parse_args()
    setup.setup(args.setting_file)
    args.func(args)


if __name__ == '__main__':
    old_time = time()
    _do_parse_args()
    print(f'{time() - old_time} seconds', file=sys.stderr)
