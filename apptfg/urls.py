from django.contrib import admin
from django.urls import path, include

from apptfg import api_views


urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth Django
    path("accounts/", include("django.contrib.auth.urls")),

    # API
    path("api/ping", api_views.ping, name="ping"),
    path("api/me", api_views.me, name="me"),
    path("api/calcular", api_views.calcular, name="calcular"),
    path("api/predictions/history", api_views.prediction_history, name="prediction_history"),
    path("api/dataset/download", api_views.dataset_download, name="dataset_download"),
    path("api/dataset/upload", api_views.dataset_upload, name="dataset_upload"),
]