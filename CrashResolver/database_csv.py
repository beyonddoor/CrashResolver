'''处理dict list的读取和写入'''

import csv
import sys

def save(csv_file: str, rows: list[dict], headers=None):
    '''保存所有的dict到csv文件'''
    with open(csv_file, 'w', encoding='utf8') as file:
        if headers is None:
            headers = rows[0].keys()
            
        writer = csv.DictWriter(file, fieldnames=headers, restval='', extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def load(csv_file: str) -> list[dict]:
    '''从csv加载dict'''
    csv.field_size_limit(sys.maxsize)
    with open(csv_file, 'r', encoding='utf8') as file:
        reader = csv.DictReader(file, dialect='excel', restval='')
        return [row for row in reader]
