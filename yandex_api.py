#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import urllib.request
import random
import json
import sys
import time
import jwt
import logging
import traceback
import config as conf
import boto3

# Идентификатор каталога
FOLDER_ID = conf.folder_id
# IAM-токен
IAM_TOKEN = None

def get_exception_traceback_descr(e):
  tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
  result=""
  for msg in tb_str:
    result+=msg
  return result

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
  except Exception as e:
    log.error(get_exception_traceback_descr(e))
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
      log.error(get_exception_traceback_descr(e))
      log.error("unknown api yandex error: %s"%str(e))
      return None

  log.error("try 3 call yandex-api - no success - skip trying")
  return None


def get_jwt_token(log,service_account_id,key_id,private_key_path):
  log.debug("=start function=")

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

def upload_file_to_cloud(log,bucket_name,data):
  log.debug("=start function=")
  try:
    session = boto3.session.Session()
    s3 = session.client(service_name='s3', endpoint_url='https://storage.yandexcloud.net' )

    exist_file_list=[]
    file_name=None
    ret_data=s3.list_objects(Bucket=bucket_name)
    log.debug("s3.list_objects return data:")
    log.debug(ret_data)
      
    if 'ResponseMetadata' not in ret_data:
      log.error("can not find 'ResponseMetadata' in s3 ret_data - yandex.storage error get files")
      log.error("return data:")
      log.error(ret_data)
      return None

    if 'HTTPStatusCode' not in ret_data['ResponseMetadata']:
      log.error("can not find 'HTTPStatusCode' in s3 ret_data - yandex.storage error get files")
      log.error("return data:")
      log.error(ret_data)
      return None

    if ret_data['ResponseMetadata']['HTTPStatusCode'] != 200:
      log.error(" ret_data['ResponseMetadata']['HTTPStatusCode'] != 200 in s3 ret_data - yandex.storage error get files")
      log.error("return data:")
      log.error(ret_data)
      return None

    # если 'Contents' нет в ret_data - значит в хранилище нет ни одного файла - это нормально - пропускаем:
    if 'Contents' in ret_data:
      for key in ret_data['Contents']:
        exist_file_list.append(key['Key'])

    for iteration in range(0,300):
      random_id=random.randint(0,4294967296)
      file_name="voice2textMatrix_data%d.oga"%random_id
      if file_name not in exist_file_list:
        break
      else:
        file_name=None
    if file_name==None:
      log.error("create uniq file_name in yandex storage")
      return None

    ## Из строки
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=data, StorageClass='COLD')
    ## Из файла
    #s3.upload_file('this_script.py', 'bucket-name', 'py_script.py')
    return "https://storage.yandexcloud.net/%s/%s"%(bucket_name,file_name)
  except Exception as e:
    log.error(get_exception_traceback_descr(e))
    log.error("error s3.put_object() - fail load file to yandex store")
    return None

def getIAMtokenByJwt(log,jwt_token):
  log.debug("=start function=")
  try:
    url="https://iam.api.cloud.yandex.net/iam/v1/tokens"

    data="{\"jwt\":\"%s\"}"%jwt_token
    post_data = data.encode('utf-8')

    #print("post_data=",post_data)

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
  except Exception as e:
    log.error(get_exception_traceback_descr(e))
    log.error("api yandex error - fail get IAM token by Jwt")
    return None

def voice2textLongAudioResult(log,job_id):
  global IAM_TOKEN
  log.debug("=start function=")
  i=0
  for i in range(1,5):
    try:
      log.info("start get result translate step trying = %d"%i)

      url="https://operation.api.cloud.yandex.net/operations/%s"%job_id
      log.debug("try create request result...")
      url_data = urllib.request.Request(url)
      url_data.add_header("Authorization", "Bearer %s" % IAM_TOKEN)
      log.debug("success create request result")
      log.debug("try request result...")
      responseData = urllib.request.urlopen(url_data).read().decode('UTF-8')
      log.debug("done request result")

      if responseData == None:
        log.error("request return None - exit")
        return None

      log.debug("try load json...")
      data = json.loads(responseData)
      #print(json.dumps(data, indent=4, sort_keys=True,ensure_ascii=False))
      log.debug("success load json")

      result_text=""
      if "done" in data:
        if data["done"]==True:
          for chank in data["response"]["chunks"]:
            result_text=result_text + " " + chank["alternatives"][0]["text"]
          return {"done":True, "result":result_text.strip()}
        else:
          log.info("need wait for result")
          return {"done":False, "result":None}
      else:
        log.warning("no 'done' in result - try again....")

      log.debug("some error - try again....")
      time.sleep(3)

    except urllib.error.HTTPError as e:
      if e.code == 401 and 'Unauthorized' in str(e):
        log.warning(str(e))
        log.info("try update IAM token")
        # только через сервисный аккаунт:
        jwt_token=get_jwt_token(log,conf.service_account_id, conf.service_account_key_id, conf.service_secret_key_path)
        if jwt_token==None:
          log.error("get jwt_token")
          return None
        log.debug("jwt token=%s"%jwt_token)
        IAM_TOKEN=getIAMtokenByJwt(log,jwt_token)
        if IAM_TOKEN==None:
          log.error("get IAM token from yandex by jwt")
          return None
        # токен получен - пробуем ещё раз:
        log.debug("success get IAM_TOKEN by jwt: %s"%IAM_TOKEN)
        log.info("after get IAM token - try call api again")
        continue
      else:
        log.warning(str(e))
        log.warning("try again...")
        continue

    except Exception as e:
      log.error(get_exception_traceback_descr(e))
      log.error("unknown api yandex error: %s"%str(e))
      return None

  log.error("try 3 call yandex-api - no success - skip trying (i=%d)"%i)
  return {"done":False, "result":None}

