import datetime
from rest_framework import serializers

from apps.goods.models import Goods
from apps.order.models import Order, OrderGoods
from muxi_shop_api.settings import IMAGE_URL

class OrderGoodsSerializer(serializers.ModelSerializer):

    create_time = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M:%S"],required=False)

    def create(self, validated_data):
        validated_data["create_time"]=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res=OrderGoods.objects.create(**validated_data)
        return res
    class Meta:
        model=OrderGoods
        fields="__all__"

class OrderSerializer(serializers.ModelSerializer):

    create_time = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M:%S"],required=False)

    def create(self, validated_data):
        validated_data["create_time"]=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res=Order.objects.create(**validated_data)
        return res
    class Meta:
        model=Order
        fields="__all__"

class OrderManyGoodsSerializer(serializers.Serializer):
    trade_no = serializers.CharField()
    email = serializers.CharField()
    order_amount = serializers.DecimalField(max_digits=10,decimal_places=2)
    address_id = serializers.IntegerField()
    pay_status = serializers.CharField()
    pay_time = serializers.DateTimeField()
    ali_trade_no = serializers.CharField()
    is_delete = serializers.IntegerField()
    create_time = serializers.DateTimeField()

    order_info = serializers.SerializerMethodField()
    
    def get_order_info(self,obj):
        '''
        获取订单中对应订单号的全部商品数据 
        然后根据商品数据的sku_id去找对应的商品的详细信息
        '''
        ser = OrderGoodsSerializer(OrderGoods.objects.filter(
            trade_no = obj.trade_no).all(),many=True).data
        for item in ser:
            goods_data = Goods.objects.filter(sku_id=item.get("sku_id")).first()
            item["p_price"] = goods_data.p_price
            item["image"] = IMAGE_URL + goods_data.image
            item["name"] = goods_data.name
            item["shop_name"] = goods_data.shop_name
        return ser