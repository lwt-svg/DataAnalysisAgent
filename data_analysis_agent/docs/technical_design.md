# 电商数据分析Agent - 技术设计文档

## 一、系统架构

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Vue3 电商前端 │────▶│ Django后端    │────▶│ MySQL 数据库  │
│  (端口8080)   │     │ (端口8000)    │     │ (muxi_shop)  │
│              │     │              │     └──────────────┘
│  购物助手页面  │────▶│ /api/agent/  │                    │
│  数据助手页面  │────▶│ /api/analysis/│                   │
└──────────────┘     └──────┬───────┘                    │
                            │ 代理转发                     │
                   ┌────────┴────────┐                   │
                   ▼                 ▼                   │
          ┌─────────────┐   ┌──────────────┐             │
          │ 购物助手Agent │   │ 数据分析Agent  │             │
          │ FastAPI:8001 │   │ FastAPI:8002  │             │
          │              │   │               │             │
          │ 18个商品Tool  │   │ 8个分析Tool    │─────────────┘
          │ ChromaDB RAG │   │ Text2SQL      │
          │ 用户画像      │   │ 趋势分析       │
          └─────────────┘   └──────────────┘
                   │                 │
                   └────────┬────────┘
                            ▼
                     ┌─────────────┐
                     │   Redis     │
                     │ (状态持久化) │
                     └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │  LangFuse   │
                     │ (链路追踪)   │
                     └─────────────┘
```

## 二、项目结构

```
fastapi-langchain(latest)/
├── ecommerce_agent/              ← 现有C端购物助手
│
├── data_analysis_agent/          ← 新建B端数据分析助手
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               ← FastAPI入口，SSE支持
│   │   ├── agent.py              ← LangGraph Agent + 意图识别
│   │   ├── config.py             ← 配置（复用同一MySQL/Redis）
│   │   ├── models.py             ← 请求/响应模型
│   │   ├── auth.py               ← JWT验证（复用同一secret）
│   │   ├── database.py           ← 数据库连接（复用同一套）
│   │   ├── schema.py             ← 数据库Schema（只加载分析相关表）
│   │   ├── token_tracker.py      ← Token统计（复用）
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── sql_query_tool.py       ← 安全SQL查询（只允许SELECT+聚合）
│   │       ├── trend_analysis_tool.py  ← 趋势分析（环比/同比/移动平均）
│   │       ├── ranking_tool.py         ← 商品/品牌/品类/用户排行
│   │       ├── rfm_tool.py             ← RFM用户分群
│   │       ├── anomaly_tool.py         ← 异常检测（Z-Score）
│   │       ├── comment_analysis_tool.py← 评论/评分分析
│   │       └── report_tool.py          ← 报告生成（Markdown）
│   ├── my_llm.py                 ← 复用LLM配置
│   ├── requirements.txt
│   ├── run.py                    ← uvicorn --port 8002
│   └── docs/
│       ├── requirements.md
│       └── technical_design.md
```

## 三、核心模块设计

### 3.1 agent.py - LangGraph Agent

#### 状态定义
```python
class AnalysisAgentState(MessagesState):
    intent: Optional[str]                    # 当前意图
    time_range: Optional[Dict[str, str]]     # 解析出的时间范围
    query_result_cache: Optional[Dict]       # 缓存查询结果（报告生成时多步复用）
```

#### 意图识别（8种）
```python
def detect_analysis_intent(text: str) -> str:
    # 1. sales_query: GMV/销售额/收入/客单价/转化率
    # 2. trend_analysis: 趋势/环比/同比/增长/变化/走势
    # 3. product_ranking: 排行/卖得好/滞销/销量/热销
    # 4. user_analysis: 用户/客户/RFM/核心用户/性别分布
    # 5. order_analysis: 订单/待支付/退款/支付状态
    # 6. comment_analysis: 评分/评论/好评/差评/评分分布
    # 7. anomaly_check: 异常/正常吗/有没有问题/不对劲
    # 8. report_generation: 报告/日报/周报/月报/总结
    # 9. general: 其他
```

#### 时间解析
```python
def parse_time_range(text: str) -> Dict[str, str]:
    # "今天" → start=today, end=today
    # "最近7天" → start=today-7, end=today
    # "本周" → start=本周一, end=today
    # "本月" → start=本月1号, end=today
    # "上个月" → start=上月1号, end=上月末
    # 无时间词 → 默认最近30天
```

#### 工作流
```
用户消息 → call_model(意图识别+时间解析+工具路由) 
        → [需要Tool?] → call_tool → 回到model 
        → [不需要] → LLM直接回复 → END
