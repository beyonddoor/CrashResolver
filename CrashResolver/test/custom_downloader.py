'''自定义条件的的downloader'''

from ..setup import setup
from ..downloader import AndroidCrashDownloader
from ..page_query import SimplePageReader


data_pattern = "groupId=16&currentPage=?????&pageSize=100&sort=&order=&product=20000048&locale=01&productId=20000048&localeId=01&startTime=2022-06-01%2000%3A00%3A00&endTime=2022-06-17%2023%3A59%3A59&rangeTime=&roleregistertime=&firstpaytime=&lastpaytime=&capricious=&myKeywords=&payStatus=&callStatus=&gameOrderType=&gameOrderInfoType=&isRepair=&platform=&exceptionCode=&logClient=&operationLineId=31014300000&platformId=0&advertiserCode=appsflyer&deviceGroupId=&mainChannel=&gameVersion=&parentchannelId=&channelId=&subchannelId=&advertiserTo=&eventKey=&serverId=&propKey=&custom=&serviceType=&serviceText=&updateType=&detail=&userType=&transactionid=&userInfoType=&userInfoText=&interfaceLogtype=&bindtype=&deviceInfoType=&deviceInfoText=&cpuabi_like=&cpuabi_notlike=&packageStatus=&packageLogType=&giftInfoType=&giftInfoText=&payamount=&bindPhones=&bingEmails=&bindState=&closeState=&isTestUser=&status=0&operateType=0&operateTypeText=&signKeyValid=&signKey=&chatInfo=&payChannel=&is_first=&userId=&area=&server=&action=&subType=&fnInterface=&event=&adPlatform=&adName=&adGroup=&gameChannelId=&chatLogType=&auditStatus=&reservationUser=&reservationType=&hotEventType=&studiotag=&isstudio=&__mask__=false&totalCount=180&queryFrom=1"
reader = SimplePageReader(headers={
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "content-type": "application/x-www-form-urlencoded",
    "i18n-locale": "zh_CN",
    "request-locale": "01",
    "request-productid": "20000048",
    "token": "0516f4da0ee0a5604e448a61eaab983061771014",
    "x-requested-with": "XMLHttpRequest"
}, data_pattern=data_pattern,page_str='?????')

setup('settings.ini')
downloader = AndroidCrashDownloader('test', reader)
downloader.download_all()
