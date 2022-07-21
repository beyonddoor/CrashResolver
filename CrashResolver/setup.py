'''
setup config and log.
'''

import logging.config
import yaml
import pprint

from .config import get_config, parse_config


def init_log(filename):
    '''init log'''
    try:
        with open(filename, 'r', encoding='utf8') as file:
            log_dict = yaml.safe_load(file)
            logging.config.dictConfig(log_dict)
    except Exception as err:
        logging.error('init_log "%s" failed: %s', filename, err)


def setup(filename):
    '''setup config and log.'''
    parse_config(filename)
    init_log(get_config().LogConfigFile)


if __name__ == '__main__':
    setup('settings.ini')
    logging.info('init_log successfully')