```

### 3.2 sql_query_tool.py - 安全SQL查询

**核心设计：Text2SQL + 安全沙箱**

```python
@tool
def execute_analytics_sql(sql: str) -> str:
    """
    执行数据分析SQL查询。只允许SELECT语句，必须包含LIMIT。
    支持聚合函数（SUM/COUNT/AVG/MAX/MIN）和GROUP BY。
    """
    # 安全检查
    # 1. 必须以SELECT开头
    # 2. 禁止 INSERT/UPDATE/DELETE/DROP/ALTER/CREATE
    # 3. 禁止子查询中包含写操作
    # 4. 必须包含 WHERE 条件（避免全表扫描）
    # 5. 必须包含 LIMIT（默认最大1000）
    # 6. 禁止 JOIN 超过3张表
```

**为什么需要单独的安全SQL工具而不是让LLM自由生成SQL？**
- 防止SQL注入：商家输入"删除所有订单"不能真的执行
- 防止慢查询：无LIMIT的SELECT可能扫描百万行数据
- 防止数据泄露：WHERE条件必须包含时间范围限制

### 3.3 trend_analysis_tool.py - 趋势分析

```python
@tool
def query_sales_trend(
    metric: str,           # "gmv" | "order_count" | "avg_order_amount"
    time_range: str,       # "7d" | "30d" | "90d"
    group_by: str = "day"  # "day" | "week" | "month"
) -> str:
    """
    查询销售趋势数据，返回时间序列。
    自动计算环比增长率。
    """
    # SQL: SELECT DATE(create_time), SUM(order_amount)
    #      FROM `order` WHERE pay_status=1 AND create_time >= %s
    #      GROUP BY DATE(create_time) ORDER BY DATE(create_time)
    # 计算环比: (当期 - 上期) / 上期 * 100%
```

### 3.4 ranking_tool.py - 排行榜

```python
@tool
def query_product_ranking(
    rank_by: str,     # "sales" | "revenue" | "comment_count"
    category: str = None,
    brand: str = None,
    limit: int = 10
) -> str:
    """查询商品排行榜，支持按销量/收入/评论数排序"""

@tool
def query_category_brand_ranking(
    rank_by: str,     # "sales" | "revenue"
    group_by: str     # "category" | "brand"
) -> str:
    """查询品类/品牌排行榜"""
```

### 3.5 rfm_tool.py - RFM用户分群

```python
@tool
def analyze_user_rfm(
    reference_date: str = None  # 参照日期，默认今天
) -> str:
    """
    RFM用户分群分析：
    - R(Recency): 最近一次购买距今天数 → R<=30天为"活跃"
    - F(Frequency): 30天内购买次数 → F>=3次为"高频"
    - M(Monetary): 30天内消费金额 → M>=500为"高价值"
    
    分群结果：
    - 重要价值用户: R活跃+F高频+M高值
    - 重要发展用户: R活跃+F低频+M高值
    - 重要保持用户: R不活跃+F高频+M高值
    - 一般用户: 其他
    """
```

### 3.6 anomaly_tool.py - 异常检测

```python
@tool
def detect_anomaly(
    metric: str,         # "order_count" | "gmv" | "avg_score"
    window_days: int = 7  # 参照窗口
) -> str:
    """
    Z-Score异常检测：
    1. 获取最近window_days天的指标序列
    2. 计算均值(μ)和标准差(σ)
    3. 今日值 = x, Z = (x - μ) / σ
    4. |Z| > 2 → 异常；|Z| > 3 → 严重异常
    
    返回：当前值、7日均值、Z值、是否异常、异常方向（偏高/偏低）
    """
```

### 3.7 comment_analysis_tool.py - 评论分析

```python
@tool
def analyze_product_comments(
    sku_id: str = None,
    product_name: str = None,
    time_range: str = "30d"
) -> str:
    """
    商品评论分析：平均评分、评分分布、评论量趋势
    """

@tool
def find_low_rated_products(limit: int = 10) -> str:
    """
    查找差评最多的商品
    """
```

### 3.8 report_tool.py - 报告生成

```python
@tool
def generate_daily_report(date: str = None) -> str:
    """
    生成经营日报：
    1. 调用 query_sales_trend 获取当日GMV/订单量/客单价
    2. 调用 query_product_ranking 获取TOP5商品
    3. 调用 detect_anomaly 检查异常
    4. 汇总为Markdown格式报告
    """

@tool
def generate_weekly_report() -> str:
    """
    生成经营周报：趋势+排行+用户+异常+下周建议
    """
