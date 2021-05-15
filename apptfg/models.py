from django.db import models

# Create your models here.

class Aves(models.Model):  
   Especie = models.CharField(max_length=50)  
   coxalL = models.DecimalField(max_digits=10, decimal_places=3)
   coxalA = models.DecimalField(max_digits=10, decimal_places=3)
   esternon = models.DecimalField(max_digits=10, decimal_places=3)
   femur = models.DecimalField(max_digits=10, decimal_places=3)
   tibiotarso = models.DecimalField(max_digits=10, decimal_places=3)
   tarsometatarso = models.DecimalField(max_digits=10, decimal_places=3)
   craneoancho = models.DecimalField(max_digits=10, decimal_places=3)
   craneolongitud = models.DecimalField(max_digits=10, decimal_places=3)
   humero = models.DecimalField(max_digits=10, decimal_places=3)
   cubito = models.DecimalField(max_digits=10, decimal_places=3)
   radio = models.DecimalField(max_digits=10, decimal_places=3)
   

   def __str__(self):
      return self.Especie

 
