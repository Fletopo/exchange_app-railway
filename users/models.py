from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from rest_framework.authtoken.models import Token

# Create your models here.
class CustomUser(AbstractUser):
    user_state = models.BooleanField(default=False)#usuario Premium 
    user_verified = models.BooleanField(default=False)#usuario verificado/confiable
    birthday = models.DateField(null=True, blank=True)
    account_creation = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    trade_score = models.FloatField(default=0)
    bio = models.TextField(blank=True, null=True)  # campo de descripción
    trade = models.IntegerField(default=0)
    can_create_publications = models.BooleanField(default=True)
    cant_trade_time = models.DateField(null=True, blank=True)
    can_trade = models.BooleanField(default=True, blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # Evita conflicto
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # Evita conflicto
        blank=True,
    )

    def calcular_trade_score(self):
        """Calcula y actualiza el trade_score basado en las calificaciones."""
        from publication.models import Calificacion  # Importación local para evitar el ciclo

        calificaciones = Calificacion.objects.filter(user_p=self)
        if calificaciones.exists():
            total_puntaje = sum(c.calificacion for c in calificaciones)
            cantidad = calificaciones.count()
            promedio = total_puntaje / cantidad
            self.trade_score = round((promedio / 5) * 100, 2)  # Convertir a porcentaje
        else:
            self.trade_score = 0.0
        self.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not Token.objects.filter(user=self).exists():
            Token.objects.create(user=self)

class Follower(models.Model):
    # El usuario que está siendo seguido (persona que tiene seguidores)
    user = models.ForeignKey(CustomUser, related_name='followers', on_delete=models.CASCADE)
    
    # El usuario que está siguiendo (persona que sigue a otro)
    follower = models.ForeignKey(CustomUser, related_name='following', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.follower.username} sigue a {self.user.username}"
