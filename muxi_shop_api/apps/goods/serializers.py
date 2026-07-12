from rest_framework import serializers

from apps.goods.models import Goods
from django.conf import settings

class GoodsSerializer(serializers.ModelSerializer):
    #image_url是序列化器字段名，这个名称决定了最终JSON输出中的key值
    image_url=serializers.SerializerMethodField() #这个方法允许你定义一个函数来处理你要处理的对象
    create_time=serializers.DateTimeField("%Y-%m-%d %H:%M:%S")

    #obj是Goods模型实例
    def get_image_url(self,obj):  #函数名是 get_序列化名()
        new_image_path=settings.IMAGE_URL + obj.image
        return new_image_path
    
    class Meta:
        model=Goods
        fields='__all__'