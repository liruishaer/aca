# -*- coding: utf-8 -*-
import re
import os
import math
import pandas
import codecs
import numpy as np
import data_io
import urllib
import hashlib
import requests
import threading
import multiprocessing
from urllib.request import urlopen
from bs4 import BeautifulSoup as bs 

def get_search_page(search_url):
    """
    Return the search results of the given searching url.
    Including the info of results title, url, detail and if or not have fl(bool)
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
        html = requests.get(search_url, headers=headers, timeout=10)
        
        bsObj = bs(html.text)
        res = bsObj.findAll("div", {"class": "rc"})
        ans = []
        for i in res:
            sample = []
            sample.append(i.h3.a.text)
            temp = get_true_url(i.h3.a["href"])
            if temp == '':
                sample.append(i.h3.a["href"])
            else:
                sample.append(temp)
            if (i.find("span", {"class", "st"}) != None):
                sample.append(i.find("span", {"class": "st"}).text)
            else:
                sample.append('Nothing')
            temp = i.div.div.find("div", {"class": "slp f"})
            if temp == None:
                sample.append(1)
            elif temp.find("a", {"class": "fl"}) == None:
                sample.append(1) 
            else:
                sample.append(0)
            ans.append(sample)
        return ans

    except Exception as e:
      print(e)
      return []

def get_true_url(url):
    """
    Get the true url after redirecting. 
    """
    try:

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',\
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',\
                    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',\
                    'Accept-Encoding': 'gzip, deflate',\
                    'Referer': 'https://www.google.com/'}
        dlurl = requests.get(url, headers=headers, timeout=10)
        return dlurl.url
    except Exception as e:  
        print(e)
        return ''
    
def get_html_text(url):
    """
    Get the html text for given url
    """
    try:

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',\
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',\
                    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',\
                    'Accept-Encoding': 'gzip, deflate',\
                    'Referer': 'https://www.google.com/'}
        html = requests.get(url, headers=headers, timeout=10)
        return html.text
    except Exception as e:  
        print(e)
        return ''

def store_html_text(data, prefix='./webpage/'):
    """
    Store the html text. Check if there is a html file in disk, if not get html text and store it.
    Input:  data - list of [id, url]
    """
    filename = hashlib.md5(data[1].encode('utf-8')).hexdigest()
    if not os.path.isfile(prefix + filename):
        html_text = get_html_text(data[1])
        if html_text == '':
            return False
        else:
            with codecs.open(prefix + filename, 'w', 'utf-8') as f:
                f.write(html_text)
            return True
def store_html_single_thread(data, prefix='./webpage/'):
    for i in data:
        store_html_text(i, prefix=prefix)

def store_multi_thread(data, threads=10, prefix='./webpage/'):
    """
    Execute task using threadings
    """
    num = len(data)
    chunk = math.ceil(num / threads)
    splited_data = [[] for i in range(threads)]
    for i, r in data.iterrows():
        splited_data[i % threads].append([r['id'], r['homepage']])
        
    print('Data split done')
    # multi thread
    threads = []
    for i in splited_data:
        t = threading.Thread(target=store_html_single_thread,
        args=(i, prefix))
        threads.append(t)
    for i in threads:
        i.start()
    for i in threads:
        i.join()
    


def get_pic_url(html, url):
    """
    Return the url of pics of given page text
    """
    try:
        pattern = re.compile(r'src="([^<> \t\r\n]+?\.(jpg|png|gif))"')
        # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
        # html = requests.get(url, headers=headers, timeout=5)
        img_list = pattern.findall(html)
        img_list = list(set(list([i[0] for i in img_list])))
        # img_list = list(filter(lambda x : ('email' not in x) and ('logo' not in x), [i[0] for i in img_list]))
        # return img_list
        for i in range(len(img_list)):
            if not img_list[i].startswith('http'):
                root_url_p = re.compile(r'http[s]?:\/\/[^/]*\/')
                root_url = root_url_p.findall(url)
                if len(root_url) > 0:
                    if img_list[i].startswith('./'):
                        img_list[i] = root_url[0] + img_list[i][2:]
                    elif img_list[i].startswith('/'):
                        img_list[i] = root_url[0] + img_list[i][1:]
                    elif img_list[i].startswith('../'):
                        img_list[i] = root_url[0] + img_list[i][3:]
                    elif img_list[i].startswith('../../'):
                        img_list[i] = root_url[0] + img_list[i][6:]
                    else:
                        img_list[i] = root_url[0] + img_list[i]
        return img_list
    except Exception as e:
        print(e)
        return []

def get_gender_name_single_page(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
    try:
        html = requests.get(url, headers=headers, timeout=5)
        bsObj = bs(html.text)
        name_list = [i.text for i in bsObj.findAll("span", {"class": "result-name"})]
        return name_list
    except Exception as e:
        print(e)
        return []
def get_gender_name():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
        boy_url = 'http://www.babynames.net/boy?page='
        girl_url = 'http://www.babynames.net/girl?page='
        boys_name = set()
        girls_name = set()
        for i in range(1, 462):
            boys_name.update(get_gender_name_single_page(boy_url + str(i)))
        for i in range(1, 316):
            girls_name.update(get_gender_name_single_page(girl_url + str(i)))
        neuter_name = boys_name & girls_name
        boys_name = boys_name - neuter_name
        girls_name = girls_name - neuter_name
        return boys_name, girls_name
    except Exception as e:
        print(e)
        return [['Error'], ['Error']]