'''generate a report from crashes'''

import os
import argparse
from pathlib import Path

import logging
import subprocess

from . import config
from . import classifier
from . import setup

logger = logging.getLogger(__name__)


class CrashReport:
    '''
    统计所有的crash，自动输出报告
    '''

    def __init__(self, symbol_func, parse_reason_func) -> None:
        self._symbol_func = symbol_func
        self._parse_reason_func = parse_reason_func

    @staticmethod
    def find_symbolated_crashes(crash_dir: str) -> list:
        for _, _, filenames in os.walk(crash_dir):
            results = []
            for filename in filenames:
                if filename.endswith(config.SymbolExt):
                    results.append(filename[0:-len(config.SymbolExt)])
            return results

    def _save_reason_stats(self, file, reasons_stat):
        file.write('reasons:\n')
        for pair in reasons_stat.items():
            count = 0
            for list in pair[1]:
                count += len(list)

            file.write(f"{count}\t{pair[0]}\n")

    def _save_pairs(self, file, pairs, crash_dir_obj: Path, symbolicate_crashes):
        reasons_stat = {}

        for pair in pairs:
            # 没有符号化，则先符号化，再解析文件
            found_crash = None
            for crash in pair[1]:
                if crash['filename'][0:-len(config.CrashExt)] in symbolicate_crashes:
                    found_crash = crash
                    logger.info(
                        f'--- already symbolicated: {found_crash["filename"]}')
                    break

            if found_crash is None:
                found_crash = pair[1][0]
                logger.info(
                    f'--- try symbolicate file: {found_crash["filename"]}')
                self._symbol_func(crash_dir_obj / found_crash['filename'])

            result_filename = found_crash['filename'][0:-
                                                      len(config.CrashExt)] + config.SymbolExt
            final_crash = classifier.read_crash(
                crash_dir_obj / result_filename, False)

            reason = self._parse_reason_func(final_crash)
            if not reason:
                reason = 'unknown'

            if reason not in reasons_stat:
                reasons_stat[reason] = []

            reasons_stat[reason].append(pair[1])

            file.write(f'\n------ {len(pair[1])} in total ------ ({reason})\n')
            file.write('\n'.join(final_crash['stacks']))
            file.write('\n')

            for crash in pair[1]:
                file.write(classifier.stringify_crash(crash))
                file.write("\n")

        file.write("\n\n")
        self._save_reason_stats(file, reasons_stat)

    def generate_report(self, crash_dir: str, output_file: str) -> None:
        logger.info(f'start generate report: {output_file}')

        symbolicated_crashes = set(
            CrashReport.find_symbolated_crashes(crash_dir))

        crash_list = classifier.read_crash_list(crash_dir, False)
        key_crashes_map = classifier.classify_by_stack(crash_list)
        crash_dir_obj = Path(crash_dir)

        pairs_sorted = list(key_crashes_map.items())
        pairs_sorted.sort(key=lambda x: len(x[1]), reverse=True)

        with open(output_file, 'w', encoding='utf8') as file:
            self._save_pairs(file, pairs_sorted,
                             crash_dir_obj, symbolicated_crashes)

        logger.info(f'finish generate report: {output_file}')


def symbolicate(filename):
    '''进行符号化'''
    subprocess.run(['bash', config.SymbolicatePath, filename])


def parse_reason(crash, reasons):
    stacks = '\n'.join(crash['stacks'])
    for reason in reasons:
        if stacks.find(reason) >= 0:
            return reason
    return None


def _do_report(args):
    crash_dir = args.crash_dir
    output_file = args.output_file
    reasons = []
    with open(args.reason_file, 'r', encoding='utf8') as file:
        reasons = [line.strip()
                   for line in file.read().split('\n') if line.strip() != '']
    report = CrashReport(
        symbolicate, lambda crash: parse_reason(crash, reasons))
    report.generate_report(crash_dir, output_file)


def _do_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--setting_file', help='setting file', default='setting.ini')

    sub_parsers = parser.add_subparsers()

    sub_parser = sub_parsers.add_parser('report')
    sub_parser.add_argument('crash_dir', help='clash report dir')
    sub_parser.add_argument('reason_file', help='reason file')
    sub_parser.add_argument('output_file', help='output report file')
    sub_parser.set_defaults(func=_do_report)

    args = parser.parse_args()
    setup.setup(args.setting_file)
    args.func(args)


if __name__ == '__main__':
    _do_parse_args()
