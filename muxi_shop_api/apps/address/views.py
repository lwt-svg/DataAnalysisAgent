from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin,RetrieveModelMixin,UpdateModelMixin,DestroyModelMixin,ListModelMixin

from apps.address.models import UserAddress
from apps.address.serializers import UserAddressSerializer
from utils.jwt_auth import JwtHeaderAuthentication
from utils import ResponseMessage
# Create your views here.

class AddressGenericAPIView(GenericAPIView,CreateModelMixin,
                            RetrieveModelMixin,UpdateModelMixin
                            ,DestroyModelMixin):
    queryset=UserAddress.objects
    serializer_class=UserAddressSerializer
    def post(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email=request.user.get("data").get("username")
        request_data = request.data
        request_data["email"] = email
        if request_data["default"] == True:
            #如果这个值是true 那么这个地址就是默认地址 我需要把所有地址先改为
            self.get_queryset().filter(email=email).update(default=0)
            request_data["default"]=1
        else:
            request_data["default"]=0
        self.get_queryset().create(**request_data)
        return ResponseMessage.AddressResponse.success("ok")
        #return self.create(request) #增加数据
    
    def get(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email=request.user.get("data").get("username")
        db_res = self.get_queryset().filter(email=email).all().order_by("default","create_time")
        ser = self.get_serializer(instance = db_res,many=True)
        return ResponseMessage.AddressResponse.success(ser.data)
        #return self.retrieve(request) #获取单条数据
    
    def put(self,request,pk):

        return self.update(request,pk) #修改数据
    
    def delete(self,request,pk):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email=request.user.get("data").get("username")
        db_res = self.get_queryset().filter(email=email,id=pk).all()
        if db_res:
            self.get_queryset().filter(email=email,id=pk).delete()
        return ResponseMessage.AddressResponse.success("ok")
        #return self.destroy(request,pk) #删除数据

class AddressListGenericAPIView(GenericAPIView,ListModelMixin):
    queryset = UserAddress.objects
    serializer_class = UserAddressSerializer
    authentication_classes = [JwtHeaderAuthentication,] #token验证
    def get(self,request):
        #拿到token的第一个值（用户信息）
        print(request.user)
        #拿到token的第二个值（token）
        print(request.auth)
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        return self.list(request) #获取多条数据
    
class UpdateAddressDetailGenericAPIView(GenericAPIView):
    queryset=UserAddress.objects
    serializer_class = UserAddressSerializer
    def post(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email = request.user.get("data").get("username")
        request_data = request.data
        request_data["email"] = email
        if request_data["default"] == True:
            self.get_queryset().filter(email=email).update(default=0)
            request_data["default"]=1
        else:
            request_data["default"]=0
        self.get_queryset().filter(id=request_data["id"]).update(**request_data)
        return ResponseMessage.AddressResponse.success("ok")