import os
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

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
    Lo que guardamos en disco.
    - pipeline: imputación + random forest
    - feature_names: columnas de entrada esperadas (huesos)
    - score: accuracy estimada (para mantener tu idea de "prob * score")
    """
    pipeline: Any
    feature_names: List[str]
    score: float


class Prediction:
    def __init__(self, model_path: str):
        self.model_path = model_path

    def model_exists(self) -> bool:
        return os.path.exists(self.model_path)

    def load_model(self) -> ModelBundle:
        return joblib.load(self.model_path)

    def train_and_save(self, data: pd.DataFrame) -> ModelBundle:
        """
        Entrena un modelo "global" usando TODAS las columnas de huesos disponibles en el dataset.
        - Permite predicción aunque el usuario no rellene todos los huesos (imputación por media).
        - Aplica SMOTE SOLO en train (después de imputar) con pipeline de imblearn.
        """
        if "Especie" not in data.columns:
            raise ValueError("El dataset no contiene la columna 'Especie'")

        y = data["Especie"]
        X = data.drop(columns=["Especie"])

        feature_names = list(X.columns)

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.1, random_state=12, stratify=y
        )

        # Pipeline: imputación -> SMOTE -> RandomForest
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

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(bundle, self.model_path)

        return bundle

    def predict_topk(
        self,
        bundle: ModelBundle,
        huesos: Dict[str, float],
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Devuelve [(especie, prob_en_%), ...] ordenado desc.
        Si faltan huesos, se imputan por la media (porque el pipeline lleva SimpleImputer).
        """
        # Crear un DataFrame con TODAS las features esperadas
        row = {name: None for name in bundle.feature_names}
        for k, v in huesos.items():
            if k in row:
                row[k] = v

        X_new = pd.DataFrame([row], columns=bundle.feature_names)

        proba = bundle.pipeline.predict_proba(X_new)[0]
        classes = bundle.pipeline.named_steps["rf"].classes_

        # Mantener tu idea original: prob_final = score * prob_modelo
        weighted = [(cls, float(bundle.score) * float(p)) for cls, p in zip(classes, proba)]

        # ordenar y top_k
        weighted.sort(key=lambda x: x[1], reverse=True)
        top = weighted[:top_k]

        # pasar a porcentaje (2 decimales)
        return [(cls, round(p * 100, 2)) for cls, p in top]