from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import io

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline


@dataclass
class ModelBundle:
    """
    Modelo serializable que guardaremos en PostgreSQL como binario.
    - pipeline: imputación + random forest
    - feature_names: columnas de entrada esperadas
    - score: accuracy estimada para ponderar la probabilidad final
    """
    pipeline: Any
    feature_names: List[str]
    score: float


class Prediction:
    @staticmethod
    def train(data: pd.DataFrame) -> ModelBundle:
        """
        Entrena un modelo usando todas las columnas de huesos disponibles
        en el dataset y devuelve un ModelBundle en memoria.
        """
        if "Especie" not in data.columns:
            raise ValueError("El dataset no contiene la columna 'Especie'")

        y = data["Especie"]
        X = data.drop(columns=["Especie"])

        feature_names = list(X.columns)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.1, random_state=12, stratify=y
        )

        pipe = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="mean")),
            ("smote", SMOTE()),
            ("rf", RandomForestClassifier(n_estimators=200, random_state=12)),
        ])

        pipe.fit(X_train, y_train)
        score = float(pipe.score(X_test, y_test))

        bundle = ModelBundle(
            pipeline=pipe,
            feature_names=feature_names,
            score=score,
        )

        return bundle

    @staticmethod
    def bundle_to_bytes(bundle: ModelBundle) -> bytes:
        """
        Serializa el modelo entrenado a bytes para guardarlo en PostgreSQL.
        """
        buffer = io.BytesIO()
        joblib.dump(bundle, buffer)
        return buffer.getvalue()

    @staticmethod
    def bundle_from_bytes(blob: bytes) -> ModelBundle:
        """
        Reconstruye un ModelBundle desde los bytes almacenados en PostgreSQL.
        """
        buffer = io.BytesIO(blob)
        return joblib.load(buffer)

    @staticmethod
    def predict_topk(
        bundle: ModelBundle,
        huesos: Dict[str, float],
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Devuelve [(especie, prob_en_%), ...] ordenado desc.
        Si faltan huesos, se imputan por la media.
        """
        row = {name: None for name in bundle.feature_names}
        for k, v in huesos.items():
            if k in row:
                row[k] = v

        X_new = pd.DataFrame([row], columns=bundle.feature_names)

        proba = bundle.pipeline.predict_proba(X_new)[0]
        classes = bundle.pipeline.named_steps["rf"].classes_

        weighted = [
            (cls, float(bundle.score) * float(p))
            for cls, p in zip(classes, proba)
        ]

        weighted.sort(key=lambda x: x[1], reverse=True)
        top = weighted[:top_k]

        return [(cls, round(p * 100, 2)) for cls, p in top]