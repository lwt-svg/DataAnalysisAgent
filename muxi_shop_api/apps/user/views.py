from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from apps.user.serializers import ChangePasswordSerializer, UserSerializer, UserUpdateSerializer
from apps.user.models import User
from utils import Password_Encoder
from utils import ResponseMessage
from utils.jwt_auth import create_token
# Create your views here.

class UserAPIView(APIView):

    # def post(self,request):
    #     request.data["password"]=Password_Encoder.get_md5(request.data.get("password"))
    #     #反序列化(需要验证数据)
    #     res=UserSerializer(data=request.data)
    #     res.is_valid(raise_exception=True)
    #     user_data=User.objects.create(**res.data)

    #     #序列化，把json返回给前端对象
    #     res1=UserSerializer(instance=user_data)
    #     return JsonResponse(res1.data)
    
    def post(self,request):
        #反序列化(需要验证数据)
        res=UserSerializer(data=request.data)
        res.is_valid(raise_exception=True)
        user_data=res.save() #使用序列化器中的create来进行数据的保存

        #序列化，把json返回给前端对象
        res1=UserSerializer(instance=user_data)
        return ResponseMessage.UserResponse.success(res1.data)
    
    def get(self,request):
        try:
            email=request.GET.get("email")
            user_data=User.objects.filter(email=email).first()
            res=UserSerializer(instance=user_data)
            return ResponseMessage.UserResponse.success(res.data)
        except Exception as e:
            print(e)
            return ResponseMessage.UserResponse.failed("用户信息获取失败")
        

class LoginView(GenericAPIView):
    def post(self,request):
        return_data={}
        request_data=request.data
        email = request_data.get("username")
        user_data = User.objects.filter(email=email).first()
        if not user_data:
            return ResponseMessage.UserResponse.other("用户名或密码错误")
        else:
            user_ser = UserSerializer(instance = user_data,many=False)
            #用户输入的密码
            user_input_password = request_data.get("password")
            md5_user_input_password = Password_Encoder.get_md5(user_input_password)

            db_password = user_data.password
            if md5_user_input_password != db_password:
                return ResponseMessage.UserResponse.other("用户名或密码错误")
            else:
                token_info={
                    "username":email  #以后在token中获取email时用request.user.get("data").get("username")
                }
                token_data = create_token(token_info) #token_data就是编码好的token
                return_data["token"]=token_data
                return_data["username"]=user_ser.data.get("name")
                #用户登入之后返回token给前端
                return ResponseMessage.UserResponse.success(return_data)

class UpdateUserAPIView(APIView):
    def post(self, request):
        if not request.user.get("data").get("username"):
            return JsonResponse(request.user,safe=False)
        try:
            # 获取当前登录用户
            email = request.user.get("data").get("username")
            current_user = User.objects.filter(email=email).first()
            
            if not current_user:
                return ResponseMessage.UserResponse.failed("用户不存在")
            
            # 使用更新序列化器
            serializer = UserUpdateSerializer(
                current_user, 
                data=request.data, 
                partial=True  # 允许部分更新
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            # 返回成功响应
            return ResponseMessage.UserResponse.success("用户信息更新成功")
            
        except Exception as e:
            print(f"更新用户信息失败: {e}")
            return ResponseMessage.UserResponse.failed("更新用户信息失败")
        
class ChangePasswordView(APIView):
    def post(self, request):
        if not request.user.get("data").get("username"):
            return JsonResponse(request.user, safe=False)
        try:
            serializer = ChangePasswordSerializer(
                data=request.data, 
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return ResponseMessage.UserResponse.success("密码修改成功")
        
        except Exception as e:
            print(f"修改密码失败: {e}")
            return ResponseMessage.UserResponse.failed("修改密码失败")