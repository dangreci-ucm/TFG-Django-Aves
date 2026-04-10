from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Aves(models.Model):
    ident = models.CharField(max_length=100)
    especie = models.CharField(max_length=100)

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
        return f"{self.ident} - {self.especie}"


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
    row_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)


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
    name = models.CharField(max_length=255)
    model_blob = models.BinaryField()
    score = models.FloatField()
    is_active = models.BooleanField(default=False)


class EmailVerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_codes")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at

    @staticmethod
    def default_expiry():
        return timezone.now() + timedelta(minutes=10)