import pandas as pd 
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split 
from sklearn.ensemble import RandomForestClassifier        # Random forest classifier


    
def data_preparation_model(tabla, col, oversample, huesos):
    """
    Preparación de los datos para evaluar el modelo y calcular su grado de ajuste
    Oversample de los datos
    -----------------------
    col: es la columna 'Especie'
    huesos: columnas para las cuales el usuario ha puesto una medida
    oversample: método usado para realizar el oversample
    """
    # Seleccionamos todas las columnas asociadas a huesos que ha puesto el usuario
    x = tabla.drop(col, axis = 1)
    names_huesos = list(huesos.keys())
    x = x.loc[:,names_huesos]
    y = tabla[col]
    # Dividimos los datos en entrenamiento y test
    X_train, X_test, Y_train, Y_test = train_test_split(x,y,test_size = .1, random_state=12)
    
    # transform the dataset
     
    x_train_res, y_train_res = oversample.fit_resample(X_train, Y_train) 
    return (x, y), (X_train, X_test, Y_train, Y_test), (x_train_res, y_train_res)

def evaluar_modelo(nombre, modelo, x_train_res, y_train_res, X_test,  Y_test):
    # ajuste
    modelo.fit(x_train_res, y_train_res.values)
    score = modelo.score(X_test,  Y_test.values)
    #print(f'Test results: el modelo {nombre} tiene una precisión de {score:.2f}')
    return score

def estimado_pos(fila):
    m = fila[fila != 0]
    return dict(zip(m.index.to_list(), m.to_list()))   

def estimar(nuevos, modelo):
    try:
        valor = pd.DataFrame(modelo.predict_proba(nuevos), columns = modelo.classes_)
        # borrar columnas que sumen 0
        t = valor.T
        t['Suma'] = t.sum(axis = 1)
        valor1 = t[t.Suma != 0].drop('Suma', axis = 1)
        valor1 = valor1.T
        valor1['Estimado'] = valor1.apply(lambda fila: estimado_pos(fila), axis = 1)
        return valor1.loc[0,'Estimado']
    except:
        return {}  # no se han calculado probabilidades    


# Random Forest Classifier with oversample all data
def crear_modelo (x, y,modelo, oversample, huesos):
    """
    modelo: modelo que usamos para predecir
    oversample: método usado para realizar el oversample
    huesos: columnas para las cuales el usuario ha puesto una medida    
    """
    x_train_res, y_train_res = oversample.fit_resample(x, y) 
    # ajuste
    modelo.fit(x_train_res, y_train_res.values)
    valor = estimar(pd.DataFrame(huesos, index = [0]) , modelo)
    return valor, modelo 

def main(data, huesos):
    """
    data: dataframe con los datos
    overfiting: es el método usado para equilibrar las especies con menos datos. Puede ser:
                SMOTE(), SVMSMOTE(), BorderlineSMOTE()
    huesos: diccionario de huesos con el valor indicado por el usuario
            por ejemplo: {'tarsometatarso':33, 'cubito':80}
    """
    overfiting=SMOTE()
    (x, y),(X_train, X_test, Y_train, Y_test), (x_train_res, y_train_res) = data_preparation_model(data, 'Especie', overfiting, huesos)
    # usaremos randomforest
    rf = RandomForestClassifier(n_estimators=10) 
    # evalúo el score del modelo
    score = evaluar_modelo('Random Forest', rf, x_train_res, y_train_res, X_test,  Y_test)
    # creo el modelo definitivo para predecir con todos los datos + oversampling
    rf = RandomForestClassifier(n_estimators=10)
    valor_estimado, modelo = crear_modelo(x, y,  rf, overfiting, huesos)
    # ahora, la probabilidad final se calcula como la probabilidad que tiene el modelo de acertar, 
    # multiplicado por la probabilidad de cada especie
    return {k: score * v     for k, v in valor_estimado.items()}, score