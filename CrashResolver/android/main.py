'''提供一些命令行功能'''

import argparse
from subprocess import PIPE, STDOUT
import json
from pathlib import Path
import sys
from time import time
from itertools import groupby
import pprint
import os
import logging
import subprocess
from concurrent import futures


from ..config import get_config
from CrashResolver import database_csv
from . import crash_parser
from .. import setup
from .. import util
from . import log_parser
from ..util import group_count, group_detail

logger = logging.getLogger(__name__)


class SymbolicateError(Exception):
    '''符号化失败'''


def _tag_thread_logs(args):
    '''给thread log分类'''
    crash_list = database_csv.load(args.db_file)
    tag_list = util.read_tag_file(args.reason_file)
    util.update_tag(crash_list, tag_list,
                    lambda crash: crash['thread_logs'], 'log')
    database_csv.save(args.db_file, crash_list)


def _tag_symbol_stacks(args):
    '''给symbol_stacks分类'''
    crash_list = database_csv.load(args.db_file)
    tag_list = util.read_tag_file(args.reason_file)
    util.update_tag(crash_list, tag_list,
                    lambda crash: crash['symbol_stacks'])
    database_csv.save(args.db_file, crash_list)


def _query_app_version(args):
    '''查询appid和版本的统计'''
    crash_list = database_csv.load(args.db_file)

    def key_func(
        x): return f'{x.get("App ID", "unknown")}-{x.get("App version", "unknown")}'
    crash_list.sort(key=key_func)
    result_list = [(len(list(lists)), key)
                   for (key, lists) in groupby(crash_list, key_func)]
    result_list.sort(key=lambda x: x[0], reverse=True)
    pprint.pprint(result_list)


def _parse(args):
    out = crash_parser.TumbstoneParser().read_crash(args.crash_file)
    pprint.pprint(out)


def _create_db(args):
    '''创建db'''
    crash_list = crash_parser.TumbstoneParser().read_crash_list(args.crash_dir)

    for crash in crash_list:
        if _is_bad(crash):
            logger.error('bad crash %s', str(crash))

    crash_list = [crash for crash in crash_list if not _is_bad(crash)]
    # headers = ['Tombstone maker', 'Crash type', 'Start time', 'Crash time', 'App ID', 'App version', 'Rooted', 'API level', 'OS version', 'Kernel version',
    #            'ABI list', 'Manufacturer', 'Brand', 'Model', 'Build fingerprint', 'ABI', 'stacks', 'thread_logs', 'reason', 'stack_key', 'filename']
    database_csv.save(args.db_file, crash_list)


def _remove_bad(args):
    crash_list = database_csv.load(args.db_file)
    for crash in crash_list:
        if _is_bad(crash):
            logger.error('bad crash %s', str(crash))

    crash_list = [crash for crash in crash_list if not _is_bad(crash)]
    database_csv.save(args.db_file, crash_list)


def _update_meta(args):
    crash_list = database_csv.load(args.db_file)
    util.update_meta(crash_list, args.meta_dir)
    database_csv.save(args.db_file, crash_list)


def symbolicate(abi_name, filename) -> dict:
    '''符号化，返回符号化之后的dict'''
    fullpath = Path(filename)
    logger.info('symbolicate %s', fullpath)
    args = get_config().AndroidSymbolicateArgs.split(',')
    args.extend([abi_name,fullpath])
    sp = subprocess.Popen(args, shell=False, stderr=STDOUT, close_fds=True, stdin=PIPE, stdout=PIPE)
    return sp.stdout.read().decode('utf8')

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
    dict_list = database_csv.load(args.db_file)

    def key(crash):
        return crash['stack_key']

    dict_list.sort(key=key, reverse=True)
    group_obj = groupby(dict_list, key)
    groups = [(key, list(lists)) for (key, lists) in group_obj]
    groups.sort(key=lambda x: len(x[1]), reverse=True)
    symbolicate_groups(groups, lambda crash: symbolicate(crash['abi_name'], Path(args.crash_dir) / crash['filename']))
    database_csv.save(args.db_file, dict_list)


def _is_bad(crash):
    return len(crash) < 10


# def _query_unkown_reason_logs(args):
#     '''reason log为未知的情况'''
#     crash_list = database_csv.load(args.arg1)

#     list_filtered = [crash for crash in crash_list if crash['reason_log'] == 'unknown']
#     list_filtered.sort(key=lambda x: x['stack_key'], reverse=True)
#     group_obj = groupby(list_filtered, lambda x: x['stack_key'])
#     groups = [[crash for crash in lists] for (key, lists) in group_obj]
#     groups.sort(key=len, reverse=True)

