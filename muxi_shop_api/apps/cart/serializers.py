from rest_framework import serializers
from apps.cart.models import ShoppingCart
from apps.goods.models import Goods
from apps.goods.serializers import GoodsSerializer

class CartSerializer(serializers.ModelSerializer):
    sku_id=serializers.CharField(required=True) #在反序列化时表示这个字段是必须要有的
    email=serializers.CharField(required=True)
    
    class Meta:
        model=ShoppingCart
        fields='__all__'

class CartDetailSerializer(serializers.Serializer):
    sku_id=serializers.CharField(required=True) #在反序列化时表示这个字段是必须要有的
    email=serializers.CharField(required=True)
    nums = serializers.IntegerField()
    is_delete = serializers.IntegerField()
    goods = serializers.SerializerMethodField()

    def get_goods(self,obj):
        ser = GoodsSerializer(Goods.objects.filter(sku_id=obj.sku_id).first())
        return ser.data
