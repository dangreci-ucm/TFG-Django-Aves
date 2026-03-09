from django.db import models
from django.contrib.auth.models import User


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


class PredictionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    input_data = models.JSONField()
    result_data = models.JSONField()
    model_name = models.CharField(max_length=200, default="latest_model")

    def __str__(self):
        username = self.user.username if self.user else "anonymous"
        return f"{username} - {self.created_at}"


class DatasetArtifact(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    row_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        status = "activo" if self.is_active else "inactivo"
        return f"Dataset {self.id} - {self.original_filename} - {status}"


class ModelArtifact(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    dataset = models.ForeignKey(
        DatasetArtifact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="models"
    )
    file_path = models.CharField(max_length=500)
    score = models.FloatField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        status = "activo" if self.is_active else "inactivo"
        return f"Modelo {self.id} - {self.created_at} - {status}"