#     for lists in groups:
#         print(f'==========={len(lists)}\n')
#         for crash in lists:
#             print(f'{crash["filename"]}\n')
#             print(f'{crash["thread_logs"]}\n')

def read_crashes(log_file, to_parse: bool):
    '''从log文件中读取crash'''
    parser = log_parser.CrashLogParser()
    result = []
    with open(log_file, 'r', encoding='utf8', errors='ignore') as file:
        logs = log_parser.parse_tumbstone_from_log(file.read())
        for log in logs:
            if to_parse:
                result.append(parser.parse_crash(log, log_file))
            else:
                result.append(log)
    return result


def _create_logdb(args):
    crash_list = []

    if args.to_parse:
        for root, dirnames, filenames in os.walk(args.log_dir):
            # print(list(dirnames), list(filenames))
            for filename in filenames:
                final_name = os.path.join(root, filename)
                crash_sub_list = read_crashes(final_name, False)
                crash_list.extend(crash_sub_list)

        return

    headers = ['Build fingerprint', 'ABI',
               'stack_key', 'stacks', 'filename', 'fulltext']
    for root, dirnames, filenames in os.walk(args.log_dir):
        # print(list(dirnames), list(filenames))
        for filename in filenames:
            final_name = os.path.join(root, filename)
            crash_sub_list = read_crashes(final_name, True)
            for crash in crash_sub_list:
                crash['filename'] = os.path.basename(root)
            crash_list.extend(crash_sub_list)

    database_csv.save(args.db_file, crash_list, headers)


def _groupby(args):
    crash_list = database_csv.load(args.db_file)
    if args.count_only:
        group_count(crash_list, lambda x: x.get(
            args.key_name, 'unkown'), args.key_name)
    else:
        group_detail(crash_list, lambda x: x.get(
            args.key_name, 'unkown'), args.key_name, args.limit)


def _show_columns(args):
    crash_list = database_csv.load(args.db_file)
    pprint.pprint(crash_list[0].keys())
    pprint.pprint(crash_list[0].values())


def _test(args):
    pass


def _do_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--setting_file', help='a ini setting file', default='setting.ini')

    sub_parsers = parser.add_subparsers()

    sub_parser = sub_parsers.add_parser(
        'parse', help='parse a single crash file')
    sub_parser.add_argument('crash_file', help='clash file')
    sub_parser.set_defaults(func=_parse)

    sub_parser = sub_parsers.add_parser(
        'save_csv', help='save android crashes to csv files')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_create_db)

    sub_parser = sub_parsers.add_parser(
        'reason_log', help='update cause reason by thread logs')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('reason_file', help='reason file')
    sub_parser.set_defaults(func=_tag_thread_logs)

    sub_parser = sub_parsers.add_parser(
        'reason', help='update cause reason by symbol stacks')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('reason_file', help='reason file')
    sub_parser.set_defaults(func=_tag_symbol_stacks)

    sub_parser = sub_parsers.add_parser(
        'remove_bad', help='remove bad records')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_remove_bad)

    sub_parser = sub_parsers.add_parser(
        'query_app_version', help='update android cause reason')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_query_app_version)

    sub_parser = sub_parsers.add_parser(
        'create_logdb')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('log_dir', help='csv database file')
    sub_parser.add_argument(
        '--to_parse', help='will parse or not', dest='to_parse', action='store_false')
    sub_parser.set_defaults(func=_create_logdb)

    sub_parser = sub_parsers.add_parser('groupby')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('--key_name', help='key name', default='stack_key')
    sub_parser.add_argument('--limit', help='limit', default=100, type=int)
    sub_parser.add_argument(
        '--count_only', help='count only', action='store_true')
    sub_parser.set_defaults(func=_groupby)

    sub_parser = sub_parsers.add_parser('columns', help='show columns')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_show_columns)

    sub_parser = sub_parsers.add_parser('test', help='test')
    sub_parser.set_defaults(func=_test)

    sub_parser = sub_parsers.add_parser('update_meta', help='update meta')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('meta_dir', help='meta dir')
    sub_parser.set_defaults(func=_update_meta)

    sub_parser = sub_parsers.add_parser(
        'symbolicate', help='symbolicate all crashes in csv')
    sub_parser.add_argument(
        '--strict', help='is stack strict match', action='store_false')
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
