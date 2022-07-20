'''提供一些命令行功能'''

import argparse
import sys
from time import time
from itertools import groupby
import operator

from CrashResolver import database_csv
from . import crash_parser
from .. import setup
from . import symbolicator
from .. import reporter
from .. import util

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


def _do_update_os_names(args):
    crash_list = database_csv.load(args.db_file)
    os_names = set(util.read_lines(args.os_file))

    for crash in crash_list:
        crash['os_symbol_ready'] = util.is_os_available(
            crash, os_names)

    database_csv.save(args.db_file, crash_list)


def _do_update_symbol(args):
    # TODO 将符号化集成进来
    pass


def _do_save_csv(args):
    '''save csv'''
    crash_list = crash_parser.IosCrashParser(
        False).read_crash_list(args.crash_dir)
    database_csv.save(args.out_file, crash_list)


def _do_group_by_stack_key(args):
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


def _do_test(args):
    pass
    # _do_list_unkown_reason(args)
    # _do_stat_reasons(args)
    # _do_list_unkown_reason_logs(args)


def _do_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--setting_file', help='a ini setting file', default='setting.ini')

    sub_parsers = parser.add_subparsers()

    # ios相关的命令
    sub_parser = sub_parsers.add_parser(
        'save_csv_ios', help='save ios crashes to csv files')
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
