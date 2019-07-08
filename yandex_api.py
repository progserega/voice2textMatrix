#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import urllib.request
import json
import sys
import time
import logging
import config as conf

# Идентификатор каталога
FOLDER_ID = conf.folder_id
# IAM-токен
IAM_TOKEN = None

def getIAMtoken(log,oauth):
  log.debug("=start function=")
  try:
    url="https://iam.api.cloud.yandex.net/iam/v1/tokens"

    data="{\"yandexPassportOauthToken\":\"%s\"}"%oauth
    post_data = data.encode('utf-8')

    url_data = urllib.request.Request(url, data=post_data)
    responseData = urllib.request.urlopen(url_data).read().decode('UTF-8')
    decodedData = json.loads(responseData)
    if decodedData.get("error_code") is None:
        log.info("token expiresAt: %s"%decodedData.get("expiresAt"))
        return(decodedData.get("iamToken"))
    else:
      log.error("get IAM-token from yandex")
      return None
  except:
    log.error("api yandex error")
    return None

def voice2textShortAudio(log,data):
  global FOLDER_ID
  global IAM_TOKEN
  log.debug("=start function=")
  for i in range(1,3):
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
    except urllib.error.HTTPError as e:
      if e.code == 401 and 'Unauthorized' in str(e):
        log.warning(str(e))
        log.info("try update IAM token")
        IAM_TOKEN=getIAMtoken(log,conf.oauth)
        if IAM_TOKEN == None:
          log.error("getIAMtoken() - exit")
          return None
        else:
          # токен получен - пробуем ещё раз:
          log.info("success get IAM token")
          log.info("after get IAM token - try call api again")
          continue
    except Exception as e:
      log.error("unknown api yandex error: %s"%str(e))
      return None

  log.error("try 3 call yandex-api - no success - skip trying")
  return None

def voice2textLongAudio(log,data):
  global FOLDER_ID
  global IAM_TOKEN
  log.debug("=start function=")
  for i in range(1,3):
    #try:
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

      # TODO upload file to storage:
      # Expires:
      t=time.mktime(time.gmtime())+1800 # храним 30 минут
      expires=time.ctime(t) + " GMT"
      #print("result: %s"%expires)
      #url.add_header("Expires", "Expires: %s" % expires)

      # TODO sent to translate:
      # set options:
      options={}
      options["config"]={}
      options["config"]["specification"]={}
      options["config"]["specification"]["languageCode"]="ru-RU"
      options["audio"]={}
      #options["audio"]["uri"]="https://storage.yandexcloud.net/voice2text/test.3gpp"
      options["audio"]["uri"]="https://storage.yandexcloud.net/speechkit/speech.ogg"
      options_as_string=json.dumps(options, indent=4, sort_keys=True,ensure_ascii=False)
      options_as_data=bytearray(options_as_string, 'utf8')

      # FIXME убрать получение токена:
      IAM_TOKEN=getIAMtoken(log,conf.oauth)
      log.debug("IAM_TOKEN: %s"%IAM_TOKEN)
      url = urllib.request.Request("https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize" , data=options_as_data)
      url.add_header("Authorization", "Bearer %s" % IAM_TOKEN)

      responseData = urllib.request.urlopen(url).read().decode('UTF-8')
      decodedData = json.loads(responseData)

      if decodedData.get("error_code") is None:
          return(decodedData.get("result"))
      else:
        log.error("api yandex error")
        return None


    #except urllib.error.HTTPError as e:
    #  if e.code == 401 and 'Unauthorized' in str(e):
    #    log.warning(str(e))
    #    log.info("try update IAM token")
    #    IAM_TOKEN=getIAMtoken(log,conf.oauth)
    #    if IAM_TOKEN == None:
    #      log.error("getIAMtoken() - exit")
    #      return None
    #    else:
    #      # токен получен - пробуем ещё раз:
    #      log.info("success get IAM token")
    #      log.info("after get IAM token - try call api again")
    #      continue
    #except Exception as e:
    #  log.error("unknown api yandex error: %s"%str(e))
    #  return None

  #log.error("try 3 call yandex-api - no success - skip trying")
  #return None


if __name__ == '__main__':
  log= logging.getLogger("yandex_api")
  if conf.debug:
    log.setLevel(logging.DEBUG)
  else:
    log.setLevel(logging.INFO)

  # create the logging file handler
  fh = logging.FileHandler(conf.log_path)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s() %(levelname)s - %(message)s')
  fh.setFormatter(formatter)

  if conf.debug:
    # логирование в консоль:
    #stdout = logging.FileHandler("/dev/stdout")
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(formatter)
    log.addHandler(stdout)

  # add handler to logger object
  log.addHandler(fh)

  log.info("Program started")

  f=open("test.3gpp","br")
  data=f.read()
  f.close()

  #text=voice2textShortAudio(log,data)
  text=voice2textLongAudio(log,data)
  if text==None:
    log.error("error call testing function")
  else:
    print("\nSuccess result: '%s'"%text)

  log.info("Program exit!")
