# views.py
import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

AGENT_API_URL = getattr(settings, 'AGENT_API_URL', 'http://localhost:8000')

@csrf_exempt
@require_POST
def chat_with_agent(request):
    """与电商助手对话"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        session_id = data.get('session_id', '')
        user_email = data.get('user_email', '')
        
        # 调用FastAPI Agent服务
        payload = {
            "message": user_message,
            "session_id": session_id,
            "user_email": user_email
        }
        
        response = requests.post(
            f"{AGENT_API_URL}/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({
                "error": "Agent服务暂时不可用",
                "response": "抱歉，智能助手暂时无法响应，请稍后再试。"
            }, status=503)
            
    except requests.exceptions.RequestException:
        return JsonResponse({
            "error": "无法连接到Agent服务",
            "response": "抱歉，智能助手服务暂时不可用。"
        }, status=503)
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "response": "处理请求时发生错误。"
        }, status=500)

@csrf_exempt
def agent_health_check(request):
    """检查Agent服务状态"""
    try:
        response = requests.get(f"{AGENT_API_URL}/health", timeout=5)
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({"status": "unhealthy"}, status=503)
    except:
        return JsonResponse({"status": "unreachable"}, status=503)