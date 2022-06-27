import argparse
from . import crash_parser
from . import setup
from . import symbolicator
from . import reporter


def _do_classify(args):
    '''统计stack指纹'''
    crash_list = crash_parser.read_crash_list(args.crash_dir, args.is_rough)
    os_names = set()
    if args.os_file:
        os_names = crash_parser.read_os_names(args.os_file)

    for crash in crash_list:
        crash['os_symbol_ready'] = crash_parser.is_os_available(
            crash, os_names)

    crashes = crash_parser.classify_by_stack(crash_list)

    crashes_sort = list(crashes.items())
    crashes_sort.sort(key=lambda x: len(x[1]), reverse=True)
    crash_parser.save_crashes_to_file(crashes_sort, args.out_file)


def _do_stat_os(args):
    '''统计os'''
    crash_list = crash_parser.read_crash_list(args.crash_dir, False)
    crash_dict = {}
    for crash in crash_list:
        arm64e = '(arm64e)' if crash['is_arm64e'] else ''
        os_version = crash['Code Type'] + arm64e + ":" + crash['OS Version']
        if os_version not in crash_dict:
            crash_dict[os_version] = 0
        crash_dict[os_version] += 1

    sort_list = list(crash_dict.items())
    sort_list.sort(key=lambda x: x[1], reverse=True)
    with open(args.out_file, 'w', encoding='utf8') as file:
        for os_version, count in sort_list:
            file.write(f'{count}\t{os_version}\n')


def _do_save_crashes_to_csv(args):
    reasons = []
    with open(args.reason_file, 'r', encoding='utf8') as file:
        reasons = [line.strip()
                   for line in file.read().split('\n') if line.strip() != '']
    report = reporter.CrashReport(symbolicator.Symbolicator(
        symbolicator.symbolicate, lambda crash: symbolicator.parse_reason(crash, reasons)))
        
    classified_crashes = report.get_symbolicated_crashes(args.crash_dir)
    crash_list = []
    for v in classified_crashes:
        crash_list.extend(v[1])
    crash_parser.save_crashes_to_csv_file(crash_list, args.out_file)


def _do_report(args):
    crash_dir = args.crash_dir
    output_file = args.output_file
    reasons = []
    with open(args.reason_file, 'r', encoding='utf8') as file:
        reasons = [line.strip()
                   for line in file.read().split('\n') if line.strip() != '']
    report = reporter.CrashReport(symbolicator.Symbolicator(
        symbolicator.symbolicate, lambda crash: symbolicator.parse_reason(crash, reasons)))
    report.generate_report(crash_dir, output_file)


def _do_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--setting_file', help='a ini setting file', default='setting.ini')

    sub_parsers = parser.add_subparsers()

    sub_parser = sub_parsers.add_parser(
        'classify', help='classify crashes by stack fingerprint')
    sub_parser.add_argument(
        '--is_rough', help='is rough stack fingerprint', action='store_true', dest='is_rough')
    sub_parser.add_argument('--os_file', help='downloaded os names')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('out_file', help='output file')
    sub_parser.set_defaults(func=_do_classify)

    sub_parser = sub_parsers.add_parser(
        'stat_os', help='statistics crashed iOS platforms')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('out_file', help='output file')
    sub_parser.set_defaults(func=_do_stat_os)

    sub_parser = sub_parsers.add_parser(
        'save_csv', help='save crashes to csv files')
    sub_parser.add_argument('crash_dir', help='clashes dir')
    sub_parser.add_argument('reason_file', help='reason file')
    sub_parser.add_argument('out_file', help='output file')
    sub_parser.set_defaults(func=_do_save_crashes_to_csv)

    sub_parser = sub_parsers.add_parser('report', help='generate a report')
    sub_parser.add_argument('crash_dir', help='clash report dir')
    sub_parser.add_argument('reason_file', help='reason file')
    sub_parser.add_argument('output_file', help='output report file')
    sub_parser.set_defaults(func=_do_report)

    args = parser.parse_args()
    setup.setup(args.setting_file)
    args.func(args)


if __name__ == '__main__':
    _do_parse_args()
