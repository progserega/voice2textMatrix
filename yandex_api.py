#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import urllib.request
import json
import sys
import time
import jwt
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


def get_jwt_token(service_account_id,key_id,private_key_path):

  with open(private_key_path, 'r') as private:
    private_key = private.read() #.encode('utf-8') # Чтение закрытого ключа из файла.

  now = int(time.time())
  payload = {
  'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
  'iss': service_account_id,
  'iat': now,
  'exp': now + 360}

  # Формирование JWT.
  encoded_token = jwt.encode(\
    payload,\
    private_key,\
    algorithm='PS256',\
    headers={'kid': key_id})

  return encoded_token.decode('utf-8')


def getIAMtokenByJwt(log,jwt_token):
  log.debug("=start function=")
  #try:
  url="https://iam.api.cloud.yandex.net/iam/v1/tokens"

  data="{\"jwt\":\"%s\"}"%jwt_token
  post_data = data.encode('utf-8')

  print("post_data=",post_data)

  url_data = urllib.request.Request(url, data=post_data)
  url_data.add_header("Content-Type", "application/json")
  responseData = urllib.request.urlopen(url_data).read().decode('UTF-8')
  decodedData = json.loads(responseData)
  if decodedData.get("error_code") is None:
      log.info("token expiresAt: %s"%decodedData.get("expiresAt"))
      return(decodedData.get("iamToken"))
  else:
    log.error("get IAM-token from yandex by jwt")
    return None
  #except:
  #  log.error("api yandex error")
  #  return None

def voice2textLongAudioResult(log,job_id):
  global IAM_TOKEN
  url="https://operation.api.cloud.yandex.net/operations/%s"%job_id
  url_data = urllib.request.Request(url)
  url_data.add_header("Authorization", "Bearer %s" % IAM_TOKEN)
  responseData = urllib.request.urlopen(url_data).read().decode('UTF-8')
  data = json.loads(responseData)

  #print(json.dumps(data, indent=4, sort_keys=True,ensure_ascii=False))

  result_text=""
  if "done" in data:
    if data["done"]==True:
      for chank in data["response"]["chunks"]:
        result_text=result_text + " " + chank["alternatives"][0]["text"]
      return {"done":True, "result":result_text.strip()}
    else:
      log.info("need wait for result")
      return {"done":False, "result":None}
  
  log.error("get result")
  return None


def voice2textLongAudio(log,data):
  # doc: https://cloud.yandex.ru/docs/speechkit/stt/transcribation
  global FOLDER_ID
  global IAM_TOKEN
  log.debug("=start function=")
  for i in range(1,3):
    #try:
      if IAM_TOKEN==None:
        # только через сервисный аккаунт:
        jwt_token=get_jwt_token(conf.service_account_id, conf.service_account_key_id, conf.service_secret_key_path)
        if jwt_token==None:
          log.error("get jwt_token")
          return None
        log.debug("jwt token=%s"%jwt_token)
        IAM_TOKEN=getIAMtokenByJwt(log,jwt_token)
        if IAM_TOKEN==None:
          log.error("get IAM token from yandex by jwt")
          return None
        log.debug("get IAM_TOKEN by jwt: %s"%IAM_TOKEN)

      # TODO upload file to storage:
      base_url="https://storage.yandexcloud.net/"
      backet="voice2text"
      # Expires:

      t=time.mktime(time.gmtime())+1800 # храним 30 минут
      expires=time.ctime(t) + " GMT"
      #print("result: %s"%expires)
      #url.add_header("Expires", "Expires: %s" % expires)

      #sys.exit(0)

      # TODO sent to translate:
      params = "&".join([
          "topic=general",
          "folderId=%s" % FOLDER_ID,
          "lang=ru-RU"
      ])
      # set options:
      options={}
      options["config"]={}
      options["config"]["specification"]={}
      options["config"]["specification"]["languageCode"]="ru-RU"
      options["audio"]={}
      options["audio"]["uri"]="https://storage.yandexcloud.net/voice2text/EE117081C56E0A51BBA8A9AC1E394411.mpga.opus"
      #options["audio"]["uri"]="https://storage.yandexcloud.net/speechkit/speech.ogg"
      options_as_string=json.dumps(options, indent=4, sort_keys=True,ensure_ascii=False)
      options_as_data=bytearray(options_as_string, 'utf8')

      log.debug("IAM_TOKEN: %s"%IAM_TOKEN)
      url = urllib.request.Request("https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize" , data=options_as_data)
      url.add_header("Authorization", "Bearer %s" % IAM_TOKEN)

      responseData = urllib.request.urlopen(url).read().decode('UTF-8')
      decodedData = json.loads(responseData)

      print("decodedData: ",decodedData)

      if decodedData.get("error_code") is None:
          return(decodedData.get("id"))
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
  job_id=voice2textLongAudio(log,data)
  if job_id==None:
    log.error("error call testing function")
  else:
    # ждём результата:
    print("\nSuccess request, job_id='%s'"%job_id)
    time.sleep(3)
    for iteration in range(0,10):
      result=voice2textLongAudioResult(log,job_id)
      if result == None:
        log.error("error voice2textLongAudioResult()")
        sys.exit(1)
      else:
        if result["done"]==False:
          log.debug("need wait result...")
          time.sleep(iteration*10)
          continue
        else:
          log.info("result text = %s"%result)
          break

  log.info("Program exit!")
