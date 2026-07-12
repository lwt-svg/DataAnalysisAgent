"""
URL configuration for muxi_shop_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from apps.comment.views import CommentAPIView, CommentGenericAPIView ,CommentCountAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", CommentGenericAPIView.as_view({
        "get":"get_list",
        "post":"insert"
    })),
    path("<int:pk>", CommentGenericAPIView.as_view({
        "get":"single",
        "post":"edit",
        "delete":"delete"
    })),
    #这样进行传参 django会从URL中提取这些参数作为关键词传递给视图函数 
    #在视图函数中 我们可以直接通过函数的参数来获取这些值
    path("detail/<str:sku_id>/<int:page>", CommentAPIView.as_view()),
    path("count/<str:sku_id>", CommentCountAPIView.as_view()),
]