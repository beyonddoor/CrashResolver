'''db的常见操作'''


def classify_by_stack(crash_list: list[dict]) -> dict[str, dict]:
    '''根据stack的指纹分类crash'''
    crashes = {}
    for crash in crash_list:
        fingerprint = crash['stack_key']
        if fingerprint not in crashes:
            crashes[fingerprint] = []

        crashes[fingerprint].append(crash)

    return crashes


def save_crashes_to_file(crash_list, filename: str):
    '''将crash的写入文件'''
    with open(filename, 'w', encoding='utf8') as file:
        for crashes_pair in crash_list:
            file.write(f'\n------ {len(crashes_pair[1])} in total ------\n')

            for crash in crashes_pair[1]:
                file.write(str(crash))
                file.write("\n")


