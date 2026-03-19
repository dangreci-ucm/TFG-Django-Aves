import io
import json
import os
from datetime import datetime

import pandas as pd
from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required

from .services import prediction_services
from .models import PredictionLog, DatasetArtifact, ModelArtifact
from .prediccion import Prediction
from apptfg.models import PredictionLog


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
    content_type = (request.META.get("CONTENT_TYPE") or "").lower()

    if "application/json" in content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)
        post_like = payload
    else:
        post_like = request.POST

    try:
        huesos = prediction_services.build_huesos_from_post(post_like)
        model_id = post_like.get("model_id")
        result_sort = prediction_services.calcular_prediccion(huesos, model_id=model_id)
        
    except ValueError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception:
        return JsonResponse({"ok": False, "error": "Error interno en la predicción"}, status=500)

    # Intentar usar el modelo activo para nombrarlo mejor en el log
    model_name = "latest_model"
    try:
        active_model = ModelArtifact.objects.filter(is_active=True).order_by("-created_at").first()
        if active_model:
            model_name = os.path.basename(active_model.file_path)
    except Exception:
        pass

    try:
        PredictionLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            input_data=huesos,
            result_data=result_sort,
            model_name=model_name,
        )
    except Exception:
        pass

    return JsonResponse({"ok": True, "results": result_sort})

@login_required
def model_list(request):
    models = ModelArtifact.objects.order_by("-created_at")

    data = []

    for m in models:
        data.append({
            "id": m.id,
            "name": m.file_path.split("/")[-1],
            "created_at": m.created_at.isoformat(),
            "score": m.score,
            "is_active": m.is_active,
        })

    return JsonResponse({
        "ok": True,
        "models": data
    })

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
@require_POST
def prediction_delete(request, prediction_id):
    try:
        prediction = PredictionLog.objects.get(id=prediction_id, user=request.user)
    except PredictionLog.DoesNotExist:
        return JsonResponse(
            {"ok": False, "error": "Predicción no encontrada"},
            status=404
        )

    prediction.delete()
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["GET"])
def dataset_download(request):
    """
    Descarga el dataset activo. Si no hay uno marcado como activo, devuelve error.
    """
    active_dataset = DatasetArtifact.objects.filter(is_active=True).order_by("-created_at").first()

    if not active_dataset:
        return JsonResponse(
            {"ok": False, "error": "No hay dataset activo disponible."},
            status=404
        )

    dataset_path = active_dataset.file_path

    if not os.path.exists(dataset_path):
        return JsonResponse(
            {"ok": False, "error": "No se encontró el archivo del dataset activo en disco."},
            status=404
        )

    return FileResponse(
        open(dataset_path, "rb"),
        as_attachment=True,
        filename=os.path.basename(dataset_path),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@login_required
@require_POST
def dataset_upload(request):
    """
    Flujo:
    1. Validar Excel subido
    2. Guardarlo en DATASET_DIR con nombre versionado
    3. Entrenar nuevo modelo y guardarlo en MODEL_DIR
    4. Crear DatasetArtifact y ModelArtifact
    5. Marcar ambos como activos
    """
    if "file" not in request.FILES:
        return JsonResponse(
            {"ok": False, "error": "No se ha enviado ningún archivo."},
            status=400
        )

    f = request.FILES["file"]

    # Validar extensión
    if not (f.name.endswith(".xlsx") or f.name.endswith(".xls")):
        return JsonResponse(
            {"ok": False, "error": "El archivo debe ser un Excel (.xlsx o .xls)."},
            status=400
        )

    required_columns = [
        "IDENT",
        "Especie",
        "coxalL",
        "coxalA",
        "esternon",
        "femur",
        "tibiotarso",
        "tarsometatarso",
        "craneoancho",
        "craneolongitud",
        "humero",
        "cubito",
        "radio",
    ]

    # Leer bytes una sola vez
    file_bytes = f.read()

    try:
        df = pd.read_excel(
            io.BytesIO(file_bytes),
            sheet_name="Base de datos",
            engine="openpyxl"
        )
    except ValueError:
        return JsonResponse(
            {"ok": False, "error": 'No se encontró la hoja "Base de datos".'},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"Error al leer el Excel: {str(e)}"},
            status=400
        )

    # Validar columnas obligatorias
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return JsonResponse(
            {
                "ok": False,
                "error": "Faltan columnas obligatorias.",
                "missing_columns": missing_columns
            },
            status=400
        )

    # Quedarnos solo con las columnas esperadas
    df = df[required_columns]

    # Detectar filas con valores nulos o vacíos
    invalid_rows = []

    for idx, row in df.iterrows():
        missing_fields = []

        for col in required_columns:
            value = row[col]

            if pd.isna(value):
                missing_fields.append(col)
            elif isinstance(value, str) and not value.strip():
                missing_fields.append(col)

        if missing_fields:
            invalid_rows.append({
                "row_excel": int(idx) + 2,  # +2 por cabecera y base 1 de Excel
                "missing_fields": missing_fields
            })

    if invalid_rows:
        return JsonResponse(
            {
                "ok": False,
                "error": "El Excel contiene filas incompletas. Todas las aves deben tener todos los huesos rellenos.",
                "invalid_rows": invalid_rows[:20]
            },
            status=400
        )

    dataset_dir = os.environ.get("DATASET_DIR")
    model_dir = os.environ.get("MODEL_DIR")

    if not dataset_dir or not model_dir:
        return JsonResponse(
            {"ok": False, "error": "MODEL_DIR o DATASET_DIR no están configurados."},
            status=500
        )

    os.makedirs(dataset_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    dataset_filename = f"dataset_{timestamp}.xlsx"
    dataset_path = os.path.join(dataset_dir, dataset_filename)

    model_filename = f"model_{timestamp}.joblib"
    model_path = os.path.join(model_dir, model_filename)

    # Guardar Excel en disco
    try:
        with open(dataset_path, "wb") as destination:
            destination.write(file_bytes)
    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"No se pudo guardar el dataset en disco: {str(e)}"},
            status=500
        )

    # Preparar dataframe para entrenamiento (sin IDENT)
    try:
        df_train = df.drop(columns=["IDENT"]).copy()
    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"Error preparando los datos para entrenamiento: {str(e)}"},
            status=500
        )

    # Entrenar y guardar nuevo modelo
    try:
        predictor = Prediction(model_path=model_path)
        bundle = predictor.train_and_save(df_train)
    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"Error durante el entrenamiento del modelo: {str(e)}"},
            status=500
        )

    # Desactivar dataset/modelo activos anteriores
    DatasetArtifact.objects.update(is_active=False)
    ModelArtifact.objects.update(is_active=False)

    # Registrar nuevo dataset
    dataset_artifact = DatasetArtifact.objects.create(
        created_by=request.user if request.user.is_authenticated else None,
        original_filename=f.name,
        file_path=dataset_path,
        row_count=len(df),
        is_active=True,
    )

    # Registrar nuevo modelo
    model_artifact = ModelArtifact.objects.create(
        created_by=request.user if request.user.is_authenticated else None,
        dataset=dataset_artifact,
        file_path=model_path,
        score=bundle.score,
        is_active=True,
    )
    prediction_services.clear_model_cache()

    return JsonResponse({
        "ok": True,
        "message": "Dataset válido, almacenado y modelo reentrenado correctamente.",
        "rows": len(df),
        "dataset_id": dataset_artifact.id,
        "model_id": model_artifact.id,
        "model_filename": model_filename,
        "score": round(bundle.score, 4),
    })