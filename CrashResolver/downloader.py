'''download crashes from url'''

from concurrent.futures import ThreadPoolExecutor
import pathlib
import argparse
import logging

import requests

from .config import get_config
from . import setup

logger = logging.getLogger(__name__)

def download(url_path_tuple):
    '''下载url到文件'''
    with open(url_path_tuple[1], 'wb') as file:
        file.write(requests.get(url_path_tuple[0]).content)
        
def download_tasks(tasks):
    '''下载所有的url到文件中'''
    with ThreadPoolExecutor(max_workers=10) as exector:
        for task in tasks:
            exector.submit(download, task)

class IosCrashDownloader:
    '''
    从crash repo获取所有的crash文件，进行分析
    platform = 1
    '''

    def __init__(self, save_dir, start_time, end_time, page_size) -> None:
        self._save_dir = save_dir
        self._start_time = start_time
        self._end_time = end_time
        self._total_page = None
        self._page_size = page_size
        
    def _get_task(self, crash_data):
        crash_url = crash_data['crashurl']
        end_pos = crash_url.rfind('/', 0)
        start_pos = crash_url.rfind('/', 0, end_pos)
        filename = crash_url[start_pos+1:end_pos]
        path = pathlib.Path(self._save_dir) / (filename + get_config().CrashExt)
        
        if path.exists():
            logger.warning('file %s exists, skip ', filename)
            return
        
        return (crash_url, path)

    def download_page(self, page):
        '''下载一页'''
        data = f'groupId=16&currentPage={page}&pageSize={self._page_size}&sort=&order=&product=20000048&locale=01&productId=20000048&localeId=01&startTime={self._start_time}%2000%3A00%3A00&endTime={self._end_time}%2023%3A59%3A59&rangeTime=%E4%BB%8A%E5%A4%A9&roleregistertime=&firstpaytime=&lastpaytime=&capricious=&myKeywords=&payStatus=&callStatus=&gameOrderType=&gameOrderInfoType=&isRepair=&platform=1&exceptionCode=&logClient=&operationLineId=&platformId=&advertiserCode=appsflyer&deviceGroupId=&mainChannel=&gameVersion=&parentchannelId=&channelId=&subchannelId=&advertiserTo=&eventKey=&serverId=&propKey=&custom=&serviceType=&serviceText=&updateType=&detail=&userType=&transactionid=&userInfoType=&userInfoText=&deviceInfoType=&deviceInfoText=&packageStatus=&packageLogType=&giftInfoType=&giftInfoText=&payamount=&bindPhones=&bingEmails=&bindState=&closeState=&isTestUser=&status=0&operateType=0&operateTypeText=&signKeyValid=&signKey=&chatInfo=&payChannel=&is_first=&userId=&area=&server=&action=&subType=&fnInterface=&event=&adPlatform=&adName=&adGroup=&gameChannelId=&chatLogType=&auditStatus=&reservationUser=&reservationType=&hotEventType=&studiotag=&isstudio=&__mask__=false&totalCount=52&queryFrom=1'
        response = requests.post(url=get_config().CrashRepoUrl, headers={
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "i18n-locale": "zh_CN",
            "request-locale": "01",
            "request-productid": "20000048",
            "token": get_config().Token,
            "x-requested-with": "XMLHttpRequest"
        }, data=data)

        json_data = response.json()
        logger.debug('json data = %s', json_data)
        self._total_page = json_data['data']['totalPage']

        tasks = []
        for crash_data in json_data['data']['list']:
            task = self._get_task(crash_data)
            if task is not None:
                tasks.append(task)

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

    def __init__(self, save_dir, start_time, end_time, page_size) -> None:
        self._save_dir = save_dir
        self._start_time = start_time
        self._end_time = end_time
        self._total_page = None
        self._page_size = page_size

    def download_page(self, page):
        '''download one page'''
        config = get_config()
        data = f'groupId=16&currentPage={page}&pageSize={self._page_size}&sort=&order=&product={config.Product}&locale=01&productId={config.ProductId}&localeId=01&startTime={self._start_time}%2000%3A00%3A00&endTime={self._end_time}%2023%3A59%3A59&rangeTime=&roleregistertime=&firstpaytime=&lastpaytime=&capricious=&myKeywords=&payStatus=&callStatus=&gameOrderType=&gameOrderInfoType=&isRepair=&platform=0&exceptionCode=&logClient=&operationLineId=&platformId=&advertiserCode=appsflyer&deviceGroupId=&mainChannel=&gameVersion=&parentchannelId=&channelId=&subchannelId=&advertiserTo=&eventKey=&serverId=&propKey=&custom=&serviceType=&serviceText=&updateType=&detail=&userType=&transactionid=&userInfoType=&userInfoText=&deviceInfoType=&deviceInfoText=&packageStatus=&packageLogType=&giftInfoType=&giftInfoText=&payamount=&bindPhones=&bingEmails=&bindState=&closeState=&isTestUser=&status=0&operateType=0&operateTypeText=&signKeyValid=&signKey=&chatInfo=&payChannel=&is_first=&userId=&area=&server=&action=&subType=&fnInterface=&event=&adPlatform=&adName=&adGroup=&gameChannelId=&chatLogType=&auditStatus=&reservationUser=&reservationType=&hotEventType=&studiotag=&isstudio=&__mask__=false&totalCount=95&queryFrom=1'
        response = requests.post(url=config.CrashRepoUrl, headers={
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "i18n-locale": "zh_CN",
            "request-locale": "01",
            "request-productid": config.Product,
            "token": config.Token,
            "x-requested-with": "XMLHttpRequest"
        }, data=data)

        save_dir = pathlib.Path(self._save_dir)
        json_data = response.json()
        logger.debug('page #%s', page)
        self._total_page = json_data['data']['totalPage']

        tasks = []
        for crash_data in json_data['data']['list']:
            task = self._get_zip_task(crash_data, save_dir)
            if task is not None:
                tasks.append(task)

            task = self._get_text_task(crash_data, save_dir)
            if task is not None:
                tasks.append(task)

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
            logger.warning('text file %s exists, skip', filename)
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
            logger.warning('zip file %s exists, skip ', filename)
            return

        return (crash_url, path)

    def download_all(self):
        '''下载所有的crash文件'''
        self.download_page(1)
        for i in range(2, self._total_page+1):
            self.download_page(i)

