import urllib.parse
import re

import requests
import logging

from .page_reader import PageReader
from .config import get_config
from .setup import setup

logger = logging.getLogger(__name__)


def query_server(query):
    '''测试query'''
    data = urllib.parse.urlencode(query)
    # data = 'groupId=16&currentPage=1&pageSize=100&sort=&order=&product=20000048&locale=01&productId=20000048&localeId=01&startTime=2020-07-29%2000%3A00%3A00&endTime=2020-07-29%2023%3A59%3A59&rangeTime=%E4%BB%8A%E5%A4%A9&roleregistertime=&firstpaytime=&lastpaytime=&capricious=&myKeywords=&payStatus=&callStatus=&gameOrderType=&gameOrderInfoType=&isRepair=&platform=1&exceptionCode=&logClient=&operationLineId=&platformId=&advertiserCode=appsflyer&deviceGroupId=&mainChannel=&gameVersion=1.1.7&parentchannelId=&channelId=&subchannelId=&advertiserTo=&eventKey=&serverId=&propKey=&custom=&serviceType=&serviceText=&updateType=&detail=&userType=&transactionid=&userInfoType=&userInfoText=&deviceInfoType=&deviceInfoText=&packageStatus=&packageLogType=&giftInfoType=&giftInfoText=&payamount=&bindPhones=&bingEmails=&bindState=&closeState=&isTestUser=&status=0&operateType=0&operateTypeText=&signKeyValid=&signKey=&chatInfo=&payChannel=&is_first=&userId=&area=&server=&action=&subType=&fnInterface=&event=&adPlatform=&adName=&adGroup=&gameChannelId=&chatLogType=&auditStatus=&reservationUser=&reservationType=&hotEventType=&studiotag=&isstudio=&__mask__=false&totalCount=&queryFrom=1'
    logger.debug('query_server %s', data)
    response = requests.post(url=get_config().IosCrashRepoUrl, headers={
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "i18n-locale": "zh_CN",
        "request-locale": "01",
        "request-productid": get_config().ProductId,
        "token": get_config().Token,
        "x-requested-with": "XMLHttpRequest"
    }, data=data)
    return response


def create_query():
    query = {
        'groupId': 16,
        'currentPage': 0,
        'pageSize': 0,
        'sort': '',
        'order': '',
        'product': '20000048',
        'locale': '01',
        'productId': '20000048',
        'localeId': '01',
        'startTime': '',
        'endTime': '',
        'rangeTime': '',
        'roleregistertime': '',
        'firstpaytime': '',
        'lastpaytime': '',
        'capricious': '',
        'myKeywords': '',
        'payStatus': '',
        'callStatus': '',
        'gameOrderType': '',
        'gameOrderInfoType': '',
        'isRepair': '',
        'platform': 1,
        'exceptionCode': '',
        'logClient': '',
        'operationLineId': '',
        'platformId': '',
        'advertiserCode': 'appsflyer',
        'deviceGroupId': '',
        'mainChannel': '',
        'gameVersion': '',
        'parentchannelId': '',
        'channelId': '',
        'subchannelId': '',
        'advertiserTo': '',
        'eventKey': '',
        'serverId': '',
        'propKey': '',
        'custom': '',
        'serviceType': '',
        'serviceText': '',
        'updateType': '',
        'detail': '',
        'userType': '',
        'transactionid': '',
        'userInfoType': '',
        'userInfoText': '',
        'deviceInfoType': '',
        'deviceInfoText': '',
        'packageStatus': '',
        'packageLogType': '',
        'giftInfoType': '',
        'giftInfoText': '',
        'payamount': '',
        'bindPhones': '',
        'bingEmails': '',
        'bindState': '',
        'closeState': '',
        'isTestUser': '',
        'status': 0,
        'operateType': 0,
        'operateTypeText': '',
        'signKeyValid': '',
        'signKey': '',
        'chatInfo': '',
        'payChannel': '',
        'is_first': '',
        'userId': '',
        'area': '',
        'server': '',
        'action': '',
        'subType': '',
        'fnInterface': '',
        'event': '',
        'adPlatform': '',
        'adName': '',
        'adGroup': '',
        'gameChannelId': '',
        'chatLogType': '',
        'auditStatus': '',
        'reservationUser': '',
        'reservationType': '',
        'hotEventType': '',
        'studiotag': '',
        'isstudio': '',
        '__mask__': 'false',
        'totalCount': '',
        'queryFrom': 1,
    }
    return query


def build_query(query, start_time, end_time, game_version, platform, locale='05'):
    '''构造查询，locale对应的区域，比如韩国为05'''
    config = get_config()
    if start_time != '':
        query['startTime'] = start_time + ' 00:00:00'
    if end_time != '':
        query['endTime'] = end_time + ' 23:59:59'
    query['product'] = config.Product
    query['productId'] = config.ProductId
    query['gameVersion'] = game_version
    query['platform'] = platform
    query['locale'] = locale
    query['localeId'] = locale
    logger.debug('query is %s', query)


class QueryPageReader(PageReader):
    '''通过query读取page'''

    def __init__(self, query) -> None:
        self._query = query

    def read_page(self, page):
        '''read page'''
        self._query['currentPage'] = page
        response = query_server(self._query)
        return response.json()


class SimplePageReader(PageReader):
    '''简单粗暴的方式读取page'''

    def __init__(self, headers, data_pattern) -> None:
        self._headers = headers
        self._data_pattern = data_pattern

    def read_page(self, page):
        '''文本替换的方式获取page'''        
        data = re.sub('&currentPage=1&', f'&currentPage={page}&', self._data_pattern)
        response = requests.post(
            url=get_config().IosCrashRepoUrl, headers=self._headers, data=data)
        return response.json()


def _do_test_query():
    query = create_query()
    query['pageSize'] = 100
    query['currentPage'] = 1
    query['platform'] = 1
    query['gameVersion'] = '1.1.7'
    query['startTime'] = '2022-07-21 00:00:00'
    query['endTime'] = '2022-07-21 23:59:59'
    print(query_server(query).text)


if __name__ == '__main__':
    setup('settings.ini')
    _do_test_query()
