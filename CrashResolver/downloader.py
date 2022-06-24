
import logging
import requests
import pathlib
import argparse

from . import config
from . import setup

logger = logging.getLogger(__name__)

class CrashDownloader:
    '''
    从crash repo获取所有的crash文件，进行分析
    '''
    
    def __init__(self, save_dir, start_time, end_time, page_size) -> None:
        self._save_dir = save_dir
        self._start_time = start_time
        self._end_time = end_time
        self._total_page = None
        self._page_size = page_size
    
    def download(self, page):
        data = f'groupId=16&currentPage={page}&pageSize={self._page_size}&sort=&order=&product=20000048&locale=01&productId=20000048&localeId=01&startTime={self._start_time}%2000%3A00%3A00&endTime={self._end_time}%2023%3A59%3A59&rangeTime=%E4%BB%8A%E5%A4%A9&roleregistertime=&firstpaytime=&lastpaytime=&capricious=&myKeywords=&payStatus=&callStatus=&gameOrderType=&gameOrderInfoType=&isRepair=&platform=1&exceptionCode=&logClient=&operationLineId=&platformId=&advertiserCode=appsflyer&deviceGroupId=&mainChannel=&gameVersion=&parentchannelId=&channelId=&subchannelId=&advertiserTo=&eventKey=&serverId=&propKey=&custom=&serviceType=&serviceText=&updateType=&detail=&userType=&transactionid=&userInfoType=&userInfoText=&deviceInfoType=&deviceInfoText=&packageStatus=&packageLogType=&giftInfoType=&giftInfoText=&payamount=&bindPhones=&bingEmails=&bindState=&closeState=&isTestUser=&status=0&operateType=0&operateTypeText=&signKeyValid=&signKey=&chatInfo=&payChannel=&is_first=&userId=&area=&server=&action=&subType=&fnInterface=&event=&adPlatform=&adName=&adGroup=&gameChannelId=&chatLogType=&auditStatus=&reservationUser=&reservationType=&hotEventType=&studiotag=&isstudio=&__mask__=false&totalCount=52&queryFrom=1'

        response = requests.post(url=config.CrashRepoUrl, headers={
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "i18n-locale": "zh_CN",
            "request-locale": "01",
            "request-productid": "20000048",
            "token": "21102dfc420cc6984ce6b9c044524e30c30e3656",
            "x-requested-with": "XMLHttpRequest"
        }, data=data)

        save_dir = pathlib.Path(self._save_dir)
        json_data = response.json()
        self._total_page = json_data['data']['totalPage']

        for crash_data in json_data['data']['list']:
            crash_url = crash_data['crashurl']
            end_pos = crash_url.rfind('/', 0)
            start_pos = crash_url.rfind('/', 0, end_pos)
            filename = crash_url[start_pos+1:end_pos]
            path = save_dir / (filename + config.CrashExt)
            logger.info('download file ', crash_url, filename)

            if path.exists():
                logger.info('file exists, skip ', filename)
                continue

            with open(path, 'wb') as file:
                file.write(requests.get(crash_url).content)

    def download_all(self):
        self.download(1)
        for i in range(2, self._total_page+1):
            self.download(i)

def do_fetch(args):
    downloader = CrashDownloader(args.save_dir, args.start_time, args.end_time, args.page_size)
    if args.page >= 0:
        downloader.download(args.page)
    else:
        downloader.download_all()

def _do_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--setting_file', help='setting file', default='setting.ini')
    
    parser.add_argument('save_dir', help='save directory for crash files')
    parser.add_argument('--start_time', help='start time', default='2022-06-20')
    parser.add_argument('--end_time', help='end time', default='2022-06-21')
    parser.add_argument('--page', help='page number, if -1 then all pages will be downloaded', default=1, type=int)
    parser.add_argument('--page_size', help='page size', default=100, type=int)
    parser.set_defaults(func=do_fetch)
    
    args = parser.parse_args()
    setup.setup(args.setting_file)
    logger.info('test')
    args.func(args)

if __name__ == '__main__':
    _do_parse_args()