```

### 3.9 System Prompt设计

```
你是电商数据分析助手，帮助商家查询经营数据、分析趋势、发现问题。

【规则】
- 所有查询必须带时间范围，默认最近30天
- SQL查询必须包含LIMIT，最大1000行
- 金额统一用"元"，百分比保留1位小数
- 排行榜默认返回TOP10
- 报告用Markdown格式输出

【意图→工具】
销售查询→execute_analytics_sql | 趋势分析→query_sales_trend
商品排行→query_product_ranking | 品类排行→query_category_brand_ranking
用户分析→analyze_user_rfm | 订单分析→execute_analytics_sql
评论分析→analyze_product_comments | 差评商品→find_low_rated_products
异常检测→detect_anomaly | 日报→generate_daily_report | 周报→generate_weekly_report

DB结构：
{SCHEMA_INFO}

中文简洁回复，数据用表格呈现。
```

## 四、API设计

### 4.1 聊天接口
```
POST /chat
Request:
{
    "message": "今天卖了多少钱",
    "session_id": "可选",
    "token": "JWT token",
    "user_email": "可选",
    "use_rag": false  // 数据分析不需要RAG
}

Response:
{
    "response": "今天（2026-05-27）的经营数据：\n| 指标 | 值 |\n|---|---|\n| GMV | ¥15,680 |\n| 订单量 | 23 |\n| 客单价 | ¥681.7 |",
    "session_id": "xxx",
    "timestamp": "2026-05-27T10:30:00",
    "source": "tool",  // tool=工具查询结果, llm=LLM直接回答
    "chart_data": null  // 可选，如果有图表数据
}
```

### 4.2 健康检查
```
GET /health
```

### 4.3 Token统计
```
GET /token-usage
```

### 4.4 工具列表
```
GET /tools
```

## 五、Django代理配置

在现有Django后端中新增数据分析代理路由：

```python
# urls.py 新增
path('api/analysis/', include('apps.analysis_agent.urls'))
```

```python
# apps/analysis_agent/urls.py
urlpatterns = [
    path('chat/', views.chat_with_analysis_agent),
    path('health/', views.analysis_agent_health_check),
]
```

## 六、前端集成方案

### 6.1 新增路由

```javascript
// router/index.js 新增
{
    path: '/analysis-agent',
    name: 'AnalysisAgent',
    component: () => import('@/views/AnalysisAgent/index.vue'),
    meta: { title: '数据助手', requireAuth: true }
}
```

### 6.2 API请求

```javascript
// 区分两个Agent的关键：请求不同端口
const SHOP_AGENT_URL = '/api/agent/chat/'      // 购物助手 → 8001
const ANALYSIS_AGENT_URL = '/api/analysis/chat/' // 数据助手 → 8002
```

### 6.3 聊天界面复用

购物助手和数据助手的聊天UI基本一致（消息列表+输入框），区别：
- 数据助手的回复中可能包含**表格**和**图表数据**
- 需要一个Markdown渲染组件（支持表格显示）
- 图表用ECharts渲染（chart_data字段）

## 七、与购物助手的复用关系

| 组件 | 复用情况 | 说明 |
|------|---------|------|
| my_llm.py | ✅ 完全复用 | 同一个LLM配置文件 |
| config.py | ✅ 复用DB/Redis配置 | 同一个MySQL/Redis |
| auth.py | ✅ 完全复用 | 同一套JWT验证 |
| database.py | ✅ 完全复用 | 同一个数据库连接 |
| token_tracker.py | ✅ 完全复用 | 同一个Token统计 |
| LangFuse | ✅ 复用同一项目 | 两个Agent的Trace在同一个LangFuse项目下 |
| schema.py | ⚠️ 部分复用 | 只加载分析相关的5张表（去掉shopping_cart、user_address） |
| agent.py | ❌ 重写 | 不同的状态定义、意图、路由逻辑 |
| tools/ | ❌ 全新 | 8个数据分析专用Tool |
| chroma_db | ❌ 不需要 | 数据分析不需要RAG |
| profile.py | ❌ 不需要 | 数据分析不需要用户画像 |

## 八、启动顺序

```bash
# 1. MySQL + Redis（必须先启动）

# 2. 购物助手Agent
cd ecommerce_agent && python run.py  # 端口8001

# 3. 数据分析Agent
cd data_analysis_agent && python run.py  # 端口8002

# 4. Django后端
python manage.py runserver 8000

# 5. Vue3前端
npm run serve  # 端口8080
```
