'''
    我们的菜单是第一个创建的
    成功了状态码是1000,失败了是1001,其他状态是1002
'''

import json
from django.http import HttpResponse, JsonResponse

#菜单响应
class MenuResponse():
    @staticmethod  #我们只需要传入data所以我们用静态方法
    def success(data):
        res={"status":1000,"data":data}
        return HttpResponse(json.dumps(res,ensure_ascii=False),content_type="application/json")
    @staticmethod
    def failed(data):
        res={"status":1001,"data":data}
        return HttpResponse(json.dumps(res,ensure_ascii=False),content_type="application/json")

    @staticmethod
    def other(data):
        res={"status":1002,"data":data}
        return HttpResponse(json.dumps(res,ensure_ascii=False),content_type="application/json")


#商品响应(响应码以2开头)
class GoodsResponse():
    @staticmethod  #我们只需要传入data所以我们用静态方法
    def success(data):
        res={"status":2000,"data":data}
        #json.dumps() s是string的意思。json.dumps()是将数据转换成字符串,而json.dump()是将数据转换成json并写入文件
        #json.dumps()是将字典转换为一个json字符串。ensure_ascii=False是保持原样数据输出,True是转换成\uXXXX 形式的Unicode转义序列
        return HttpResponse(json.dumps(res,ensure_ascii=False),content_type="application/json")
    @staticmethod
    def failed(data):
        res={"status":2001,"data":data}
        return HttpResponse(json.dumps(res,ensure_ascii=False),content_type="application/json")

    @staticmethod
    def other(data):
        res={"status":2002,"data":data}
        return HttpResponse(json.dumps(res,ensure_ascii=False),content_type="application/json")


#购物车响应(响应码以3开头)
class CartResponse():
    @staticmethod  #我们只需要传入data所以我们用静态方法
    def success(data):
        res={"status":3000,"data":data}
        return JsonResponse(res,safe=True)
    def failed(data):
        res={"status":3001,"data":data}
        return JsonResponse(res,safe=True)
    @staticmethod
    def other(data):
        res={"status":3002,"data":data}
        return JsonResponse(res,safe=True)
    
    
#用户响应(响应码以4开头)
class UserResponse():
    @staticmethod  #我们只需要传入data所以我们用静态方法
    def success(data):
        res={"status":4000,"data":data}
        return JsonResponse(res,safe=True)
    def failed(data):
        res={"status":4001,"data":data}
        return JsonResponse(res,safe=True)
    @staticmethod
    def other(data):
        res={"status":4002,"data":data}
        return JsonResponse(res,safe=True)
    
#评论响应(响应码以5开头)
class CommentResponse():
    @staticmethod  #我们只需要传入data所以我们用静态方法
    def success(data):
        res={"status":5000,"data":data}
        return JsonResponse(res,safe=False)
    def failed(data):
        res={"status":5001,"data":data}
        return JsonResponse(res,safe=True)
    @staticmethod
    def other(data):
        res={"status":5002,"data":data}
        return JsonResponse(res,safe=True)
    
#订单响应(响应码以6开头)
class OrderResponse():
    @staticmethod  #我们只需要传入data所以我们用静态方法
    def success(data):
        res={"status":6000,"data":data}
        return JsonResponse(res,safe=False)
    def failed(data):
        res={"status":6001,"data":data}
        return JsonResponse(res,safe=True)
    @staticmethod
    def other(data):
        res={"status":6002,"data":data}
        return JsonResponse(res,safe=True)
    
#地址响应(响应码以7开头)
class AddressResponse():
    @staticmethod  #我们只需要传入data所以我们用静态方法
    def success(data):
        res={"status":7000,"data":data}
        return JsonResponse(res,safe=False)
    def failed(data):
        res={"status":7001,"data":data}
        return JsonResponse(res,safe=True)
    @staticmethod
    def other(data):
        res={"status":7002,"data":data}
        return JsonResponse(res,safe=True)