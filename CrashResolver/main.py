'''提供一些命令行功能'''

import argparse
import sys
from time import time
from itertools import groupby
import operator

from CrashResolver import database_csv
from . import crash_parser
from . import setup
from . import symbolicator
from . import reporter
from . import crashdb_util
from . import util

# def _do_save_csv_ios(args):
#     reasons = []
#     with open(args.reason_file, 'r', encoding='utf8') as file:
#         reasons = [line.strip()
#                    for line in file.read().split('\n') if line.strip() != '']

#     parser = crash_parser.IosCrashParser(False)
#     report = reporter.CrashReport(symbolicator.Symbolicator(
#         symbolicator.symbolicate,
#         lambda crash: symbolicator.parse_reason(crash, reasons),
#         parser),
#         parser
#     )

#     classified_crashes = report.get_symbolicated_crashes(args.crash_dir)
#     crash_list = []
#     for v in classified_crashes:
#         crash_list.extend(v[1])
#     crash_parser.save_crashes_to_csv_file(crash_list, args.out_file)


def update_reason_android(crash: dict, reasons: list):
    if crash['thread_logs'] == '':
        crash['reason_log'] = 'empty'
        return

    for reason in reasons:
        if reason in crash['thread_logs']:
            crash['reason_log'] = reason
            return
    crash['reason_log'] = 'unknown'


def _do_update_reasons_android(args):
    crash_list = database_csv.load(args.db_file)
    reasons = util.read_lines(args.reason_file)

    for crash in crash_list:
        if len(crash) < 10:
            continue
        update_reason_android(crash, reasons)

    database_csv.save(args.db_file, crash_list)


def _do_save_csv_android(args):
    '''save csv'''
    crash_list = crash_parser.AndroidCrashParser().read_crash_list(args.crash_dir)
    database_csv.save(args.out_file, crash_list)


def _do_update_os_names_ios(args):
    crash_list = database_csv.load(args.db_file)
    os_names = set(util.read_lines(args.os_file))

    for crash in crash_list:
        crash['os_symbol_ready'] = crashdb_util.is_os_available(
            crash, os_names)

    database_csv.save(args.db_file, crash_list)


def _do_update_symbol_ios(args):
    # TODO 将符号化集成进来
    pass


def _do_save_csv_ios(args):
    '''save csv'''
    crash_list = crash_parser.IosCrashParser(
        False).read_crash_list(args.crash_dir)
    database_csv.save(args.out_file, crash_list)


def _do_group_by_stack_key_ios(args):
    crash_list = database_csv.load(args.db_file)
    crash_list.sort(key=lambda x: x['stack_key'], reverse=True)
    group_obj = groupby(crash_list, lambda x: x['stack_key'])
    groups = [[crash for crash in lists] for (key, lists) in group_obj]
    groups.sort(key=len, reverse=True)

    for lists in groups:
        print(f'==========={len(lists)}\n')
        for crash in lists:
            print(str(crash))


def _do_stat_os(args):
    '''统计os'''
    crash_list = database_csv.load(args.db_file)

    crash_dict = {}
    for crash in crash_list:
        arm64e = '(arm64e)' if crash['is_arm64e'] else ''
        os_version = crash['Code Type'] + arm64e + ":" + crash['OS Version']
        if os_version not in crash_dict:
            crash_dict[os_version] = 0
        crash_dict[os_version] += 1

    sort_list = list(crash_dict.items())
    sort_list.sort(key=lambda x: x[1], reverse=True)
    for os_version, count in sort_list:
        print(f'{count}\t{os_version}')


def _do_report(args):
    crash_dir = args.crash_dir
    output_file = args.output_file
    reasons = []
    with open(args.reason_file, 'r', encoding='utf8') as file:
        reasons = [line.strip()
                   for line in file.read().split('\n') if line.strip() != '']

    parser = crash_parser.IosCrashParser(False)

    report = reporter.CrashReport(symbolicator.Symbolicator(
        symbolicator.symbolicate,
        lambda crash: symbolicator.parse_reason(crash, reasons),
        parser),
        parser)
    report.generate_report(crash_dir, output_file)


