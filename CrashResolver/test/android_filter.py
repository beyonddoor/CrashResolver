
import csv
import sys
import re
from ..android import main

def load(csv_file: str):
    csv.field_size_limit(sys.maxsize)

    with open(csv_file, 'r', encoding='utf8') as file:
        # TODO 考虑使用DictReader
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

records = load('db_android.csv')
pattern = re.compile("'2022-07-[15|16|17|18|19|20].*")
lists = list(record for record in records if pattern.match(record['Start time']))
main.group_detail(lists, lambda x: x['stack_key'])

# print(len(list(lists)))