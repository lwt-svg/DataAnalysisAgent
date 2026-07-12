from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from apps.order.models import Order, OrderGoods
from apps.order.serializers import OrderGoodsSerializer, OrderManyGoodsSerializer, OrderSerializer
from django.http import JsonResponse
from apps.cart.models import ShoppingCart
from utils import ResponseMessage
# Create your views here.

class OrderGoodsGenericAPIView(GenericAPIView):
    queryset=OrderGoods.objects
    serializer_class=OrderGoodsSerializer

    def post(self,request):
        #反序列化数据
        res=self.get_serializer(data=request.data)
        res.is_valid(raise_exception=True)
        res.save()
        return JsonResponse("ok",safe=False)
    
    def get(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email = request.user.get("data").get("username")
        
        trade_no = request.GET.get("trade_no")
        db_res = Order.objects.filter(
            email=email,is_delete=0,trade_no=trade_no
        ).first()
        
        #序列化数据
        order_res = OrderManyGoodsSerializer(instance=db_res)
        return ResponseMessage.OrderResponse.success(order_res.data)

#商品订单接口(在购物车中点击去结算时触发)
class OrderGenericAPIView(GenericAPIView):
    queryset = Order.objects
    serializer_class = OrderSerializer
    def post(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email = request.user.get("data").get("username")
        #生成订单号
        import time
        trade_no = int(time.time()*1000)

        request_data = request.data
        trade_data = request_data["trade"] #订单数据
        goods_data = request_data["goods"] #商品数据
        trade_data["trade_no"] = trade_no
        trade_data["email"] = email
        #新创建的订单,支付状态就是0
        trade_data["pay_status"] = 0
        trade_data["is_delete"] = 0
        serializer = self.get_serializer(data = trade_data)
        serializer.is_valid()
        serializer.save()
        goods_order_data={}
        #对订单中的商品数据进行操作
        for data in goods_data:
            goods_order_data["trade_no"] = trade_no
            goods_order_data["sku_id"] = data["sku_id"]
            goods_order_data["goods_num"] = data["nums"]
            OrderGoods.objects.create(**goods_order_data) #把添加到订单中的商品添加到订单商品数据库中
            #然后把这个商品从购物车中删除
            ShoppingCart.objects.filter(sku_id=data["sku_id"],email=trade_data["email"]).update(is_delete=1)
        return ResponseMessage.OrderResponse.success(serializer.data)
    
    #获取订单商品信息
    def get(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email = request.user.get("data").get("username")
        pay_status = request.GET.get("pay_status")
        if pay_status == "-1": #获取所有订单
            db_res = Order.objects.filter(
                email=email,is_delete=0
                ).all().order_by("create_time")
        else:
            db_res = Order.objects.filter(
                email=email,is_delete=0,pay_status=pay_status
                ).all().order_by("create_time")
        #序列化数据
        order_res = OrderManyGoodsSerializer(instance=db_res,many=True)
        return ResponseMessage.OrderResponse.success(order_res.data)
    
class deleteOrderGoods(GenericAPIView):
    queryset = Order.objects
    serializer_class = OrderSerializer
    def post(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        email = request.user.get("data").get("username")
        request_data = request.data
        trade_no = request_data["trade_no"]
        self.get_queryset().filter(trade_no=trade_no,email=email).delete()
        return ResponseMessage.OrderResponse.success("ok")
    

class OrderDetailGenericAPIView(GenericAPIView):
    queryset = Order.objects
    serializer_class = OrderSerializer
    def post(self,request):
        if not request.user.get("status"):
            return JsonResponse(request.user,safe=False)
        #email = request.user.get("data").get("username")
        trade_no = request.data.get("trade_no")
        self.get_queryset().filter(trade_no=trade_no).update(**request.data)
        return ResponseMessage.OrderResponse.success("ok")