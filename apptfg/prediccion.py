from dataclasses import dataclass
from typing import Dict, List, Tuple
import io

import joblib
import numpy as np

from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer

from apptfg.services.dataset_services import get_aves_dataset


@dataclass
class ModelBundle:
    """
    Modelo serializable que guardaremos en PostgreSQL como binario.
    - model: modelo comprimido con joblib
    """
    model: RandomForestClassifier
    feature_names: List[str]
    species_names: List[str]
    score: float


class Prediction:
    @staticmethod
    def train() -> ModelBundle:
        """
        Entrena un modelo usando todas las columnas de huesos disponibles
        en el dataset y devuelve un ModelBundle en memoria.
        """
        dataset = get_aves_dataset()
        if dataset.empty:
            raise ValueError("Error al obtener el dataset")
        dataset.columns = dataset.columns.str.strip()

        # Identificar columnas de características (todas excepto Especie e IDENT)
        feature_names = [col for col in dataset.columns
                         if col not in ['Especie', 'IDENT']]

        X = dataset[feature_names].values
        y = dataset['Especie'].values

        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)

        pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler()),  # normalizamos las variables
            ('classifier', RandomForestClassifier(random_state=42))  # modelo elegido
        ])

        parameters = {
            'classifier__n_estimators': [50, 100, 200],
            'classifier__max_depth': [None, 10, 20, 30],
            'classifier__min_samples_split': [2, 5, 10],
            'classifier__min_samples_leaf': [1, 2, 4]
        }

        # Configura la validación cruzada
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

        grid = GridSearchCV(
            estimator=pipeline,
            param_grid=parameters,
            cv=cv,
            scoring='balanced_accuracy',
            return_train_score=True,
            n_jobs=-1,  # usar todos los núcleos
            verbose=1,  # muestra progreso (opcional)
            refit=True  # Reentrenar el modelo con los mejores parametros encontrados
        )

        grid.fit(X, y_encoded)  # Entrenamos el modelo

        bundle = ModelBundle(
            model=grid.best_estimator_,
            feature_names=feature_names,
            species_names=label_encoder.classes_,
            score=grid.best_score_
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
        """
        # Crear array con valores faltantes
        X_input = np.full((1, len(bundle.feature_names)), np.nan)

        # Llenar valores conocidos
        known_features = []
        for i, col in enumerate(bundle.feature_names):
            if col in huesos.keys():
                X_input[0, i] = huesos[col]
                known_features.append(col)

        if len(known_features) == 0:
            raise ValueError("Debes proporcionar al menos una medida")

        # Compatibilidad con modelos serializados antes del merge:
        # main guardaba el estimador en bundle.pipeline;
        # models/render lo guarda en bundle.model.
        estimator = getattr(bundle, 'model', None) or getattr(bundle, 'pipeline', None)
        if estimator is None:
            raise ValueError('El modelo cargado no contiene ni model ni pipeline')

        probas = estimator.predict_proba(X_input)[0]

        species_names = getattr(bundle, 'species_names', None)

        if species_names is None:
            if hasattr(estimator, 'named_steps'):
                classifier = (
                    estimator.named_steps.get('classifier')
                    or estimator.named_steps.get('rf')
                )
                species_names = getattr(classifier, 'classes_', None)
            else:
                species_names = getattr(estimator, 'classes_', None)

        if species_names is None:
            raise ValueError('No se pudieron obtener las clases del modelo')

        probabilidades = {
            str(species_names[i]): float(probas[i])
            for i in range(len(species_names))
        }

        # Ordenar alternativas por probabilidad
        sorted_species = sorted(
            probabilidades.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top = sorted_species[:top_k]

        return [(cls, round(p * 100, 2)) for cls, p in top]