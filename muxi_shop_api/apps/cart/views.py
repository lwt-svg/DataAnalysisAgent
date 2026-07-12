from django.http import JsonResponse
from django.shortcuts import render,HttpResponse
from rest_framework.views import APIView
from apps.cart.models import ShoppingCart
from apps.cart.serializers import CartSerializer,CartDetailSerializer
from utils import ResponseMessage

# Create your views here.
class CartAPIView(APIView):
    #我们的购物车应该是登入之后才能访问的
    # @todo 后续补充登入权限验证
    def post(self,request):
        request_data=request.data #接收前端发过来的数据
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email = request.user.get("data").get("username")
        request_data["email"]=email
        sku_id=request_data.get('sku_id')
        nums=request_data.get('nums')
        is_delete=request_data.get('is_delete')
        #判断一下数据是否存在，如果存在就更新，不存在就插入
        data_exists=ShoppingCart.objects.filter(
            email=email,
            is_delete=0,
            sku_id=sku_id
        )
        #如果存在就更新
        if data_exists.exists():
            exists_cart_data=data_exists.first()
            if is_delete==0:
                new_nums=nums + exists_cart_data.nums
                request_data['nums']=new_nums
            elif is_delete==1:
                new_nums=exists_cart_data.nums
                request_data['is_delete']=is_delete
            #反序列化 data
            res=CartSerializer(data=request_data)
            res.is_valid(raise_exception=True) #反序列化之后要数据验证
            #更新数据到数据库
            ShoppingCart.objects.filter(
                email=email,
                is_delete=0, #是否删除
                sku_id=sku_id
            ).update(**res.data)
            if is_delete==0:
                return ResponseMessage.CartResponse.success("更新成功")
            elif is_delete==1:
                return ResponseMessage.CartResponse.success("删除成功")
        #如果没有就插入
        else:
            res=CartSerializer(data=request_data)
            res.is_valid(raise_exception=True)
            ShoppingCart.objects.create(**res.data)
            return ResponseMessage.CartResponse.success("插入成功")
        
    def get(self,request):
        email=request.GET.get("email") #从前端发送的GET请求中的URL参数中获取email值
        cart_res=ShoppingCart.objects.filter(email=email,is_delete=0)
        #序列化数据(将对象数据转换为字典类型)
        res=CartSerializer(instance=cart_res,many=True) #告诉序列化我有多条数据
        return ResponseMessage.CartResponse.success(res.data)
    
#使用序列化器 达到多表关联查询的目的(因为shopping_cart中没有商品数据)
class CartDetailAPIView(APIView):
    def get(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email = request.user.get("data").get("username")
        fliters = {
            "email":email,
            "is_delete":0
        }
        shopping_cart = ShoppingCart.objects.filter(**fliters).all()
        db_data = CartDetailSerializer(instance=shopping_cart,many=True)
        return ResponseMessage.CartResponse.success(db_data.data)
    

class UpdateCartNumAPIView(APIView):
    def post(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        #从token中获取email
        print(request.user)
        email = request.user.get("data").get("username")
        request_data = request.data
        ShoppingCart.objects.filter(
            email=email,
            sku_id=request_data.get("sku_id"),
            is_delete=0
        ).update(nums=request_data["nums"])
        return ResponseMessage.CartResponse.success("OK")

#获取购物车商品数量的接口
from django.db.models import Sum
class CartCountAPIView(APIView):
    def post(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email = request.user.get("data").get("username")
        user_cart_count= ShoppingCart.objects.filter(
            email=email,
            is_delete = 0
        ).aggregate(total_count = Sum("nums"))
        return ResponseMessage.CartResponse.success(user_cart_count)
    

class DeleteCartGoodsAPIView(APIView):
    def post(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        #从token中获取email
        print(request.user)
        email = request.user.get("data").get("username")
        request_data = request.data
        ShoppingCart.objects.filter(
            email=email,
            sku_id__in = request_data, #sku_id__in 是django orm的字段查询表达式,表示“字段值在某个列表中”的条件查询            is_delete=0
        ).update(is_delete=1)
        return ResponseMessage.CartResponse.success("OK")