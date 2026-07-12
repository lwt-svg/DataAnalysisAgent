DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "muxi_shop",
        "USER": "root",
        "PASSWORD": "123456",
        "HOST": "localhost",
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET NAMES utf8mb4 COLLATE utf8mb4_general_ci",
        }
    }
}

IMAGE_URL = 'http://127.0.0.1:8000/static/product_images/'

# ======================= 支付宝沙箱环境配置 =======================
APPID = "9021000158614658"

# 本地开发配置
LOCAL_IP = "127.0.0.1"
LOCAL_PORT = "8000"
FRONTEND_PORT = "8080"

# 是否是开发环境（使用沙箱）
ALIPAY_DEBUG = True

# 异步通知URL（支付宝支付成功后，支付宝服务器会回调这个URL）
# 注意：本地测试时，支付宝无法访问 localhost，所以这个回调在本地无法工作
# 如果需要测试真实回调，需要使用内网穿透工具（如 ngrok）
APP_NOTIFY_URL = f"http://{LOCAL_IP}:{LOCAL_PORT}/pay/alipay/notify/"

# 同步返回URL（用户在支付宝页面支付成功后，会跳转回这个URL）
RETURN_URL = f"http://{LOCAL_IP}:{LOCAL_PORT}/pay/alipay/return/"

# 前端页面URL（用于跳转回前端）
FRONTEND_SUCCESS_URL = f"http://{LOCAL_IP}:{FRONTEND_PORT}/payment/success"
FRONTEND_FAIL_URL = f"http://{LOCAL_IP}:{FRONTEND_PORT}/payment/fail"

# 支付超时时间（分钟）
PAYMENT_TIMEOUT_MINUTES = 30

# 是否启用模拟支付（当支付宝沙箱回调不可用时启用）
# 本地测试建议设置为 True，使用模拟支付
ENABLE_MOCK_PAYMENT = True

# ======================= 密钥配置 =======================
# 商户私钥（从 apps/pay/keys/private_key.txt 读取）
PRIVATE_KEY_STRING = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAnG3yx++0J3QFBw6el1ERlT4y93lcfwr6WQcWIRw3AfXg7geLgPeotQXmVhKmNY+9AiZqQKTZRywQj9azxPuHy5SoI0+0PxR25vYTkWqNSJPsn0ZlB4z6VIWSwQC/KVFA349fXAd8e5Ptl/TwfzWyn+s3MdqCxNhkDv/sHawJ+VpiUeN53YXAEIhvD4XJw1RvDWiSqA24XUUAonyHjYTT6hEeDxSZ/JB3BFw2qmXg97pd9bGpCyTbpvQWP7iGRAHLxYQuwzkbPe3SzHa1d0VeSemq1BJVG7X33pguz6FG/pg/7/K8J+D7lloblsdF5azSvpdFcS/zvXpKtkScQHcihwIDAQABAoIBAE8e3Xl7KGf8Kr7TCiwG+Rm/iA/b9ojbiJyXFP5SQxBeyRIcBteIbHCDN2m5rQ/SUAtSWtOvjaaOByJ5uhucDadO3Wxe2BA/zZQsSuF2P1fCWiCFfnw/Ni6iEQRF2GqRinqJDfaCYtgujjIZ1brB8kMouZYhq5rcyF892rN3XOQdonq+V/Hr3FDGVl9kQQfbmxA4ixAcLfuTPfSUuVzH3MWBbj74Aoz8R2DkPl4NlPpaF2gAEG0E83akzHQwmthjIh3IA20n2/+5rnRG4LDteaQnsiuJAh6Aqlhe30IRNdtkw4MfMoEQN1C++QTXJUps7XvAY8YH4mJkx0IG4Kyz3UECgYEA6JZCPAJARZF/ddkFSO4anLLvSCo9lsWFCDPf1q+xVRSWzPQWfAXD8YkmVatKHezt4OPJb7fieU+Q7qfJqzPGmqEGlwo3j0PhBou3GK5bl27yFxO1W8bFweCbHkwjdzsKKVPs+meDBM85dfluOnK9310JA3EKpruSiF66MJjodm8CgYEArC0erBtvYZ+a+XpCGUCCDhGKmIzFPbyv3S/Zp/0r/QQjY6sV1IbTSK1hsGq8WD/4fuhE5Vpiehmp33QfDedQtEVftgS6LYs6cGWHwK67LBM17f3/ox3eIfdeSKL/V1/BIUSb2OsRwEcAca/hsYLLbQcPLDvshL/dfYY7iHLp4WkCgYEAz2r4xGVJhgD8R09zrBdTOj1EsPmilSuuuKLyUpW6MmK7HSnsR0wo8uTZf/rSjR93AGCDipLVcFPprzuI2JnC2rERnG7rH2NscRb2ARe07LZvRO85hBAe2giArSM/WZwYMsT6iFD5gbd/ydrYV11uQJzKZfxQgGK0idLYfnBOlxcCgYAaCazEzFVYxyFRryqF1RqV9BMopMlDX+Ccq5rX69KWLeUIMpxXipgzOn02h725/tqenpOkt7mCy5TEBTSZDq1GxeMGjMp3DsIks0YHXqVRsgoK1smtKlwoeNdaVsQUu5diZ5TGBi6mDFbF2ppgFO6cq1+hCeLn5HgjfoRMS0yRWQKBgQCPlMKrn2qT/qx9kyqWu/gqsUTXDHvc09igQDJqVO/tmPLWFb1UYYuufjvuaV0EAQvjvvcacRXqcX2j80El2RJf6ScsIR288jw4DxCP/4/5SAKQzz4Q65pcP5o9Z0VEHbn4TyyyPNEi4rhOd2DoLYpHY8U3vV8xQ4mQGiHI8zo9XA==
-----END RSA PRIVATE KEY-----"""

# 支付宝公钥（从 apps/pay/keys/alipay_key.txt 读取）
ALI_PUB_KEY_STRING = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAoj7Er4EKuTOsEEQOfU63yAChp9U4x8ElRJp9SujE2QPqrt0AqmH6zvJkPzlFi/1FTTxVb/sLEnSUWTVZi24NyhRzw2UHmKLnyyZ/W0GDFICDAUApDEdPXiRQCP9IC1Xb3/83TX8/LRQKrbkq1CiSPffywm2cNm3UL2vkp9RGpW8W6HgMARmginGZ2x2aUqbVe9ZyKu4jp+/fCLlX04TaXtjMZpeZNcVsZHcnIC6JqwF3147JkuacTmHoVq10YNYgso3Pb3wy1Nb7qwwbI6yRXxhiOvOLdbRodZBWbkvs7m3Nrq+QTgvttOCYZ5qgrK2Xy6skyyGzRov+WD0ebv1nkwIDAQAB
-----END PUBLIC KEY-----"""
