import io
import json
from datetime import datetime
from django.contrib.auth.models import User
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST

from .bone_imputation import impute_dataframes
from .models import Aves, DatasetArtifact, ModelArtifact, PredictionLog
from .prediccion import Prediction
from .services import prediction_services

from django.db.models import Min, Max

from apptfg.services.dataset_services import get_aves_dataset


def ping(request):
    return JsonResponse({"ok": True})


def require_staff_api(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"ok": False, "error": "Debes iniciar sesión."},
            status=401
        )

    if not request.user.is_staff:
        return JsonResponse(
            {"ok": False, "error": "No tienes permisos para realizar esta acción."},
            status=403
        )

    return None


@ensure_csrf_cookie
def me(request):
    if request.user.is_authenticated:
        return JsonResponse({
            "authenticated": True,
            "username": request.user.get_username(),
            "id": request.user.id,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
        })

    return JsonResponse({
        "authenticated": False,
        "is_staff": False,
        "is_superuser": False,
    })


def validate_prediction_input_ranges(input_data):
    """
    Valida que los valores enviados estén dentro del rango min/max
    del dataset almacenado en Aves.
    """
    stats = Aves.objects.aggregate(
        coxalL_min=Min("coxalL"), coxalL_max=Max("coxalL"),
        coxalA_min=Min("coxalA"), coxalA_max=Max("coxalA"),
        esternon_min=Min("esternon"), esternon_max=Max("esternon"),
        femur_min=Min("femur"), femur_max=Max("femur"),
        tibiotarso_min=Min("tibiotarso"), tibiotarso_max=Max("tibiotarso"),
        tarsometatarso_min=Min("tarsometatarso"), tarsometatarso_max=Max("tarsometatarso"),
        craneoA_min=Min("craneoancho"), craneoA_max=Max("craneoancho"),
        craneoL_min=Min("craneolongitud"), craneoL_max=Max("craneolongitud"),
        humero_min=Min("humero"), humero_max=Max("humero"),
        cubito_min=Min("cubito"), cubito_max=Max("cubito"),
        radio_min=Min("radio"), radio_max=Max("radio"),
    )

    field_labels = {
        "coxalL": "Longitud del Coxal",
        "coxalA": "Anchura del Coxal",
        "esternon": "Esternón",
        "femur": "Fémur",
        "tibiotarso": "Tibiotarso",
        "tarsometatarso": "Tarsometatarso",
        "craneoA": "Anchura del Cráneo",
        "craneoL": "Longitud del Cráneo",
        "humero": "Húmero",
        "cubito": "Cúbito",
        "radio": "Radio",
    }

    for field, value in input_data.items():
        if value is None:
            continue

        min_val = stats.get(f"{field}_min")
        max_val = stats.get(f"{field}_max")

        if min_val is None or max_val is None:
            continue

        if value < min_val:
            return False, (
                f"El valor de '{field_labels.get(field, field)}' es menor que el mínimo permitido "
                f"({min_val})."
            )

        if value > max_val:
            return False, (
                f"El valor de '{field_labels.get(field, field)}' es mayor que el máximo permitido "
                f"({max_val})."
            )

    return True, None


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

    model_id = post_like.get("model_id")

    # Solo staff puede seleccionar manualmente un modelo
    if model_id and not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse(
            {
                "ok": False,
                "error": "No tienes permisos para seleccionar manualmente el modelo."
            },
            status=403
        )

    try:
        huesos = prediction_services.build_huesos_from_post(post_like)

        # Validar rangos con el dataset actual
        ok_ranges, range_error = validate_prediction_input_ranges(huesos)
        if not ok_ranges:
            return JsonResponse({"ok": False, "error": range_error}, status=400)

        result_sort = prediction_services.calcular_prediccion(huesos, model_id=model_id)

    except ValueError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"Error interno en la predicción: {str(e)}"},
            status=500
        )

    model_name = "unknown_model"
    try:
        if model_id:
            selected_model = ModelArtifact.objects.filter(id=model_id).first()
            if selected_model:
                model_name = selected_model.name
        else:
            model_name = prediction_services.get_active_model_name()

        # Quitar extensión .joblib si la hubiera
        if model_name:
            model_name = model_name.rsplit(".", 1)[0]

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
        # No se rompe la predicción si falla el log
        pass

    return JsonResponse({"ok": True, "results": result_sort})


