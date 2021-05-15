from django.urls import path
from . import views

urlpatterns = [
    path('', views.principal, name='principal'),
    path('iden', views.iden, name='iden'),
    path('calcular',views.calcular, name='calcular'),
]
