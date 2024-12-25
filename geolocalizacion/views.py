from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from .models import UserLocation
from .serializer import UserLocationSerializer
from django.contrib.auth.models import User
from rest_framework.exceptions import AuthenticationFailed
from users.models import CustomUser  # Asegúrate de importar el modelo correcto

@api_view(['GET'])
def get_other_user_location(request, username):
    """Obtenemos la ubicación de otro usuario autenticado."""
    try:
        # Usamos CustomUser en lugar de User
        other_user = CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        raise NotFound(detail="User not found.")
    
    location = UserLocation.objects.filter(user=other_user).last()
    if location:
        serializer = UserLocationSerializer(location)
        return Response({'user': other_user.username, 'location': serializer.data}, status=status.HTTP_200_OK)
    
    return Response({'message': 'No location found for user.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def user_location(request):
    """Actualizar o crear la ubicación de un usuario autenticado."""
    # Verificar que el usuario esté autenticado
    if not request.user.is_authenticated:
        raise AuthenticationFailed('No autorizado')

    # Obtener las coordenadas de la solicitud
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    if not latitude or not longitude:
        return Response({'error': 'Coordenadas inválidas'}, status=status.HTTP_400_BAD_REQUEST)

    # Crear o actualizar la ubicación
    location = UserLocation.objects.filter(user=request.user).last()
    
    # Crear o actualizar la ubicación
    if location:
        # Si ya existe una ubicación, actualizarla
        serializer = UserLocationSerializer(location, data=request.data, partial=True, context={'request': request})
    else:
        # Si no existe, crear una nueva
        serializer = UserLocationSerializer(data=request.data, context={'request': request})

    # Validar y guardar la ubicación
    if serializer.is_valid():
        serializer.save()  # Aquí `save()` usa el usuario del contexto
        return Response({'message': 'Ubicación guardada correctamente', 'data': serializer.data}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)