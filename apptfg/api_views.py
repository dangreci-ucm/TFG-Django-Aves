import json
import os
from django.conf import settings
from django.http import FileResponse

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


from . import services
from .models import PredictionLog

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
    # 3) Guardar historial de predicciones
    try:
        PredictionLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            input_data=huesos,
            result_data=result_sort,
            model_name="latest_model"
        )
    except Exception:
        # Si hay fallo en el log, no rompe la predicción
        pass
    # 4) Devolver resultados reales
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

@login_required
@require_http_methods(["GET"])
def prediction_history(request):
    logs = (
        PredictionLog.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    results = []
    for log in logs:
        results.append({
            "id": log.id,
            "created_at": log.created_at.isoformat(),
            "username": log.user.username if log.user else "anonymous",
            "input_data": log.input_data,
            "result_data": log.result_data,
            "model_name": log.model_name,
        })

    return JsonResponse({
        "ok": True,
        "results": results
    })


@login_required
@require_http_methods(["GET"])
def dataset_download(request):
    dataset_path = os.environ.get("DATASET_PATH")

    if not dataset_path:
        return JsonResponse(
            {"ok": False, "error": "DATASET_PATH no está configurado."},
            status=500
        )

    if not os.path.exists(dataset_path):
        return JsonResponse(
            {"ok": False, "error": "No se encontró el dataset actual."},
            status=404
        )

    return FileResponse(
        open(dataset_path, "rb"),
        as_attachment=True,
        filename=os.path.basename(dataset_path),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )