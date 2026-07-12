# 请求/响应模型

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AnalysisRequest(BaseModel):
    """数据分析请求"""
    message: str
    session_id: Optional[str] = None
    token: Optional[str] = None
    user_email: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None


class AnalysisResponse(BaseModel):
    """数据分析响应"""
    response: str
    session_id: Optional[str] = None
    timestamp: str
    source: Optional[str] = None       # tool / llm / skill
    chart_data: Optional[Dict[str, Any]] = None  # 图表数据（前端渲染用）
