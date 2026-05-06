import numpy as np
import pandas as pd

from pandas import DataFrame
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler


def strongest_correlation(species_table: DataFrame, bones_to_impute: list):
    # obtenemos las correlaciones entre los huesos para la especie
    correlation_dict = species_table.corr().replace(1, np.nan).unstack().dropna()[bones_to_impute].to_dict()

    # sumamos las correlaciones por hueso, usamos valor absoluto por si hay correlaciones inversas
    correlation_sum = dict.fromkeys(bones_to_impute, 0)
    for correlation, value in correlation_dict.items():
        for bone in correlation:
            if bone in correlation_sum: correlation_sum[bone] += abs(value)

    return max(correlation_sum, key=correlation_sum.get)


def impute_model_ridge(bone, species_table: pd.DataFrame, known_bones: list):
    X = species_table.loc[:, known_bones].values
    Y = np.array(species_table[bone])

    #  Los modelos con regularización requieren escalado
    scaler = StandardScaler().fit(X)
    X_scaled = scaler.transform(X)

    # Definir el modelo y el diccionario de hiperparámetros
    model = Ridge()
    parameters = {'alpha': [0.1, 1.0, 10.0, 100.0, 1000.0]}

    # Buscamos los mejores hiperparámetos del modelo
    cv = min(5, len(species_table))
    if cv < 2:
        raise Exception('La especie debe tener al menos 2 filas para imputar huesos faltantes')
    clf = GridSearchCV(model, parameters, cv=cv, scoring='neg_root_mean_squared_error')
    clf.fit(X_scaled, Y)

    # devolvemos el mejor modelo y el scaler
    return clf.best_estimator_, scaler


def impute_dataframe(df: DataFrame, dataset: DataFrame):
    df = df.copy()

    # Guardamos la especie del df lo ponemos a nulo para que no interfiera en los calculos
    species = df['Especie'].iloc[0]
    if pd.isna(species):
        raise Exception('El dataframe debe contener una Especie')
    df.loc[:, 'Especie'] = np.nan

    # Obtenemos una tabla con todos las aves de la especie y obtenemos sus correlaciones
    species_table = dataset.loc[dataset['Especie'] == species].copy()
    if species_table.empty:
        raise Exception('El dataframe debe contener una Especie conocida')
    species_table = species_table.drop(columns='Especie')

    # Vemos qué huesos nos faltan en el dataframe y los vamos rellenando uno a uno usando regresión lineal
    bones_to_impute = [bones for bones in species_table.keys() if bones not in df.dropna(axis=1).keys()]
    while bones_to_impute:
        known_bones = [bones for bones in species_table.keys() if bones in df.dropna(axis=1).keys()]
        bone = strongest_correlation(species_table, bones_to_impute)
        model, scaler = impute_model_ridge(bone, species_table, known_bones)
        X_scaled = scaler.transform(df.dropna(axis=1).values)
        predicted_bone_value = model.predict(X_scaled)
        df.loc[:, bone] = predicted_bone_value
        bones_to_impute.remove(bone)

    # Restablecemos la especie y devolvemos el dataframe relleno
    df.loc[:, 'Especie'] = species
    return df


def impute_dataframes(dataframes: DataFrame, dataset: DataFrame):
    dataframes = dataframes.copy()
    dataset = dataset.copy()

    if 'IDENT' in dataframes:
        dataframes = dataframes.drop(columns='IDENT')
    if 'IDENT' in dataset:
        dataset = dataset.drop(columns='IDENT')

    for i in range(len(dataframes.index)):
        imputed_df = impute_dataframe(dataframes.iloc[[i]].copy(), dataset)
        dataframes.loc[dataframes.index[i], imputed_df.columns] = imputed_df.iloc[0]

    return dataframes
