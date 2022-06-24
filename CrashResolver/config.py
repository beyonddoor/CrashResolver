import configparser

LogConfigFile = 'log.yaml'
'''logging config file'''

CrashExt = '.txt'
'''crash文件的后缀'''

SymbolExt = '.sym'
'''符号化的crash文件后缀'''

SymbolicatePath = './symbolicate.sh'
'''符号化脚本的路径'''

CrashRepoUrl = ''
'''crash文件的仓库地址'''

def parse_config(filename):
    global CrashExt, SymbolExt, SymbolicatePath, CrashRepoUrl, LogConfigFile

    try:
        with open(filename, 'r') as file:
            config = configparser.ConfigParser()
            config.read_file(file)
            section = config['global']
            CrashExt = section.get('CrashExt', '.txt')
            SymbolExt = section.get('CrashExt', '.sym')
            SymbolicatePath = section.get('SymbolicatePath', '.sym')
            CrashRepoUrl = section.get('CrashRepoUrl', '.sym')
            LogConfigFile = section.get('LogConfigFile', 'log.yaml')
            
    except Exception as e:
        print(f'parse config "{filename}" error: {e}')

def write_config(filename):
    with open(filename, 'w') as file:
        config = configparser.ConfigParser()
        config['CrashExt'] = CrashExt
        config['SymbolExt'] = SymbolExt
        config['SymbolicatePath'] = SymbolicatePath
        config['CrashRepoUrl'] = CrashRepoUrl
        config.write(file)
