# 电商数据分析Agent（B端）

> 基于 LangGraph Multi-Agent Supervisor 架构的电商数据分析助手，支持自然语言查询、Text2SQL、自动生成报告和可视化图表。

## 项目亮点

- **Multi-Agent Supervisor架构**：Supervisor规则路由 + 3个职责子Agent（SQL/分析/报告），降低单Agent提示词臃肿
- **Text2SQL安全沙箱**：5层防护（白名单SELECT + 黑名单关键词 + 自动LIMIT + 反引号转义 + 时间范围注入）
- **Skills预定义Tool链**：日报/周报/巡检等高频场景一键触发，6类查询并行执行
- **并行查询优化**：ThreadPoolExecutor并行执行6个SQL，周报生成8s→2s，提升12倍
- **SSE流式输出**：FastAPI StreamingResponse + 前端ReadableStream实时渲染图表
- **四级降级方案**：LLM限速重试 → contentFilter降级 → 空响应手动调Skill → markdown兜底
- **防无限循环机制**：has_tool_result检测 + MAX_TOOL_CALLS限制
- **Redis会话持久化**：AsyncRedisSaver作为LangGraph Checkpointer，支持跨请求上下文恢复
- **复合图表渲染**：composite类型支持bar/line/pie混合渲染，Vue3递归组件

## 技术栈

| 层级 | 技术 |
|------|------|
| LLM | 智谱GLM-4 |
| Agent框架 | LangGraph (StateGraph + Supervisor) |
| 后端 | FastAPI + SSE |
| 数据库 | MySQL + Redis |
| 前端 | Vue3 + Element Plus + ECharts |
| 可观测性 | LangFuse |
| 向量检索 | ChromaDB + bge-m3 |

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

### Text2SQL安全沙箱流程

```
用户自然语言
   ↓
Schema精简（只传相关表DDL）
   ↓
品类映射（"服装"→"服饰鞋靴"）
   ↓
LLM生成SQL
   ↓
5层安全校验：
  1. 白名单：只允许SELECT
  2. 黑名单：禁止DROP/DELETE/UPDATE/INSERT/ALTER
  3. 自动LIMIT：无LIMIT自动补LIMIT 100
  4. 反引号转义：表名/字段名加反引号
  5. 时间范围注入：无时间条件自动加默认范围
   ↓
执行SQL → 返回结果
```

### 周报Skill并行执行流程

```
"本周周报"
   ↓
Report Agent识别Skill
   ↓
并行执行6个查询（ThreadPoolExecutor）：
  ├── GMV总览（今日GMV/订单量/客单价）
  ├── 订单趋势（近7天每日订单量）
  ├── 用户分群（RFM分析）
  ├── 商品TOP榜（销量TOP10）
  ├── 品类分布（各品类销售占比）
  └── 评论分析（好评率/差评关键词）
   ↓
汇总结果 → 匹配ECharts图表类型 → SSE流式输出
```

## 快速开始

### 环境要求

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 后端 |
| MySQL | 8.0+ | 数据库 |
| Redis | 6.0+ | 会话持久化 |
| Ollama | latest | 本地Embedding模型 |

### 1. 安装依赖

```bash
cd data_analysis_agent
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：
```bash
# 智谱API
ZHIPU_API_KEY=your_api_key

# 数据库
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=muxi_shop

# Redis
REDIS_URL=redis://localhost:6379/0

# LangFuse（可选）
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=http://localhost:3000
```

### 3. 启动服务

```bash
python run.py  # 端口8023
```

### 4. 启动前端

```bash
cd ../django+vue3/muxi_shop_web
npm install
npm run serve  # 端口8080
```

## 功能特性

### 数据查询

| 类型 | 示例 | 说明 |
|------|------|------|
| 销售查询 | "今天GMV多少" | 单表聚合查询 |
| 趋势分析 | "最近7天销售趋势" | 时间序列分析 |
| 商品排行 | "最近30天热销TOP10" | 排行榜 |
| 用户分群 | "最近30天用户RFM分析" | RFM模型分群 |
| 异常检测 | "异常巡检" | GMV/订单量异常检测 |
| 评论分析 | "手机类商品好评率" | 评论情感分析 |

### 自动报告

| 类型 | 示例 | 输出 |
|------|------|------|
| 日报 | "今日日报" | GMV/订单/用户/商品/评论概览 |
| 周报 | "本周周报" | 6类查询并行 + ECharts图表 |
| 巡检 | "异常巡检" | 异常指标告警 |

### 可视化图表

| 图表类型 | 数据场景 | ECharts配置 |
|---------|---------|------------|
| 折线图 | 时间趋势 | xAxis=time, yAxis=value |
| 柱状图 | 排行榜/对比 | category vs value |
| 饼图 | 品类分布 | 占比统计 |
| 复合图 | 多维度分析 | 递归渲染子图表 |

## API文档

### 对话接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/chat` | POST | 同步对话 |
| `/chat/stream` | POST | SSE流式对话 |
| `/health` | GET | 健康检查 |
| `/tools` | GET | 工具列表 |

### 请求示例

