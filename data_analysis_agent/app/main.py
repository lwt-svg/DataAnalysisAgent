# 数据分析Agent - FastAPI入口
# 端口：8023（购物助手8022）

import re
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from .config import (
    ALLOWED_ORIGINS, REDIS_URL,
    LANGFUSE_ENABLED, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
)
from .auth import get_user_email_from_token
from .models import AnalysisRequest, AnalysisResponse
from .agent import builder, detect_analysis_intent
from .tools import match_skill, all_tool_funcs
from .token_tracker import token_tracker


agent = None
langfuse_handler = None


# ======================= LangFuse 初始化 =======================
# 新版langfuse的CallbackHandler只接受public_key参数，
# secret_key和host需要通过环境变量或Langfuse client传入
if LANGFUSE_ENABLED and LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
    try:
        from langfuse.langchain import CallbackHandler

        # 方式1：通过环境变量自动初始化
        # .env文件中已设置 LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST
        # CallbackHandler会自动读取这些环境变量
        langfuse_handler = CallbackHandler()

        print(f"✅ LangFuse 已启用，host: {LANGFUSE_HOST}")
        print(f"✅ LangFuse public_key: {LANGFUSE_PUBLIC_KEY[:15]}...")
    except ImportError:
        print("⚠️ langfuse 包未安装，请运行: pip install langfuse")
        langfuse_handler = None
    except Exception as e:
        print(f"⚠️ LangFuse 初始化失败: {e}")
        langfuse_handler = None
