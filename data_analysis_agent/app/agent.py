# 数据分析Agent - Multi-Agent Supervisor 架构
# 设计目标：
#   1. Supervisor 负责意图识别和路由
#   2. 三个子Agent按职责分组绑定不同Tool，避免LLM被无关Tool干扰
#       - SQL Agent:  execute_analytics_sql（销售/订单查询）
#       - Analysis Agent: 趋势/排行/RFM/异常/评论工具
#       - Report Agent: 日报/周报/Skill
#   3. Skill优先匹配（避免LLM多轮决策，最快路径）
#   4. 通用问题LLM直接回复

import re
import json
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

import redis.asyncio as redis
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from my_llm import llm
from .tools import (
    all_tool_funcs,
    execute_analytics_sql,
    query_sales_trend,
    query_product_ranking, query_category_brand_ranking,
    analyze_user_rfm,
    detect_anomaly, anomaly_patrol,
    analyze_product_comments, find_low_rated_products,
    generate_daily_report, generate_weekly_report,
    run_skill, match_skill
)
from .schema import get_database_schema
from .config import REDIS_URL


# ================== 配置 ==================
SESSION_TTL = 1800
MAX_RECENT_MESSAGES = 3
MAX_CONTEXT_MESSAGES = 4
MAX_TOOL_CALLS = 5  # 单次对话最大Tool调用次数（防无限循环）

# 按职责分组的Tool集
SQL_AGENT_TOOLS = [execute_analytics_sql]
ANALYSIS_AGENT_TOOLS = [
    query_sales_trend,
    query_product_ranking, query_category_brand_ranking,
    analyze_user_rfm,
    detect_anomaly,
    analyze_product_comments, find_low_rated_products,
]
REPORT_AGENT_TOOLS = [
    generate_daily_report, generate_weekly_report,
    run_skill, anomaly_patrol
]

# Schema只加载一次（启动时）
SCHEMA_INFO = get_database_schema()

# Redis客户端（连不上时降级为None，会话缓存不生效但不影响主流程）
_redis_client = None
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    print(f"⚠️ Redis客户端创建失败: {e}，会话缓存功能将不可用")
    redis_client = None

# 各子Agent绑定各自Tool
llm_sql = llm.bind_tools(SQL_AGENT_TOOLS)
llm_analysis = llm.bind_tools(ANALYSIS_AGENT_TOOLS)
llm_report = llm.bind_tools(REPORT_AGENT_TOOLS)
llm_general = llm  # 通用回复不绑Tool


# ================== 429重试机制 ==================
import asyncio

