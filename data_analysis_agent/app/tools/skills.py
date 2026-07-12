# Skills - 预定义Tool调用链
# 设计目标：预定义常用业务流程的Tool编排
# 优势：
#   1. 避免LLM多轮决策，直接执行预定义流程，响应速度更快
#   2. 业务流程标准化，结果更稳定
#   3. 简单意图匹配即可触发完整分析流程

import time
import json
from typing import Dict, Any

from langchain.tools import tool

from .report_tool import generate_daily_report, generate_weekly_report
from .anomaly_tool import anomaly_patrol
from .ranking_tool import query_product_ranking, query_category_brand_ranking
from .comment_analysis_tool import analyze_product_comments, find_low_rated_products
from .rfm_tool import analyze_user_rfm
from .trend_analysis_tool import query_sales_trend


# Skill注册表：intent -> skill函数
SKILL_REGISTRY = {
    "daily_briefing": "daily_briefing",
    "weekly_review": "weekly_review",
    "anomaly_patrol": "anomaly_patrol",
    "product_deep_dive": "product_deep_dive"
}


def _get_skill_description() -> str:
    """返回所有Skill的描述（用于System Prompt）"""
    return """【预定义Skills】用户问题匹配以下场景时，直接调用对应Skill，无需多步推理：
1. daily_briefing - "今日日报"/"今日概览"/"今天经营情况" → run_skill("daily_briefing")
2. weekly_review - "本周周报"/"周复盘"/"本周经营总结" → run_skill("weekly_review")
3. anomaly_patrol - "异常巡检"/"今日有没有异常"/"巡检一下" → run_skill("anomaly_patrol")
4. product_deep_dive - "商品深度分析"/"重点商品复盘" → run_skill("product_deep_dive")
"""


@tool
def run_skill(skill_name: str, params: str = "{}") -> str:
    """
    执行预定义Skill（Tool调用链），避免LLM多轮决策。

    支持的Skill：
    - daily_briefing: 今日经营日报（6维数据并行查询）
    - weekly_review: 本周经营周报 + RFM用户分群
    - anomaly_patrol: 异常巡检（4个核心指标）
    - product_deep_dive: 商品深度分析（TOP排行 + 评论分析 + 差评商品）

    参数：
    - skill_name: Skill名称
    - params: JSON格式参数，可选

    返回：JSON格式，包含Skill执行结果和子Tool的输出
    """
    start_time = time.time()
    print(f"[Skill] 执行 {skill_name}, params={params}")

    try:
        params_dict = json.loads(params) if params else {}
    except:
        params_dict = {}

    if skill_name not in SKILL_REGISTRY:
        return f"未知Skill: {skill_name}，支持的Skill: {', '.join(SKILL_REGISTRY.keys())}"

    # 分发到具体Skill
    if skill_name == "daily_briefing":
        result = _skill_daily_briefing(params_dict)
    elif skill_name == "weekly_review":
        result = _skill_weekly_review(params_dict)
    elif skill_name == "anomaly_patrol":
        result = _skill_anomaly_patrol(params_dict)
    elif skill_name == "product_deep_dive":
        result = _skill_product_deep_dive(params_dict)
    else:
        return f"Skill {skill_name} 未实现"

    elapsed = time.time() - start_time
    result["skill_name"] = skill_name
    result["elapsed_sec"] = round(elapsed, 3)
    print(f"[Skill] {skill_name} 完成, 总耗时{elapsed:.3f}s")

    return json.dumps(result, ensure_ascii=False, default=str)


def _skill_daily_briefing(params: dict) -> dict:
    """Skill 1: 今日日报 - 直接调用generate_daily_report"""
    print("[Skill] daily_briefing → generate_daily_report")
    date_text = params.get("date")
    result_str = generate_daily_report.invoke({"date_text": date_text})
    try:
        result = json.loads(result_str)
        return {
            "skill": "daily_briefing",
            "description": "今日经营日报",
            "result": result,
            "tools_called": ["generate_daily_report"]
        }
    except:
        return {"skill": "daily_briefing", "error": result_str}


