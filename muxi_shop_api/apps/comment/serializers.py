from rest_framework import serializers
from apps.comment.models import Comment
import datetime
class CommentSerializer(serializers.ModelSerializer):

    create_time = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M:%S"],required=False)

    def create(self, validated_data):
        validated_data["create_time"]=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res=Comment.objects.create(**validated_data)
        return res
    
    class Meta:
        model = Comment
        fields =  "__all__"