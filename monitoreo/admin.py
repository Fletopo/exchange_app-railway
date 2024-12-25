from django.contrib import admin
from .models import ResponseTime

@admin.register(ResponseTime)
class ResponseTimeAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'duration_ms', 'timestamp')  # Columnas visibles
    search_fields = ('event_name',)  # Campo de búsqueda
    list_filter = ('timestamp',)  # Filtro por fecha
    ordering = ('-timestamp',)  # Ordenar por fecha más reciente
