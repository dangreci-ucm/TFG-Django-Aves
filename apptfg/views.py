import operator

from imblearn.over_sampling import SMOTE
from django.shortcuts import render

from .prediccion import Prediction
from .read_data import ReadData

# Create your views here.

data_from_excel = ReadData()
prediction= Prediction()

def principal(request):
    return render(request, 'apptfg/pagina_principal.html', {})

def iden(request):
   return render(request, 'apptfg/identificacion.ejs',{})


def calcular(request):
   print("CALCULANDO")
   if request.method=='POST':
      print("method post")
      todos_huesos = {'coxalL':float(request.POST.get('coxalL')), 
                     'coxalA':float( request.POST.get('coxalA')),
                     'esternon':float( request.POST.get('esternon')),
                     'femur':float( request.POST.get('femur')),
                     'tibiotarso': float(request.POST.get('tibiotarso')),
                     'tarsometatarso':float( request.POST.get('tarsometatarso')),
                     'craneoancho':float( request.POST.get('craneoA')),
                     'craneolongitud':float( request.POST.get('craneoL')),
                     'humero':float(request.POST.get('humero')),
                     'cubito':float( request.POST.get('cubito')),
                     'radio':float(request.POST.get('radio'))}
                           
      # eliminamos los que tengan valor 0
      print(todos_huesos.items())
      huesos = {k:v for k,v in todos_huesos.items() if v > 0}
      if len(huesos)<=0: 
         return render(request,'apptfg/identificacion.ejs', {'msg':'Debe introducir al menos un valor'})
      path = 'apptfg/datos.html'
      result, score_modelo = prediction.main(data_from_excel.data,SMOTE(), huesos)
      print(result)
      # Calculate percentage
      result=percentage(result)
      # Sort the result of the prediction, result is a dictionarity
      result_sort= sorted(result.items(), key=operator.itemgetter(1),reverse=True) 
      print(result_sort)                     
      return render(request,'apptfg/identificacion.ejs', {'msg':'Resultados:','valor': result_sort})

   return render(request,'apptfg/identificacion.ejs',{})

def percentage(dic):
   for k,v in dic.items():
      dic[k]=round(v*100,2)
   
   return dic