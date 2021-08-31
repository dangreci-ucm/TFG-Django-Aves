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
   return render(request, 'apptfg/identificacion.html',{})

def descargas(request):
   return render(request,'apptfg/descargas.html',{})

def contacto(request):
   return render (request,'apptfg/contacto.html',{})

def calcular(request):
   print("CALCULANDO")
   if request.method=='POST':
      print("method post")
      todos_huesos = {
                     'coxalL':request.POST.get('coxalL'), 
                     'coxalA':request.POST.get('coxalA'),
                     'esternon':request.POST.get('esternon'),
                     'femur':request.POST.get('femur'),
                     'tibiotarso': request.POST.get('tibiotarso'),
                     'tarsometatarso': request.POST.get('tarsometatarso'),
                     'craneoancho': request.POST.get('craneoA'),
                     'craneolongitud': request.POST.get('craneoL'),
                     'humero':request.POST.get('humero'),
                     'cubito': request.POST.get('cubito'),
                     'radio':request.POST.get('radio')
                     }
                           
      # eliminamos los que tengan valor 0
      print(todos_huesos.items())
      huesos = {k:float(v) for k,v in todos_huesos.items() if v!=''}
      if len(huesos)<=0: 
         return render(request,'apptfg/identificacion.html', {'msg':'Debe introducir al menos un valor'})

      result, score_modelo = prediction.main(data_from_excel.data,SMOTE(), huesos)
      print(result)
      # Calculate percentage
      result=percentage(result)
      # Sort the result of the prediction, result is a dictionarity
      result_sort= sorted(result.items(), key=operator.itemgetter(1),reverse=True) 
      print(result_sort)                     
      return render(request,'apptfg/identificacion.html', {'msg':'Resultados:','valor': result_sort, 'ave':result_sort[0]})

   return render(request,'apptfg/identificacion.html',{})

def percentage(dic):
   for k,v in dic.items():
      dic[k]=round(v*100,2)
   
   return dic