else:
    print("ℹ️ LangFuse 未启用（设置 LANGFUSE_ENABLED=true 开启）")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 应用生命周期管理。

    启动时：
    - 连接 Redis checkpointer，若失败则降级到内存模式。
    - 初始化 LangGraph Agent。

    关闭时：
    - 安全退出 Redis 连接。
    - 输出关闭日志。
    """
    global agent
    try:
        async with AsyncRedisSaver.from_conn_string(REDIS_URL) as checkpointer:
            agent = builder.compile(checkpointer=checkpointer)
            print(f"✅ 数据分析Agent 已初始化，Redis checkpointer 已启动（{REDIS_URL}）")
            if langfuse_handler:
                print("✅ LangFuse 回调处理器已注入 Agent 链路")
            yield
        print("✅ 应用关闭，Redis checkpointer 已退出")
    except Exception as e:
        print(f"⚠️ Redis 连接失败: {e}")
        print("⚠️ 降级到内存模式（MemorySaver），会话状态不会持久化！")
        from langgraph.checkpoint.memory import MemorySaver
        agent = builder.compile(checkpointer=MemorySaver())
        print("✅ 数据分析Agent 已初始化（内存模式）")
        if langfuse_handler:
            print("✅ LangFuse 回调处理器已注入 Agent 链路")
        yield
        print("✅ 应用关闭")


app = FastAPI(
    title='电商数据分析Agent',
    description='B端数据分析助手API服务 - Multi-Agent架构',
    version='1.0.0',
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"]
)


@app.get('/')
async def root():
    return {
        'message': '电商数据分析Agent服务已启动',
        'status': 'running',
        'port': 8023,
        'architecture': 'Multi-Agent Supervisor'
    }


@app.get('/health')
async def health():
    """健康检查（前端判断 status === 'healthy'）"""
    return {'status': 'healthy', 'service': 'data_analysis_agent'}


def _find_chart_data(obj) -> dict:
    """
    递归查找chart_data字段。
    Skill返回格式可能嵌套：
    - {"chart_data": ...}                        — 直接格式
    - {"result": {"chart_data": ...}}            — daily_briefing/anomaly_patrol
    - {"weekly_report": {"chart_data": ...}}     — weekly_review
    """
    if isinstance(obj, dict):
        if "chart_data" in obj and obj["chart_data"]:
            return obj["chart_data"]
        for v in obj.values():
            found = _find_chart_data(v)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_chart_data(item)
            if found:
                return found
    return None


@app.post('/chat', response_model=AnalysisResponse)
async def chat(request: AnalysisRequest, authorization: Optional[str] = Header(None)):
    """数据分析聊天接口"""
    global agent
    start_total = time.time()
    try:
        if agent is None:
            raise HTTPException(status_code=500, detail="Agent 尚未初始化")

        print(f"\n========== 数据分析请求 ==========")
        print(f"用户问题: {request.message[:80]}...")
        t1 = time.time()

        # 1. 处理token
        token_to_use = None
        if request.token:
            token_to_use = request.token
        elif authorization:
            token_to_use = authorization

        user_email = None
        if token_to_use:
            user_email = get_user_email_from_token(token_to_use)
        elif request.user_email:
            user_email = request.user_email

        t2 = time.time()
        print(f"token处理耗时: {t2 - t1:.3f}s")

        # 2. 构造上下文消息
        messages_for_agent = []
        if request.history:
            for msg in request.history:
                role = msg.get('role')
                content = msg.get('content')
                if not content:
                    continue
                if role == 'user':
                    messages_for_agent.append(HumanMessage(content=content))
                elif role == 'assistant':
                    messages_for_agent.append(AIMessage(content=content))

        # 拼接用户身份信息
        if user_email:
            user_context = f"当前登录用户(管理员): {user_email}\n用户问题: {request.message}"
        else:
            user_context = f"用户问题: {request.message}"
        messages_for_agent.append(HumanMessage(content=user_context))

        t3 = time.time()
        print(f"构建上下文耗时: {t3 - t2:.3f}s")

        # 3. 生成session_id
        # 如果前端没传session_id，生成唯一ID（不用user_email，避免旧会话状态污染）
        if request.session_id:
            thread_id = request.session_id
        else:
            import uuid
            thread_id = f"analysis_{uuid.uuid4().hex[:12]}"
        print(f"使用的 thread_id: {thread_id}")

        invoke_start = time.time()

        # 4. 构建Agent配置
        agent_config = {
            "configurable": {
                "thread_id": thread_id,
                "user_email": user_email
            }
        }

        # 5. 注入callbacks（LangFuse + TokenTracker）
        callbacks = []
        if langfuse_handler:
            callbacks.append(langfuse_handler)

        # 识别意图并设置Token追踪
        user_intent = detect_analysis_intent(request.message)
        skill_match = match_skill(request.message)
        trace_intent = f"skill:{skill_match}" if skill_match else user_intent
        token_tracker.set_trace_info(trace_id=thread_id, intent=trace_intent)
        callbacks.append(token_tracker)

        if callbacks:
            agent_config["callbacks"] = callbacks

        print(f"识别意图: {user_intent}, Skill匹配: {skill_match}")

        # 6. 调用Agent
        result = await agent.ainvoke(
            {"messages": messages_for_agent},
            config=agent_config
        )
        invoke_end = time.time()
        print(f"agent.invoke 耗时: {invoke_end - invoke_start:.3f}s")

        # 7. 提取响应
        response_message = result["messages"][-1]
        response_text = response_message.content

        # 尝试从工具结果中提取chart_data
        chart_data = None
        source = "llm"
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                continue
            if isinstance(msg, ToolMessage):
                try:
                    parsed = json.loads(msg.content)
                    found = _find_chart_data(parsed)
                    if found:
                        chart_data = found
                        source = "tool"
                        break
                except:
                    pass

        # 清理response_text中的JSON代码块（chart_data已作为独立字段返回）
        response_text = re.sub(r'```json\s*[\s\S]*?```', '', response_text).strip()
        # 兜底：清理孤立的```代码块
        response_text = re.sub(r'```\s*[\s\S]*?```', '', response_text).strip()

        t4 = time.time()
        print(f"提取响应耗时: {t4 - invoke_end:.3f}s")
        print(f"总耗时: {t4 - start_total:.3f}s")
        print(f"回复来源: {source}")

        # 打印Token消耗
        token_tracker.print_summary()

        return AnalysisResponse(
            response=response_text,
            session_id=thread_id,
            timestamp=datetime.now().isoformat(),
            source=source,
            chart_data=chart_data
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")


# ======================= SSE 流式输出 =======================

def _sse_format(data: dict) -> str:
    """格式化为SSE事件"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post('/chat/stream')
