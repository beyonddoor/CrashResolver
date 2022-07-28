'''config for package'''

import configparser
import logging

from collections import namedtuple
_Config = namedtuple('Config', ['LogConfigFile', 'CrashExt', 'SymbolExt', 'IosSymbolicateArgs', 'IosCrashRepoUrl', 'AndroidCrashRepoUrl', 'Token', 'Product', 'ProductId',
                                'AndroidSymbolicateArgs'], defaults=[''])

_configVal = _Config('', '.txt', '.sym', '', '', '', '', '', '', '')
logger = logging.getLogger(__name__)


def get_config() -> _Config:
    '''get config'''
    return _configVal


def parse_config(filename):
    '''parse config'''

    # try:
    with open(filename, 'r', encoding='utf8') as file:
        config = configparser.ConfigParser()
        config.read_file(file)
        section = config['global']

        values = {
            'CrashExt': section.get('CrashExt', '.txt'),
            'SymbolExt': section.get('SymbolExt', '.sym'),
            'IosSymbolicateArgs': section.get('IosSymbolicateArgs', ''),
            'IosCrashRepoUrl': section.get('IosCrashRepoUrl', ''),
            'AndroidCrashRepoUrl': section.get('AndroidCrashRepoUrl', ''),
            'LogConfigFile': section.get('LogConfigFile', 'log.yaml'),
            'Product': section.get('Product', ''),
            'ProductId': section.get('ProductId', ''),
            'Token': section.get('Token', ''),
            'AndroidSymbolicateArgs': section.get('AndroidSymbolicateArgs', ''),
        }

        global _configVal
        _configVal = _Config(**values)

    # except TypeError as err:
    #     logger.error('parse config "%s" error: %s', filename, err)


def write_config(filename):
    '''write config'''
    with open(filename, 'w', encoding='utf8') as file:
        config = configparser.ConfigParser()
        config['CrashExt'] = _configVal.CrashExt
        config['SymbolExt'] = _configVal.SymbolExt
        config['IosSymbolicateArgs'] = _configVal.IosSymbolicateArgs
        config['IosCrashRepoUrl'] = _configVal.IosCrashRepoUrl
        config['AndroidCrashRepoUrl'] = _configVal.AndroidCrashRepoUrl
        config['Token'] = _configVal.Token
        config['Product'] = _configVal.Product
        config['ProductId'] = _configVal.ProductId
        config['AndroidSymbolicateArgs'] = _configVal.AndroidSymbolicateArgs
        config.write(file)
