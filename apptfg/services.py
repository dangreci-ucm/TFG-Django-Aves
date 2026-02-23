import operator
import os
from typing import Dict, Any, List, Tuple, Optional

from .read_data import ReadData
from .prediccion import Prediction, ModelBundle


# 1) Datos base (excel -> dataframe)
_data_from_excel = ReadData()

# 2) Modelo persistente en disco (montar como volumen en docker-compose)
MODEL_PATH = os.environ.get("MODEL_PATH", "/app/model_store/latest_model.joblib")
_predictor = Prediction(model_path=MODEL_PATH)

# Cache en memoria (para no cargar de disco en cada request)
_cached_bundle: Optional[ModelBundle] = None


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


def _get_or_create_model_bundle() -> ModelBundle:
    global _cached_bundle

    if _cached_bundle is not None:
        return _cached_bundle

    if _predictor.model_exists():
        _cached_bundle = _predictor.load_model()
        return _cached_bundle

    # Si no existe, entrenamos una vez y guardamos
    _cached_bundle = _predictor.train_and_save(_data_from_excel.data)
    return _cached_bundle


def retrain_model() -> None:
    """
    Útil para el futuro: cuando metas nuevos datos en la BD,
    llamas a esto para reentrenar y dejar un nuevo modelo en disco.
    """
    global _cached_bundle
    _cached_bundle = _predictor.train_and_save(_data_from_excel.data)


def calcular_prediccion(huesos: Dict[str, float]) -> List[Tuple[str, float]]:
    if len(huesos) <= 0:
        raise ValueError("Debe introducir al menos un valor")

    bundle = _get_or_create_model_bundle()
    # top-3 (como pide tu tutor)
    result_top3 = _predictor.predict_topk(bundle, huesos, top_k=3)

    # ya viene en porcentaje y ordenado
    return result_top3