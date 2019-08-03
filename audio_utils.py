#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import os
import random
import json
import sys
import time
import logging
import config as conf
from pydub import AudioSegment


def load_sound(log,file_name): #,audio_type):
  # автоопределение входного файла
  try:
    #sound = AudioSegment.from_file(file_name, audio_type) # audiu_type may be: "mp4", "wma", "aac", "ogg", "flv", "mp3", "wav"
    sound = AudioSegment.from_file(file_name) # audiu_type may be: "mp4", "wma", "aac", "ogg", "flv", "mp3", "wav"
  except:
    log.error('Cannot load sound: %s'%file_name)
    return None
  return sound

def save_as_wav(log,sound,file_name):
  try:
    sound.export(file_name, format="wav")
  except:
    log.error('Cannot save sound as wav: %s'%file_name)
  return True

def save_as_opus(log,sound,file_name):
  try:
    sound.export(file_name, format="opus")
  except:
    log.error('Cannot save sound as opus: %s'%file_name)
  return True

if __name__ == '__main__':
  log= logging.getLogger("audio_utils")
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

  #sound = load_sound(log,"A1D6A591F31ED0F704EDD00C0B59297D.oga", "ogg")
  sound = load_sound(log,"EE117081C56E0A51BBA8A9AC1E394411.mpga", "ogg")
  save_as_opus(log,sound,"out.oga")
  sys.exit()

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
