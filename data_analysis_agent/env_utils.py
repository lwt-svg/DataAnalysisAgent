# 环境变量加载工具

from dotenv import load_dotenv
import os

load_dotenv(override=True)

# 智谱GLM
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL")

# 通义千问（备用）
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL")

# DeepSeek（备用）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
