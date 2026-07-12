# 电商数据分析Agent（B端）

> 基于 LangGraph Multi-Agent Supervisor 架构的电商数据分析助手，支持自然语言查询、自动生成报告和可视化图表。

## 项目亮点

- **Multi-Agent Supervisor架构**：Supervisor规则路由 + 3个职责子Agent（SQL/分析/报告）
- **Text2SQL安全沙箱**：5层防护（白名单SELECT + 黑名单 + 自动LIMIT + 反引号转义 + 时间范围注入）
- **Skills预定义Tool链**：日报/周报/巡检等高频场景一键触发
- **并行查询优化**：ThreadPoolExecutor并行执行6个SQL，报告生成8s→2s
- **SSE流式输出**：FastAPI StreamingResponse + 前端ReadableStream实时渲染
- **防无限循环机制**：has_tool_result检测 + MAX_TOOL_CALLS限制
- **Redis会话持久化**：AsyncRedisSaver作为LangGraph Checkpointer

## 技术栈

| 层级 | 技术 |
|------|------|
| LLM | 智谱GLM-4 |
| Agent框架 | LangGraph (StateGraph + Supervisor) |
| 后端 | FastAPI + SSE |
| 数据库 | MySQL + Redis |
| 前端 | Vue3 + Element Plus + ECharts |
| 可观测性 | LangFuse |

## 架构图

```
用户提问
   ↓
Supervisor（规则路由，不调LLM）
   ├── SQL Agent → execute_analytics_sql（Text2SQL安全沙箱）
   ├── Analysis Agent → 趋势/排行/RFM/异常/评论（7个工具）
   ├── Report Agent → 日报/周报/Skill（4个工具）
   └── General Agent → 闲聊（不绑工具）
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑.env填入智谱API Key和LangFuse Key

# 3. 启动后端
python run.py  # 端口8023

# 4. 启动前端
cd django+vue3/muxi_shop_web
npm install
npm run serve  # 端口8080
```

## 支持的查询类型

| 类型 | 示例 |
|------|------|
| 销售查询 | "今天GMV多少" |
| 趋势分析 | "最近7天销售趋势" |
| 商品排行 | "最近30天热销TOP10" |
| 用户分群 | "最近30天用户RFM分析" |
| 异常检测 | "异常巡检" |
| 日报/周报 | "今日日报" / "本周周报" |
| 复杂查询 | "最近30天手机类商品销售趋势" |

## 项目结构

```
data_analysis_agent/
├── app/
│   ├── main.py          # FastAPI入口（/chat + /chat/stream）
│   ├── agent.py         # Multi-Agent架构核心
│   ├── config.py        # 配置管理
│   ├── tools/           # 14个工具
│   │   ├── sql_query_tool.py    # Text2SQL安全沙箱
│   │   ├── report_tool.py       # 日报/周报（并行查询）
│   │   ├── skills.py            # Skills预定义Tool链
│   │   ├── trend_analysis_tool.py
│   │   ├── ranking_tool.py
│   │   ├── rfm_tool.py
│   │   ├── anomaly_tool.py
│   │   └── comment_analysis_tool.py
│   └── ...
├── scripts/             # 测试脚本
├── docs/                # 设计文档
└── run.py               # 启动入口
```
