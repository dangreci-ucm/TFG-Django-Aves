import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from . import services


def ping(request):
    return JsonResponse({"status": "ok"})

@ensure_csrf_cookie
def me(request):
    if request.user.is_authenticated:
        return JsonResponse({
            "authenticated": True,
            "username": request.user.get_username(),
        })
    return JsonResponse({"authenticated": False})


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


@login_required
@require_POST
def dataset_upload(request):
    if 'file' not in request.FILES:
        return JsonResponse({"error": "No se ha enviado ningún archivo (campo 'file')."}, status=400)

    f = request.FILES['file']

    # aquí: validar extensión, tamaño, etc.
    # aquí: parsear excel, guardar en BD, etc.

    return JsonResponse({"message": "Archivo recibido correctamente."})