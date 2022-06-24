import config
import yaml
import logging

def init_log(filename):
    try:
        with open(filename, 'r') as file:
            log_dict = yaml.safe_load(file)
            logging.config.dictConfig(log_dict)
    except Exception as e:
        logging.error(f'init_log error: {filename}')
        
        
def setup():
    config.parse_config('settings.ini')
    init_log(config.LogConfigFile)
    