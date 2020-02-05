#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import time
import json
import sqlite3
import logging
import collections
import jwt
import img2pdf
import requests
from urllib import parse

succ=False
def getmidstring(html, start_str, end):
    start = html.find(start_str)
    if start >= 0:
        start += len(start_str)
        end = html.find(end, start)
        if end >= 0:
            return html[start:end].strip()
    return ""
def gettoken():
    global HEADERS
    print("Reboot...")
    s=requests.session()
    headers2={
    "Accept":"application/json, text/javascript, */*; q=0.01",
    "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8",
    "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
    "Origin":"http://open.izhixue.cn",
    "Referer":"http://open.izhixue.cn/oauth/authorize?response_type=code&client_id=wqxuetang&redirect_uri=https%3A%2F%2Fwww.wqxuetang.com%2Fv1%2Flogin%2Fcallbackwq&scope=userinfo&state=https%3A%2F%2Flib-nuanxin.wqxuetang.com%2F%23%2F",
    "User-Agent":"Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36"
    }
    r=s.post("http://open.izhixue.cn/checklogin?response_type=code&client_id=wqxuetang&redirect_uri=https%3A%2F%2Fwww.wqxuetang.com%2Fv1%2Flogin%2Fcallbackwq&scope=userinfo&state=https%3A%2F%2Flib-nuanxin.wqxuetang.com%2F%23%2F",{"account":"手机号/邮箱","password":"密码"},headers=headers2)
    # 请自行替换上面的账号和密码
    tmp=parse.unquote(parse.unquote(r.text))
    url=getmidstring(tmp,'"data":"','"}')
    s.get(url)
    cookies=s.cookies.get_dict()
    res=""
    for x in cookies.keys() :
        res=res+x+"="+cookies[x]+"; "
    print(res)
    HEADERS['Cookie']=res
class TryAgain(ValueError):
    pass
class APIError(ValueError):
    pass
try:
    from httpx import Client as Session
