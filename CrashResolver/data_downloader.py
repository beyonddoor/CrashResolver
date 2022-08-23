'''
从数据后台下载，支持分页功能

curl 'http://gscinterface.z4v.cn/v3/log/logQuery/getPlayerAlternatelyEventLog.htm' \
  -H 'Connection: keep-alive' \
  -H 'i18n-locale: zh_CN' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'request-productid: 20000048' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'token: 1216749c661dabae4ba098303e664e43fcd12016' \
  -H 'request-locale: 05' \
  -H 'Origin: http://gsc.longtubas.com' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7' \
  --data-raw 'groupId=14&currentPage=1&pageSize=100&sort=&order=&product=20000048&locale=05&productId=20000048&localeId=05&startTime=&endTime=&rangeTime=&roleregistertime=&firstpaytime=&lastpaytime=&capricious=&myKeywords=&payStatus=&callStatus=&gameOrderType=&gameOrderInfoType=&isRepair=&platform=&exceptionCode=&logClient=sdkclient&operationLineId=&platformId=0&advertiserCode=appsflyer&deviceGroupId=&mainChannel=&gameVersion=1.2.6&parentchannelId=&channelId=&subchannelId=&advertiserTo=&eventKey=&serverId=&propKey=&custom=&serviceType=actId&serviceText=Game_ClientUpdate_NotFind&updateType=&detail=&userType=&transactionid=&userInfoType=&userInfoText=&interfaceLogtype=&bindtype=&deviceInfoType=&deviceInfoText=&cpuabi_like=&cpuabi_notlike=&packageStatus=&packageLogType=&giftInfoType=&giftInfoText=&payamount=&bindPhones=&bingEmails=&bindState=&closeState=&isTestUser=&status=0&operateType=0&operateTypeText=&signKeyValid=&signKey=&chatInfo=&payChannel=&is_first=&userId=&area=&server=&action=&subType=&fnInterface=&event=&adPlatform=&adName=&adGroup=&gameChannelId=&chatLogType=&auditStatus=&reservationUser=&reservationType=&hotEventType=&studiotag=&isstudio=&__mask__=false&totalCount=63848&queryFrom=1' \
  --compressed \
  --insecure
  
  fetch("http://gscinterface.z4v.cn/v3/log/logQuery/getPlayerAlternatelyEventLog.htm", {
  "headers": {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "content-type": "application/x-www-form-urlencoded",
    "i18n-locale": "zh_CN",
    "request-locale": "05",
    "request-productid": "20000048",
    "token": "1216749c661dabae4ba098303e664e43fcd12016",
    "x-requested-with": "XMLHttpRequest"
  },
  "referrerPolicy": "no-referrer",
  "body": "groupId=14&currentPage=1&pageSize=100&sort=&order=&product=20000048&locale=05&productId=20000048&localeId=05&startTime=&endTime=&rangeTime=&roleregistertime=&firstpaytime=&lastpaytime=&capricious=&myKeywords=&payStatus=&callStatus=&gameOrderType=&gameOrderInfoType=&isRepair=&platform=&exceptionCode=&logClient=sdkclient&operationLineId=&platformId=0&advertiserCode=appsflyer&deviceGroupId=&mainChannel=&gameVersion=1.2.6&parentchannelId=&channelId=&subchannelId=&advertiserTo=&eventKey=&serverId=&propKey=&custom=&serviceType=actId&serviceText=Game_ClientUpdate_NotFind&updateType=&detail=&userType=&transactionid=&userInfoType=&userInfoText=&interfaceLogtype=&bindtype=&deviceInfoType=&deviceInfoText=&cpuabi_like=&cpuabi_notlike=&packageStatus=&packageLogType=&giftInfoType=&giftInfoText=&payamount=&bindPhones=&bingEmails=&bindState=&closeState=&isTestUser=&status=0&operateType=0&operateTypeText=&signKeyValid=&signKey=&chatInfo=&payChannel=&is_first=&userId=&area=&server=&action=&subType=&fnInterface=&event=&adPlatform=&adName=&adGroup=&gameChannelId=&chatLogType=&auditStatus=&reservationUser=&reservationType=&hotEventType=&studiotag=&isstudio=&__mask__=false&totalCount=63848&queryFrom=1",
  "method": "POST",
  "mode": "cors",
  "credentials": "omit"
});

'''


from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
import pathlib
import argparse
import logging
import json
import os
import urllib.parse
import requests
import re

from .page_reader import PageReader
from .database_csv import save as save_db, load

