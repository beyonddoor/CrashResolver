'''download crashes from url'''

from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
import pathlib
import argparse
import logging
import json
import urllib.parse

import requests

from .config import get_config
from . import setup
from .page_query import QueryPageReader, build_query, create_query
from .page_reader import PageReader

logger = logging.getLogger(__name__)

def _get_meta_task(crash_data, save_dir):
    '''下载crashurl的文本'''
    if crash_data['crashurl'] == '':
        return

    crash_url = crash_data['crashurl']
    end_pos = crash_url.rfind('/', 0)
    start_pos = crash_url.rfind('/', 0, end_pos)
    filename = crash_url[start_pos+1:end_pos]
    path = save_dir / (filename + '.meta')

    if path.exists():
        logger.info('meta file %s exists, skip', filename)
        return

    return (crash_data, path)

def download(url_path_tuple):
    '''下载url到文件'''
    logger.debug('download url=%s file=%s', url_path_tuple[0], url_path_tuple[1])
    with open(url_path_tuple[1], 'wb') as file:
        file.write(requests.get(url_path_tuple[0]).content)
        
def download_tasks(tasks):
    '''下载所有的url到文件中'''
    with ThreadPoolExecutor(max_workers=10) as executor:
        for task in tasks:
            executor.submit(download, task)
            


class IosCrashDownloader:
    '''
    从crash repo获取所有的crash文件，进行分析
    platform = 1
    '''

    def __init__(self, save_dir, page_reader: PageReader) -> None:
        logger.debug('query %s', page_reader)
        self._save_dir = pathlib.Path(save_dir)
        self._page_reader = page_reader
        self._total_page = None
        
    def _get_task(self, crash_data):
        crash_url = crash_data['crashurl']
        end_pos = crash_url.rfind('/', 0)
        start_pos = crash_url.rfind('/', 0, end_pos)
        filename = crash_url[start_pos+1:end_pos]
        path = self._save_dir / (filename + get_config().CrashExt)
        
        if path.exists():
            logger.info('file %s exists, skip ', filename)
            return
        
        return (crash_url, path)

    def download_page(self, page):
        '''下载一页'''        
        json_data = self._page_reader.read_page(page)
        logger.debug('json data = %s', json_data)
        self._total_page = json_data['data']['totalPage']

        tasks = []
        for crash_data in json_data['data']['list']:
            task = self._get_task(crash_data)
            if task is not None:
                tasks.append(task)

            task = _get_meta_task(crash_data, self._save_dir)
            if task is not None:
                logger.debug('download meta %s', crash_data['crashurl'])
                with open(task[1], 'w', encoding='utf8') as file:
                    file.write(json.dumps(crash_data, ensure_ascii=False, indent=4))

        download_tasks(tasks)
        

    def download_all(self):
        '''下载所有的crash文件'''
        self.download_page(1)
        for i in range(2, self._total_page+1):
            self.download_page(i)


class AndroidCrashDownloader:
    '''
    从crash repo获取所有的crash文件，进行分析
    platform = 0
    '''
    def __init__(self, save_dir, page_reader:PageReader) -> None:
        self._save_dir = pathlib.Path(save_dir)
        self._total_page = None
        self._page_reader = page_reader
        
    @abstractmethod
    def read_page(self, page):
        '''读取指定page的json'''

    def download_page(self, page):
        '''download one page'''
        json_data = self._page_reader.read_page(page)
        logger.debug('page #%s', page)
        self._total_page = json_data['data']['totalPage']
        
        save_dir = self._save_dir
        tasks = []
        for crash_data in json_data['data']['list']:
            task = self._get_zip_task(crash_data, save_dir)
            if task is not None:
                tasks.append(task)

            task = self._get_text_task(crash_data, save_dir)
            if task is not None:
                tasks.append(task)

            task = _get_meta_task(crash_data, save_dir)
            if task is not None:
                logger.debug('download meta %s', crash_data['crashurl'])
                with open(task[1], 'w', encoding='utf8') as f:
                    f.write(json.dumps(crash_data, ensure_ascii=False, indent=4))

        download_tasks(tasks)

    def _get_text_task(self, crash_data, save_dir):
        '''下载crashurl的文本'''
        if crash_data['crashurl'] == '':
            return

        crash_url = crash_data['crashurl']
        end_pos = crash_url.rfind('/', 0)
        start_pos = crash_url.rfind('/', 0, end_pos)
        filename = crash_url[start_pos+1:end_pos]
        path = save_dir / (filename + get_config().CrashExt)

        if path.exists():
            logger.info('text file %s exists, skip', filename)
            return

        return (crash_url, path)

    def _get_zip_task(self, crash_data, save_dir):
        '''下载crashzipurl的zip'''
        if crash_data['crashzipurl'] == '':
            return

        crash_url = crash_data['crashzipurl']
        end_pos = crash_url.rfind('/', 0)
        start_pos = crash_url.rfind('/', 0, end_pos)
        filename = crash_url[start_pos+1:end_pos]
        path = save_dir / (filename + '.zip')

        if path.exists():
            logger.info('zip file %s exists, skip ', filename)
            return

        return (crash_url, path)

    def download_all(self):
        '''下载所有的crash文件'''
        self.download_page(1)
        for i in range(2, self._total_page+1):
            self.download_page(i)
            

def _do_download_ios(args):
    print(args)
    query = create_query()
    build_query(query, args.start_time, args.end_time, args.game_version, 1, args.locale)
    query['pageSize'] = args.page_size
    downloader = IosCrashDownloader(args.save_dir, QueryPageReader(query))
    if args.page >= 0:
        downloader.download_page(args.page)
    else:
        downloader.download_all()

def _do_download_android(args):
    query = create_query()
    build_query(query, args.start_time, args.end_time, args.game_version, 0, args.locale)
    query['pageSize'] = args.page_size
    
    downloader = AndroidCrashDownloader(args.save_dir, QueryPageReader(query))
    if args.page >= 0:
        downloader.download_page(args.page)
    else:
        downloader.download_all()


def _do_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--setting_file', help='setting file', default='setting.ini')

    sub_parsers = parser.add_subparsers()

    sub_parser = sub_parsers.add_parser('ios', help='download ios crashes')
    sub_parser.add_argument('save_dir', help='save directory for crash files')
    sub_parser.add_argument('--locale', help='locale', default='01')
    sub_parser.add_argument('--start_time', help='start time',
                            default='')
    sub_parser.add_argument(
        '--end_time', help='end time', default='')
    sub_parser.add_argument(
        '--page', help='page number, if -1 then all pages will be downloaded', default=1, type=int)
    sub_parser.add_argument(
        '--page_size', help='page size', default=100, type=int)
    sub_parser.add_argument(
        '--game_version', help='game version', default='')
    sub_parser.set_defaults(func=_do_download_ios)

    sub_parser = sub_parsers.add_parser(
        'android', help='download android crashes')
    sub_parser.add_argument('save_dir', help='save directory for crash files')
    sub_parser.add_argument('--locale', help='locale', default='01')
    sub_parser.add_argument('--start_time', help='start time',
                            default='')
    sub_parser.add_argument(
        '--end_time', help='end time', default='')
    sub_parser.add_argument(
        '--page', help='page number, if -1 then all pages will be downloaded', default=1, type=int)
    sub_parser.add_argument(
        '--page_size', help='page size', default=100, type=int)
    sub_parser.add_argument(
        '--game_version', help='game version', default='')
    sub_parser.set_defaults(func=_do_download_android)
    
    args = parser.parse_args()
    setup.setup(args.setting_file)
    args.func(args)

if __name__ == '__main__':
    _do_parse_args()
    