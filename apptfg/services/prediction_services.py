from typing import Dict, Any, List, Tuple, Optional

from apptfg.prediccion import Prediction, ModelBundle
from apptfg.models import ModelArtifact


# Caché en memoria para no deserializar el modelo en cada request
_cached_bundle: Optional[ModelBundle] = None
_cached_model_id: Optional[int] = None


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
    """
    Convierte los valores recibidos del formulario/API en floats.
    Mantiene exactamente los nombres que espera el modelo entrenado.
    """
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
    Debe llamarse cuando se entrena/sube un nuevo modelo o se cambia el activo.
    """
    global _cached_bundle, _cached_model_id
    _cached_bundle = None
    _cached_model_id = None


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


def get_model_display_name(model: ModelArtifact) -> str:
    """
    Nombre lógico del modelo para mostrar en logs o frontend.
    """
    if getattr(model, "name", None):
        return model.name
    return f"model_{model.id}.joblib"


def load_bundle_from_artifact(model: ModelArtifact) -> ModelBundle:
    """
    Deserializa el modelo desde PostgreSQL.
    """
    if not model.model_blob:
        raise FileNotFoundError("El modelo no tiene datos binarios almacenados en la base de datos.")

    return Prediction.bundle_from_bytes(model.model_blob)


def _get_bundle_for_model(model: ModelArtifact) -> ModelBundle:
    """
    Obtiene el bundle de un modelo concreto usando caché por model.id.
    """
    global _cached_bundle, _cached_model_id

    if _cached_bundle is not None and _cached_model_id == model.id:
        return _cached_bundle

    bundle = load_bundle_from_artifact(model)

    _cached_bundle = bundle
    _cached_model_id = model.id

    return bundle


def get_active_model_name() -> str:
    """
    Nombre del modelo activo, útil para logs o frontend.
    """
    artifact = get_active_model_artifact()
    if not artifact:
        return "unknown_model"
    return get_model_display_name(artifact)


def calcular_prediccion(huesos: Dict[str, float], model_id=None) -> List[Tuple[str, float]]:
    """
    Calcula la predicción usando el modelo activo o uno concreto si se indica model_id.
    """
    if len(huesos) <= 0:
        raise ValueError("Debe introducir al menos un valor")

    if model_id:
        model = ModelArtifact.objects.filter(id=model_id).first()
    else:
        model = get_active_model_artifact()

    if not model:
        raise ValueError("No se encontró modelo")

    bundle = _get_bundle_for_model(model)
    result_top3 = Prediction.predict_topk(bundle, huesos, top_k=3)

    return result_top3