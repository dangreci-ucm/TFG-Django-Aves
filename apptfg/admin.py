from django.contrib import admin
from .models import Aves
from .models import PredictionLog

admin.site.register(Aves)

@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "model_name")
    list_filter = ("created_at", "model_name")
    search_fields = ("user__username", "model_name")

