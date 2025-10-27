# -*- coding: utf-8 -*-

import os
import hashlib
import hmac
import json
import sys
import time
import base64
from datetime import datetime
# 加载.env文件中的环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Please install it with 'pip install python-dotenv'")
if sys.version_info[0] <= 2:
    from httplib import HTTPSConnection
else:
    from http.client import HTTPSConnection


audio_file = "D:/Edge下载/Video_description_generation_and_automatic_dubbing-master/Video_description_generation_and_automatic_dubbing-master/fuck.mp3"  # 替换为你的音频文件路径


def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def tts(text,audio_path):
  # 从环境变量中获取密钥
  secret_id = os.environ.get('TENCENT_SECRET_ID', '')
  secret_key = os.environ.get('TENCENT_SECRET_KEY', '')
  
  # 检查密钥是否存在
  if not secret_id or not secret_key:
      raise ValueError("请确保TENCENT_SECRET_ID和TENCENT_SECRET_KEY环境变量已正确设置")

  token = ""

  service = "tts"
  host = "tts.tencentcloudapi.com"
  region = ""
  version = "2019-08-23"
  action = "TextToVoice"

  payload =  ("{\"Text\":\""+text+
              "\",\"SessionId\":\"session-1234\",\"Volume\":1,\"Speed\":1,\"ProjectId\":0,\"ModelType\":1,\"VoiceType\":101054,\"PrimaryLanguage\":1,\"Codec\":\"mp3\",\"EmotionCategory\":\"neutral\"}")

  params = json.loads(payload)
  endpoint = "https://tts.tencentcloudapi.com"
  algorithm = "TC3-HMAC-SHA256"
  timestamp = int(time.time())
  date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

  # ************* 步骤 1：拼接规范请求串 *************
  http_request_method = "POST"
  canonical_uri = "/"
  canonical_querystring = ""
  ct = "application/json; charset=utf-8"
  canonical_headers = "content-type:%s\nhost:%s\nx-tc-action:%s\n" % (ct, host, action.lower())
  signed_headers = "content-type;host;x-tc-action"
  hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
  canonical_request = (http_request_method + "\n" +
                     canonical_uri + "\n" +
                     canonical_querystring + "\n" +
                     canonical_headers + "\n" +
                     signed_headers + "\n" +
                     hashed_request_payload)

  # ************* 步骤 2：拼接待签名字符串 *************
  credential_scope = date + "/" + service + "/" + "tc3_request"
  hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
  string_to_sign = (algorithm + "\n" +
                  str(timestamp) + "\n" +
                  credential_scope + "\n" +
                  hashed_canonical_request)

  # ************* 步骤 3：计算签名 *************
  secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
  secret_service = sign(secret_date, service)
  secret_signing = sign(secret_service, "tc3_request")
  signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

  #  ************* 步骤 4：拼接 Authorization *************
  authorization = (algorithm + " "
                 "Credential=" + secret_id + "/" + credential_scope + ", " +
                 "SignedHeaders=" + signed_headers + ", " +
                 "Signature=" + signature)

  # ************* 步骤 5：构造并发起请求 *************
  headers = {
    "Authorization": authorization,
    "Content-Type": "application/json; charset=utf-8",
    "Host": host,
    "X-TC-Action": action,
    "X-TC-Timestamp": timestamp,
    "X-TC-Version": version
  }
  if region:
    headers["X-TC-Region"] = region
  if token:
    headers["X-TC-Token"] = token

  try:
    req = HTTPSConnection(host)
    req.request("POST", "/", headers=headers, body=payload.encode("utf-8"))
    resp = req.getresponse()
    # 读取并解析响应
    response_data = resp.read().decode('utf-8')
    resp_dict = json.loads(response_data)

    # 直接提取 Audio
    audio_data = resp_dict["Response"]["Audio"]
    #print(audio_data)
    #print(resp.read())
  except Exception as err:
    print(err)


  #将base64转换为MP3文件
  audio_data_mp3 = base64.b64decode(audio_data)
  fout = open(audio_path, 'wb')
  fout.write(audio_data_mp3)
  fout.close()

if __name__ == "__main__":
   tts("a woman is singing.",'output/tts_test.mp3')

