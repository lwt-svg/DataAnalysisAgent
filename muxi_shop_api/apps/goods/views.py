from datetime import datetime
import decimal
import json
from django.http import JsonResponse
from django.shortcuts import render,HttpResponse
from rest_framework.views import APIView

from apps.goods.models import Goods
from apps.goods.serializers import GoodsSerializer
from utils import ResponseMessage
from utils.ResponseMessage import GoodsResponse

# Create your views here.
#获取商品分类的接口
#访问方式：http://localhost:8000/goods/category/1/2
class GoodsCategoryAPIView(APIView): #APIView继承了Django的View类并重写了一些里面的方法
    def get(self,request,category_id,page):
        current_page=(page-1)*20 #一页20条数据
        end_data= page *20
        category_data=Goods.objects.filter(
            type_id=category_id).all()[current_page:end_data]
        res=[]
        for item in category_data:
            res.append(item.to_dict())
        return GoodsResponse.success(res)

class GoodsDetialAPIView(APIView):
    def get(self,request,sku_id):
        print(sku_id)
        goods_data=Goods.objects.filter(sku_id=sku_id).first()
        #进行序列化的动作，序列化时的参数是instance，反序列化的参数是data
        res=GoodsSerializer(instance=goods_data)
        return GoodsResponse.success(res.data)
    
class GoodsFindAPIView(APIView):
    def get(self,request):
        goods_data = Goods.objects.filter(find=1).all()
        res = GoodsSerializer(instance=goods_data,many=True)
        return ResponseMessage.GoodsResponse.success(res.data)


class GoodsSearchAPIView(APIView):
    def get(self,request,keyword,page,order_by):
        order_dict={
            1:"r.comment_count",
            2:"g.p_price"
        }
        limit_page = (page-1) * 15
        from django.db import connection
        from django.conf import settings
        sql = """
            select r.comment_count,concat('{}',g.image) as image,g.name,g.p_price,g.shop_name,g.sku_id from goods g
                left join(
                    select count(c.sku_id) as comment_count,c.sku_id from comment c group by c.sku_id
                ) r 
                on g.sku_id COLLATE utf8mb4_general_ci = r.sku_id COLLATE utf8mb4_general_ci
                where g.name like "%{}%"
                order by {} desc limit {},15
        """.format(settings.IMAGE_URL,keyword,order_dict[order_by],limit_page)
        cursor = connection.cursor()
        cursor.execute(sql)
        res = self.dict_fetchall(cursor) #将得到的数据（元组）转换为字典格式
        final_list = []
        for item in res:
            # 处理 Decimal 类型
            processed_item = {}
            for key, value in item.items():
                if isinstance(value, decimal.Decimal):
                    processed_item[key] = float(value)
                else:
                    processed_item[key] = value
            final_list.append(processed_item)
        return ResponseMessage.GoodsResponse.success(final_list)

    def dict_fetchall(self,cursor):
        desc = cursor.description #返回一个元组列表 每个元组的第一个元素是列名
        return [dict(zip([col[0] for col in desc],row)) for row in cursor.fetchall()]
    
class GoodsSearchDataCountAPIView(APIView):
    def get(self,request,keyword):
        #name_contains 会在数据库中查找name字段包含keyword的记录
        #比如查看数据库中name字段包含关键字 手机 的所有记录
        count = Goods.objects.filter(name__contains=keyword).count()
        return HttpResponse(count)
    