@login_required
def historial_predicciones(request):
    """
    Devuelve el historial del usuario autenticado.
    """
    logs = (
        PredictionLog.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    data = []
    for log in logs:
        # limpiar nombre del modelo (quitar .joblib si existe)
        clean_model_name = (
            log.model_name.rsplit(".", 1)[0]
            if log.model_name else None
        )

        data.append({
            "id": log.id,
            "created_at": log.created_at.isoformat(),
            "input_data": log.input_data,
            "result_data": log.result_data,
            "model_name": clean_model_name,
            "user": request.user.username,  # para evitar undefined
        })

    return JsonResponse({"ok": True, "items": data})


@login_required
@require_http_methods(["DELETE"])
def borrar_prediccion(request, prediction_id):
    """
    Borra una predicción solo si pertenece al usuario autenticado.
    """
    deleted, _ = PredictionLog.objects.filter(id=prediction_id, user=request.user).delete()

    if deleted == 0:
        return JsonResponse(
            {"ok": False, "error": "Predicción no encontrada o sin permisos."},
            status=404
        )

    return JsonResponse({"ok": True})


@login_required
def model_list(request):
    staff_error = require_staff_api(request)
    if staff_error:
        return staff_error

    models = ModelArtifact.objects.exclude(name__iexact="unknown").order_by("-created_at")
    total_models = models.count()

    data = []
    for m in models:
        data.append({
            "id": m.id,
            "name": m.name,
            "created_at": m.created_at.isoformat(),
            "score": m.score,
            "is_active": m.is_active,
            "can_delete": total_models > 1,
        })

    return JsonResponse({
        "ok": True,
        "models": data
    })


@login_required
@require_http_methods(["POST"])
def set_active_model(request, model_id):
    """
    Marca un modelo como activo. Solo staff.
    """
    staff_error = require_staff_api(request)
    if staff_error:
        return staff_error

    model = ModelArtifact.objects.filter(id=model_id).first()
    if not model:
        return JsonResponse(
            {"ok": False, "error": "Modelo no encontrado."},
            status=404
        )

    with transaction.atomic():
        ModelArtifact.objects.update(is_active=False)
        model.is_active = True
        model.save(update_fields=["is_active"])

    prediction_services.clear_model_cache()

    return JsonResponse({
        "ok": True,
        "message": "Modelo activado correctamente.",
        "model_id": model.id,
        "model_name": model.name,
    })


@login_required
@require_http_methods(["DELETE"])
def model_delete(request, model_id):
    """
    Elimina un modelo guardado. Solo staff.
    No se permite borrar el único modelo disponible.
    Si se borra el modelo activo, se activa automáticamente el más reciente restante.
    """
    staff_error = require_staff_api(request)
    if staff_error:
        return staff_error

    queryset = ModelArtifact.objects.exclude(name__iexact="unknown")
    total_models = queryset.count()

    if total_models <= 1:
        return JsonResponse(
            {"ok": False, "error": "No se puede eliminar el único modelo disponible."},
            status=400
        )

    model = queryset.filter(id=model_id).first()
    if not model:
        return JsonResponse(
            {"ok": False, "error": "Modelo no encontrado."},
            status=404
        )

    was_active = model.is_active

    with transaction.atomic():
        model.delete()

        if was_active:
            new_active = (
                ModelArtifact.objects
                .exclude(name__iexact="unknown")
                .order_by("-created_at")
                .first()
            )

            if new_active:
                ModelArtifact.objects.update(is_active=False)
                new_active.is_active = True
                new_active.save(update_fields=["is_active"])

    prediction_services.clear_model_cache()

    return JsonResponse({
        "ok": True,
        "message": "Modelo eliminado correctamente."
    })


@login_required
@require_http_methods(["GET"])
def dataset_download(request):
    """
    Descarga el dataset actual reconstruido desde PostgreSQL.
    Formatos soportados:
      - /api/dataset/download
      - /api/dataset/download?format=xlsx
      - /api/dataset/download?format=csv
    Solo staff.
    """
    staff_error = require_staff_api(request)
    if staff_error:
        return staff_error

    dataset_format = (request.GET.get("format") or "xlsx").lower()
    if dataset_format not in ("xlsx", "csv"):
        return JsonResponse(
            {"ok": False, "error": "Formato no válido. Usa 'xlsx' o 'csv'."},
            status=400
        )

    df = get_aves_dataset()
    if df.empty:
        return JsonResponse(
            {"ok": False, "error": "No hay datos de dataset disponibles en la base de datos."},
            status=404
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if dataset_format == "csv":
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        response = HttpResponse(csv_buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="dataset_{timestamp}.csv"'
        return response

    xlsx_buffer = io.BytesIO()
    with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Base de datos")  # REVISAR

    xlsx_buffer.seek(0)

    return FileResponse(
        xlsx_buffer,
        as_attachment=True,
        filename=f"dataset_{timestamp}.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def build_aves_instances_from_df(df: pd.DataFrame):
    """
    Convierte el DataFrame del Excel en instancias de Aves.
    """
    aves_to_create = []

    for _, row in df.iterrows():
        aves_to_create.append(
            Aves(
                especie=str(row["Especie"]).strip(),
                coxalL=row["coxalL"],
                coxalA=row["coxalA"],
                esternon=row["esternon"],
                femur=row["femur"],
                tibiotarso=row["tibiotarso"],
                tarsometatarso=row["tarsometatarso"],
                craneoancho=row["craneoancho"],
                craneolongitud=row["craneolongitud"],
                humero=row["humero"],
                cubito=row["cubito"],
                radio=row["radio"],
            )
        )

    return aves_to_create


@login_required
@require_POST
def dataset_upload(request):
    """
    Flujo:
    1. Validar Excel subido
    2. Actualizar la tabla Aves con las nuevas entradas
    3. Entrenar nuevo modelo en memoria
    4. Crear DatasetArtifact
    5. Crear ModelArtifact con model_blob
    6. Marcar ambos como activos
    Solo staff.
    """
    staff_error = require_staff_api(request)
    if staff_error:
        return staff_error

    if "file" not in request.FILES:
        return JsonResponse(
            {"ok": False, "error": "No se ha enviado ningún archivo."},
            status=400
        )

    f = request.FILES["file"]

    if not (f.name.endswith(".xlsx") or f.name.endswith(".xls")):
        return JsonResponse(
            {"ok": False, "error": "El archivo debe ser un Excel (.xlsx o .xls)."},
            status=400
        )

    required_columns = [
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

    df = df[required_columns].copy()

    invalid_rows = []
    for idx, row in df.iterrows():
        missing_fields = []

        for col in required_columns:
            value = row[col]
            if pd.isna(value):
                missing_fields.append(col)
            elif isinstance(value, str) and not value.strip():
                missing_fields.append(col)

        if 'Especie' in missing_fields:
            invalid_rows.append({
                "row_excel": int(idx) + 2,
                "error": 'No contiene especie'
            })
        elif len(missing_fields) == len(required_columns)-1:
            invalid_rows.append({
                "row_excel": int(idx) + 2,
                "error": 'No contiene valores'
            })

    if invalid_rows:
        return JsonResponse(
            {
                "ok": False,
                "error": "El Excel contiene fallos: todas las aves deben tener Especie y al menos un hueso.",
                "invalid_rows": invalid_rows[:20]
            },
            status=400
        )

    numeric_columns = [
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

    for col in numeric_columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except Exception:
            return JsonResponse(
                {"ok": False, "error": f"La columna {col} contiene valores no numéricos."},
                status=400
            )

    # Imputamos mediante los huesos faltantes del dataframe usando recursion lineal
    try:
        dataset = get_aves_dataset()
        if dataset.empty:
            return JsonResponse(
                {"ok": False, "error": "No hay datos de dataset disponibles en la base de datos."},
                status=404
            )
        imputed_df = impute_dataframes(df, dataset)
    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"Error preparando los datos para entrenamiento: {str(e)}"},
            status=500
        )
    # TODO: Mostrarle el dataframe entrenado al usuario a modo de preview
    # TODO: Si confirma, añadir el dataframe a la base de datos

    # Preparamos los datos del dataframe para guardarlos en la base de datos
    try:
        aves_to_create = build_aves_instances_from_df(imputed_df)
    except Exception as e:
        return JsonResponse(
            {
                "ok": False,
                "error": f"Error preparando las filas del dataset para guardar en la base de datos: {str(e)}"
            },
            status=500
        )

    # Inserto aves_to_create en la base de datos
    try:
        with transaction.atomic():
            Aves.objects.bulk_create(aves_to_create, batch_size=500)
            DatasetArtifact.objects.update(is_active=False)
            dataset_artifact = DatasetArtifact.objects.create(
                created_by=request.user if request.user.is_authenticated else None,
                original_filename=f.name,
                row_count=len(df),
                is_active=True,
            )
            prediction_services.clear_model_cache()

    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"Error insertando nuevas aves en la base de datos: {str(e)}"},
            # TODO: esto es un fallo critico hay que ver que como puede fallar y pensar como manejarlo
            status=500
        )

    # Una vez actualizada la base de datos, entrenamos un nuevo modelo
    try:
        bundle = Prediction.train()
    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"Error durante el entrenamiento del modelo: {str(e)}"},
            status=500
        )

    # Guardamos el nuevo modelo en la base de datos
    try:
        with transaction.atomic():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = f"model_{timestamp}.joblib"
            model_bytes = Prediction.bundle_to_bytes(bundle)
            ModelArtifact.objects.update(is_active=False)

            model_artifact = ModelArtifact.objects.create(
                created_by=request.user if request.user.is_authenticated else None,
                dataset=dataset_artifact,
                name=model_name,
                model_blob=model_bytes,
                score=bundle.score,
                is_active=True,
            )

            prediction_services.clear_model_cache()

    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"Error guardando modelo en la base de datos: {str(e)}"},
            status=500
        )

    return JsonResponse({
        "ok": True,
        "message": "Dataset almacenado en PostgreSQL y modelo reentrenado correctamente.",
        "rows": len(df),
        "dataset_id": dataset_artifact.id,
        "model_id": model_artifact.id,
        "model_name": model_name,
        "score": round(bundle.score, 4),
    })


