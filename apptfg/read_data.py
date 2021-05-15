import pandas as pd 
import os

class ReadData:

    def __init__(self):
        THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
       
        self.path = os.path.join(THIS_FOLDER, 'static/bbdd/version 2016.xlsx')
        self.data = self.read_data_from_excel()
        

    def read_data_from_excel(self):
        print("LEYENDDDDDDDDDDDDDDDDDDDDDDDDDDOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
        # lectura 
        # esto sería bueno hacerlo solo una vez, no cada vez que se quiere predecir
        data = pd.read_excel(self.path, sheet_name="Base de datos") #Leemos la base de datos
        data.dropna(inplace = True)
        data.pop('IDENT')
        return data