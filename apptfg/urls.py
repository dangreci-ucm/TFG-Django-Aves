from django.urls import path
from . import views

urlpatterns = [
    path('', views.principal, name='principal'),
    path('iden', views.iden, name='iden'),
    path('descargas',views.descargas,name='descargas'),
    path('contacto',views.contacto,name='contacto'),
    path('calcular',views.calcular, name='calcular'),
]