def _do_download_ios(args):
    downloader = IosCrashDownloader(
        args.save_dir, args.start_time, args.end_time, args.page_size)
    if args.page >= 0:
        downloader.download_page(args.page)
    else:
        downloader.download_all()


def _do_download_android(args):
    downloader = AndroidCrashDownloader(
        args.save_dir, args.start_time, args.end_time, args.page_size)
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
    sub_parser.add_argument('--start_time', help='start time',
                            default='2022-06-20')
    sub_parser.add_argument(
        '--end_time', help='end time', default='2022-06-21')
    sub_parser.add_argument(
        '--page', help='page number, if -1 then all pages will be downloaded', default=1, type=int)
    sub_parser.add_argument(
        '--page_size', help='page size', default=100, type=int)
    sub_parser.set_defaults(func=_do_download_ios)

    sub_parser = sub_parsers.add_parser(
        'android', help='download android crashes')
    sub_parser.add_argument('save_dir', help='save directory for crash files')
    sub_parser.add_argument('--start_time', help='start time',
                            default='2022-06-20')
    sub_parser.add_argument(
        '--end_time', help='end time', default='2022-06-21')
    sub_parser.add_argument(
        '--page', help='page number, if -1 then all pages will be downloaded', default=1, type=int)
    sub_parser.add_argument(
        '--page_size', help='page size', default=100, type=int)
    sub_parser.set_defaults(func=_do_download_android)
    
    args = parser.parse_args()
    setup.setup(args.setting_file)
    args.func(args)

if __name__ == '__main__':
    _do_parse_args()
    