async def chat_stream(request: AnalysisRequest, authorization: Optional[str] = Header(None)):
    """
    SSE流式聊天接口
    事件类型:
    - start: 开始分析
    - intent: 意图识别结果
    - tool_start: 工具开始执行
    - tool_end: 工具执行完成
    - chunk: LLM输出片段
    - done: 分析完成（含完整结果）
    - error: 出错
    """
    global agent

    async def event_generator():
        try:
            if agent is None:
                yield _sse_format({"type": "error", "message": "Agent 尚未初始化"})
                return

            print(f"\n========== SSE 数据分析请求 ==========")
            print(f"用户问题: {request.message[:80]}...")

            # 1. 处理token
            token_to_use = None
            if request.token:
                token_to_use = request.token
            elif authorization:
                token_to_use = authorization

            user_email = None
            if token_to_use:
                user_email = get_user_email_from_token(token_to_use)
            elif request.user_email:
                user_email = request.user_email

            # 2. 构造上下文
            messages_for_agent = []
            if request.history:
                for msg in request.history:
                    role = msg.get('role')
                    content = msg.get('content')
                    if not content:
                        continue
                    if role == 'user':
                        messages_for_agent.append(HumanMessage(content=content))
                    elif role == 'assistant':
                        messages_for_agent.append(AIMessage(content=content))

            if user_email:
                user_context = f"当前登录用户(管理员): {user_email}\n用户问题: {request.message}"
            else:
                user_context = f"用户问题: {request.message}"
            messages_for_agent.append(HumanMessage(content=user_context))

            # 3. 生成session_id
            # 如果前端没传session_id，生成唯一ID（不用user_email，避免旧会话状态污染）
            if request.session_id:
                thread_id = request.session_id
            else:
                import uuid
                thread_id = f"analysis_{uuid.uuid4().hex[:12]}"

            # 4. 识别意图
            user_intent = detect_analysis_intent(request.message)
            skill_match = match_skill(request.message)

            yield _sse_format({
                "type": "start",
                "message": "开始分析..."
            })
            yield _sse_format({
                "type": "intent",
                "message": f"识别意图：{user_intent}" + (f"，匹配Skill：{skill_match}" if skill_match else "")
            })

            # 5. 构建Agent配置
            agent_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "user_email": user_email
                }
            }

            callbacks = []
            if langfuse_handler:
                callbacks.append(langfuse_handler)
            trace_intent = f"skill:{skill_match}" if skill_match else user_intent
            token_tracker.set_trace_info(trace_id=thread_id, intent=trace_intent)
            callbacks.append(token_tracker)
            if callbacks:
                agent_config["callbacks"] = callbacks

            # 6. 流式执行Agent
            final_response = ""
            chart_data = None
            source = "llm"
            current_node_name = ""

            # 节点名称映射
            node_names = {
                "supervisor_node": "主管路由",
                "sql_agent_node": "SQL查询Agent",
                "analysis_agent_node": "分析Agent",
                "report_agent_node": "报告Agent",
                "general_agent_node": "通用Agent",
                "tools": "工具执行"
            }

            # 流式输出时跟踪是否在代码块内（避免JSON代码块碎片推送给前端）
            in_code_block = False
            code_block_buffer = ""

            async for event in agent.astream_events(
                {"messages": messages_for_agent},
                config=agent_config,
                version="v2"
            ):
                kind = event["event"]
                name = event.get("name", "")
                data = event.get("data", {})

                # 节点开始
                if kind == "on_chain_start" and name in node_names:
                    display_name = node_names[name]
                    current_node_name = display_name
                    yield _sse_format({
                        "type": "step",
                        "message": f"进入{display_name}"
                    })

                # 链路错误（如LLM调用失败、429限速等）
                elif kind == "on_chain_error":
                    error_msg = str(data.get("error", "未知错误"))
                    print(f"[SSE错误] on_chain_error: {error_msg}")
                    # 友好化429错误提示
                    if "429" in error_msg or "速率限制" in error_msg:
                        friendly_msg = "AI模型调用频率过高，请稍等1分钟后重试"
                    else:
                        friendly_msg = f"分析过程出错: {error_msg[:200]}"
                    yield _sse_format({"type": "error", "message": friendly_msg})
                    return

                # 工具开始
                elif kind == "on_tool_start":
                    source = "tool"  # 只要有工具被调用，source就是tool（不只是有chart_data时）
                    yield _sse_format({
                        "type": "tool_start",
                        "message": f"正在调用工具：{name}"
                    })

                # 工具结束
                elif kind == "on_tool_end":
                    yield _sse_format({
                        "type": "tool_end",
                        "message": f"工具执行完成：{name}"
                    })

                    # 尝试提取chart_data（递归查找，支持Skill嵌套格式）
                    output = data.get("output", "")
                    try:
                        if isinstance(output, str):
                            parsed = json.loads(output)
                        else:
                            parsed = output
                        found = _find_chart_data(parsed)
                        if found:
                            chart_data = found
                            source = "tool"
                    except:
                        pass

                # LLM流式输出
                elif kind == "on_chat_model_stream":
                    chunk = data.get("chunk", "")
                    if hasattr(chunk, "content") and chunk.content:
                        content = chunk.content
                        if isinstance(content, list):
                            text_part = ""
                            for part in content:
                                if isinstance(part, dict) and "text" in part:
                                    text_part += part["text"]
                                elif isinstance(part, str):
                                    text_part += part
                            content = text_part
                        if content and isinstance(content, str):
                            # 过滤JSON代码块（避免前端显示```json...```碎片）
                            if "```" in content:
                                # 检测代码块开始/结束
                                if not in_code_block and "```" in content:
                                    parts = content.split("```")
                                    for i, part in enumerate(parts):
                                        if i % 2 == 0:
                                            # 代码块外的内容，正常推送
                                            if part.strip():
                                                final_response += part
                                                yield _sse_format({"type": "chunk", "message": part})
                                        else:
                                            # 代码块内的内容，缓冲不推送
                                                in_code_block = True
                                                code_block_buffer = part
                                else:
                                    # 在代码块内，继续缓冲
                                    code_block_buffer += content
                                    # 检测代码块结束
                                    if "```" in code_block_buffer:
                                        in_code_block = False
                                        code_block_buffer = ""
                            elif in_code_block:
                                # 在代码块内，缓冲不推送
                                code_block_buffer += content
                            else:
                                # 正常文字，推送
                                final_response += content
                                yield _sse_format({"type": "chunk", "message": content})

            # 清理最终响应中的JSON代码块（兜底）
            final_response = re.sub(r'```json\s*[\s\S]*?```', '', final_response).strip()
            final_response = re.sub(r'```\s*[\s\S]*?```', '', final_response).strip()

            # 如果流式没收集到内容（降级方案返回的AIMessage不触发on_chat_model_stream事件），
            # 或者没提取到chart_data（降级方案的ToolMessage不触发on_tool_end事件），
            # 从最终状态中补救提取
            if not final_response or not chart_data:
                try:
                    final_state = await agent.aget_state(agent_config)
                    if final_state and final_state.values:
                        msgs = final_state.values.get("messages", [])
                        if msgs:
                            # 1. 从后往前找 ToolMessage，提取 chart_data
                            if not chart_data:
                                for msg in reversed(msgs):
                                    if isinstance(msg, ToolMessage):
                                        try:
                                            parsed = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                                            found = _find_chart_data(parsed)
                                            if found:
                                                chart_data = found
                                                source = "tool"
                                                print(f"[SSE补救] 从最终状态提取到chart_data, source={source}")
                                                break
                                        except:
                                            pass
                            # 2. 获取最后一条 message 的 content 作为 final_response
                            if not final_response:
                                last_msg = msgs[-1]
                                if hasattr(last_msg, "content"):
                                    final_response = last_msg.content or ""
                                    final_response = re.sub(r'```json\s*[\s\S]*?```', '', final_response).strip()
                                    final_response = re.sub(r'```\s*[\s\S]*?```', '', final_response).strip()
                                    print(f"[SSE补救] 从最终状态提取到final_response, 长度={len(final_response)}")
                except Exception as e:
                    print(f"[SSE补救] 从最终状态提取失败: {e}")

            # 如果还是没有内容，给一个友好的默认回复（避免前端卡住）
            if not final_response and not chart_data:
                final_response = "抱歉，分析过程中遇到了一些问题，请稍后重试。如果持续出现此问题，可能是AI模型调用频率受限，请等待1-2分钟后再试。"

            print(f"\n流式输出完成，回复长度: {len(final_response)}, chart_data: {'有' if chart_data else '无'}")
            print(f"回复来源: {source}")

            # 打印Token消耗
            token_tracker.print_summary()

            yield _sse_format({
                "type": "done",
                "response": final_response,
                "chart_data": chart_data,
                "source": source,
                "session_id": thread_id
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_str = str(e)
            # 友好化429错误
            if "429" in error_str or "速率限制" in error_str:
                friendly_msg = "AI模型调用频率过高（429限速），请等待1-2分钟后重试"
            elif "timeout" in error_str.lower() or "超时" in error_str:
                friendly_msg = "请求超时，AI模型响应时间过长，请稍后重试"
            else:
                friendly_msg = f"分析过程出错: {error_str[:200]}"
            yield _sse_format({"type": "error", "message": friendly_msg})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ======================= 辅助接口 =======================

@app.get('/token-usage')
async def get_token_usage():
    """获取Token消耗统计"""
    return token_tracker.get_summary()


@app.get('/tools')
async def get_tools():
    """获取工具列表（按子Agent分组）"""
    groups = {
        "SQL Agent": ["execute_analytics_sql"],
        "Analysis Agent": [
            "query_sales_trend", "query_product_ranking",
            "query_category_brand_ranking", "analyze_user_rfm",
            "detect_anomaly", "analyze_product_comments",
            "find_low_rated_products"
        ],
        "Report Agent": [
            "generate_daily_report", "generate_weekly_report",
            "run_skill", "anomaly_patrol"
        ]
    }
    tools = []
    for group, names in groups.items():
        for t in all_tool_funcs:
            if t.name in names:
                tools.append({
                    "agent_group": group,
                    "name": t.name,
                    "description": t.description[:200] if t.description else ""
                })
    return tools


@app.get('/debug/intent')
async def debug_intent(text: str):
    """调试意图识别"""
    intent = detect_analysis_intent(text)
    skill = match_skill(text)
    return {
        "text": text,
        "intent": intent,
        "skill_match": skill
    }