def _skill_weekly_review(params: dict) -> dict:
    """Skill 2: 本周周报 + RFM分群（2步调用）"""
    print("[Skill] weekly_review → generate_weekly_report + analyze_user_rfm")
    week_offset = params.get("week_offset", 0)

    # 第1步：生成周报（try-except防止单个工具失败导致整个Skill崩溃）
    try:
        report_str = generate_weekly_report.invoke({"week_offset": week_offset})
        try:
            report = json.loads(report_str)
        except:
            report = {"error": report_str[:500]}
        print(f"[Skill] weekly_report 完成, 结果长度={len(report_str)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        report = {"error": f"generate_weekly_report 执行失败: {str(e)}"}
        print(f"[Skill] weekly_report 失败: {e}")

    # 第2步：RFM分群（独立try-except，即使周报失败也尝试RFM）
    try:
        rfm_str = analyze_user_rfm.invoke({"time_range_text": "最近30天"})
        try:
            rfm = json.loads(rfm_str)
        except:
            rfm = {"error": rfm_str[:500]}
        print(f"[Skill] rfm_analysis 完成, 结果长度={len(rfm_str)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        rfm = {"error": f"analyze_user_rfm 执行失败: {str(e)}"}
        print(f"[Skill] rfm_analysis 失败: {e}")

    return {
        "skill": "weekly_review",
        "description": "本周经营周报 + 用户分群分析",
        "weekly_report": report,
        "rfm_analysis": rfm,
        "tools_called": ["generate_weekly_report", "analyze_user_rfm"]
    }


def _skill_anomaly_patrol(params: dict) -> dict:
    """Skill 3: 异常巡检 - 调用anomaly_patrol"""
    print("[Skill] anomaly_patrol → anomaly_patrol tool")
    result_str = anomaly_patrol.invoke({})
    try:
        result = json.loads(result_str)
        return {
            "skill": "anomaly_patrol",
            "description": "异常巡检（4个核心指标）",
            "result": result,
            "tools_called": ["anomaly_patrol"]
        }
    except:
        return {"skill": "anomaly_patrol", "error": result_str}


def _skill_product_deep_dive(params: dict) -> dict:
    """Skill 4: 商品深度分析 - TOP排行 + 评论分析 + 差评商品"""
    print("[Skill] product_deep_dive → 排行 + 评论 + 差评")
    time_range = params.get("time_range_text", "最近30天")

    # 并行执行3个查询（独立）
    import concurrent.futures

    def call_ranking():
        return query_product_ranking.invoke({
            "rank_by": "revenue",
            "time_range_text": time_range,
            "limit": 10
        })

    def call_category():
        return query_category_brand_ranking.invoke({
            "rank_by": "revenue",
            "group_by": "category",
            "time_range_text": time_range
        })

    def call_low_rated():
        return find_low_rated_products.invoke({
            "time_range_text": time_range,
            "limit": 5
        })

    ranking_result = None
    category_result = None
    low_rated_result = None

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f1 = executor.submit(call_ranking)
        f2 = executor.submit(call_category)
        f3 = executor.submit(call_low_rated)

        ranking_result = f1.result()
        category_result = f2.result()
        low_rated_result = f3.result()

    try:
        ranking = json.loads(ranking_result)
    except:
        ranking = {"error": ranking_result}

    try:
        category = json.loads(category_result)
    except:
        category = {"error": category_result}

    try:
        low_rated = json.loads(low_rated_result)
    except:
        low_rated = {"error": low_rated_result}

    return {
        "skill": "product_deep_dive",
        "description": "商品深度分析（TOP排行+品类分布+差评商品）",
        "top_products": ranking,
        "category_distribution": category,
        "low_rated_products": low_rated,
        "tools_called": ["query_product_ranking", "query_category_brand_ranking", "find_low_rated_products"]
    }


def match_skill(text: str) -> str:
    """
    意图文本匹配Skill名称（供agent.py调用，避免LLM决策）
    返回匹配的skill_name，无匹配返回None
    """
    if not text:
        return None
    t = text.lower()

    # daily_briefing
    if any(k in t for k in ["今日日报", "今日概览", "今日经营", "今天的日报", "今日报告", "日报"]):
        if not any(k in t for k in ["本周", "周报", "本月", "月报"]):
            return "daily_briefing"

    # weekly_review
    if any(k in t for k in ["本周周报", "周复盘", "本周经营", "本周总结", "周报", "本周报告"]):
        return "weekly_review"

    # anomaly_patrol
    if any(k in t for k in ["异常巡检", "巡检一下", "今日有没有异常", "巡检", "异常检查"]):
        return "anomaly_patrol"

    # product_deep_dive
    if any(k in t for k in ["商品深度分析", "商品复盘", "重点商品分析", "商品深度", "商品分析报告"]):
        return "product_deep_dive"

    return None
