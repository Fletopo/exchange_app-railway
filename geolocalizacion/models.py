from django.conf import settings
from django.db import models

class UserLocation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Puedes agregar un índice en timestamp y coordenadas si planeas hacer búsquedas o filtrados por estos campos
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.latitude}, {self.longitude}"
    

    