except ImportError:
    from requests import Session
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Referer": "https://lib-nuanxin.wqxuetang.com/read/pdf/2175744",
    "Cookie": "",
    'referer':'',
    'sec-fetch-mode': 'no-cors',
    'sec-fetch-site': 'same-origin'
}
re_author = re.compile(r'《.+?》\s*(.+?)\s*【')
logging.basicConfig(stream=sys.stderr, format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)
class WQXTDownloader:
    baseurl = 'https://lib-nuanxin.wqxuetang.com/read/pdf/'
    jwt_secret = "g0NnWdSE8qEjdMD8a1aq12qEYphwErKctvfd3IktWHWiOBpVsgkecur38aBRPn2w"
    loading_img = '3f08d2c4b0d8cac7641730c7f27f7263c8687bc67cdf179de6996edb9d8409bf09664e035b56d72c00d0b46d8dca1868a48290f469064efd5ba611958fe614e1'
    def __init__(self, downloadpath='.', db='wqxt.db'):
        self.downloadpath = downloadpath
        self.db = sqlite3.connect(db)
        self.session = Session()
        self.session.headers.update(HEADERS)
        self.init_db()
    def init_db(self):
        cur = self.db.cursor()
        cur.execute('PRAGMA case_sensitive_like=1')
        cur.execute('CREATE TABLE IF NOT EXISTS api_cache ('
            'url TEXT PRIMARY KEY,'
            'updated INTEGER,'
            'value TEXT'
        ')')
        cur.execute('CREATE TABLE IF NOT EXISTS book_img ('
            'bookid INTEGER,'
            'page INTEGER,'
            'updated INTEGER,'
            'data BLOB,'
            'PRIMARY KEY (bookid, page)'
        ')')
        self.db.commit()
    def json_call(self, bookid, url, cache=True):
        global HEADERS
        HEADERS['referer']=self.baseurl + str(bookid)
        cur = self.db.cursor()
        url = url % bookid
        if cache:
            cur.execute('SELECT value FROM api_cache WHERE url=?', (url,))
            res = cur.fetchone()
            if res:
                return json.loads(res[0])
        r = self.session.get(url, headers=HEADERS,timeout=30)
        r.raise_for_status()
        result = r.json()
        #print(result)
        if result['errcode']!=0:
            name = url.rsplit('/', 1)[-1]
            gettoken()
        cur.execute('REPLACE INTO api_cache VALUES (?,?,?)', (
            url, int(time.time()), json.dumps(result['data'])))
        self.db.commit()
        return result['data']
    def get_img(self, bookid, page, jwtkey):
        global HEADERS
        cur_time = time.time()
        jwttoken = jwt.encode({
            "p": page,
            "t": int(cur_time*1000),
            "b": str(bookid),
            "w": 1000,
            "k": json.dumps(jwtkey),
            "iat": int(cur_time)
        }, self.jwt_secret, algorithm='HS256').decode('ascii')
        HEADERS['referer']="https://lib-nuanxin.wqxuetang.com/read/pdf/" + str(bookid)
        try:
            r = self.session.get(
            "https://lib-nuanxin.wqxuetang.com/page/img/%s/%s?k=%s" % (
            bookid, page, jwttoken), headers=HEADERS)
            #print(HEADERS)
            #os._exit(0)
            result = r.content
            while r.headers.get('pragma') != 'catch':
                #print("Sleep...")
                #time.sleep(61)
                print(HEADERS)
                with open("err.jpg","wb") as f:
                    f.write(result)
                print("https://lib-nuanxin.wqxuetang.com/page/img/%s/%s?k=%s" % (bookid, page, jwttoken))
                #os._exit(0)
                raise TryAgain()
        except:
            print("https://lib-nuanxin.wqxuetang.com/page/img/%s/%s?k=%s" % (bookid, page, jwttoken))
        return result
    def download_pdf(self, bookid, convertimg=False):
        global succ
        global alldone
        logging.info('%s: Loading metadata', bookid)
        try:
            r = self.session.get(self.baseurl + str(bookid))
            r.raise_for_status()
            metadata = self.json_call(bookid, "https://lib-nuanxin.wqxuetang.com/v1/read/initread?bid=%s")
            title = metadata['name'].replace("/","&").replace(":","")
        except Exception as e:
            print(str(e))
            alldone=False
            return 0
        try:
            os.mkdir("%s-%s" % (bookid, title))
        except:
            pass
        try:
            author = re_author.match(metadata['title']).group(1)
        except Exception:
            author = None
        try:
            contents = self.json_call(bookid, "https://lib-nuanxin.wqxuetang.com/v1/book/catatree?bid=%s")
            sizes = self.json_call(bookid, "https://lib-nuanxin.wqxuetang.com/page/size/?bid=%s")
            jwtkey = self.json_call(bookid, "https://lib-nuanxin.wqxuetang.com/v1/read/k?bid=%s", cache=False)
            page_num = int(metadata['pages'])
        except Exception as e:
            #exit()
            print("https://lib-nuanxin.wqxuetang.com/v1/read/k?bid="+str(bookid)+"  ERROR")
            print(str(e))
            #gettoken()
            alldone=False
            return 0
        images = [None] * page_num
        tasks = collections.deque(range(1, page_num+1))
        while tasks:
            i = tasks.popleft()
            if os.path.exists("%s-%s\%s.jpg" % (bookid, title,i))==False:
                alldone=False
                try:
                    img = self.get_img(bookid, i, jwtkey)
                    logging.info('%s: %s/%s', bookid, i, page_num)
                    with open("%s-%s\%s.jpg" % (bookid, title,i), "wb") as f:
                        f.write(img)
                    succ=True
                    #time.sleep(2)
                except TryAgain:
                    logging.info('%s: %s/%s not loaded', bookid, i, page_num)
                    alldone=False
                    break
                except APIError:
                    gettoken()
                except Exception:
                    logging.exception('%s: %s/%s', bookid, i, page_num)
                    pass
alldone=False

if __name__ == '__main__':
    # usage: python3 crawl_wqxt.py <book_id>
    dl = WQXTDownloader()
    a=sys.argv[1]
    gettoken()
    while alldone==False:
      alldone=True
      for i in a:
        logging.info('%s/%s', a.index(i)+1, len(a))
        dl.download_pdf(i)
    if alldone==True:
        input("OK")
