'''
自定义条件的的downloader
日期的参数 startTime=2022-08-12%2000%3A00%3A00&endTime=2022-08-12%2023%3A59%3A59
'''

import os

from ..setup import setup
from ..downloader import AndroidCrashDownloader
from ..downloader import IosCrashDownloader
from ..page_query import SimplePageReader


def download_android(save_dir):
    '''下载android的crash'''
    data_pattern = "groupId=16&currentPage=1&pageSize=100&sort=&order=&product=20000048&locale=05&productId=20000048&localeId=05&startTime=2022-08-12%2000%3A00%3A00&endTime=2022-08-13%2023%3A59%3A59&rangeTime=&roleregistertime=&firstpaytime=&lastpaytime=&capricious=&myKeywords=&payStatus=&callStatus=&gameOrderType=&gameOrderInfoType=&isRepair=&platform=0&exceptionCode=&logClient=&operationLineId=&platformId=&advertiserCode=appsflyer&deviceGroupId=&mainChannel=&gameVersion=1.2.6&parentchannelId=&channelId=&subchannelId=&advertiserTo=&eventKey=&serverId=&propKey=&custom=&serviceType=&serviceText=&updateType=&detail=&userType=&transactionid=&userInfoType=&userInfoText=&interfaceLogtype=&bindtype=&deviceInfoType=&deviceInfoText=&cpuabi_like=&cpuabi_notlike=&packageStatus=&packageLogType=&giftInfoType=&giftInfoText=&payamount=&bindPhones=&bingEmails=&bindState=&closeState=&isTestUser=&status=0&operateType=0&operateTypeText=&signKeyValid=&signKey=&chatInfo=&payChannel=&is_first=&userId=&area=&server=&action=&subType=&fnInterface=&event=&adPlatform=&adName=&adGroup=&gameChannelId=&chatLogType=&auditStatus=&reservationUser=&reservationType=&hotEventType=&studiotag=&isstudio=&__mask__=false&totalCount=1717&queryFrom=1"
    reader = SimplePageReader(headers={
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "i18n-locale": "zh_CN",
        "request-locale": "01",
        "request-productid": "20000048",
        "token": "1216749c661dabae4ba098303e664e43fcd12016",
        "x-requested-with": "XMLHttpRequest"
    }, data_pattern=data_pattern)

    setup('settings.ini')
    os.makedirs(save_dir, exist_ok=True)
    downloader = AndroidCrashDownloader(save_dir, reader)
    downloader.download_all()


def download_ios(save_dir):
    '''下载ios的crash'''
    data_pattern = "groupId=16&currentPage=1&pageSize=100&sort=&order=&product=20000048&locale=05&productId=20000048&localeId=05&startTime=2022-08-12%2000%3A00%3A00&endTime=2022-08-13%2023%3A59%3A59&rangeTime=&roleregistertime=&firstpaytime=&lastpaytime=&capricious=&myKeywords=&payStatus=&callStatus=&gameOrderType=&gameOrderInfoType=&isRepair=&platform=1&exceptionCode=&logClient=&operationLineId=&platformId=&advertiserCode=appsflyer&deviceGroupId=&mainChannel=&gameVersion=1.2.5&parentchannelId=&channelId=&subchannelId=&advertiserTo=&eventKey=&serverId=&propKey=&custom=&serviceType=&serviceText=&updateType=&detail=&userType=&transactionid=&userInfoType=&userInfoText=&interfaceLogtype=&bindtype=&deviceInfoType=&deviceInfoText=&cpuabi_like=&cpuabi_notlike=&packageStatus=&packageLogType=&giftInfoType=&giftInfoText=&payamount=&bindPhones=&bingEmails=&bindState=&closeState=&isTestUser=&status=0&operateType=0&operateTypeText=&signKeyValid=&signKey=&chatInfo=&payChannel=&is_first=&userId=&area=&server=&action=&subType=&fnInterface=&event=&adPlatform=&adName=&adGroup=&gameChannelId=&chatLogType=&auditStatus=&reservationUser=&reservationType=&hotEventType=&studiotag=&isstudio=&__mask__=false&totalCount=3845&queryFrom=1"
    reader = SimplePageReader(headers={
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "i18n-locale": "zh_CN",
        "request-locale": "05",
        "request-productid": "20000048",
        "token": "1216749c661dabae4ba098303e664e43fcd12016",
        "x-requested-with": "XMLHttpRequest"
    }, data_pattern=data_pattern)

    setup('settings.ini')
    os.makedirs(save_dir, exist_ok=True)
    downloader = IosCrashDownloader(save_dir, reader)
    downloader.download_all()


download_android('android-0812')
print('android-0812 done')
download_ios('ios-0812')
print('ios-0812 done')