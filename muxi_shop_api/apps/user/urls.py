from django.contrib import admin
from django.urls import path

from apps.user.views import ChangePasswordView, UpdateUserAPIView, UserAPIView,LoginView

urlpatterns = [
    #path("admin/", admin.site.urls),
    path("", UserAPIView.as_view()),
    path("login/", LoginView.as_view()),
    path("update/", UpdateUserAPIView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),  # 修改密码
]