import operator
from typing import Dict, Any, List, Tuple

from imblearn.over_sampling import SMOTE

from .prediccion import Prediction
from .read_data import ReadData


# Cargamos una vez (igual que se hace ahora en views.py)
_data_from_excel = ReadData()
_prediction = Prediction()


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
    Replica mapeo actual:
      - coxalL, coxalA, esternon, femur, tibiotarso, tarsometatarso, humero, cubito, radio
      - craneoA -> craneoancho
      - craneoL -> craneolongitud
    y elimina vacíos.
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

    # eliminar vacíos / None
    huesos = {k: v for k, v in todos_huesos.items() if v is not None}

    return huesos


def percentage(dic: Dict[str, float]) -> Dict[str, float]:
    for k, v in dic.items():
        dic[k] = round(v * 100, 2)
    return dic


def calcular_prediccion(huesos: Dict[str, float]) -> List[Tuple[str, float]]:
    """
    Devuelve lo mismo que tu view:
      lista ordenada [(especie, porcentaje), ...]
    """
    if len(huesos) <= 0:
        raise ValueError("Debe introducir al menos un valor")

    result, score_modelo = _prediction.main(_data_from_excel.data, SMOTE(), huesos)

    # pasar a porcentaje y ordenar
    result = percentage(result)
    result_sort = sorted(result.items(), key=operator.itemgetter(1), reverse=True)

    return result_sort
