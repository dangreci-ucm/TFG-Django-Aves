import operator

from django.shortcuts import render
from . import services


def principal(request):
    # frontend/html/pagina_principal.html
    return render(request, 'pagina_principal.html', {})


def iden(request):
    # frontend/html/identificacion.html
    return render(request, 'identificacion.html', {})


def descargas(request):
    # frontend/html/descargas.html
    return render(request, 'descargas.html', {})


def contacto(request):
    # frontend/html/contacto.html
    return render(request, 'contacto.html', {})


def calcular(request):
    # Este endpoint renderiza la misma pantalla de identificación, mostrando resultados
    if request.method == 'POST':
        huesos = services.build_huesos_from_post(request.POST)

        try:
            result_sort = services.calcular_prediccion(huesos)
        except ValueError as e:
            return render(request, 'identificacion.html', {'msg': str(e)})

        return render(request, 'identificacion.html', {'msg': 'Resultados', 'valor': result_sort})

    return render(request, 'identificacion.html', {})

def percentage(dic):
   for k,v in dic.items():
      dic[k]=round(v*100,2)
   
   return dic