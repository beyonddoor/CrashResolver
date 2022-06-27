'''generate a report from crashes'''

import os
import argparse
from pathlib import Path

import logging

from . import config
from . import crash_parser

logger = logging.getLogger(__name__)


def find_symbolated_crashes(crash_dir: str) -> list[str]:
    '''查找已经符号化的crashes，返回文件名，不包含后缀'''
    for _, _, filenames in os.walk(crash_dir):
        results = []
        for filename in filenames:
            if filename.endswith(config.SymbolExt):
                results.append(filename[0:-len(config.SymbolExt)])
        return results


class CrashReport:
    '''
    统计所有的crash，自动输出报告
    '''

    def __init__(self, symbol_obj) -> None:
        self._symbolicator = symbol_obj

    def _save_reason_stats(self, file, reasons_stat):
        file.write(
            "\n--------------------------report--------------------------\n")
        for pair in reasons_stat.items():
            count = 0
            for list in pair[1]:
                count += len(list)

            file.write(f"{count}\t{pair[0]}\n")

    def _save_tuple_list(self, file, tuper_list, crash_dir: Path, symbolicate_crashes):
        reasons_stat = {}

        for pair in tuper_list:
            self._symbolicator.symbolicate_same_crashes(
                pair[1], crash_dir, symbolicate_crashes)

            reason = pair[1][0]['crash_reason']
            if reason is None:
                reason = 'unknown'

            crash_list = [] if reason not in reasons_stat else reasons_stat[reason]
            crash_list.append(pair[1])
            reasons_stat[reason] = crash_list

        for pair in tuper_list:
            crash = pair[1][0]
            reason = crash['crash_reason']
            file.write(f'\n------ {len(pair[1])} in total ------ ({reason})\n')
            file.write('\n'.join(crash['symbol_stacks']))
            file.write('\n')

            for crash in pair[1]:
                file.write(crash_parser.stringify_crash(crash))
                file.write("\n")

        self._save_reason_stats(file, reasons_stat)

    def generate_report(self, crash_dir: str, output_file: str) -> None:
        '''生成报告'''
        logger.info(
            'start generate report: {output_file}', output_file=output_file)

        symbolicated_crashes = set(find_symbolated_crashes(crash_dir))

        crash_list = crash_parser.read_crash_list(crash_dir, False)

        key_crashes_map = crash_parser.classify_by_stack(crash_list)
        pairs_sorted = list(key_crashes_map.items())
        pairs_sorted.sort(key=lambda x: len(x[1]), reverse=True)

        with open(output_file, 'w', encoding='utf8') as file:
            self._save_tuple_list(file, pairs_sorted,
                                  crash_dir, symbolicated_crashes)

        logger.info(
            'finish generate report: {output_file}', output_file=output_file)
