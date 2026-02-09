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

]
