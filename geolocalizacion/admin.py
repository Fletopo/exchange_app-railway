# api/geolocalizacion/admin.py
from django.contrib import admin
from .models import UserLocation

class LocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'timestamp')
    search_fields = ('user__username', 'latitude', 'longitude')
    list_filter = ('timestamp',)

    # Excluye el campo 'timestamp' del formulario
    exclude = ('timestamp',)

admin.site.register(UserLocation, LocationAdmin)
