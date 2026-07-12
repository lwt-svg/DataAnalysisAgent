# apps/agent/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Agent聊天接口
    path('api/agent/chat/', views.chat_with_agent, name='agent_chat'),
    path('api/agent/health/', views.agent_health_check, name='agent_health'),
]