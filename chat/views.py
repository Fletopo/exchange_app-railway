from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Message, MessageMedia
from publication.serializer import UserSerializer, MessageSerializer
from users.models import CustomUser
from django.http import JsonResponse
from rest_framework.response import Response
from django.db.models import Q
from rest_framework import status

class ChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # Para manejar archivos

    def list(self, request):
        """Obtener los usuarios con los que se ha intercambiado mensajes"""
        user = request.user
        chats = CustomUser.objects.filter(
            Q(sent_messages__receiver=user) | Q(received_messages__sender=user)
        ).distinct()
        serializer = UserSerializer(chats, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Obtener los mensajes entre el usuario autenticado y otro usuario"""
        user = request.user
        receiver_id = pk  # El ID del usuario con el que se quiere obtener los mensajes

        messages = Message.objects.filter(
            Q(sender=user, receiver_id=receiver_id) | Q(sender_id=receiver_id, receiver=user)
        ).order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Crear un nuevo mensaje y asociar imágenes si se incluyen"""
        receiver_id = request.data.get('receiver')
        content = request.data.get('content')
        sender = request.user

        # Crear el mensaje
        message = Message.objects.create(sender=sender, receiver_id=receiver_id, content=content)

        # Manejar las imágenes si se incluyen
        images = request.FILES.getlist('images')
        for image in images:
            MessageMedia.objects.create(message=message, image=image)

        # Serializar y devolver el mensaje creado
        serializer = MessageSerializer(message)
        return JsonResponse(serializer.data, status=201)

    def destroy(self, request, pk=None):
        user = request.user
        receiver_id = pk  # ID del usuario con quien se desea eliminar los mensajes

        messages = Message.objects.filter(
            Q(sender=user, receiver_id=receiver_id) | Q(sender_id=receiver_id, receiver=user)
        )

        if not messages.exists():
            return Response({"detail": "No se encontraron mensajes entre estos usuarios."}, status=status.HTTP_404_NOT_FOUND)

        # Eliminar los mensajes
        messages.delete()

        return Response({"detail": "Mensajes eliminados exitosamente."}, status=status.HTTP_200_OK)
    
    