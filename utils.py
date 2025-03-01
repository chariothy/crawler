import sys, os
from datetime import datetime as dt, date, timedelta, time as _time
from typing import Pattern
from pybeans import AppTool
import json
import time
import random
import io

class CrawlerUtil(AppTool):
    """
    蜘蛛公用代码
    """
    def __init__(self, spider_name):
        super(CrawlerUtil, self).__init__(spider_name)
        self._session = None


    @property
    def session(self):
        """
        Lazy loading
        """
        if self._session:
            return self._session
        assert(self['mysql'] is not None)
        DB_CONN = 'mysql+mysqlconnector://{c[user]}:{c[pwd]}@{c[host]}:{c[port]}/{c[db]}?ssl_disabled=True' \
            .format(c=self['mysql'])
        engine = create_engine(
            DB_CONN, 
            pool_size=20, 
            max_overflow=0, 
            echo=self['log.sql'] == 1,
            json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False))
        self._session = sessionmaker(bind=engine)()
        return self._session

    def fail(self, **kwargs):
        #self.E(kwargs)
        assert 'failure' in kwargs \
            and 'request_url' in kwargs \
            and 'response_url' in kwargs \
            and 'cookies' in kwargs \
            and 'headers' in kwargs \
            and 'body' in kwargs \
            and 'status' in kwargs \
            and 'meta' in kwargs
        
        failure = kwargs['failure']
        if isinstance(failure.value, CloseSpider):
            msg = failure.value.reason
        else:
            msg = '{}: {}'.format(failure.value.__class__.__name__, failure.value)
        subject = f'[TRAPPED ERROR] {msg}'
        body = subject +  '\n' \
            + '\n> ----------------------------------------------------------------------------' \
            + '\n> Request  Url: ' + kwargs['request_url'] \
            + '\n> Response Url: ' + kwargs['response_url'] \
            + '\n> Cookies     : ' + json.dumps(kwargs['cookies'], ensure_ascii=False, indent=2) \
            + '\n> Headers     : ' + json.dumps(kwargs['headers'], ensure_ascii=False, indent=2) \
            + '\n> Request Body: ' + str(kwargs['body']) \
            + '\n> Status      : ' + str(kwargs['status']) \
            + '\n> Meta        : ' + json.dumps(kwargs['meta'], ensure_ascii=False, indent=2)
        if 'item' in kwargs:
            body += '\n> Item        : ' + json.dumps(kwargs['item'], ensure_ascii=False, indent=2)
        body += '\n> ' + failure.getTraceback()
        body += '\n> ----------------------------------------------------------------------------'
        self.print('FATAL', body)
        
        try:
            self.send_email(subject, body)
        except Exception as ex:
            body += '\n发送错误邮件时出错：{}'.format(ex)
            
        try:
            self.ding(subject, '\n'.join((f'- {c}' for c in body.split('\n'))))
        except Exception as ex:
            body += '\n发送错误消息时出错：{}'.format(ex)
            
        raise CloseSpider(subject)
    
    

    def random(self):
        return random.Random().random()
    
    
    def ding(self, title: str, text: str):
        result = notify_by_ding_talk(self['dingtalk'], title, text)
        self.D(result)
        
        
    def sleep(self, sec=3):
        time.sleep(sec)
        
    
    def timestamp(self):
        return time.time_ns()
    
    
    def env(self, key:str='ENV', default=''):
        env = os.environ.get(key, default=default)
        self.D(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ENV = {env} <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        return env
    
    
    def convert_date_str(self, date_str:str, from_format:str='%Y/%m/%d', to_format='%Y-%m-%d') -> str:
        a_date = dt.strptime(date_str,from_format).date()
        return dt.strftime(a_date,to_format)
    
        
    def extract_str(self, reg:Pattern, content:str, default=None):
        """从字符串中提取文本信息

        Args:
            reg (Pattern): 编译后的正则对象
            content (str): 要提取内容的字符串
            default (str|None)
        """
        match = reg.search(content)
        if match:
            groups = match.groups()
            if groups:
                return groups[0].strip()
            else:
                return default
        else:
            return default
    