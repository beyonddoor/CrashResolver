'''提供一些命令行功能'''

import argparse
import sys
from time import time
from itertools import groupby
import pprint

from CrashResolver import database_csv
from . import crash_parser
from .. import setup
from .. import util


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
    crash_list = crash_parser.AndroidCrashParser().read_crash_list(args.crash_dir)

    for crash in crash_list:
        if _is_bad(crash):
            print(f' bad {str(crash)}')

    crash_list = [crash for crash in crash_list if not _is_bad(crash)]
    database_csv.save(args.db_file, crash_list)


def _remove_bad(args):
    crash_list = database_csv.load(args.db_file)
    for crash in crash_list:
        if _is_bad(crash):
            print(f' bad {str(crash)}')

    crash_list = [crash for crash in crash_list if not _is_bad(crash)]
    database_csv.save(args.db_file, crash_list)


def _is_bad(crash):
    return len(crash) < 10


def _query_unkown_reason_log(args):
    '''查询reason log为unknown的情况，根据stack key归类'''
    crash_list = database_csv.load(args.arg1)

    list_filtered = [
        crash for crash in crash_list if crash['reason_log'] == 'unknown']
    list_filtered.sort(key=lambda x: x['stack_key'], reverse=True)
    group_obj = groupby(list_filtered, lambda x: x['stack_key'])
    groups = [[crash for crash in lists]
              for (key, lists) in group_obj]  # operator.attrgetter('stack_key')
    groups.sort(key=len, reverse=True)

    for lists in groups:
        print(f'==========={len(lists)}\n')
        for crash in lists:
            print(str(crash))


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


def _query_reason_log_stat(args):
    '''reason log的统计'''
    crash_list = database_csv.load(args.arg1)
    crash_list.sort(key=lambda x: x['reason_log'], reverse=True)
    group_obj = groupby(crash_list, lambda x: x['reason_log'])
    groups = [(key, len(list(lists)))
              for (key, lists) in group_obj]
    groups.sort(key=lambda x: x[1], reverse=True)

    print(len(crash_list))
    for lists in groups:
        print(f'{lists[1]}\t{lists[0]}')


def _do_test(args):
    # _do_list_unkown_reason(args)
    _query_reason_log_stat(args)
    # _do_list_unkown_reason_logs(args)


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
        'query_reason_log_stat')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_query_reason_log_stat)

    sub_parser = sub_parsers.add_parser(
        'query_unkown_reason_log')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_query_unkown_reason_log)

    sub_parser = sub_parsers.add_parser('test', help='test only')
    sub_parser.add_argument('arg1', help='arg1')
    sub_parser.set_defaults(func=_do_test)

    args = parser.parse_args()
    setup.setup(args.setting_file)
    args.func(args)


if __name__ == '__main__':
    old_time = time()
    _do_parse_args()
    print(f'{time() - old_time} seconds', file=sys.stderr)
