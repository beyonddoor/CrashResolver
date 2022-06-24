from . import config
import yaml
import logging.config

def init_log(filename):
    try:
        with open(filename, 'r') as file:
            log_dict = yaml.safe_load(file)
            logging.config.dictConfig(log_dict)
    except Exception as e:
        logging.error(f'init_log "{filename}" error: {e}')
        
        
def setup(filename):
    config.parse_config(filename)
    init_log(config.LogConfigFile)
    