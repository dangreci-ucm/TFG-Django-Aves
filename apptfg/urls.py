from django.urls import path
#from . import views
from . import api_views  # API

urlpatterns = [
    #SE PUEDE LIMPIAR LAS URLs Y DEJAR SOLO LAS API
    #path('', views.principal, name='principal'),
    #path('iden', views.iden, name='iden'),
    #path('descargas',views.descargas,name='descargas'),
    #path('contacto',views.contacto,name='contacto'),
    #path('calcular',views.calcular, name='calcular'),
     
     #API
    path('api/ping', api_views.ping, name='api_ping'),
    path("api/calcular", api_views.calcular, name="api_calcular"),
    path("api/me", api_views.me, name="api_me"),
    path("api/predictions/history", api_views.prediction_history, name="prediction_history"),
    path("api/dataset/download", api_views.dataset_download, name="dataset_download"),
]
