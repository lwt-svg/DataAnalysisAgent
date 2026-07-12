from django.shortcuts import render
from rest_framework.viewsets import ViewSetMixin
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin,UpdateModelMixin,DestroyModelMixin,ListModelMixin,RetrieveModelMixin
from rest_framework.views import APIView

from apps.comment.models import Comment
from apps.comment.serializers import CommentSerializer
from django.http import JsonResponse

from utils import ResponseMessage
# Create your views here.

#ViewSetMixin 必须第一个继承,否则as_view()方法会去别的方法中寻找
class CommentGenericAPIView(ViewSetMixin,GenericAPIView,
                            CreateModelMixin,RetrieveModelMixin,
                            UpdateModelMixin,DestroyModelMixin,ListModelMixin):
    queryset = Comment.objects
    serializer_class = CommentSerializer

    def insert(self,request):
        #这个方法添加时的create_time为空 现在我重写一下create
        # print("我是添加数据")
        # return self.create(request)

        #反序列化数据
        res=self.get_serializer(data=request.data)
        res.is_valid(raise_exception=False)
        res.save()  
        return JsonResponse("插入成功",safe=False)
    
    def delete(self,request,pk):
        print("删除数据")
        return self.destroy(request,pk)
    
    def edit(self,request,pk):
        print("修改数据")
        return  self.update(request,pk)
    
    def single(self,request,pk):
        print("查询单个数据")
        return self.retrieve(request,pk)
    
    def get_list(self,request):
        print("查询多个数据")
        return self.list(request)
    
class CommentAPIView(APIView):
    def get(self,request,sku_id,page):
        start = (int(page)-1) * 15
        end = int(page) *15
        db_res = Comment.objects.filter(sku_id=sku_id).all()[start:end]
        ser_data = CommentSerializer(instance=db_res,many=True)
        return ResponseMessage.CommentResponse.success(ser_data.data)
    
class CommentCountAPIView(APIView):
    def get(self,request,sku_id):
        db_res = Comment.objects.filter(sku_id=sku_id).count()
        return JsonResponse(db_res,safe=False)