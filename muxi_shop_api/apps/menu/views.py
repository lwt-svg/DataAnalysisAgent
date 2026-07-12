from django.shortcuts import render,HttpResponse
from django.views import View
from apps.menu.models import MainMenu,SubMenu
import json

from utils import ResponseMessage
# Create your views here.
class GoodsMainMenu(View):
    def get(self,request):
        print("get请求")
        main_menu=MainMenu.objects.all() #获取主菜单对象
        res=[]
        for item in main_menu:
            res.append(item.to_dict())
        return ResponseMessage.MenuResponse.success(res)
       
    def post(self,request):
        print("post请求")
        return HttpResponse("post请求")

class GoodsSubMenu(View):
    def get(self,request):
        param_id = request.GET.get("main_menu_id")
        sub_menu=SubMenu.objects.filter(main_menu_id=param_id) #获取主菜单对象
        res=[]
        for item in sub_menu:
            res.append(item.to_dict())
        return ResponseMessage.MenuResponse.success(res)

    def post(self,request):
        print("post请求")
        return HttpResponse("post请求")