def _do_list_broken(args):
    crash_list = database_csv.load(args.arg1)
    for crash in crash_list:
        if len(crash) < 10:
            print(str(crash))


def _do_list_unkown_reason(args):
    crash_list = database_csv.load(args.arg1)

    list_filtered = [crash for crash in crash_list if len(
        crash) >= 10 and crash['reason_log'] == 'unknown']
    list_filtered.sort(key=lambda x: x['stack_key'], reverse=True)
    group_obj = groupby(list_filtered, lambda x: x['stack_key'])
    groups = [[crash for crash in lists]
              for (key, lists) in group_obj]  # operator.attrgetter('stack_key')
    groups.sort(key=len, reverse=True)

    for lists in groups:
        print(f'==========={len(lists)}\n')
        for crash in lists:
            print(str(crash))


def _do_list_unkown_reason_logs(args):
    crash_list = database_csv.load(args.arg1)

    list_filtered = [crash for crash in crash_list if len(
        crash) >= 10 and crash['reason_log'] == 'unknown']
    list_filtered.sort(key=lambda x: x['stack_key'], reverse=True)
    group_obj = groupby(list_filtered, lambda x: x['stack_key'])
    groups = [[crash for crash in lists] for (key, lists) in group_obj]
    groups.sort(key=len, reverse=True)

    for lists in groups:
        print(f'==========={len(lists)}\n')
        for crash in lists:
            print(f'{crash["filename"]}\n')
            print(f'{crash["thread_logs"]}\n')


def _do_stat_reasons(args):
    crash_list = database_csv.load(args.arg1)

    list_filtered = [crash for crash in crash_list if len(crash) >= 10]
    list_filtered.sort(key=lambda x: x['reason_log'], reverse=True)
    group_obj = groupby(list_filtered, lambda x: x['reason_log'])
    groups = [(key, len(list(lists)))
              for (key, lists) in group_obj]  # operator.attrgetter('stack_key')
    groups.sort(key=lambda x: x[1], reverse=True)

    print(len(crash_list))
    for lists in groups:
        print(f'{lists[1]}\t{lists[0]}')


def _do_test(args):
    # _do_list_unkown_reason(args)
    _do_stat_reasons(args)
    # _do_list_unkown_reason_logs(args)


def _do_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--setting_file', help='a ini setting file', default='setting.ini')

    sub_parsers = parser.add_subparsers()

    # android相关命令
    sub_parser = sub_parsers.add_parser(
        'save_csv_android', help='save android crashes to csv files')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('out_file', help='output file')
    sub_parser.set_defaults(func=_do_save_csv_android)

    sub_parser = sub_parsers.add_parser(
        'update_reason_android', help='update android cause reason')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.add_argument('reason_file', help='reason file')
    sub_parser.set_defaults(func=_do_update_reasons_android)

    # ios相关的命令
    sub_parser = sub_parsers.add_parser(
        'save_csv_ios', help='save ios crashes to csv files')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('out_file', help='output file')
    sub_parser.set_defaults(func=_do_save_csv_ios)

    sub_parser = sub_parsers.add_parser(
        'classify', help='classify crashes by stack fingerprint')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_do_group_by_stack_key_ios)

    sub_parser = sub_parsers.add_parser(
        'stat_os', help='statistics crashed iOS platforms')
    sub_parser.add_argument('db_file', help='csv database file')
    sub_parser.set_defaults(func=_do_stat_os)

    sub_parser = sub_parsers.add_parser('report', help='generate a report')
    sub_parser.add_argument('crash_dir', help='clash report dir')
    sub_parser.add_argument('reason_file', help='reason file')
    sub_parser.add_argument('output_file', help='output report file')
    sub_parser.set_defaults(func=_do_report)

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