@login_required
@require_http_methods(["GET"])
def user_list(request):
    """
    Lista de usuarios. Solo staff.
    """
    staff_error = require_staff_api(request)
    if staff_error:
        return staff_error

    users = User.objects.order_by("id")

    items = []
    for u in users:
        items.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_staff": u.is_staff,
            "is_superuser": u.is_superuser,
            "is_active": u.is_active,
            "date_joined": u.date_joined.isoformat() if u.date_joined else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        })

    return JsonResponse({
        "ok": True,
        "items": items,
    })


@login_required
@require_http_methods(["POST"])
def user_set_staff(request, user_id):
    """
    Cambia el permiso is_staff de un usuario. Solo staff.
    Body JSON esperado:
    {
      "is_staff": true/false
    }
    """
    staff_error = require_staff_api(request)
    if staff_error:
        return staff_error

    target = User.objects.filter(id=user_id).first()
    if not target:
        return JsonResponse(
            {"ok": False, "error": "Usuario no encontrado."},
            status=404
        )

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {"ok": False, "error": "JSON inválido."},
            status=400
        )

    if "is_staff" not in payload:
        return JsonResponse(
            {"ok": False, "error": "Falta el campo is_staff."},
            status=400
        )

    new_is_staff = bool(payload["is_staff"])

    # Evitar que un admin se quite a sí mismo el rol staff
    if request.user.id == target.id and not new_is_staff:
        return JsonResponse(
            {"ok": False, "error": "No puedes quitarte a ti mismo el permiso de administrador."},
            status=403
        )

    # Evitar dejar el sistema sin staff
    if target.is_staff and not new_is_staff:
        remaining_staff = User.objects.filter(is_staff=True).exclude(id=target.id).count()
        if remaining_staff == 0:
            return JsonResponse(
                {"ok": False, "error": "No puedes quitar el permiso al último administrador."},
                status=400
            )

    target.is_staff = new_is_staff
    target.save(update_fields=["is_staff"])

    return JsonResponse({
        "ok": True,
        "message": "Permisos actualizados correctamente.",
        "user": {
            "id": target.id,
            "username": target.username,
            "is_staff": target.is_staff,
        }
    })


