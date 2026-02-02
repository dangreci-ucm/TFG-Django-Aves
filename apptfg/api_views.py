import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from . import services


def ping(request):
    return JsonResponse({"status": "ok"})


@csrf_exempt  # para desarrollo; si se usan sesiones/usuarios, mejor quitarlo y manejar CSRF en frontend
@require_http_methods(["POST"])
def calcular(request):
    """
    API real: recibe medidas (form-urlencoded o JSON) y devuelve resultados del modelo en JSON.
    """
    # 1) Leer payload desde JSON o desde form-urlencoded
    content_type = (request.META.get("CONTENT_TYPE") or "").lower()

    if "application/json" in content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

        # Convertir payload a un dict "tipo POST" para reutilizar el servicio
        # Si la build_huesos_from_post espera QueryDict, mejor adaptar services para aceptar dict.
        post_like = payload

    else:
        # Lo que envía un <form> normal
        post_like = request.POST

    # 2) Construir huesos (validación mínima incluida en services)
    try:
        huesos = services.build_huesos_from_post(post_like)
        result_sort = services.calcular_prediccion(huesos)
    except ValueError as e:
        # errores de validación (ej: "introduce al menos un valor")
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception:
        # evita filtrar detalles internos del modelo en la API
        return JsonResponse({"ok": False, "error": "Error interno en la predicción"}, status=500)

    # 3) Devolver resultados reales
    # Ideal: result_sort debería ser una lista de dicts serializables (strings/floats/ints)
    return JsonResponse({"ok": True, "results": result_sort})


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
