'''
打点数据的统计
'''

import sys

from ..database_csv import load

def load_file(filename):
    records = load(filename)
    devices_map = {}
    for record in records:
        android_id = record['androidId']
        if android_id not in devices_map:
            devices_map[android_id] = []
        devices_map[android_id].append(record['nowtime'])
    return devices_map


# not_found
devices_map = load_file(sys.argv[1])

# 
devices_map2 = load_file(sys.argv[2])

temp_list = []
for android_id, v  in devices_map.items():
    if len(v) > 1 and android_id in devices_map2:
        temp_list.append((android_id, v))
        
temp_list.sort(key=lambda x: len(x[1]), reverse=True)
for pair in temp_list:
    print(pair[0], pair[1])