def voice2textLongAudioAddRequest(log,data):
  # doc: https://cloud.yandex.ru/docs/speechkit/stt/transcribation
  global FOLDER_ID
  global IAM_TOKEN
  log.debug("=start function=")
  file_url=None

  for i in range(1,5):
    log.info("start upload step trying = %d"%i)
    try:
      # upload file to storage:
      log.debug("try upload_file_to_cloud()")
      file_url=upload_file_to_cloud(log,conf.bucket_name,data)
      if file_url==None:
        log.error("upload_file_to_cloud() - try again...")
        continue
    except Exception as e:
      log.error(get_exception_traceback_descr(e))
      log.error("unknown api yandex error: %s"%str(e))
      log.error("try again...")
      continue
    if file_url!=None:
      log.info("success upload %d bytes of data to yandex-cloud storage as: %s"%(len(data),file_url))
      break
    else:
      log.error("error upload, all 3 try was fail - exit")
      return None

  for i in range(1,6):
    log.info("start request step trying = %d"%i)
    try:
      if IAM_TOKEN==None:
        # только через сервисный аккаунт:
        log.debug("try get jwt token...")
        jwt_token=get_jwt_token(log,conf.service_account_id, conf.service_account_key_id, conf.service_secret_key_path)
        if jwt_token==None:
          log.error("get jwt_token")
          return None
        log.debug("jwt token=%s"%jwt_token)
        IAM_TOKEN=getIAMtokenByJwt(log,jwt_token)
        if IAM_TOKEN==None:
          log.error("get IAM token from yandex by jwt")
          return None
        log.debug("get IAM_TOKEN by jwt: %s"%IAM_TOKEN)

      # sent to translate:
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
      #options["audio"]["uri"]="https://storage.yandexcloud.net/voice2text/EE117081C56E0A51BBA8A9AC1E394411.mpga.opus"
      options["audio"]["uri"]=file_url
      #options["audio"]["uri"]="https://storage.yandexcloud.net/speechkit/speech.ogg"
      options_as_string=json.dumps(options, indent=4, sort_keys=True,ensure_ascii=False)
      options_as_data=bytearray(options_as_string, 'utf8')

      #log.debug("IAM_TOKEN: %s"%IAM_TOKEN)
      log.debug("create request data for translate request...")
      url = urllib.request.Request("https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize" , data=options_as_data)
      url.add_header("Authorization", "Bearer %s" % IAM_TOKEN)

      log.debug("success create request data for translate request")
      log.debug("try send translate request...")
      responseData = urllib.request.urlopen(url).read().decode('UTF-8')
      if responseData == None:
        log.error("responseData == None - try again")
        continue
      log.debug("request end, try decode json...")
      decodedData = json.loads(responseData)
      log.debug("response is:")
      log.debug(decodedData)

      if decodedData.get("error_code") is None:
          return(decodedData.get("id"))
      else:
        log.error("api yandex error. Error send request to translate. Request return error response:")
        log.error(decodedData)
        return None

    except urllib.error.HTTPError as e:
      if e.code == 401 and 'Unauthorized' in str(e):
        log.warning(str(e))
        log.info("try update IAM token")
        # только через сервисный аккаунт:
        jwt_token=get_jwt_token(log,conf.service_account_id, conf.service_account_key_id, conf.service_secret_key_path)
        if jwt_token==None:
          log.error("get jwt_token")
          return None
        log.debug("jwt token=%s"%jwt_token)
        IAM_TOKEN=getIAMtokenByJwt(log,jwt_token)
        if IAM_TOKEN==None:
          log.error("get IAM token from yandex by jwt")
          return None
        # токен получен - пробуем ещё раз:
        log.debug("success get IAM_TOKEN by jwt: %s"%IAM_TOKEN)
        log.info("after get IAM token - try call api again")
        continue
    except Exception as e:
      log.error(get_exception_traceback_descr(e))
      log.error("unknown api yandex error: %s"%str(e))
      return None

  log.error("try 3 call yandex-api - no success - skip trying (i=%d)"%i)
  return None


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

  f=open("A1D6A591F31ED0F704EDD00C0B59297D.oga","br")
  data=f.read()
  f.close()

  job_id=voice2textLongAudioAddRequest(log,data)
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
          log.info("result text = %s"%result["result"])
          break

  log.info("Program exit!")
