import os
import sys

# Ensure project root is on sys.path so `import muxi_shop_api` works
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import datetime
import jwt
from muxi_shop_api import settings




'''
自定义一个盐
SALT="SFSGSVSZFFWESG"
'''

#直接使用django中的secret_key当作盐
def create_token():
    headers={
        'alg':'HS256',
        'typ':"jwt"
    }
    payload={
        'user_id':1,
        "username":'lwt',
        "exp":datetime.datetime.now() + datetime.timedelta(minutes=1)  #定义超时时间
    }

    res = jwt.encode(headers=headers,payload=payload,key=settings.SECRET_KEY,algorithm='HS256')
    return res

def get_payload(token):
    try:
        return jwt.decode(token,settings.SECRET_KEY,algorithms=["HS256"])
    except jwt.exceptions.DecodeError:
        print("token认证失败")
    except jwt.exceptions.ExpiredSignatureError:
        print("token已经失效")
    except jwt.exceptions.InvalidTokenError:
        print("无效的token")
    

if __name__ == "__main__":
    # token=create_token()
    # print(token)
    token="""eyJhbGciOiJIUzI1NiIsInR5cCI6Imp3dCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6Imx3dCIsImV4cCI6MTc2MjI4NzA1N30.t3UMyEgh8DPPkZyhSr_JYcHYxFcTWI1y4LeghA-xEj8"""
    payload = get_payload(token)
    print(payload)