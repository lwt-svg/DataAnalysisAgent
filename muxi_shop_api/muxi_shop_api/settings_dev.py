DATABASES = {
    "default": {
        #"ENGINE": "django.db.backends.sqlite3",
        #"NAME": BASE_DIR / "db.sqlite3",
        "ENGINE": "django.db.backends.mysql",
        "NAME": "muxi_shop",
        "USER": "admin",
        "PASSWORD": "123456",
        "HOST": "192.168.1.119",
    }
}
IMAGE_URL='http://localhost:8000/static/product_images/'

#支付宝沙箱环境配置
APPID = "9021000158614658"	
#异步接收url
APP_NOTIFY_URL = "http://127.0.0.1:8000/alipay/notify"
#同步url 就是用户在页面上支付成功之后，然后就跳转的页面
RETURN_URL="http://127.0.0.1:8000/alipay/return"
#是否是开发环境
ALIPAY_DEBUG=True