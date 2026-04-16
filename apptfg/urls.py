from django.contrib import admin
from django.urls import path, include

from apptfg import api_views, views


urlpatterns = [
    #path("admin/", admin.site.urls), (ya está la ruta en mysite/urls.py)

    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/register/", views.register_view, name="register"),
    path("accounts/verify-email/", views.verify_email_view, name="verify_email"),
    path("accounts/resend-verification-code/", views.resend_verification_code_view, name="resend_verification_code"),

    path("api/ping", api_views.ping, name="ping"),
    path("api/me", api_views.me, name="me"),
    
    path("api/calcular", api_views.calcular, name="calcular"),
    path("api/predictions/history", api_views.historial_predicciones, name="prediction_history"),
    path("api/dataset/download", api_views.dataset_download, name="dataset_download"),
    path("api/dataset/upload", api_views.dataset_upload, name="dataset_upload"),
    path("api/models", api_views.model_list, name="model_list"),
    path("api/predictions/<int:prediction_id>/delete", api_views.borrar_prediccion, name="prediction_delete"),

    path("api/models/<int:model_id>/activate", api_views.set_active_model, name="set_active_model"), #REVISAR

    path("api/users", api_views.user_list, name="user_list"),
    path("api/users/<int:user_id>/set-staff", api_views.user_set_staff, name="user_set_staff"),
    path("api/users/<int:user_id>/delete", api_views.user_delete, name="user_delete"),
]