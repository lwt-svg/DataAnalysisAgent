# apps/pay/views.py
"""
支付视图模块
处理支付宝支付相关的所有请求
"""
import logging
import json
import time
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from apps.pay.alipay import payment_service
from apps.order.models import Order
from muxi_shop_api import settings
from datetime import datetime

logger = logging.getLogger('alipay')


@method_decorator(csrf_exempt, name='dispatch')
class CreatePaymentAPIView(APIView):
    """创建支付订单（支持真实支付宝和模拟支付）"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # 获取请求数据
            data = request.data
            logger.info(f"创建支付请求数据: {data}")
            
            # 验证参数
            trade_no = data.get("tradeNo") or data.get("trade_no")
            total_amount = data.get("orderAmount") or data.get("total_amount")
            
            if not trade_no:
                return JsonResponse({
                    "code": 400,
                    "success": False,
                    "msg": "订单号不能为空",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not total_amount:
                return JsonResponse({
                    "code": 400,
                    "success": False,
                    "msg": "订单金额不能为空",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # 确保金额是数字
                total_amount = float(total_amount)
                if total_amount <= 0:
                    raise ValueError("金额必须大于0")
            except (ValueError, TypeError):
                return JsonResponse({
                    "code": 400,
                    "success": False,
                    "msg": "订单金额格式错误",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取商品描述
            subject = data.get("subject", f"慕希商城订单-{trade_no}")
            
            # 是否强制使用模拟支付
            force_mock = data.get("force_mock", False)
            
            # 创建支付
            payment_result = payment_service.create_payment(
                trade_no=trade_no,
                total_amount=total_amount,
                subject=subject,
                use_mock=force_mock
            )
            
            # 返回支付结果
            response_data = {
                "code": 200,
                "success": True,
                "msg": "支付订单创建成功",
                "data": {
                    "trade_no": trade_no,
                    "payment_url": payment_result["payment_url"],
                    "payment_type": payment_result["payment_type"],
                    "amount": total_amount,
                    "subject": subject,
                    "timestamp": int(time.time())
                }
            }
            
            logger.info(f"支付订单创建成功: trade_no={trade_no}, type={payment_result['payment_type']}")
            
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"创建支付订单失败: {str(e)}", exc_info=True)
            return JsonResponse({
                "code": 500,
                "success": False,
                "msg": f"系统错误: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class AliPayNotifyAPIView(APIView):
    """支付宝异步通知回调"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # 获取通知数据
            data = request.POST.dict()
            if not data:
                # 尝试从请求体获取
                try:
                    body_data = json.loads(request.body.decode('utf-8'))
                    data = body_data
                except:
                    pass
            
            logger.info(f"支付宝异步通知数据: {data}")
            
            # 获取支付类型
            payment_type = data.get('payment_type', 'alipay')
            
            # 验证签名
            is_valid = payment_service.verify_payment(data, payment_type)
            
            if not is_valid:
                logger.error("支付宝异步通知签名验证失败")
                return HttpResponse('fail')  # 支付宝要求返回fail
            
            # 提取业务数据
            out_trade_no = data.get('out_trade_no')
            trade_status = data.get('trade_status')
            total_amount = data.get('total_amount')
            
            logger.info(f"支付宝支付通知: trade_no={out_trade_no}, status={trade_status}, amount={total_amount}")
            
            # 处理支付结果
            if trade_status in ['TRADE_SUCCESS', 'TRADE_FINISHED']:
                try:
                    order = Order.objects.filter(trade_no=out_trade_no).first()
                    if order:
                        order.pay_status = '1'
                        order.pay_time = datetime.now()
                        order.ali_trade_no = data.get('trade_no', '')
                        order.save()
                        logger.info(f"订单状态更新成功: {out_trade_no}")
                    else:
                        logger.warning(f"未找到订单: {out_trade_no}")
                except Exception as e:
                    logger.error(f"更新订单状态失败: {str(e)}")
                
                logger.info(f"订单支付成功: {out_trade_no}")
                
                return HttpResponse('success')
            else:
                logger.warning(f"订单支付未成功: {out_trade_no}, status={trade_status}")
                return HttpResponse('fail')
                
        except Exception as e:
            logger.error(f"处理支付宝异步通知失败: {str(e)}", exc_info=True)
            return HttpResponse('fail')


