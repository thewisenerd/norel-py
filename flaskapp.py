from flask import Flask, request

import logging
from logging.handlers import RotatingFileHandler

import base64
import binascii
import json
import re

import requests
from   requests.adapters import HTTPAdapter
import requesocks

app = Flask(__name__)

def getProxy():
  r = requests.get('http://gimmeproxy.com/api/getProxy')
  if r.status_code != 200:
    return False
  j = r.json()
  if j.has_key('error'):
    return False
  return j

err_list = {}

def pusherrors():
  global err_list
  err_list['E_UNKNOWN']        = {'code' :  '1', 'shortcode' : 'E_UNKNOWN'       , 'msg' : "unknown error occoured"};
  err_list['E_UNKNOWN_ACTION'] = {'code' : '-1', 'shortcode' : 'E_UNKNOWN_ACTION', 'msg' : "cannot understand action.usage: /?url=<base64 encoded url>"};
  err_list['E_NO_PROXY']       = {'code' : '-2', 'shortcode' : 'E_NO_PROXY'      , 'msg' : "no proxy found"};
  err_list['E_CONNECT_FAIL']   = {'code' : '-3', 'shortcode' : 'E_CONNECT_FAIL'  , 'msg' : "failed to connect"};
  err_list['E_DECODE_ERR']     = {'code' : '-4', 'shortcode' : 'E_DECODE_ERR'    , 'msg' : "decode url fail"};
  err_list['E_INVALID_URL']    = {'code' : '-5', 'shortcode' : 'E_INVALID_URL'   , 'msg' : "invalid decoded url"};

def getURL(url, proxy):
  s = None
  if proxy['type'] in ["socks4", "socks5"]:
    s = requesocks.session()
  else:
    s = requests.session()

  s.proxies = {'http': proxy['curl'], 'https': proxy['curl']};

  headers = {
    'User-Agent:': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
  }

  try:
    r = s.get(url, headers=headers, verify=False, timeout=5)
  except (requests.exceptions.RequestException, requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
    return json.dumps(err_list['E_CONNECT_FAIL'])

  return r.text

@app.route('/')
def norel():
  url = request.args.get('url')
  if url == None:
    ret = err_list['E_UNKNOWN_ACTION']
    return json.dumps(ret)

  try:
    url = base64.decodestring(url)
  except binascii.Error:
    ret = err_list['E_DECODE_ERR']
    return json.dumps(ret)

  t = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url)
  if (len(t) != 1):
    ret = err_list['E_INVALID_URL']
    return json.dumps(ret)

  random_proxy = getProxy()

  if random_proxy == False:
    ret = err_list['E_NO_PROXY']
    return json.dumps(ret)

  return getURL(url, random_proxy)

@app.errorhandler(500)
def error500(error):
  return json.dumps(err_list['E_UNKNOWN'])

if __name__ == '__main__':
  pusherrors()
  app.debug = True
  app.run()