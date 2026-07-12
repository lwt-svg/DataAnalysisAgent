# apps/pay/urls.py
from django.urls import path
from .views import (
    CreatePaymentAPIView,      # 创建支付订单
    AliPayNotifyAPIView,       # 支付宝异步通知
    AliPayReturnAPIView,       # 支付宝同步返回
    MockPaymentPageAPIView,    # 模拟支付页面
    MockPaymentNotifyAPIView,  # 模拟支付异步通知
    CheckPaymentStatusAPIView, # 检查支付状态
    PaymentTestAPIView,        # 支付测试接口
)

urlpatterns = [
    # 支付订单创建
    path("create/", CreatePaymentAPIView.as_view(), name="create_payment"),
    
    # 支付宝回调接口
    path("alipay/notify/", AliPayNotifyAPIView.as_view(), name="alipay_notify"),
    path("alipay/return/", AliPayReturnAPIView.as_view(), name="alipay_return"),
    
    # 模拟支付接口
    path("mock/pay/", MockPaymentPageAPIView.as_view(), name="mock_payment_page"),
    path("mock/notify/", MockPaymentNotifyAPIView.as_view(), name="mock_payment_notify"),
    
    # 支付状态查询
    path("status/", CheckPaymentStatusAPIView.as_view(), name="check_payment_status"),
    
    # 测试接口
    path("test/", PaymentTestAPIView.as_view(), name="payment_test"),
]