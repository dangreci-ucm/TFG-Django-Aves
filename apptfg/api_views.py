import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

def ping(request):
    return JsonResponse({"status": "ok"})

@csrf_exempt
@require_http_methods(["POST"])
def calcular(request):
    """
    MVP: recibe medidas y devuelve JSON.
    Más adelante: aquí llamas a prediccion.py y devuelves resultados reales.
    """
    # Si el frontend manda JSON:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    # Mock de respuesta (para probar integración rápido)
    return JsonResponse({
        "ok": True,
        "input": payload,
        "results": [
            {"especie": "Aguilucho Pálido", "probabilidad": 39.5, "imagen": "/static/img/img_aves/aguilucho.jpg"},
            {"especie": "Halcón Peregrino", "probabilidad": 3.52, "imagen": "/static/img/img_aves/halcon.jpg"},
        ]
    })


#import json
#from django.http import JsonResponse
#from django.views.decorators.http import require_http_methods
#from django.views.decorators.csrf import csrf_exempt
#
#from . import services
#
#def ping(request):
#    return JsonResponse({"status": "ok"})
#
#@csrf_exempt
#@require_http_methods(["POST"])
#def calcular(request):
#   # Soporta JSON (frontend separado) y form-encoded
#    if request.content_type and "application/json" in request.content_type:
#        payload = json.loads(request.body.decode("utf-8") or "{}")
#        huesos = services.build_huesos_from_json(payload)
#    else:
#        huesos = services.build_huesos_from_post(request.POST)
#
#    try:
#        result_sort = services.calcular_prediccion(huesos)
#    except ValueError as e:
#        return JsonResponse({"ok": False, "error": str(e)}, status=400)
#
#    return JsonResponse({
#        "ok": True,
#        "results": [{"especie": k, "probabilidad": v} for k, v in result_sort],
#   })
