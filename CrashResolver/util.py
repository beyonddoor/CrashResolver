
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
