#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import urllib.request
import json
import sys
import config as conf

# Идентификатор каталога
FOLDER_ID = conf.FOLDER_ID
# IAM-токен
IAM_TOKEN = conf.IAM_TOKEN

def voice2text(log,data):
  global FOLDER_ID
  global IAM_TOKEN

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

