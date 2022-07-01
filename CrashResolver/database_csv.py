'''处理dict list的读取和写入'''

import csv
import sys

def get_values(dict, headers, default):
    result = []
    for h in headers:
        result.append(dict.get(h, default))
    return result

def save(csv_file: str, dict_list: list[dict], headers=None):
    '''保存所有的dict到csv文件'''
    with open(csv_file, 'w', encoding='utf8') as file:
        writer = csv.writer(file, 'excel')
        if headers is None:
            headers = dict_list[0].keys()
        
        writer.writerow(headers)

        for crash in dict_list:
            writer.writerow(get_values(crash, headers, 'unknown'))

def load(csv_file: str):
    csv.field_size_limit(sys.maxsize)

    with open(csv_file, 'r', encoding='utf8') as file:
        reader = csv.reader(file, 'excel')
        items = []
        headers = []
        for index, columns in enumerate(reader):
            if index == 0:
                headers = columns
            else:
                item = {}
                for column_index, column in enumerate(columns):
                    item[headers[column_index]] = column
                items.append(item)
        
        return items