logger = logging.getLogger(__name__)


class SimplePageReader(PageReader):
    '''简单粗暴的方式读取page'''

    def __init__(self, url, headers, data_pattern) -> None:
        self._headers = headers
        self._url = url
        self._data_pattern = data_pattern

    def read_page(self, page):
        '''文本替换的方式获取page'''
        data = re.sub('&currentPage=1&',
                      f'&currentPage={page}&', self._data_pattern)
        response = requests.post(
            url=self._url, headers=self._headers, data=data)
        return response.json()


class DataDownloader:
    '''
    下载数据
    '''

    def __init__(self, data_file, page_reader: PageReader, max_workers=10) -> None:
        logger.debug('query %s', page_reader)
        self._data_file = pathlib.Path(data_file)
        self._page_reader = page_reader
        self._total_page = None
        self._records = []
        self._max_workers = max_workers

    def download_page(self, page):
        '''下载一页'''
        json_data = self._page_reader.read_page(page)
        self._total_page = json_data['data']['totalPage']
        logger.debug('page #%s/%s pagesize=%s', page,
                     self._total_page, len(json_data['data']['list']))
        return list(json_data['data']['list'])

    def download_all(self):
        '''下载所有的crash文件'''
        self.download_page(1)
        executor = ThreadPoolExecutor(max_workers=self._max_workers)
        futures = []
        for i in range(2, self._total_page+1):
            futures.append(executor.submit(self.download_page, i))
        for future in futures:
            self._records.extend(future.result())

    def save(self):
        '''保存db'''
        save_db(self._data_file, self._records)


def download_event(event_name, save_file, max_workers=10):
    '''下载自定义事件
    Game_ClientUpdate_NotFind
    Game_WriteUpDateFile_End
    '''
    data_pattern = "groupId=14&currentPage=1&pageSize=100&sort=&order=&product=20000048&locale=05&productId=20000048&localeId=05&startTime=&endTime=&rangeTime=&roleregistertime=&firstpaytime=&lastpaytime=&capricious=&myKeywords=&payStatus=&callStatus=&gameOrderType=&gameOrderInfoType=&isRepair=&platform=&exceptionCode=&logClient=sdkclient&operationLineId=&platformId=0&advertiserCode=appsflyer&deviceGroupId=&mainChannel=&gameVersion=1.2.6&parentchannelId=&channelId=&subchannelId=&advertiserTo=&eventKey=&serverId=&propKey=&custom=&serviceType=actId&serviceText=Game_ClientUpdate_NotFind&updateType=&detail=&userType=&transactionid=&userInfoType=&userInfoText=&interfaceLogtype=&bindtype=&deviceInfoType=&deviceInfoText=&cpuabi_like=&cpuabi_notlike=&packageStatus=&packageLogType=&giftInfoType=&giftInfoText=&payamount=&bindPhones=&bingEmails=&bindState=&closeState=&isTestUser=&status=0&operateType=0&operateTypeText=&signKeyValid=&signKey=&chatInfo=&payChannel=&is_first=&userId=&area=&server=&action=&subType=&fnInterface=&event=&adPlatform=&adName=&adGroup=&gameChannelId=&chatLogType=&auditStatus=&reservationUser=&reservationType=&hotEventType=&studiotag=&isstudio=&__mask__=false&totalCount=63848&queryFrom=1"
    data = re.sub('&serviceText=[^&]*&',
                  f'&serviceText={event_name}&', data_pattern)
    page_reader = SimplePageReader(url='http://gscinterface.z4v.cn/v3/log/logQuery/getPlayerAlternatelyEventLog.htm', headers={
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "i18n-locale": "zh_CN",
        "request-locale": "05",
        "request-productid": "20000048",
        "token": "1216749c661dabae4ba098303e664e43fcd12016",
        "x-requested-with": "XMLHttpRequest"
    }, data_pattern=data)

    downloader = DataDownloader(save_file, page_reader, max_workers)
    downloader.download_all()
    downloader.save()

def _download_event(args):
    download_event(args.event_name, args.save_file, args.max_workers)

def _do_parse_args():
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers()

    sub_parser = sub_parsers.add_parser('event', help='download event')
    sub_parser.add_argument('event_name', help='event name')
    sub_parser.add_argument('save_file', help='save file')
    sub_parser.add_argument('--max_workers', help='max workers', type=int, default=10)
    sub_parser.set_defaults(func=_download_event)
    
    args = parser.parse_args()
    args.func(args)

FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
_do_parse_args()
