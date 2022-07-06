'''
setup config and log.
'''

import logging.config
import yaml

from . import config


def init_log(filename):
    '''init log'''
    try:
        with open(filename, 'r', encoding='utf8') as file:
            log_dict = yaml.safe_load(file)
            logging.config.dictConfig(log_dict)
            logging.info('init_log successfully')
    except Exception as err:
        logging.error('init_log "%s" failed: %s', filename, err)


def setup(filename):
    '''setup config and log.'''
    config.parse_config(filename)
    init_log(config.LogConfigFile)
