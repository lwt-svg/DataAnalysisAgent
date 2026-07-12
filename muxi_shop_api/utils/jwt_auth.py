import os
import sys

# Ensure project root is on sys.path so `import muxi_shop_api` works
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import datetime
import jwt
from muxi_shop_api import settings
from rest_framework.authentication import BaseAuthentication

#直接使用django中的secret_key当作盐
def create_token(payload,timeout=100000):
    headers={
        'alg':'HS256',
        'typ':"jwt"
    }
    payload["exp"]=datetime.datetime.now() + datetime.timedelta(minutes=timeout)  #定义超时时间

    res = jwt.encode(headers=headers,payload=payload,key=settings.SECRET_KEY,algorithm='HS256')
    return res

def get_payload(token):
    res = {"status":False,"data":None,"error":None}
    try:
        #解码验证 token不存储在本地
        payload = jwt.decode(token,settings.SECRET_KEY,algorithms=["HS256"])
        res["status"]=True
        res["data"]=payload
    except jwt.exceptions.DecodeError:
        print("token认证失败")
        res["error"]="token认证失败"
    except jwt.exceptions.ExpiredSignatureError:
        print("token已经失效")
        res["error"]="token已经失效"
    except jwt.exceptions.InvalidTokenError:
        print("无效的token")
        res["error"]="无效的token"
    return res


#用户在头部进行token的参数配置
class JwtHeaderAuthentication(BaseAuthentication):
    #token是用户登入之后看此用户是否有访问某页面权限和身份验证用的（查看是不是我们的用户）
    def authenticate(self, request):
        #request.META.get() 是从请求头部获取信息
        # token = request.META.get("HTTP_TOKEN") #postman中获取
        token = request.META.get("HTTP_AUTHORIZATION")
        res_payload = get_payload(token)
        return (res_payload,token)