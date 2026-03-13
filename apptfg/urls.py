from django.contrib import admin
from django.urls import path, include

from apptfg import api_views, views


urlpatterns = [
    #path("admin/", admin.site.urls), (ya está la ruta en mysite/urls.py)

    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/register/", views.register_view, name="register"),
    path("accounts/verify-email/", views.verify_email_view, name="verify_email"),

    path("api/ping", api_views.ping, name="ping"),
    path("api/me", api_views.me, name="me"),
    path("api/calcular", api_views.calcular, name="calcular"),
    path("api/predictions/history", api_views.prediction_history, name="prediction_history"),
    path("api/dataset/download", api_views.dataset_download, name="dataset_download"),
    path("api/dataset/upload", api_views.dataset_upload, name="dataset_upload"),
    path("api/models", api_views.model_list, name="model_list"),
]