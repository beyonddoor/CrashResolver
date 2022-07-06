'''提供一些命令行功能'''

import argparse
import sys
from time import time
from itertools import groupby
import pprint
import os

from CrashResolver import database_csv
from . import crash_parser
from .. import setup
from .. import util
from . import log_parser


def update_reason_log(crash: dict, reasons: list):
    '''从log的特征归类，赋值reason_log'''
    if crash['thread_logs'] == '':
        crash['reason_log'] = 'empty'
        return

    for reason in reasons:
        if reason in crash['thread_logs']:
            crash['reason_log'] = reason
            return
    crash['reason_log'] = 'unknown'


def _update_reason_log_all(args):
    crash_list = database_csv.load(args.db_file)
    reasons = util.read_lines(args.reason_file)

    for crash in crash_list:
        update_reason_log(crash, reasons)

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


def _create_db(args):
    '''创建db'''
    crash_list = crash_parser.TumbstoneParser().read_crash_list(args.crash_dir)

    for crash in crash_list:
        if _is_bad(crash):
            print(f' bad {str(crash)}')

    crash_list = [crash for crash in crash_list if not _is_bad(crash)]
    headers = ['Tombstone maker', 'Crash type', 'Start time', 'Crash time', 'App ID', 'App version', 'Rooted', 'API level', 'OS version', 'Kernel version',
               'ABI list', 'Manufacturer', 'Brand', 'Model', 'Build fingerprint', 'ABI', 'stacks', 'thread_logs', 'reason', 'stack_key', 'filename']
    database_csv.save(args.db_file, crash_list, headers)


def _remove_bad(args):
    crash_list = database_csv.load(args.db_file)
    for crash in crash_list:
        if _is_bad(crash):
            print(f' bad {str(crash)}')

    crash_list = [crash for crash in crash_list if not _is_bad(crash)]
    database_csv.save(args.db_file, crash_list)


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


def group_count(item_list, key):
    '''根据key进行分类'''
    item_list.sort(key=key, reverse=True)
    group_obj = groupby(item_list, key)
    groups = [(key, len(list(lists)))
              for (key, lists) in group_obj]
    groups.sort(key=lambda x: x[1], reverse=True)

    total = len(item_list)
    print(f'total: #{len(item_list)}')
    print(f'total groups: #{len(groups)}')
    print('\n')

    for lists in groups:
        print(f'{lists[1]}/{lists[1]/total:0.2}\t{lists[0]}')

def group_detail(dict_list:list[dict], key):
    '''根据key进行分类'''
    dict_list.sort(key=key, reverse=True)
    group_obj = groupby(dict_list, key)
    groups = [(key, len(list(lists))) for (key, lists) in group_obj]
    groups.sort(key=lambda x: x[1], reverse=True)

    print(f'total: #{len(dict_list)}')
    print(f'total groups: #{len(groups)}')
    print('\n')

    total = len(dict_list)
    for lists in groups:
        print(f"========== {lists[1]}/{lists[1]/total:0.2} ==========")
        print(lists[0])
        print('\n')


def _do_test(args):
    # _do_list_unkown_reason(args)
    # _query_reason_log_stat(args)
    # _do_list_unkown_reason_logs(args)
    pass


def read_crashes(log_file, to_parse: bool):
    parser = log_parser.CrashLogParser()
    result = []
    with open(log_file, 'r', encoding='utf8', errors='ignore') as file:
        logs = log_parser.parse_tumbstone_from_log(file.read())
        for log in logs:
            if to_parse:
                result.append(parser.parse_crash(log))
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


def _group_by(args):
    crash_list = database_csv.load(args.db_file)
    if args.count_only:
        group_count(crash_list, lambda x: x.get(args.column_name, 'unkown'))
    else:
        group_detail(crash_list, lambda x: x.get(args.column_name, 'unkown'))


def _show_columns(args):
    crash_list = database_csv.load(args.db_file)
    pprint.pprint(crash_list[0].keys())
    pprint.pprint(crash_list[0].values())

def _do_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--setting_file', help='a ini setting file', default='setting.ini')

    sub_parsers = parser.add_subparsers()

    sub_parser = sub_parsers.add_parser(
        'save_csv_android', help='save android crashes to csv files')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_create_db)

    sub_parser = sub_parsers.add_parser(
        'update_reason_android', help='update android cause reason')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('reason_file', help='reason file')
    sub_parser.set_defaults(func=_update_reason_log_all)

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

    sub_parser = sub_parsers.add_parser('group_by')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('column_name', help='column name')
    sub_parser.add_argument('--count_only', help='count only', action='store_false')
    sub_parser.set_defaults(func=_group_by)

    sub_parser = sub_parsers.add_parser('columns', help='show columns')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_show_columns)

    sub_parser = sub_parsers.add_parser('test', help='test only')
    sub_parser.add_argument('arg1', help='arg1')
    sub_parser.add_argument('--arg2', help='arg2')
    sub_parser.set_defaults(func=_do_test)

    args = parser.parse_args()
    setup.setup(args.setting_file)
    args.func(args)


if __name__ == '__main__':
    old_time = time()
    _do_parse_args()
    print(f'{time() - old_time} seconds', file=sys.stderr)
