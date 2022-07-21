'''公用的一些util'''

from itertools import groupby

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
        print(f'{lists[1]}/{lists[1]/total:0.2}\t{lists[0]}')


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
            
            