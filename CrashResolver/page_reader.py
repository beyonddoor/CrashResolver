'''读取分页的数据，解析为json'''

from abc import abstractmethod


class PageReader:
    '''读取指定的page'''
    @abstractmethod
    def read_page(self, page):
        '''读取指定的page'''
