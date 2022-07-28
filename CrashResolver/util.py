'''公用的一些util'''

from itertools import groupby
import json
from pathlib import Path

def group_count(item_list, key, key_name):
    '''根据key进行分类'''
    item_list.sort(key=key, reverse=True)
    group_obj = groupby(item_list, key)
    groups = [(key, len(list(lists)))
              for (key, lists) in group_obj]
    groups.sort(key=lambda x: x[1], reverse=True)

    total = len(item_list)
    print(f'total: #{len(item_list)}')
    print(f'groups count: #{len(groups)}')
    print(f'groups key: #{key_name}')
    print('\n')

    for lists in groups:
        print(f'{lists[1]}/{(lists[1]/total*100):2.2f}%\t{lists[0]}')


def group_detail(dict_list: list[dict], key, key_name, head=10):
    '''根据key进行分类'''
    dict_list.sort(key=key, reverse=True)
    group_obj = groupby(dict_list, key)
    groups = [(key, list(lists)) for (key, lists) in group_obj]
    groups.sort(key=lambda x: len(x[1]), reverse=True)

    print(f'Total: #{len(dict_list)}')
    print(f'Groups Count: #{len(groups)}')
    print('\n')

    total = len(dict_list)
    for lists in groups:
        print(
            f"========== {len(lists[1])} ({len(lists[1])*100/total:2.2f}%) ==========")
        print(key_name, ': ', lists[0])
        print()
        for i in lists[1][0:head]:
            print(i['filename'])
        print()


def is_os_available(crash: dict, os_names: set) -> bool:
    '''os的符号是否可用'''
    arm64e = 'arm64e' if crash['is_arm64e'] else 'arm64'
    return (crash['OS Version'] + ' ' + arm64e) in os_names


# def read_os_names(filename) -> set:
#     '''读取已经下载就绪的os名字，比如 iPhone OS 13.6 (17G68) arm64e'''
#     lines = []
#     with open(filename, 'r', encoding='utf8') as file:
#         lines = file.read().split('\n')
#     return set(line for line in lines if line.strip() != '')

def read_lines(filename):
    '''读取文件中的非空行'''
    with open(filename, 'r', encoding='utf8') as f:
        lines = f.read().splitlines()
    return list(line for line in lines if line.strip() != '')

def dump_to_txt(filename: str, dict_list: list[dict]):
    '''保存所有的dict到txt文件'''
    with open(filename, 'w', encoding='utf8') as file:
        for item in dict_list:
            file.write(str(item))
            file.write('\n')
            
def update_meta(crash_list, meta_dir):
    '''更新meta信息'''
    meta_dir_obj = Path(meta_dir)
    for crash in crash_list:
        meta_filename = meta_dir_obj / (Path(crash['filename']).stem + '.meta')
        json_content = None
        if meta_filename.exists():
            with open(meta_filename, 'r', encoding='utf8') as f:
                json_content = json.load(f)
        if json_content:
            crash['roleId'] = json_content.get('roleId', 'unkown')
            crash['userId'] = json_content.get('userId', 'unkown')
        else:
            crash['roleId'] = 'unkown'
            crash['userId'] = 'unkown'

def read_tag_file(filename):
    '''读取crash的标记文件，这个文件的格式是每行为"category subcategory"'''
    return [reason.strip().split(' ', maxsplit=1) for reason in read_lines(filename)]

def update_tag(crash_list, tag_list, key_func, prefix=None):
    '''根据keyfunc给所有的crash标记，增加reason1和reason2字段'''
    field_reason1 = 'reason1'
    field_reason2 = 'reason2'
    if prefix is not None:
        field_reason1 = prefix + '_reason1'
        field_reason2 = prefix + '_reason2'
    for crash in crash_list:
        crash[field_reason1] = 'unknown'
        crash[field_reason2] = 'unknown'
        
        value = key_func(crash)
        for reason in tag_list:
            if reason[1] in value:
                crash[field_reason1] = reason[0]
                crash[field_reason2] = reason[1]
                break

        if crash[field_reason2] == 'unknown':
            print(crash['filename'], ' unkown')