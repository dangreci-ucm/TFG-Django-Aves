import pandas as pd 
import os

class ReadData:

    def __init__(self):
        THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
       
        self.path = os.path.join(THIS_FOLDER, 'static/bbdd/bbdd rapaces.xlsx')
        self.data = self.read_data_from_excel()
        

    def read_data_from_excel(self):
        data = pd.read_excel(self.path, sheet_name="Base de datos") #Leemos la base de datos
        data.dropna(inplace = True)
        data.pop('IDENT')
        return data