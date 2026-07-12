# Token消耗统计 + LangFuse集成
# 复用购物助手的TokenTracker实现，按意图统计token消耗

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class TokenTracker(BaseCallbackHandler):
    """Token消耗追踪器，作为LangChain Callback Handler集成"""

    def __init__(self, results_dir: str = None):
        self.records: List[Dict[str, Any]] = []
        self.current_trace_id: Optional[str] = None
        self.current_intent: Optional[str] = None

        if results_dir is None:
            results_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "tests", "results"
            )
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)

    def set_trace_info(self, trace_id: str = None, intent: str = None):
        """设置当前追踪信息"""
        self.current_trace_id = trace_id
        self.current_intent = intent

    def on_llm_start(self, serialized, prompts, **kwargs):
        pass

    def on_llm_end(self, response: LLMResult, **kwargs):
        """LLM调用结束，记录token消耗"""
        try:
            # 智谱API的response结构和标准OpenAI不同，需要兼容处理
            for generation_list in response.generations:
                for generation in generation_list:
                    # 安全获取generation_info
                    gen_info = getattr(generation, 'generation_info', None) or {}
                    token_usage = gen_info.get("token_usage") or gen_info.get("usage") or {}

                    prompt_tokens = (
                        token_usage.get("prompt_tokens")
                        or token_usage.get("input_tokens")
                        or token_usage.get("inputTokenCount")
                        or 0
                    )
                    completion_tokens = (
                        token_usage.get("completion_tokens")
                        or token_usage.get("output_tokens")
                        or token_usage.get("outputTokenCount")
                        or 0
                    )
                    total_tokens = (
                        token_usage.get("total_tokens")
                        or (prompt_tokens + completion_tokens)
                        or 0
                    )

                    if total_tokens > 0 or prompt_tokens > 0 or completion_tokens > 0:
                        record = {
                            "timestamp": datetime.now().isoformat(),
                            "trace_id": self.current_trace_id,
                            "intent": self.current_intent,
                            "agent_type": "data_analysis",
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens,
                            "model_name": "glm-4"
                        }
                        self.records.append(record)
                        print(f"[TokenTracker] LLM调用: input={prompt_tokens}, output={completion_tokens}, total={total_tokens}")
        except Exception as e:
            # 静默失败，不影响主流程
            pass

    def on_llm_error(self, error, **kwargs):
        print(f"[TokenTracker] LLM调用错误: {error}")

    def get_summary(self) -> Dict[str, Any]:
        if not self.records:
            return {"total_calls": 0, "total_tokens": 0}

        total_prompt = sum(r["prompt_tokens"] for r in self.records)
        total_completion = sum(r["completion_tokens"] for r in self.records)
        total_tokens = sum(r["total_tokens"] for r in self.records)

        by_intent = defaultdict(lambda: {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        for r in self.records:
            intent = r.get("intent") or "unknown"
            by_intent[intent]["calls"] += 1
            by_intent[intent]["prompt_tokens"] += r["prompt_tokens"]
            by_intent[intent]["completion_tokens"] += r["completion_tokens"]
            by_intent[intent]["total_tokens"] += r["total_tokens"]

        return {
            "agent_type": "data_analysis",
            "total_calls": len(self.records),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_tokens,
            "avg_tokens_per_call": round(total_tokens / len(self.records), 1) if self.records else 0,
            "by_intent": dict(by_intent),
            "timestamp": datetime.now().isoformat()
        }

    def save_report(self, filename: str = "token_usage_analysis.json"):
        report = self.get_summary()
        filepath = os.path.join(self.results_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[TokenTracker] 报告已保存: {filepath}")
        return filepath

    def print_summary(self):
        summary = self.get_summary()
        if summary["total_calls"] == 0:
            print("\n========== Token消耗统计（数据分析Agent）==========")
            print("暂无Token使用记录")
            print("=================================================\n")
            return

        print("\n========== Token消耗统计（数据分析Agent）==========")
        print(f"总调用次数: {summary['total_calls']}")
        print(f"总Token消耗: {summary['total_tokens']}")
        print(f"  输入Token: {summary['total_prompt_tokens']}")
        print(f"  输出Token: {summary['total_completion_tokens']}")
        print(f"  平均每次: {summary['avg_tokens_per_call']}")
        print()
        print("按意图分组:")
        for intent, stats in summary.get("by_intent", {}).items():
            print(f"  {intent}: {stats['calls']}次, 总{stats['total_tokens']}tokens")
        print("=================================================\n")


# 全局Token追踪实例
token_tracker = TokenTracker()
