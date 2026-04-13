from django.contrib import admin
from .models import Aves, PredictionLog, DatasetArtifact, ModelArtifact


@admin.register(Aves)
class AvesAdmin(admin.ModelAdmin):
    list_display = (
        "especie",
        "ident",
        "coxalL",
        "coxalA",
        "esternon",
        "femur",
        "tibiotarso",
        "tarsometatarso",
        "craneoancho",
        "craneolongitud",
        "humero",
        "cubito",
        "radio",
    )
    search_fields = ("especie", "ident")


@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "model_name")
    list_filter = ("created_at", "model_name")
    search_fields = ("user__username", "model_name")
    ordering = ("-created_at",)


@admin.register(DatasetArtifact)
class DatasetArtifactAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "original_filename",
        "created_by",
        "created_at",
        "row_count",
        "is_active",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("original_filename", "created_by__username")
    ordering = ("-created_at",)


@admin.register(ModelArtifact)
class ModelArtifactAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "created_by",
        "created_at",
        "score",
        "is_active",
        "dataset",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "created_by__username")
    ordering = ("-created_at",)