async def _llm_invoke_with_retry(llm_instance, messages, max_retries=3):
    """
    带重试的LLM调用：
    - 遇到429速率限制时等待后重试
    - 遇到400 contentFilter（内容审查）时简化messages后重试
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            response = await llm_instance.ainvoke(messages)
            return response
        except Exception as e:
            last_error = e
            error_str = str(e)
            # 检测429速率限制
            if "429" in error_str or "速率限制" in error_str or "RateLimit" in error_str:
                wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                print(f"⚠️ 智谱API速率限制(429)，{wait_time}秒后重试（第{attempt+1}/{max_retries}次）")
                await asyncio.sleep(wait_time)
                continue
            # 检测400内容审查（contentFilter）— 简化messages后重试
            if "1301" in error_str or "contentFilter" in error_str or "敏感内容" in error_str:
                print(f"⚠️ 智谱API内容审查(1301)，简化messages后重试（第{attempt+1}/{max_retries}次）")
                # 降级策略：去掉SystemMessage，只保留最后一条HumanMessage
                # 如果还是触发审查，第二次用纯中文简洁提示
                if attempt == 0:
                    simplified = []
                    for msg in messages:
                        if isinstance(msg, HumanMessage):
                            simplified.append(msg)
                    if not simplified:
                        simplified = [HumanMessage(content="请生成一份经营分析报告。")]
                    messages = simplified
                else:
                    # 第二次重试：用极简中文提示，避免任何可能触发审查的英文/符号
                    messages = [HumanMessage(content="请调用工具生成本周经营周报。")]
                await asyncio.sleep(1)
                continue
            # 其他错误直接抛出
            raise e
    # 重试耗尽，抛出最后一个错误
    raise last_error

print("[Agent] 工具分组:")
print(f"  SQL Agent: {[t.name for t in SQL_AGENT_TOOLS]}")
print(f"  Analysis Agent: {[t.name for t in ANALYSIS_AGENT_TOOLS]}")
print(f"  Report Agent: {[t.name for t in REPORT_AGENT_TOOLS]}")


# ================== 意图识别 ==================
def is_sales_query(text: str) -> bool:
    """销售查询：GMV/销售额/收入/客单价/转化率/卖了"""
    keywords = ["销售额", "gmv", "收入", "营收", "客单价", "转化率", "卖了多少钱",
                "成交额", "总销售", "今日销售", "本月销售",
                "销售数据", "销售情况", "销售量", "销售是多少", "销售多少",
                "卖了多少", "消费数据", "消费多少"]
    return any(k in text for k in keywords)


def is_trend_query(text: str) -> bool:
    """趋势分析：趋势/环比/同比/增长/变化/走势"""
    keywords = ["趋势", "环比", "同比", "增长", "变化", "走势", "上升", "下降",
                "对比上月", "比上个月", "比上周", "比昨天"]
    return any(k in text for k in keywords)


def is_ranking_query(text: str) -> bool:
    """商品排行：排行/卖得好/滞销/销量/热销/Top"""
    keywords = ["排行", "排行榜", "卖得最好", "热销", "top", "销量榜", "滞销",
                "top5", "top10", "前几名", "排名"]
    return any(k in text.lower() for k in keywords)


def is_user_analysis_query(text: str) -> bool:
    """用户分析：用户/客户/RFM/核心用户/性别分布"""
    keywords = ["用户分群", "rfm", "核心用户", "高价值用户", "活跃用户",
                "用户分析", "客户分析", "复购率", "用户画像", "用户分布"]
    return any(k in text.lower() for k in keywords)


def is_order_query(text: str) -> bool:
    """订单分析：订单/待支付/退款/支付状态"""
    keywords = ["订单分析", "待支付", "退款", "支付状态", "订单情况",
                "订单统计", "未支付", "已支付订单"]
    return any(k in text for k in keywords)


def is_complex_analysis_query(text: str) -> bool:
    """复杂分析：品类筛选/品牌筛选/毛利/退货率/多条件组合
    这类查询需要灵活的Text2SQL，路由到sql_agent
    """
    keywords = [
        # 品类/品牌筛选（支持"手机"和"手机类"两种说法）
        "手机", "电器", "美妆", "女装", "男装", "零食", "数码", "服饰",
        "服装", "鞋", "包", "食品", "家电", "电脑", "配件",
        "类目", "品类", "品牌", "分类",
        # 毛利/成本
        "毛利", "毛利率", "利润", "成本", "采购价",
        # 退货率/取消率
        "退货率", "退换货", "取消率",
        # 多条件组合（包含"且""并""同时"等连接词）
    ]
    # 品类/品牌/毛利/退货率关键词
    if any(k in text for k in keywords):
        return True
    # 多条件组合：同时包含数值筛选条件（如"低于XX""超过XX"）+ 商品/订单相关词
    has_condition = bool(re.search(r"(低于|超过|高于|小于|大于|不低于|不超过|至少|最多)\s*\d", text))
    has_subject = any(k in text for k in ["商品", "产品", "客单价", "销量", "评分"])
    if has_condition and has_subject:
        return True
    return False


def is_comment_query(text: str) -> bool:
    """评论分析：评分/评论/好评/差评/评分分布"""
    keywords = ["评论分析", "评分分布", "好评率", "差评", "评分情况",
                "评论情况", "用户评价", "商品评分", "平均分"]
    return any(k in text for k in keywords)


def is_anomaly_query(text: str) -> bool:
    """异常检测：异常/正常吗/有没有问题/不对劲"""
    keywords = ["异常", "不正常", "有没有问题", "不对劲", "奇怪",
                "为什么降低", "为什么下降", "突变", "暴涨", "暴跌"]
    return any(k in text for k in keywords)


def is_report_query(text: str) -> bool:
    """报告生成：报告/日报/周报/月报/总结"""
    keywords = ["报告", "日报", "周报", "月报", "总结", "汇报", "复盘"]
    return any(k in text for k in keywords)


def detect_analysis_intent(text: str) -> str:
    """识别9种意图，返回意图标签"""
    text = text or ""

    # 优先检测报告类（因为"日报"包含"日"，可能误匹配其他）
    if is_report_query(text):
        return "report_generation"
    if is_anomaly_query(text):
        return "anomaly_check"
    # 复杂分析优先（品类/毛利/退货率/多条件组合，需要Text2SQL）
    if is_complex_analysis_query(text):
        return "complex_analysis"
    if is_user_analysis_query(text):
        return "user_analysis"
    if is_trend_query(text):
        return "trend_analysis"
    if is_ranking_query(text):
        return "product_ranking"
    if is_comment_query(text):
        return "comment_analysis"
    if is_sales_query(text):
        return "sales_query"
    if is_order_query(text):
        return "order_analysis"

    return "general"


# 路由映射：意图 → 子Agent节点
INTENT_TO_NODE = {
    "sales_query": "sql_agent",
    "order_analysis": "sql_agent",
    "complex_analysis": "sql_agent",  # 复杂分析走sql_agent（Text2SQL最灵活）
    "trend_analysis": "analysis_agent",
    "product_ranking": "analysis_agent",
    "user_analysis": "analysis_agent",
    "comment_analysis": "analysis_agent",
    "anomaly_check": "analysis_agent",
    "report_generation": "report_agent",
    "general": "general_agent"
}


# ================== 系统提示词 ==================
def build_system_prompt(agent_type: str = "supervisor") -> str:
    """根据Agent类型构造System Prompt"""
    common_rule = """【最高优先级规则 - 必须遵守】
