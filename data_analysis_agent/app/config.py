import os

# 加载.env文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv未安装时降级为纯环境变量

# ======================= 基础配置 =======================
JWT_SECRET_KEY = "django-insecure-9jal3=*t5n-!8^ns-w9&yw7j9s1g&niy+q!em-x=-wun129zrj"
JWT_ALGORITHM = "HS256"

# 复用同一数据库（与购物助手共享muxi_shop库）
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "muxi_shop"
}

ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:80",
    "http://127.0.0.1",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:8082",
    "http://127.0.0.1:8082"
]

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0") 

# ======================= 性能配置 =======================
SQL_QUERY_TIMEOUT = 10           # SQL查询超时10秒
SQL_MAX_ROWS = 1000              # 单次查询最大返回行数
DEFAULT_TIME_RANGE_DAYS = 30     # 默认时间范围30天
CHART_MAX_POINTS = 90            # 趋势图最大数据点数（90天）

# ======================= 查询缓存配置 =======================
SQL_CACHE_ENABLED = True         # 是否启用SQL查询缓存
SQL_CACHE_TTL = 300              # 缓存TTL 5分钟（300秒）

# ======================= LangFuse 可观测性配置 =======================
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
