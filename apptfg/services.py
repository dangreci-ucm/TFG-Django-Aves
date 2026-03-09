import os
from typing import Dict, Any, List, Tuple, Optional

from .prediccion import Prediction, ModelBundle
from .models import ModelArtifact


# Cache en memoria para no cargar el joblib en cada request
_cached_bundle: Optional[ModelBundle] = None
_cached_model_path: Optional[str] = None


def _to_float_or_none(v: Any):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def build_huesos_from_post(post: Dict[str, Any]) -> Dict[str, float]:
    todos_huesos = {
        "coxalL": _to_float_or_none(post.get("coxalL")),
        "coxalA": _to_float_or_none(post.get("coxalA")),
        "esternon": _to_float_or_none(post.get("esternon")),
        "femur": _to_float_or_none(post.get("femur")),
        "tibiotarso": _to_float_or_none(post.get("tibiotarso")),
        "tarsometatarso": _to_float_or_none(post.get("tarsometatarso")),
        "craneoancho": _to_float_or_none(post.get("craneoA")),
        "craneolongitud": _to_float_or_none(post.get("craneoL")),
        "humero": _to_float_or_none(post.get("humero")),
        "cubito": _to_float_or_none(post.get("cubito")),
        "radio": _to_float_or_none(post.get("radio")),
    }
    return {k: v for k, v in todos_huesos.items() if v is not None}


def clear_model_cache() -> None:
    """
    Limpia el modelo cacheado en memoria.
    Debe llamarse cuando se entrena/sube un nuevo modelo.
    """
    global _cached_bundle, _cached_model_path
    _cached_bundle = None
    _cached_model_path = None


def get_active_model_artifact() -> Optional[ModelArtifact]:
    """
    Devuelve el modelo activo más reciente.
    """
    return (
        ModelArtifact.objects
        .filter(is_active=True)
        .order_by("-created_at")
        .first()
    )


def get_active_model_path() -> str:
    """
    Obtiene la ruta del modelo activo desde la base de datos.
    """
    artifact = get_active_model_artifact()

    if not artifact:
        raise FileNotFoundError("No hay ningún modelo activo registrado en la base de datos.")

    if not artifact.file_path:
        raise FileNotFoundError("El modelo activo no tiene ruta de archivo asociada.")

    if not os.path.exists(artifact.file_path):
        raise FileNotFoundError(f"No se encontró el archivo del modelo activo: {artifact.file_path}")

    return artifact.file_path


def _get_active_model_bundle() -> ModelBundle:
    """
    Carga el ModelBundle activo desde disco.
    Usa caché en memoria si sigue siendo el mismo archivo.
    """
    global _cached_bundle, _cached_model_path

    active_model_path = get_active_model_path()

    if _cached_bundle is not None and _cached_model_path == active_model_path:
        return _cached_bundle

    predictor = Prediction(model_path=active_model_path)
    _cached_bundle = predictor.load_model()
    _cached_model_path = active_model_path

    return _cached_bundle


def get_active_model_name() -> str:
    """
    Nombre de archivo del modelo activo, útil para logs o frontend.
    """
    artifact = get_active_model_artifact()
    if not artifact:
        return "unknown_model"
    return os.path.basename(artifact.file_path)


def calcular_prediccion(huesos: Dict[str, float]) -> List[Tuple[str, float]]:
    if len(huesos) <= 0:
        raise ValueError("Debe introducir al menos un valor")

    bundle = _get_active_model_bundle()
    predictor = Prediction(model_path=_cached_model_path)
    result_top3 = predictor.predict_topk(bundle, huesos, top_k=3)

    return result_top3