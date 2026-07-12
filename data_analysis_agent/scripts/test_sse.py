# -*- coding: utf-8 -*-
"""测试SSE流式输出"""
import requests
import json

url = "http://localhost:8023/chat/stream"
data = {
    "message": "最近7天销售额趋势",
    "user_email": "test@test.com",
    "session_id": "sse_test_001"
}

print(f"发送SSE请求: {data['message']}")
print("=" * 60)

response = requests.post(url, json=data, stream=True, timeout=120)
print(f"状态码: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")
print()

event_count = 0
for line in response.iter_lines(decode_unicode=True):
    if line and line.startswith("data: "):
        try:
            event = json.loads(line[6:])
            event_count += 1

            etype = event.get("type")
            msg = event.get("message", "")

            if etype == "chunk":
                # chunk只打印前50字符，避免刷屏
                print(f"  [{event_count}] chunk: {msg[:50]}..." if len(msg) > 50 else f"  [{event_count}] chunk: {msg}")
            elif etype == "done":
                print(f"\n  [{event_count}] DONE")
                print(f"  source: {event.get('source')}")
                print(f"  response长度: {len(event.get('response', ''))}")
                cd = event.get("chart_data")
                print(f"  chart_data类型: {cd.get('type') if cd else 'None'}")
                print(f"  session_id: {event.get('session_id')}")
                print(f"\n  回复前200字: {event.get('response', '')[:200]}")
            else:
                print(f"  [{event_count}] {etype}: {msg}")
        except:
            pass

print(f"\n总共收到 {event_count} 个事件")
