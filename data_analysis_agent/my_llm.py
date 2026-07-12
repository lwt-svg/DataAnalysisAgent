# LLM配置

from langchain_openai import ChatOpenAI
from env_utils import ZHIPU_API_KEY, ZHIPU_BASE_URL


# 智谱GLM-4.7-flash
llm = ChatOpenAI(
    model_name="glm-4.7-flash",
    temperature=0.3,  # 数据分析场景温度更低，结果更稳定
    api_key=ZHIPU_API_KEY,
    base_url=ZHIPU_BASE_URL,
    max_completion_tokens=2048,  # 数据分析需要更长输出
)
