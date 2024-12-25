from django.db import models

class ResponseTime(models.Model):
    event_name = models.CharField(max_length=255)  # Nombre del evento o acción
    duration_ms = models.IntegerField()  # Tiempo en milisegundos como entero
    timestamp = models.DateTimeField(auto_now_add=True)  # Fecha y hora de registro

    def __str__(self):
        return f"{self.event_name} - {self.duration_ms} ms"
