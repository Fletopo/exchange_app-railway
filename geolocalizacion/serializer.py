from rest_framework import serializers
from .models import UserLocation

class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = ['latitude', 'longitude', 'timestamp', 'user']
        extra_kwargs = {'user': {'read_only': True}}  # El campo 'user' no debe ser modificado por el cliente

    def create(self, validated_data):
        """
        Crear una nueva instancia de UserLocation, vinculada a un usuario.
        """
        # Obtiene el usuario desde el contexto de la solicitud
        user = self.context['request'].user
        latitude = validated_data.get('latitude')
        longitude = validated_data.get('longitude')
        timestamp = validated_data.get('timestamp')

        # Crear la ubicación vinculada al usuario
        location = UserLocation.objects.create(
            user=user,  # Asociamos la ubicación al usuario autenticado
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp
        )
        return location

    def update(self, instance, validated_data):
        """
        Actualizar la ubicación existente de un usuario.
        """
        instance.latitude = validated_data.get('latitude', instance.latitude)
        instance.longitude = validated_data.get('longitude', instance.longitude)
        instance.timestamp = validated_data.get('timestamp', instance.timestamp)
        instance.save()
        return instance