```bash
# 同步对话
curl -X POST http://localhost:8023/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "今天GMV多少",
    "user_email": "admin@muxi.com"
  }'

# SSE流式对话
curl -X POST http://localhost:8023/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "本周周报",
    "user_email": "admin@muxi.com"
  }'
```

### SSE事件类型

| 事件 | 说明 |
|------|------|
| `start` | 开始处理 |
| `intent` | 意图识别结果 |
| `tool_start` | 工具开始执行 |
| `tool_end` | 工具执行完成 |
| `chunk` | LLM输出片段 |
| `chart_data` | 图表数据 |
| `done` | 处理完成 |
| `error` | 出错 |

## 使用示例

### 销售查询

```
用户: 今天GMV多少
助手: 今日GMV为 ¥128,560，共 342 笔订单，客单价 ¥375.9
      [柱状图：各时段GMV分布]
```

### 趋势分析

```
用户: 最近7天销售趋势
助手: 近7天销售趋势如下：
      - GMV趋势：稳步上升，日均增长8.5%
      - 订单量：从280增长到342
      [折线图：7天GMV + 订单量趋势]
```

### 用户分群

```
用户: 最近30天用户RFM分析
助手: RFM用户分群结果：
      - 高价值用户：1,234人（占比15%）
      - 活跃用户：3,456人（占比42%）
      - 沉睡用户：2,345人（占比28%）
      - 流失用户：1,234人（占比15%）
      [饼图：用户分群占比]
```

### 自动周报

```
用户: 本周周报
助手: ## 经营周报（2026.07.06 - 2026.07.12）

      ### 一、GMV总览
      本周GMV ¥928,560，环比增长12.5%...

      ### 二、订单趋势
      [折线图：7天订单量趋势]

      ### 三、商品TOP榜
      [柱状图：销量TOP10]

      ### 四、用户分群
      [饼图：RFM分群占比]

      ### 五、品类分布
      [饼图：各品类销售占比]

      ### 六、评论分析
      好评率 87%，主要好评：性价比高、物流快...
```

## 四级降级方案

| 级别 | 触发条件 | 降级策略 |
|------|---------|---------|
| 1 | LLM 429限速 | 指数退避重试3次（5s/10s/15s） |
| 2 | contentFilter触发 | 简化messages重试（去掉ToolMessage） |
| 3 | LLM返回空响应（tool_calls=0） | 手动调用Skill跳过LLM决策 |
| 4 | 全部失败 | markdown报告兜底（用工具返回数据拼报告） |

## 项目结构

```
data_analysis_agent/
├── app/
│   ├── main.py              # FastAPI入口（/chat + /chat/stream）
│   ├── agent.py             # Multi-Agent架构核心
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── auth.py              # JWT认证
│   ├── models.py            # 请求/响应模型
│   ├── token_tracker.py     # Token消耗追踪
│   └── tools/               # 14个工具
│       ├── sql_query_tool.py       # Text2SQL安全沙箱
│       ├── report_tool.py          # 日报/周报（并行查询）
│       ├── skills.py               # Skills预定义Tool链
│       ├── trend_analysis_tool.py  # 趋势分析
│       ├── ranking_tool.py         # 排行榜
│       ├── rfm_tool.py             # RFM用户分群
│       ├── anomaly_tool.py         # 异常检测
│       └── comment_analysis_tool.py # 评论分析
├── tests/
│   ├── test_e2e_quality.py  # 端到端质量评估
│   ├── test_intent.py       # 意图准确率测试
│   └── results/             # 测试结果
├── scripts/                 # 工具脚本
└── run.py                   # 启动入口
```

## 测试体系

### 意图准确率测试

```bash
python tests/test_intent.py
```

覆盖6种意图（sql_query/analysis/report/general/trend/ranking），101条测试用例。

### 端到端质量评估

```bash
python tests/test_e2e_quality.py --mode api
```

26个测试用例覆盖8大场景，LLM-as-Judge从4维打分（相关性/完整性/准确性/友好度）。

### 性能测试

```bash
python tests/test_performance.py
```

单请求延迟 + 并发压测（1/5/10/20并发）。

## 配置说明

### 数据库配置

```python
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "muxi_shop"),
    "port": 3306
}
```

### Redis配置

```python
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

### LangFuse配置

```python
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
```

## 技术要点

### Text2SQL优化

1. **Schema精简**：只传相关表DDL，减少token干扰
2. **品类映射**："服装"→"服饰鞋靴"，避免LLM生成错误品类名
3. **多表前缀约束**：`order.create_time`，避免歧义字段报错
4. **SQL校验**：正则禁止DDL/DML，自动补LIMIT 100

### 复合图表渲染

```javascript
// composite类型递归渲染
if (chartData.type === 'composite') {
    chartData.children.forEach(child => {
        renderChart(child)  // 递归
    })
}
```

### 空响应降级

```python
# LLM返回空响应时触发降级
if tool_calls_count == 0 and not response.content and skill_name:
    return await _fallback_call_skill(skill_name)
```

## 许可证

本项目仅供学习交流使用，禁止用于商业用途。
