'''config for package'''

import configparser
import logging

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

AndroidCrashRepoUrl = ''
'''android crash文件的仓库地址'''

Token = ""
'''登陸的token'''

Product = ''
'''产品'''

ProductId = ''
'''产品id'''

logger = logging.getLogger(__name__)

def parse_config(filename):
    '''parse config'''
    global CrashExt, SymbolExt, SymbolicatePath, CrashRepoUrl, LogConfigFile, Token
    global AndroidCrashRepoUrl
    global Product
    global ProductId

    try:
        with open(filename, 'r', encoding='utf8') as file:
            config = configparser.ConfigParser()
            config.read_file(file)
            section = config['global']
            CrashExt = section.get('CrashExt', '.txt')
            SymbolExt = section.get('SymbolExt', '.sym')
            SymbolicatePath = section.get('SymbolicatePath', '.sym')
            CrashRepoUrl = section.get('CrashRepoUrl', '')
            AndroidCrashRepoUrl = section.get('AndroidCrashRepoUrl', '')
            LogConfigFile = section.get('LogConfigFile', 'log.yaml')
            Product = section.get('Product', '')
            ProductId = section.get('ProductId', '')
            Token = section.get('Token', '')

    except Exception as err:
        logger.error('parse config "%s" error: %s', filename, err)


def write_config(filename):
    '''write config'''
    with open(filename, 'w', encoding='utf8') as file:
        config = configparser.ConfigParser()
        config['CrashExt'] = CrashExt
        config['SymbolExt'] = SymbolExt
        config['SymbolicatePath'] = SymbolicatePath
        config['CrashRepoUrl'] = CrashRepoUrl
        config['AndroidCrashRepoUrl'] = AndroidCrashRepoUrl
        config['Token'] = Token
        config['Product'] = Product
        config['ProductId'] = ProductId
        config.write(file)
