import datetime
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.user.models import User
from utils import Password_Encoder

class UserSerializer(serializers.ModelSerializer):
    #email作为用户名进行的登入，这里我们需要做一个唯一性的检验
    email=serializers.EmailField(
        required=True,allow_blank=False, #必须要有email，不允许为空字符串
        validators=[UniqueValidator(queryset=User.objects.all(),message="该用户已存在 ")]
    )
    birthday = serializers.DateTimeField(input_formats=['%Y-%m-%d'])
    password = serializers.CharField(write_only=True)
    create_time = serializers.DateTimeField("%Y-%m-%d %H:%M:%S",required=False)

    def create(self, validated_data): #validated_data就是request.data
        validated_data["password"]=Password_Encoder.get_md5(validated_data["password"])
        validated_data["create_time"]=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res=User.objects.create(**validated_data)
        return res
    
    class Meta:
        model = User
        fields='__all__'

# 用于用户信息更新的序列化器
class UserUpdateSerializer(serializers.ModelSerializer):
    birthday = serializers.DateTimeField(input_formats=['%Y-%m-%d'], required=False)
    
    def update(self, instance, validated_data):
        # 只更新允许修改的字段
        instance.name = validated_data.get('name', instance.name)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.birthday = validated_data.get('birthday', instance.birthday)
        instance.save()
        return instance
    
    class Meta:
        model = User
        fields = ['name', 'gender', 'birthday']  # 只包含可修改的字段

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        # 验证新密码和确认密码是否一致
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("新密码和确认密码不一致")
        
        return attrs

    def validate_old_password(self, value):
        # 获取当前用户
        email = self.context['request'].user.get("data").get("username")
        current_user = User.objects.filter(email=email).first()
        
        if not current_user:
            raise serializers.ValidationError("用户不存在")
            
        # 验证旧密码是否正确（使用 MD5 加密后比较）
        old_password_md5 = Password_Encoder.get_md5(value)
        if old_password_md5 != current_user.password:
            raise serializers.ValidationError("旧密码错误")
            
        return value

    def save(self, **kwargs):
        # 获取当前用户
        email = self.context['request'].user.get("data").get("username")
        current_user = User.objects.filter(email=email).first()
        
        # 使用 MD5 加密新密码
        new_password_md5 = Password_Encoder.get_md5(self.validated_data['new_password'])
        current_user.password = new_password_md5
        current_user.save()
        return current_user