- 【禁止编造数据】你没有任何预置数据记忆，所有数据必须通过工具查询获得
- 【必须调用工具】对于任何涉及具体数字、日期、商品名称、用户信息的查询，你必须先调用工具查询，再基于工具返回的结果回复
- 【不调工具就不回复数字】如果你没有调用工具，你的回复中不应该包含任何具体数字、金额、百分比、日期
- 【基于工具结果回复】工具返回什么数据，你就基于什么数据回复。如果工具返回空结果，告诉用户"未查询到相关数据"

【格式规则】
- 所有查询必须带时间范围，默认"最近30天"
- 金额统一用"元"，百分比保留1位小数
- 排行榜默认返回TOP10
- 数据用Markdown表格呈现（用|分隔列，用---分隔表头和内容），简洁明了
- 列表用"-"标记（不用"*"），加粗用"**text**"
- 【重要】绝对不要在文字回复中输出chart_data的JSON代码块（如```json ... ```），图表数据会由系统自动作为独立字段返回给前端，你只需输出文字分析和表格
- 回复中禁止包含任何```json```或```代码块，只输出纯Markdown文字和表格

【复杂查询处理指引】
当用户提出复杂分析问题时（如多条件筛选、品类分析、毛利分析等），按以下策略处理：
1. 品类/品牌筛选：用WHERE goods.main_category LIKE '%手机%'或main_brand LIKE '%华为%'
   [需JOIN goods表: order_goods.sku_id = goods.sku_id]
   【品类名称映射】用户说的品类名和数据库实际品类名可能不同，SQL中用LIKE匹配：
   - "服装"/"衣服"/"男装"/"女装" → main_category LIKE '%服饰%'
   - "手机"/"手机数码" → main_category LIKE '%手机%'
   - "电子产品"/"电子商品" → main_category LIKE '%电子%'
   - "电脑"/"办公" → main_category LIKE '%电脑%'
   - "食品"/"零食"/"饮料" → main_category LIKE '%食品%'
   - "美妆"/"化妆品"/"护肤" → main_category LIKE '%美妆%'
   - 查询品类时建议用宽泛匹配（如'%服饰%'而非精确'服饰鞋靴'），避免漏掉数据
2. 客单价筛选：先用SQL算出每类商品的客单价，再用HAVING筛选（如HAVING 客单价 < 90）
3. 退货率/取消率：用pay_status='2'计算（pay_status: 0=待支付,1=已支付,2=已取消/退货）
4. 毛利分析：毛利 = (goods.jd_price - goods.p_price) * order_goods.goods_num
5. 多条件组合：可在一条SQL中用多个WHERE/HAVING条件组合
6. 无法精确计算的概念（如"引流款""爆款"）：向用户说明数据限制，用近似指标替代
   - 引流款 ≈ 销量高但单价低的商品（如jd_price < 50 且 销量 TOP20%）
   - 爆款 ≈ 销量+销售额双高的商品
   - 转化率 ≈ 支付率（无浏览数据，用pay_status='1'占比近似）
"""

    if agent_type == "supervisor":
        return f"""你是电商数据分析助手的主管(Supervisor)，负责识别用户意图并路由到对应子Agent。

{common_rule}

【支持的分析场景】
1. 销售查询：GMV、销售额、收入、客单价
2. 趋势分析：环比、同比、增长走势
3. 商品排行：销量榜、收入榜、热销/滞销
4. 用户分析：RFM分群、核心用户识别
5. 订单分析：订单统计、支付状态
6. 评论分析：评分分布、好评率、差评商品
7. 异常检测：指标异常、Z-Score检测
8. 报告生成：日报、周报

【预定义Skills】（用户提到以下场景时优先调用run_skill）
- daily_briefing: "今日日报"/"今日概览"
- weekly_review: "本周周报"/"周复盘"
- anomaly_patrol: "异常巡检"/"巡检一下"
- product_deep_dive: "商品深度分析"

DB结构：
{SCHEMA_INFO}

中文简洁回复。"""

    elif agent_type == "sql_agent":
        return f"""你是数据分析助手的SQL查询子Agent，负责通过execute_analytics_sql工具执行SQL查询。
你不仅能处理简单的销售/订单查询，还能处理复杂的品类分析、毛利分析、多条件组合查询。

{common_rule}

【核心规则】
- 必须调用execute_analytics_sql工具执行查询，禁止直接输出SQL语句
- 工具会自动注入时间范围和LIMIT，你只需提供SQL和time_range_text
- SQL只允许SELECT，必须包含LIMIT
- 涉及order/order_goods/comment表时，传入time_range_text参数（如"最近30天"）

【重要：多表JOIN必须用表前缀】
当SQL涉及JOIN多个表时，所有字段必须使用表前缀，否则会报"Column is ambiguous"错误。
- create_time字段在order、order_goods、comment三张表中都存在，多表JOIN时必须写`order`.create_time或order_goods.create_time
- 其他同名字段也要加前缀，如order.trade_no、order_goods.trade_no
- 正确示例：SELECT DATE(`order`.create_time) AS 日期 FROM order_goods JOIN `order` ON ...
- 错误示例：SELECT DATE(create_time) AS 日期 FROM order_goods JOIN `order` ON ...（会报错）

【复杂查询能力】
你可以生成多表JOIN和聚合查询，例如：
- 品类销售分析：JOIN order_goods + goods + \`order\`，WHERE goods.main_category LIKE '%手机%'
- 毛利分析：SELECT (goods.jd_price - goods.p_price) * order_goods.goods_num AS 毛利
- 多条件筛选：用WHERE + HAVING组合（如HAVING 客单价 < 90 AND 退货率 > 15）
- 品类趋势对比：GROUP BY 日期 + 品类，对比不同品类的销售趋势

【工具参数说明】
- sql: SELECT查询语句（必须含LIMIT）
- time_range_text: 时间范围描述（如"最近30天"、"今天"、"上周"）

DB结构：
{SCHEMA_INFO}"""

    elif agent_type == "analysis_agent":
        return f"""你是数据分析助手的分析子Agent，负责调用分析工具进行数据洞察。

{common_rule}

【可用工具】
- query_sales_trend: 趋势分析（GMV/订单量/客单价/用户数的时间序列+环比）
- query_product_ranking: 商品排行榜（按销售额/销量/评论数）
- query_category_brand_ranking: 品类/品牌排行榜
- analyze_user_rfm: RFM用户分群分析
- detect_anomaly: 异常检测（Z-Score，7/14/30日窗口）
- analyze_product_comments: 商品评论分析（评分分布+趋势）
- find_low_rated_products: 差评商品查找

【强制规则】
- 【必须调用工具】收到用户问题后，你必须调用上述工具之一来获取数据，禁止直接回复
- 【禁止编造】如果工具返回空结果，告诉用户"未查询到相关数据"，不要编造数据
- 工具返回的chart_data直接转给前端，不要在文字中重复数据
- 用简洁文字+表格+关键洞察的格式回复

DB结构：
{SCHEMA_INFO}"""

    elif agent_type == "report_agent":
        return f"""你是数据分析助手的报告子Agent，负责生成经营报告。

{common_rule}

【可用工具】
- generate_daily_report: 生成今日经营日报（6维数据并行查询）
- generate_weekly_report: 生成本周经营周报
- run_skill: 执行预定义Skill（daily_briefing/weekly_review/anomaly_patrol/product_deep_dive）
- anomaly_patrol: 异常巡检

【规则】
- 用户问"日报"→调用generate_daily_report或run_skill("daily_briefing")
- 用户问"周报"→调用generate_weekly_report或run_skill("weekly_review")
- 报告生成后，将Markdown内容直接返回给用户
- 工具返回的chart_data直接转给前端

DB结构：
{SCHEMA_INFO}"""

    else:  # general_agent
        return f"""你是电商数据分析助手，帮助商家解答经营相关问题。

{common_rule}

如果用户的问题不需要查询数据，可以基于常识直接回答。
如果需要查询数据，请告知用户可以提问的具体方向（如销售查询、趋势分析等）。

DB结构：
{SCHEMA_INFO}"""


# ================== State ==================
class AnalysisAgentState(MessagesState):
    intent: Optional[str]                # 识别出的意图
    target_node: Optional[str]           # 路由目标节点
    time_range_text: Optional[str]       # 时间范围描述
    skill_name: Optional[str]            # 匹配的Skill名
    query_result_cache: Optional[Dict]   # 缓存查询结果（报告生成多步复用）


# ================== Supervisor 节点 ==================
async def supervisor_node(state: AnalysisAgentState) -> Dict[str, Any]:
    """
    Supervisor节点：识别意图 + 路由
    不调用LLM，纯规则匹配，响应最快
    """
    last_user_msg = ""
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content or ""
            break

    # 提取用户问题（去掉"当前登录用户"等前缀）
    text = last_user_msg
    m = re.search(r"用户问题[:：]\s*(.*)", text, re.S)
    if m:
        text = m.group(1).strip()

    # 1. 优先匹配Skill
    skill_name = match_skill(text)

    # 2. 识别意图
    intent = detect_analysis_intent(text)

    # 3. 决定路由
    if skill_name:
        target_node = "report_agent"  # Skill走report_agent
        print(f"[Supervisor] 匹配Skill: {skill_name}, 路由到 report_agent")
    else:
        target_node = INTENT_TO_NODE.get(intent, "general_agent")
        print(f"[Supervisor] 意图: {intent}, 路由到: {target_node}")

    return {
        "intent": intent,
        "target_node": target_node,
        "skill_name": skill_name,
        "messages": state.get("messages", [])
    }


def route_from_supervisor(state: AnalysisAgentState) -> str:
    """路由函数：根据target_node返回下一节点名"""
    return state.get("target_node", "general_agent")


# ================== SQL Agent 节点 ==================
async def sql_agent_node(state: AnalysisAgentState) -> Dict[str, Any]:
    """SQL子Agent：处理销售/订单查询"""
    messages = state.get("messages", [])
    system_msg = SystemMessage(content=build_system_prompt("sql_agent"))
    context_msgs = _build_llm_messages(messages, MAX_CONTEXT_MESSAGES)

    # 检测是否已有Tool结果：仅当最后一条是ToolMessage时才跳过工具（说明当前查询周期的工具刚执行完）
    # 注意：不能检查所有消息，否则多轮对话中上一轮的ToolMessage会导致新查询跳过工具调用
    has_tool_result = len(messages) > 0 and isinstance(messages[-1], ToolMessage)
    if has_tool_result:
        response = await _llm_invoke_with_retry(llm, [system_msg] + context_msgs)
    else:
        response = await _llm_invoke_with_retry(llm_sql, [system_msg] + context_msgs)
    return {"messages": [response]}


# ================== Analysis Agent 节点 ==================
async def analysis_agent_node(state: AnalysisAgentState) -> Dict[str, Any]:
    """分析子Agent：处理趋势/排行/用户/异常/评论分析"""
    messages = state.get("messages", [])
    system_msg = SystemMessage(content=build_system_prompt("analysis_agent"))
    context_msgs = _build_llm_messages(messages, MAX_CONTEXT_MESSAGES)

    has_tool_result = len(messages) > 0 and isinstance(messages[-1], ToolMessage)
    if has_tool_result:
        response = await _llm_invoke_with_retry(llm, [system_msg] + context_msgs)
    else:
        response = await _llm_invoke_with_retry(llm_analysis, [system_msg] + context_msgs)
    return {"messages": [response]}


# ================== Report Agent 节点 ==================
async def _fallback_call_skill(skill_name: str) -> dict:
    """
    降级方案：手动调用Skill并生成回复。
    用于LLM调用失败、返回空响应、或触发内容审查时。
    返回 {"messages": [ToolMessage, AIMessage], "skill_name": None}
    """
    print(f"[ReportAgent] 降级方案：手动调用Skill: {skill_name}")
    try:
        from .tools import run_skill as _run_skill_tool
        skill_result = await _run_skill_tool.ainvoke({"skill_name": skill_name, "params": "{}"})
        skill_result_str = str(skill_result)
        print(f"[ReportAgent] Skill手动执行完成, 结果长度={len(skill_result_str)}")
        # 构造ToolMessage（让main.py能从中提取chart_data）
        tool_msg = ToolMessage(content=skill_result_str, tool_call_id="fallback_skill_call")
        # 从Skill返回的JSON中提取markdown报告作为回复内容
        fallback_text = _extract_report_from_skill_result(skill_result_str, skill_name)
        # 用普通LLM总结结果（不带tools，可能不会触发审查/限速）
        cleaned_for_llm = _strip_chart_data_from_tool_result(skill_result_str)
        summary_msg = HumanMessage(content=f"以下是工具返回的经营报告数据，请基于此生成简洁的总结（不要重复表格数据，只输出关键洞察）：\n{cleaned_for_llm[:6000]}")
        try:
            summary_response = await _llm_invoke_with_retry(llm, [summary_msg])
            print(f"[ReportAgent] LLM总结完成(降级), response长度={len(summary_response.content) if summary_response.content else 0}")
            return {"messages": [tool_msg, summary_response], "skill_name": None}
        except Exception as e2:
            print(f"[ReportAgent] LLM总结也失败: {e2}，使用提取的markdown报告作为最终回复")
            fallback_response = AIMessage(content=fallback_text)
            return {"messages": [tool_msg, fallback_response], "skill_name": None}
    except Exception as e2:
        print(f"[ReportAgent] 手动调用Skill也失败: {e2}")
        raise


async def report_agent_node(state: AnalysisAgentState) -> Dict[str, Any]:
    """报告子Agent：处理报告生成 + Skill执行"""
    messages = state.get("messages", [])

    # 检查是否已有ToolMessage（说明Skill已执行过）——仅看最后一条，避免多轮对话污染
    has_tool_result = len(messages) > 0 and isinstance(messages[-1], ToolMessage)

    skill_name = state.get("skill_name")
    print(f"[ReportAgent] 进入, skill_name={skill_name}, has_tool_result={has_tool_result}, messages_count={len(messages)}")

    if skill_name and not has_tool_result:
        # 首次进入且匹配到Skill，注入Skill调用提示
        skill_hint = HumanMessage(
            content=f"请直接调用 run_skill 工具，参数 skill_name='{skill_name}'，params='{{}}'"
        )
        messages_for_llm = [skill_hint]
        print(f"[ReportAgent] 注入Skill提示: {skill_name}")
    else:
        # Skill已执行或无Skill，正常处理（含工具结果）
        messages_for_llm = _build_llm_messages(messages, MAX_CONTEXT_MESSAGES)
        print(f"[ReportAgent] 使用工具结果总结, messages_for_llm长度={len(messages_for_llm)}")

    system_msg = SystemMessage(content=build_system_prompt("report_agent"))

    # 有Tool结果时用普通LLM（不bind_tools），避免LLM又调工具导致循环
    try:
        if has_tool_result:
            response = await _llm_invoke_with_retry(llm, [system_msg] + messages_for_llm)
            print(f"[ReportAgent] LLM总结完成, response长度={len(response.content) if response.content else 0}")
        else:
            response = await _llm_invoke_with_retry(llm_report, [system_msg] + messages_for_llm)
            tool_calls_count = len(response.tool_calls) if response.tool_calls else 0
            print(f"[ReportAgent] LLM调用工具完成, tool_calls={tool_calls_count}")
            # 新增：LLM返回空响应（无tool_calls且无content）时，走降级方案
            if tool_calls_count == 0 and not response.content and skill_name:
                print(f"[ReportAgent] LLM返回空响应，触发降级方案")
                return await _fallback_call_skill(skill_name)
    except Exception as e:
        # LLM调用失败（如contentFilter审查/429限速），走降级方案
        if skill_name and not has_tool_result:
            print(f"[ReportAgent] LLM调用失败({str(e)[:100]})，触发降级方案")
            return await _fallback_call_skill(skill_name)
        else:
            print(f"[ReportAgent] LLM调用失败: {e}")
            raise

    # 清除skill_name，避免循环
    return {"messages": [response], "skill_name": None}


# ================== General Agent 节点 ==================
async def general_agent_node(state: AnalysisAgentState) -> Dict[str, Any]:
    """通用Agent：处理不明确的问题"""
    messages = state.get("messages", [])
    system_msg = SystemMessage(content=build_system_prompt("general_agent"))
    context_msgs = _build_llm_messages(messages, MAX_CONTEXT_MESSAGES)
    response = await _llm_invoke_with_retry(llm_general, [system_msg] + context_msgs)
    return {"messages": [response]}


def _strip_chart_data_from_tool_result(result_str: str) -> str:
    """
    从工具返回的JSON字符串中剥离chart_data字段，减少传给LLM的内容。
    chart_data是给前端的图表数据，LLM不需要看，剥离后可大幅减少输入长度。
    如果解析失败，返回原始字符串。
    """
    if not result_str or not result_str.strip().startswith("{"):
        return result_str
    try:
        parsed = json.loads(result_str)
        _remove_chart_data_recursive(parsed)
        return json.dumps(parsed, ensure_ascii=False, default=str)
    except:
        return result_str


def _remove_chart_data_recursive(obj):
    """递归删除dict/list中的chart_data字段"""
    if isinstance(obj, dict):
        obj.pop("chart_data", None)
        for v in obj.values():
            _remove_chart_data_recursive(v)
    elif isinstance(obj, list):
        for item in obj:
            _remove_chart_data_recursive(item)


def _extract_report_from_skill_result(skill_result_str: str, skill_name: str) -> str:
    """
    从Skill返回的JSON中提取markdown报告，作为LLM不可用时的最终回复。
    支持的Skill返回结构：
    - daily_briefing: {"result": {"markdown": "...", ...}}
    - weekly_review:  {"weekly_report": {"markdown": "...", ...}}
    - anomaly_patrol: {"result": {"markdown": "...", ...}} 或 {"result": {"alerts": [...]}}
    - product_deep_dive: {"top_products": {...}, ...} — 无markdown，用结构化文本
    如果提取失败，返回基于skill_name的友好默认文本。
    """
    # 默认文本（按skill_name区分，避免"日报却返回周报"的错误）
    default_text_map = {
        "daily_briefing": "今日日报已生成，请查看下方图表与数据。",
        "weekly_review": "本周周报已生成，请查看下方图表与数据。",
        "anomaly_patrol": "异常巡检完成，请查看下方详情。",
        "product_deep_dive": "商品深度分析完成，请查看下方详情。"
    }
    default_text = default_text_map.get(skill_name, "分析报告已生成，请查看下方图表与数据。")

    if not skill_result_str or not skill_result_str.strip().startswith("{"):
        return default_text

    try:
        parsed = json.loads(skill_result_str)
    except:
        return default_text

    # 递归查找 markdown 字段（任意层级）
    def find_markdown(obj):
        if isinstance(obj, dict):
            if "markdown" in obj and isinstance(obj["markdown"], str) and obj["markdown"].strip():
                return obj["markdown"]
            for v in obj.values():
                found = find_markdown(v)
                if found:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = find_markdown(item)
                if found:
                    return found
        return None

    markdown = find_markdown(parsed)
    if markdown:
        # 加一个简短前缀（说明是降级输出）
        return markdown

    return default_text


def _build_llm_messages(messages: List, max_count: int) -> List:
    """
    构建发给LLM的消息列表（智谱API兼容格式）：
    - 智谱API不支持OpenAI的tool_calls消息链，需要特殊处理
    - 如果有ToolMessage，把用户问题+工具结果合并为一条HumanMessage
    - 明确告知LLM"基于工具结果回答，不要再调工具"
    - 最多取最近max_count条
    """
    # 先收集最近的消息
    recent = messages[-max_count * 2:]

    # 检查是否有ToolMessage（说明是Tool执行后回到Agent）——仅看最后一条，避免多轮对话中旧ToolMessage误判
    has_tool_msg = len(recent) > 0 and isinstance(recent[-1], ToolMessage)

    if has_tool_msg:
        # Tool执行后回到Agent：合并当前用户问题 + 当前工具结果
        # 注意：只收集最后一条HumanMessage之后的ToolMessage，避免混入上一轮的旧工具结果
        user_question = ""
        tool_results = []
        for msg in recent:
            if isinstance(msg, HumanMessage):
                user_question = msg.content or ""
                tool_results = []  # 重置：只保留此HumanMessage之后的ToolMessage
            elif isinstance(msg, ToolMessage):
                tool_results.append(msg.content or "")

        # 构造合并消息
        combined = f"{user_question}\n\n【工具返回结果】\n"
        for i, result in enumerate(tool_results, 1):
            # 剥离chart_data字段，减少传给LLM的内容（chart_data是给前端的，LLM不需要看）
            # 这样可以避免weekly_review等返回的大JSON导致LLM输入过长或被干扰
            cleaned_result = _strip_chart_data_from_tool_result(result)
            combined += f"\n--- 结果{i} ---\n{cleaned_result}\n"
        combined += "\n请基于以上工具返回结果，直接回答用户问题。如果结果足够回答，不要再调用工具。"

        return [HumanMessage(content=combined)]

    else:
        # 普通对话：过滤带tool_calls的AIMessage
        result = []
        for msg in recent:
            if isinstance(msg, HumanMessage):
                result.append(HumanMessage(content=msg.content or ""))
            elif isinstance(msg, AIMessage):
                if getattr(msg, "tool_calls", None):
                    continue
                if msg.content:
                    result.append(AIMessage(content=msg.content))

        if len(result) > max_count:
            result = result[-max_count:]
        return result


# ================== Tool 执行节点 ==================
async def tool_node(state: AnalysisAgentState) -> Dict[str, Any]:
    """执行LLM请求的Tool调用"""
    messages = state.get("messages", [])
    last_msg = messages[-1]

    if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
        return {"messages": []}

    tool_messages = []
    for tool_call in last_msg.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        # 智谱API要求tool_call_id非空，若为空则生成一个
        tool_call_id = tool_call.get("id") or f"call_{tool_name}_{len(tool_messages)}"

        # 从all_tool_funcs找到对应工具
        tool_func = None
        for t in all_tool_funcs:
            if t.name == tool_name:
                tool_func = t
                break

        if not tool_func:
            tool_messages.append(ToolMessage(
                content=f"工具 {tool_name} 不存在",
                tool_call_id=tool_call_id
            ))
            continue

        print(f"[ToolNode] 执行工具: {tool_name}, 参数: {tool_args}, call_id: {tool_call_id}")
        try:
            # 异步调用工具
            result = await tool_func.ainvoke(tool_args)
            # 限制ToolMessage内容长度，避免超长导致API报错
            # weekly_review返回嵌套JSON（周报+RFM+chart_data），需要更高阈值
            result_str = str(result)
            if len(result_str) > 20000:
                result_str = result_str[:20000] + "\n...(结果过长已截断)"
            tool_messages.append(ToolMessage(
                content=result_str,
                tool_call_id=tool_call_id
            ))
        except Exception as e:
            import traceback
            traceback.print_exc()
            tool_messages.append(ToolMessage(
                content=f"工具执行失败: {str(e)}",
                tool_call_id=tool_call_id
            ))

    return {"messages": tool_messages}


def should_continue_after_tool(state: AnalysisAgentState) -> str:
    """Tool执行后判断是否继续"""
    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else None

    # 如果是ToolMessage，回到原Agent节点继续
    if isinstance(last_msg, ToolMessage):
        # 通过target_node路由回原Agent
        target = state.get("target_node", "general_agent")
        return target

    return END


def should_continue_from_agent(state: AnalysisAgentState) -> str:
    """Agent节点后判断是否需要调用Tool（含最大循环次数限制）"""
    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else None

    # 只统计当前轮次的ToolMessage数量（最后一个HumanMessage之后的），防止跨轮次累积误判
    last_human_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], HumanMessage):
            last_human_idx = i
            break
    current_turn_msgs = messages[last_human_idx + 1:] if last_human_idx >= 0 else messages
    tool_msg_count = sum(1 for m in current_turn_msgs if isinstance(m, ToolMessage))
    if tool_msg_count >= MAX_TOOL_CALLS:
        print(f"[防循环] 当前轮次已达到最大Tool调用次数 {MAX_TOOL_CALLS}，强制结束")
        return END

    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tools"
    return END


# ================== 构建Graph ==================
def build_graph():
    """构建Multi-Agent Supervisor工作流（返回未compile的workflow，由main.py注入checkpointer后compile）"""
    workflow = StateGraph(AnalysisAgentState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("sql_agent", sql_agent_node)
    workflow.add_node("analysis_agent", analysis_agent_node)
    workflow.add_node("report_agent", report_agent_node)
    workflow.add_node("general_agent", general_agent_node)
    workflow.add_node("tools", tool_node)

    # 入口 → Supervisor
    workflow.add_edge(START, "supervisor")

    # Supervisor → 子Agent（条件路由）
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "sql_agent": "sql_agent",
            "analysis_agent": "analysis_agent",
            "report_agent": "report_agent",
            "general_agent": "general_agent",
        }
    )

    # 各子Agent → Tool（如果有tool_calls）或 END
    for agent_name in ["sql_agent", "analysis_agent", "report_agent"]:
        workflow.add_conditional_edges(
            agent_name,
            should_continue_from_agent,
            {
                "tools": "tools",
                END: END
            }
        )

    # Tool → 子Agent（继续处理）或 END
    workflow.add_conditional_edges(
        "tools",
        should_continue_after_tool,
        {
            "sql_agent": "sql_agent",
            "analysis_agent": "analysis_agent",
            "report_agent": "report_agent",
            "general_agent": "general_agent",
            END: END
        }
    )

    # general_agent → END
    workflow.add_edge("general_agent", END)

    return workflow  # 返回未compile的workflow


# 构建workflow（main.py会注入checkpointer后compile）
builder = build_graph()


# ================== 会话缓存（Redis） ==================
async def get_session_cache(session_id: str) -> Optional[Dict[str, Any]]:
    key = f"analysis_session:{session_id}"
    data = await redis_client.get(key)
    return json.loads(data) if data else None


async def update_session_cache(session_id: str, messages: List[Any], metadata: Dict[str, Any] = None):
    serializable_msgs = []
    for msg in messages[-MAX_RECENT_MESSAGES * 2:]:
        if isinstance(msg, (SystemMessage, AIMessage, ToolMessage, HumanMessage)):
            role = "system" if isinstance(msg, SystemMessage) else \
                   "assistant" if isinstance(msg, AIMessage) else \
                   "tool" if isinstance(msg, ToolMessage) else "user"
            serializable_msgs.append({"role": role, "content": msg.content})
        else:
            serializable_msgs.append({"role": "unknown", "content": str(msg)})

    cache_data = {
        "recent_messages": serializable_msgs,
        "metadata": metadata or {},
        "last_updated": datetime.now().isoformat()
    }
    await redis_client.setex(
        f"analysis_session:{session_id}",
        SESSION_TTL,
        json.dumps(cache_data, ensure_ascii=False)
    )


# 导出供main.py使用
__all__ = [
    "builder",
    "detect_analysis_intent",
    "match_skill",
    "build_system_prompt",
    "get_session_cache",
    "update_session_cache",
    "AnalysisAgentState",
    "all_tool_funcs"
]