@method_decorator(csrf_exempt, name='dispatch')
class AliPayReturnAPIView(APIView):
    """支付宝同步返回页面"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            data = request.GET.dict()
            logger.info(f"支付宝同步返回数据: {data}")
            
            out_trade_no = data.get('out_trade_no')
            total_amount = data.get('total_amount')
            trade_status = data.get('trade_status')
            
            if out_trade_no:
                try:
                    order = Order.objects.filter(trade_no=out_trade_no).first()
                    if order:
                        order.pay_status = '1'
                        order.pay_time = datetime.now()
                        order.ali_trade_no = data.get('trade_no', '')
                        order.save()
                        logger.info(f"订单状态更新成功（同步）: {out_trade_no}")
                except Exception as e:
                    logger.error(f"更新订单状态失败（同步）: {str(e)}")
                
                logger.info(f"订单支付成功（同步）: {out_trade_no}")
                return redirect(f"{settings.FRONTEND_SUCCESS_URL}?trade_no={out_trade_no}&amount={total_amount}&timestamp={int(time.time())}")
            else:
                logger.error(f"支付宝同步返回缺少订单号")
                return redirect(f"{settings.FRONTEND_FAIL_URL}?msg=订单号缺失")
                
        except Exception as e:
            logger.error(f"处理支付宝同步返回失败: {str(e)}")
            return redirect(f"{settings.FRONTEND_FAIL_URL}?msg=系统异常")


@method_decorator(csrf_exempt, name='dispatch')
class MockPaymentPageAPIView(APIView):
    """模拟支付页面"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # 获取支付参数
            trade_no = request.GET.get('trade_no')
            amount = request.GET.get('amount')
            subject = request.GET.get('subject', '慕希商城订单')
            
            if not trade_no or not amount:
                return HttpResponse("支付参数不完整")
            
            context = {
                'trade_no': trade_no,
                'amount': amount,
                'subject': subject,
                'timestamp': int(time.time()),
                'success_url': f"{settings.FRONTEND_SUCCESS_URL}?trade_no={trade_no}&amount={amount}",
                'fail_url': f"{settings.FRONTEND_FAIL_URL}?trade_no={trade_no}",
                'api_base': f"http://{settings.LOCAL_IP}:{settings.LOCAL_PORT}"
            }
            
            # 渲染模拟支付页面
            return render(request, 'pay/mock_payment.html', context)
            
        except Exception as e:
            logger.error(f"加载模拟支付页面失败: {str(e)}")
            return HttpResponse(f"加载支付页面失败: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class MockPaymentNotifyAPIView(APIView):
    """模拟支付异步通知"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            data = request.data
            logger.info(f"模拟支付异步通知: {data}")
            
            trade_no = data.get('out_trade_no')
            trade_status = data.get('trade_status')
            
            if not trade_no:
                return JsonResponse({'success': False, 'msg': '参数错误'})
            
            # 获取模拟支付服务
            mock_service = payment_service._mock_alipay
            
            if trade_status == 'TRADE_SUCCESS':
                mock_service.process_mock_payment(trade_no, 'success')
                
                try:
                    order = Order.objects.filter(trade_no=trade_no).first()
                    if order:
                        order.pay_status = '1'
                        order.pay_time = datetime.now()
                        order.save()
                        logger.info(f"模拟支付订单状态更新成功: {trade_no}")
                except Exception as e:
                    logger.error(f"模拟支付更新订单状态失败: {str(e)}")
                
                return JsonResponse({'success': True, 'msg': '支付成功'})
            else:
                mock_service.process_mock_payment(trade_no, 'failed')
                return JsonResponse({'success': False, 'msg': '支付失败'})
                
        except Exception as e:
            logger.error(f"处理模拟支付通知失败: {str(e)}")
            return JsonResponse({'success': False, 'msg': '系统错误'})


@method_decorator(csrf_exempt, name='dispatch')
class CheckPaymentStatusAPIView(APIView):
    """检查支付状态"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            trade_no = request.GET.get('tradeNo') or request.GET.get('trade_no')
            
            if not trade_no:
                return JsonResponse({
                    "code": 400,
                    "success": False,
                    "msg": "订单号不能为空",
                    "data": None
                })
            
            # 检查模拟支付状态
            mock_service = payment_service._mock_alipay
            mock_status = mock_service.get_payment_status(trade_no)
            
            # TODO: 这里应该检查真实支付宝的支付状态
            # 实际项目中应该查询数据库或调用支付宝查询接口
            
            # 如果模拟支付中有记录，返回模拟支付状态
            if mock_status:
                status_map = {
                    'created': 'pending',
                    'paid': 'success',
                    'cancelled': 'cancelled',
                    'failed': 'failed'
                }
                
                payment_status = status_map.get(mock_status, 'unknown')
                
                response_data = {
                    "code": 200,
                    "success": True,
                    "msg": "获取支付状态成功",
                    "data": {
                        "trade_no": trade_no,
                        "status": payment_status,
                        "payment_type": "mock",
                        "checked_at": int(time.time())
                    }
                }
                
                if payment_status == 'success':
                    # 获取支付时间
                    payment_info = mock_service.mock_payments.get(trade_no, {})
                    response_data['data']['paid_at'] = payment_info.get('paid_at')
                    
            else:
                # 如果没有模拟支付记录，假设为待支付状态
                # TODO: 实际应该查询数据库
                response_data = {
                    "code": 200,
                    "success": True,
                    "msg": "获取支付状态成功",
                    "data": {
                        "trade_no": trade_no,
                        "status": "pending",
                        "payment_type": "unknown",
                        "checked_at": int(time.time())
                    }
                }
            
            logger.info(f"检查支付状态: trade_no={trade_no}, status={response_data['data']['status']}")
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"检查支付状态失败: {str(e)}")
            return JsonResponse({
                "code": 500,
                "success": False,
                "msg": f"系统错误: {str(e)}",
                "data": None
            })


@method_decorator(csrf_exempt, name='dispatch')
class PaymentTestAPIView(APIView):
    """支付测试接口"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """测试支付服务是否正常"""
        try:
            # 测试数据
            test_trade_no = f"TEST_{int(time.time())}"
            test_amount = "0.01"
            test_subject = "测试支付"
            
            # 尝试创建支付
            payment_result = payment_service.create_payment(
                trade_no=test_trade_no,
                total_amount=test_amount,
                subject=test_subject,
                use_mock=True  # 强制使用模拟支付进行测试
            )
            
            return JsonResponse({
                "code": 200,
                "success": True,
                "msg": "支付服务测试正常",
                "data": {
                    "payment_service": "正常",
                    "mock_service": "正常" if payment_service._mock_alipay else "异常",
                    "real_alipay": "正常" if payment_service._real_alipay else "不可用",
                    "test_payment_url": payment_result["payment_url"],
                    "payment_type": payment_result["payment_type"]
                }
            })
            
        except Exception as e:
            logger.error(f"支付服务测试失败: {str(e)}")
            return JsonResponse({
                "code": 500,
                "success": False,
                "msg": f"支付服务测试失败: {str(e)}",
                "data": None
            })