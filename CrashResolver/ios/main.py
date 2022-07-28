'''提供一些命令行功能'''

import argparse
import re
import sys
from time import time
from itertools import groupby
from pathlib import Path
import subprocess
import logging
from concurrent import futures

from CrashResolver import database_csv
from . import crash_parser
from .. import setup
from .. import util
from ..util import group_count, group_detail
from ..config import get_config

logger = logging.getLogger(__name__)


class SymbolicateError(Exception):
    '''符号化失败'''


def get_os_version(crash):
    '''codetype和版本组成的更有区分性的信息'''
    arm64e = '(arm64e)' if crash['is_arm64e'] else ''
    os_version = crash['Code Type'] + arm64e + ":" + crash['OS Version']
    return os_version

    # try:
    #     final_crash = do_symbolicate(first_crash['filename'])
    # except SymbolicateError as err:
    #     logger.exception('symbolicate %s failed: %s',
    #                      first_crash['filename'], err, stack_info=False)
    # for crash in group[1]:
    #     crash['symbol_stacks'] = final_crash['stacks'] if final_crash else ''


def symbolicate(fullpath, is_strict)->dict:
    '''符号化，返回符号化之后的dict'''
    sym_path = fullpath.with_suffix(get_config().SymbolExt)
    if not sym_path.exists():
        logger.info('symbolicate %s', fullpath)
        args = get_config().IosSymbolicateArgs.split(',')
        args.append(fullpath)
        subprocess.run(args, check=False)
        if not sym_path.exists():
            raise SymbolicateError(f'symbolicate failed {fullpath}')
    return crash_parser.IosCrashParser(is_strict).read_crash(sym_path)


def symbolicate_groups(crash_groups, symbolicate_func):
    '''符号化分组的crash'''

    def symbolicate_group(group):
        first_crash = group[1][0]
        symbol_str = None
        try:
            symbol_str = symbolicate_func(first_crash)
        except SymbolicateError as err:
            logger.exception('symbolicate %s failed: %s',
                             first_crash['filename'], err, stack_info=False)
        for crash in group[1]:
            crash['symbol_stacks'] = symbol_str

    executor = futures.ThreadPoolExecutor(max_workers=5)
    results = executor.map(symbolicate_group, crash_groups)
    for result in results:
        pass


def _do_symbolicate(args):
    '''符号化，保存结果到db'''
    dict_list = database_csv.load(args.db_file)

    def key(crash):
        return crash['stack_key']

    dict_list.sort(key=key, reverse=True)
    group_obj = groupby(dict_list, key)
    groups = [(key, list(lists)) for (key, lists) in group_obj]
    groups.sort(key=lambda x: len(x[1]), reverse=True)
    symbolicate_groups(groups, lambda crash: symbolicate(
        Path(crash['filename'])/args.crash_dir, args.strict))
    database_csv.save(args.db_file, dict_list)


def _do_update_os_names(args):
    crash_list = database_csv.load(args.db_file)
    os_names = set(util.read_lines(args.os_file))

    for crash in crash_list:
        crash['os_symbol_ready'] = util.is_os_available(
            crash, os_names)

    database_csv.save(args.db_file, crash_list)


def _update_meta(args):
    crash_list = database_csv.load(args.db_file)
    util.update_meta(crash_list, args.meta_dir)
    database_csv.save(args.db_file, crash_list)


def _do_update_reason(args):
    '''标记crash原因'''
    crash_list = database_csv.load(args.db_file)
    tag_list = util.read_tag_file(args.reason_file)
    util.update_tag(crash_list, tag_list, lambda crash: crash['symbol_stacks'])
    database_csv.save(args.db_file, crash_list)


def _do_save_csv(args):
    '''save csv'''
    crash_list = crash_parser.IosCrashParser(
        args.strict).read_crash_list(args.crash_dir)
    database_csv.save(args.out_file, crash_list)


def _do_groupby_key(args):
    '''根据key分类'''
    crash_list = database_csv.load(args.db_file)
    group_detail(
        crash_list, lambda crash: crash[args.key_name], args.key_name,  args.limit)


def _do_list_fields(args):
    '''显示字段'''
    crash_list = database_csv.load(args.db_file)
    print(crash_list[0].keys())


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
    sub_parser.add_argument(
        '--strict', help='is stack strict match', action='store_false')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('out_file', help='output file')
    sub_parser.set_defaults(func=_do_save_csv)

    sub_parser = sub_parsers.add_parser(
        'groupby', help='group crashes by key')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('--key_name', help='keyname', default='stack_key')
    sub_parser.add_argument('--limit', help='limit', default=100, type=int)
    sub_parser.set_defaults(func=_do_groupby_key)

    sub_parser = sub_parsers.add_parser(
        'stat_os', help='statistics crashed iOS platforms')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_do_stat_os)

    sub_parser = sub_parsers.add_parser(
        'update_os', help='update "os_symbol_ready" field')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('os_file', help='os file')
    sub_parser.set_defaults(func=_do_update_os_names)

    sub_parser = sub_parsers.add_parser(
        'symbolicate', help='symbolicate all crashes in csv')
    sub_parser.add_argument(
        '--strict', help='is stack strict match', action='store_false')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('crash_dir', help='clash report dir')
    sub_parser.set_defaults(func=_do_symbolicate)

    sub_parser = sub_parsers.add_parser('reason', help='update crash reason')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('reason_file', help='reason file')
    sub_parser.set_defaults(func=_do_update_reason)

    sub_parser = sub_parsers.add_parser('fields', help='list fields')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_do_list_fields)

    sub_parser = sub_parsers.add_parser('update_meta', help='update meta')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('meta_dir', help='meta dir')
    sub_parser.set_defaults(func=_update_meta)

    args = parser.parse_args()
    setup.setup(args.setting_file)
    args.func(args)


if __name__ == '__main__':
    old_time = time()
    _do_parse_args()
    print(f'{time() - old_time} seconds', file=sys.stderr)
