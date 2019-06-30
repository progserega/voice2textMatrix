#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import urllib.request
import json
import sys
import config as conf

# Идентификатор каталога
FOLDER_ID = conf.folder_id
# IAM-токен
# FIXME remove
IAM_TOKEN = conf.IAM_TOKEN

def getIAMtoken(log,oauth):
  try:
    url="https://iam.api.cloud.yandex.net/iam/v1/tokens"

    data="{\"yandexPassportOauthToken\":\"%s\"}"%oauth
    post_data = data.encode('utf-8')

    url_data = urllib.request.Request(url, data=post_data)
    responseData = urllib.request.urlopen(url_data).read().decode('UTF-8')
    decodedData = json.loads(responseData)
    if decodedData.get("error_code") is None:
        return(decodedData.get("iamToken"))
    else:
      log.error("get IAM-token from yandex")
      return None
  except:
    log.error("api yandex error")
    return None

def voice2text(log,data):
  global FOLDER_ID
  global IAM_TOKEN
  try:
    #if IAM_TOKEN==None:
    #  IAM_TOKEN=getIAMtoken(log,conf.oauth)
    #  if IAM_TOKEN==None:
    #    log.error("get IAM token from yandex")
    #    return None

    params = "&".join([
        "topic=general",
        "folderId=%s" % FOLDER_ID,
        "lang=ru-RU"
    ])
    url = urllib.request.Request("https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?%s" % params, data=data)
    url.add_header("Authorization", "Bearer %s" % IAM_TOKEN)

    responseData = urllib.request.urlopen(url).read().decode('UTF-8')
    decodedData = json.loads(responseData)

    if decodedData.get("error_code") is None:
        return(decodedData.get("result"))
    else:
      log.error("api yandex error")
      return None
  except:
    log.error("api yandex error")
    return None
