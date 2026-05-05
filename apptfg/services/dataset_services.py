import pandas as pd
from pandas import DataFrame

from apptfg.models import Aves


def get_aves_dataset() -> DataFrame:
    aves = Aves.objects.all().order_by("id")
    if not aves.exists():
        return pd.DataFrame()
    rows = []
    for ave in aves:
        rows.append({
            "IDENT": ave.ident,
            "Especie": ave.especie,
            "coxalL": ave.coxalL,
            "coxalA": ave.coxalA,
            "esternon": ave.esternon,
            "femur": ave.femur,
            "tibiotarso": ave.tibiotarso,
            "tarsometatarso": ave.tarsometatarso,
            "craneoancho": ave.craneoancho,
            "craneolongitud": ave.craneolongitud,
            "humero": ave.humero,
            "cubito": ave.cubito,
            "radio": ave.radio,
        })

    df = pd.DataFrame(rows)
    return df
