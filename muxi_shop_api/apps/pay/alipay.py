# apps/pay/alipay.py
"""
支付宝支付模块
包含真实支付宝支付和模拟支付两种方案
"""
import base64
import json
import logging
import time
import hashlib
from datetime import datetime
from urllib.parse import quote, urlencode
from muxi_shop_api import settings
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

logger = logging.getLogger('alipay')

class AlipayService:
    """支付宝支付服务基类"""
    
    def __init__(self):
        self.app_id = settings.APPID
        self.debug = settings.ALIPAY_DEBUG
        self.enable_mock = settings.ENABLE_MOCK_PAYMENT
        
        # 沙箱环境和正式环境网关
        if self.debug:
            self.gateway = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
        else:
            self.gateway = "https://openapi.alipay.com/gateway.do"
        
        logger.info(f"支付宝服务初始化: app_id={self.app_id}, gateway={self.gateway}, debug={self.debug}")
    
    def create_payment_url(self, trade_no, total_amount, subject, **kwargs):
        """创建支付URL（基类方法，子类需要实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def verify_payment(self, data):
        """验证支付结果（基类方法，子类需要实现）"""
        raise NotImplementedError("子类必须实现此方法")


class RealAlipayService(AlipayService):
    """真实支付宝支付服务"""
    
    def __init__(self):
        super().__init__()
        
        # 加载密钥
        try:
            # 商户私钥
            self.app_private_key = RSA.import_key(settings.PRIVATE_KEY_STRING)
            logger.info("商户私钥加载成功")
            
            # 支付宝公钥
            self.alipay_public_key = RSA.import_key(settings.ALI_PUB_KEY_STRING)
            logger.info("支付宝公钥加载成功")
            
        except Exception as e:
            logger.error(f"密钥加载失败: {str(e)}")
            raise
    
    def create_payment_url(self, trade_no, total_amount, subject, **kwargs):
        """创建支付宝支付页面URL"""
        try:
            # 格式化金额（确保两位小数）
            total_amount_str = f"{float(total_amount):.2f}"
            
            # 构建业务参数
            biz_content = {
                "out_trade_no": str(trade_no),
                "total_amount": total_amount_str,
                "subject": subject,
                "product_code": "FAST_INSTANT_TRADE_PAY",
                "timeout_express": f"{settings.PAYMENT_TIMEOUT_MINUTES}m",
            }
            
            # 添加额外参数
            if kwargs:
                biz_content.update(kwargs)
            
            # 构建公共参数
            params = self._build_common_params("alipay.trade.page.pay", biz_content)
            
            # 生成签名
            signed_params = self._sign_params(params)
            
            # 构建完整URL
            payment_url = self._build_payment_url(signed_params)
            
            logger.info(f"支付宝支付URL生成成功: trade_no={trade_no}, amount={total_amount_str}")
            return payment_url
            
        except Exception as e:
            logger.error(f"创建支付宝支付URL失败: {str(e)}", exc_info=True)
            raise
    
    def verify_payment(self, data):
        """验证支付宝回调签名"""
        try:
            # 获取签名
            sign = data.get('sign')
            if not sign:
                logger.error("回调数据中没有签名")
                return False
            
            # 获取签名类型
            sign_type = data.get('sign_type', 'RSA2')
            
            # 准备验证数据（移除sign和sign_type）
            verify_data = {k: v for k, v in data.items() 
                          if k not in ['sign', 'sign_type']}
            
            # 对参数排序
            sorted_items = sorted(verify_data.items(), key=lambda x: x[0])
            
            # 构建待验证字符串
            sign_string = "&".join(f"{k}={v}" for k, v in sorted_items)
            
            # 验证签名
            if sign_type == 'RSA2':
                verifier = PKCS1_v1_5.new(self.alipay_public_key)
                digest = SHA256.new(sign_string.encode('utf-8'))
                
                try:
                    signature_bytes = base64.b64decode(sign)
                    is_valid = verifier.verify(digest, signature_bytes)
                    
                    if is_valid:
                        logger.info("支付宝回调签名验证成功")
                    else:
                        logger.warning("支付宝回调签名验证失败")
                    
                    return is_valid
                except Exception as e:
                    logger.error(f"签名验证异常: {str(e)}")
                    return False
            else:
                logger.error(f"不支持的签名类型: {sign_type}")
                return False
                
        except Exception as e:
            logger.error(f"验证支付宝回调失败: {str(e)}", exc_info=True)
            return False
    
    def _build_common_params(self, method, biz_content):
        """构建公共参数"""
        # 将biz_content转换为JSON字符串（紧凑格式）
        biz_content_str = json.dumps(biz_content, ensure_ascii=False, separators=(',', ':'))
        
        params = {
            "app_id": self.app_id,
            "method": method,
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": settings.APP_NOTIFY_URL,
            "return_url": settings.RETURN_URL,
            "biz_content": biz_content_str
        }
        
        return params
    
    def _sign_params(self, params):
        """对参数进行签名"""
        # 移除sign字段（如果存在）
        params.pop("sign", None)
        
        # 按字母顺序排序参数
        sorted_params = dict(sorted(params.items()))
        
        # 构建待签名字符串
        sign_string = "&".join(f"{k}={v}" for k, v in sorted_params.items())
        
        # 使用RSA2进行签名
        signer = PKCS1_v1_5.new(self.app_private_key)
        signature = signer.sign(SHA256.new(sign_string.encode('utf-8')))
        
        # Base64编码
        sign = base64.b64encode(signature).decode('utf-8')
        
        # 将签名添加到参数中
        signed_params = sorted_params.copy()
        signed_params['sign'] = sign
        
        return signed_params
    
    def _build_payment_url(self, params):
        """构建支付URL"""
        # 对参数值进行URL编码
        encoded_params = {}
        for key, value in params.items():
            # 特别处理biz_content，确保正确编码
            if key == 'biz_content':
                encoded_params[key] = quote(value, safe='')
            else:
                encoded_params[key] = quote(str(value), safe='')
        
        # 构建查询字符串
        query_string = "&".join(f"{k}={v}" for k, v in encoded_params.items())
        
        # 返回完整URL
        return f"{self.gateway}?{query_string}"


class MockAlipayService(AlipayService):
    """模拟支付服务（用于开发和测试）"""
    
    def __init__(self):
        super().__init__()
        self.mock_payments = {}  # 存储模拟支付状态
        logger.info("模拟支付服务初始化完成")
    
    def create_payment_url(self, trade_no, total_amount, subject, **kwargs):
        """创建模拟支付页面URL"""
        try:
            # 生成模拟支付页面URL
            # 这里我们直接使用 settings 中的配置，而不是 Site 模型
            mock_url = f"http://{settings.LOCAL_IP}:{settings.LOCAL_PORT}/pay/mock/pay/"
            
            # 添加参数
            params = {
                'trade_no': trade_no,
                'amount': total_amount,
                'subject': subject,
                'timestamp': int(time.time())
            }
            
            # 生成签名（模拟）
            params['sign'] = self._generate_mock_sign(params)
            
            # 构建查询字符串
            query_string = urlencode(params)
            payment_url = f"{mock_url}?{query_string}"
            
            # 初始化支付状态
            self.mock_payments[trade_no] = {
                'trade_no': trade_no,
                'amount': total_amount,
                'subject': subject,
                'status': 'created',  # 已创建
                'created_at': datetime.now().isoformat(),
                'paid_at': None,
                'payment_url': payment_url
            }
            
            logger.info(f"模拟支付URL生成成功: trade_no={trade_no}, amount={total_amount}")
            return payment_url
            
        except Exception as e:
            logger.error(f"创建模拟支付URL失败: {str(e)}", exc_info=True)
            raise
    
    def verify_payment(self, data):
        """验证模拟支付结果（始终返回成功）"""
        trade_no = data.get('out_trade_no')
        
        if not trade_no:
            return False
        
        # 检查支付状态
        if trade_no in self.mock_payments:
            payment = self.mock_payments[trade_no]
            if payment['status'] == 'paid':
                return True
        
        return False
    
    def process_mock_payment(self, trade_no, action='success'):
        """处理模拟支付"""
        if trade_no not in self.mock_payments:
            logger.error(f"未找到模拟支付记录: {trade_no}")
            return False
        
        payment = self.mock_payments[trade_no]
        
        if action == 'success':
            payment['status'] = 'paid'
            payment['paid_at'] = datetime.now().isoformat()
            logger.info(f"模拟支付成功: trade_no={trade_no}")
            return True
        elif action == 'cancel':
            payment['status'] = 'cancelled'
            logger.info(f"模拟支付取消: trade_no={trade_no}")
            return True
        else:
            payment['status'] = 'failed'
            logger.info(f"模拟支付失败: trade_no={trade_no}")
            return False
    
    def get_payment_status(self, trade_no):
        """获取支付状态"""
        if trade_no in self.mock_payments:
            return self.mock_payments[trade_no]['status']
        return None
    
    def _generate_mock_sign(self, params):
        """生成模拟签名（用于测试）"""
        # 简单地将参数排序后拼接，然后取MD5
        sign_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return hashlib.md5(sign_string.encode()).hexdigest()


class PaymentService:
    """支付服务工厂类"""
    
    _instance = None
    _real_alipay = None
    _mock_alipay = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_services()
        return cls._instance
    
    def _init_services(self):
        """初始化支付服务"""
        try:
            # 初始化真实支付宝服务
            self._real_alipay = RealAlipayService()
            logger.info("真实支付宝服务初始化成功")
        except Exception as e:
            logger.warning(f"真实支付宝服务初始化失败，将使用模拟支付: {str(e)}")
            self._real_alipay = None
        
        # 初始化模拟支付服务
        self._mock_alipay = MockAlipayService()
        logger.info("模拟支付服务初始化成功")
    
    def get_alipay_service(self, force_mock=False):
        """获取支付宝支付服务"""
        if force_mock:
            return self._mock_alipay
        
        # 根据配置决定使用哪种支付方式
        if settings.ENABLE_MOCK_PAYMENT and self._real_alipay is None:
            return self._mock_alipay
        
        # 优先使用真实支付宝
        return self._real_alipay if self._real_alipay else self._mock_alipay
    
    def create_payment(self, trade_no, total_amount, subject, use_mock=None, **kwargs):
        """创建支付"""
        # 决定使用哪种支付方式
        if use_mock is None:
            use_mock = settings.ENABLE_MOCK_PAYMENT and self._real_alipay is None
        
        if use_mock:
            service = self._mock_alipay
            payment_type = "mock"
        else:
            service = self._real_alipay if self._real_alipay else self._mock_alipay
            payment_type = "alipay" if self._real_alipay else "mock"
        
        # 创建支付URL
        payment_url = service.create_payment_url(trade_no, total_amount, subject, **kwargs)
        
        return {
            "payment_url": payment_url,
            "payment_type": payment_type,
            "trade_no": trade_no,
            "service": service
        }
    
    def verify_payment(self, data, payment_type="alipay"):
        """验证支付结果"""
        if payment_type == "alipay" and self._real_alipay:
            return self._real_alipay.verify_payment(data)
        else:
            return self._mock_alipay.verify_payment(data)


# 创建全局支付服务实例
payment_service = PaymentService()