@login_required
@require_http_methods(["DELETE"])
def user_delete(request, user_id):
    """
    Borra un usuario. Solo staff.
    """
    staff_error = require_staff_api(request)
    if staff_error:
        return staff_error

    target = User.objects.filter(id=user_id).first()
    if not target:
        return JsonResponse(
            {"ok": False, "error": "Usuario no encontrado."},
            status=404
        )

    if request.user.id == target.id:
        return JsonResponse(
            {"ok": False, "error": "No puedes borrarte a ti mismo desde esta pantalla."},
            status=403
        )

    if target.is_superuser:
        return JsonResponse(
            {"ok": False, "error": "No se permite borrar superusuarios desde esta pantalla."},
            status=403
        )

    if target.is_staff:
        remaining_staff = User.objects.filter(is_staff=True).exclude(id=target.id).count()
        if remaining_staff == 0:
            return JsonResponse(
                {"ok": False, "error": "No puedes borrar al último administrador."},
                status=400
            )

    target.delete()

    return JsonResponse({
        "ok": True,
        "message": "Usuario eliminado correctamente."
    })


@require_http_methods(["GET"])
def dataset_stats(request):
    """
    Devuelve mínimos y máximos del dataset activo para cada hueso,
    calculados directamente desde la tabla Aves.
    """
    stats = Aves.objects.aggregate(
        coxalL_min=Min("coxalL"), coxalL_max=Max("coxalL"),
        coxalA_min=Min("coxalA"), coxalA_max=Max("coxalA"),
        esternon_min=Min("esternon"), esternon_max=Max("esternon"),
        femur_min=Min("femur"), femur_max=Max("femur"),
        tibiotarso_min=Min("tibiotarso"), tibiotarso_max=Max("tibiotarso"),
        tarsometatarso_min=Min("tarsometatarso"), tarsometatarso_max=Max("tarsometatarso"),
        craneoA_min=Min("craneoancho"), craneoA_max=Max("craneoancho"),
        craneoL_min=Min("craneolongitud"), craneoL_max=Max("craneolongitud"),
        humero_min=Min("humero"), humero_max=Max("humero"),
        cubito_min=Min("cubito"), cubito_max=Max("cubito"),
        radio_min=Min("radio"), radio_max=Max("radio"),
    )

    return JsonResponse({
        "ok": True,
        "stats": stats,
    })
