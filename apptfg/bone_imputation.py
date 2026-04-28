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
    clf = GridSearchCV(model, parameters, cv=5, scoring='neg_root_mean_squared_error')
    clf.fit(X_scaled, Y)

    # devolvemos el mejor modelo y el scaler
    return clf.best_estimator_, scaler


def impute_dataframe(df: DataFrame, dataset: DataFrame):
    # Guardamos la especie del df lo ponemos a nulo para que no interfiera en los calculos
    species = df['Especie'].tolist()[0]
    if species is np.nan:
        raise Exception('El dataframe debe contener una Especie')
    df['Especie'] = np.nan

    # Obtenemos una tabla con todos las aves de la especie y obtenemos sus correlaciones
    species_table = dataset[dataset['Especie'] == species]
    if species_table.empty:
        raise Exception('El dataframe debe contener una Especie conocida')
    species_table.drop(columns='Especie', inplace=True)

    # Vemos qué huesos nos faltan en el dataframe y los vamos rellenando uno a uno usando regresión lineal
    bones_to_impute = [bones for bones in species_table.keys() if bones not in df.dropna(axis=1).keys()]
    while bones_to_impute:
        known_bones = [bones for bones in species_table.keys() if bones in df.dropna(axis=1).keys()]
        bone = strongest_correlation(species_table, bones_to_impute)
        model, scaler = impute_model_ridge(bone, species_table, known_bones)
        X_scaled = scaler.transform(df.dropna(axis=1).values)
        predicted_bone_value = model.predict(X_scaled)
        df[bone] = predicted_bone_value
        bones_to_impute.remove(bone)

    # Restablecemos la especie y devolvemos el dataframe relleno
    df['Especie'] = species
    return df


def impute_dataframes(dataframes: DataFrame, dataset: DataFrame):
    if 'IDENT' in dataframes:
        dataframes.drop(columns='IDENT', inplace=True)
    if 'IDENT' in dataset:
        dataset.drop(columns='IDENT', inplace=True)
    for i in range(len(dataframes.index)):
        imputed_df = impute_dataframe(dataframes.iloc[[i]], dataset)
        dataframes.iloc[[i]] = imputed_df
    return dataframes