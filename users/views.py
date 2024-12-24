from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from rest_framework.authtoken.models import Token
from .models import CustomUser, Follower
from publication.models import Publicacion, Calificacion, Contrato
from publication.serializer import PublicacionSerializer, UserSerializer, FollowerSerializer, ContratoSerializer, CalificacionSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from chat.models import Message

class UserViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='chat-users')
    def chat_users(self, request):
        user = request.user
        interacted_users = CustomUser.objects.filter(
            Q(sent_messages__receiver=user) | Q(received_messages__sender=user)
        ).distinct()

        data = []
        for interacted_user in interacted_users:
            # Obtener el último mensaje entre el usuario autenticado y el usuario interactuado
            last_message = Message.objects.filter(
                Q(sender=user, receiver=interacted_user) | Q(sender=interacted_user, receiver=user)
            ).order_by('-timestamp').first()

            data.append({
                'user': UserSerializer(interacted_user, context={'request': request}).data,
                'last_message': {
                    'content': last_message.content if last_message else None,
                    'timestamp': last_message.timestamp if last_message else None,
                    'is_read': last_message.is_read if last_message else None,
                }
            })

        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'],permission_classes=[IsAuthenticated], url_path='follow')
    def follow_user(self, request, pk=None):
        current_user = request.user  # Usuario actual obtenido desde el token

        # Verificar que el usuario objetivo exista
        try:
            target_user = CustomUser.objects.get(id=pk)
        except CustomUser.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=404)

        # Evitar que un usuario se siga a sí mismo
        if current_user == target_user:
            return Response({"error": "No puedes seguirte a ti mismo."}, status=400)

        # Verificar si ya existe la relación de seguimiento
        if Follower.objects.filter(user=target_user, follower=current_user).exists():
            return Response({"error": "Ya estás siguiendo a este usuario."}, status=400)

        # Crear la relación de seguimiento
        Follower.objects.create(user=target_user, follower=current_user)

        return Response({"message": "Usuario seguido exitosamente."}, status=200)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated], url_path='unfollow')
    def unfollow_user(self, request, pk=None):
        current_user = request.user  # Usuario actual obtenido desde el token

        # Verificar que el usuario objetivo exista utilizando el pk
        try:
            target_user = CustomUser.objects.get(id=pk)
        except CustomUser.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=404)

        # Intentar eliminar la relación de seguimiento
        try:
            follower_relation = Follower.objects.get(user=target_user, follower=current_user)
            follower_relation.delete()
            return Response({"message": "Usuario dejado de seguir exitosamente."}, status=200)
        except Follower.DoesNotExist:
            return Response({"error": "No estás siguiendo a este usuario."}, status=400)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='update-profile')
    def update_user(self, request, pk=None):
        print(f"Datos recibidos para actualizar el perfil: {request.data}")  # Ver los datos enviados
        print('username', request.data['username'])
        try:
            user = CustomUser.objects.get(id=pk)

            # Verificar si el usuario autenticado es el que está haciendo la actualización
            if request.user != user:
                return Response({"error": "No tienes permisos para actualizar este usuario."}, status=status.HTTP_403_FORBIDDEN)
            # Actualizar los campos proporcionados en la solicitud
            if 'username' in request.data:
                print('username', request.data['username'])
                user.username = request.data['username']
            if 'email' in request.data:
                print('email', request.data['email'])
                user.email = request.data['email']
            if 'bio' in request.data:
                print('bio', request.data['bio'])
                user.bio = request.data['bio']
            if 'profile_picture' in request.data:
                print('profile_picture', request.data['profile_picture'])
                user.profile_picture = request.data['profile_picture']
            if 'profile_picture' not in request.data:  # Si es explícitamente null o cadena vacía
                    user.profile_picture = None  # Si es explícitamente null o cadena vacía
            
            user.save()
            return Response({"message": "Usuario actualizado exitosamente."}, status=status.HTTP_200_OK)
        
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='up-trade-score')
    def up_trade_score(self, request, pk = None):
        try:
            user = CustomUser.objects.get(id=pk)
            user.trade+=1
            user.save()
            return Response('actualizado', status = status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny], url_path='get-user')
    def get_user(self, request, pk=None):
        try:
            user = CustomUser.objects.get(id=pk)
            # Obtenemos las publicaciones, contratos y calificaciones del usuario
            user_publish = user.publicaciones.all()
            user_contract = Contrato.objects.filter(
                Q(user_p=user) | Q(user_r=user)
            )
            user_calificaciones = Calificacion.objects.filter(user_p=user)

            # Obtenemos los seguidores y seguidos
            followers = user.followers.all()  # Usando la relación inversa 'followers'
            following = user.following.all()  # Usando la relación inversa 'following'

            # Serializadores para las publicaciones, contratos, calificaciones, seguidores y seguidos
            publish_serializer = PublicacionSerializer(user_publish, many=True)
            contract_serializer = ContratoSerializer(user_contract, many=True)
            calificacion_serializer = CalificacionSerializer(user_calificaciones, many=True)
            user_serializer = UserSerializer(user)
            followers_serializer = FollowerSerializer(followers, many=True)
            following_serializer = FollowerSerializer(following, many=True)

            # Respuesta combinada con la información del usuario, publicaciones, contratos, calificaciones, seguidores y seguidos
            return Response({
                'user': user_serializer.data,
                'publish': publish_serializer.data,
                'contract': contract_serializer.data,
                'calificacion': calificacion_serializer.data,
                'followers': followers_serializer.data,
                'following': following_serializer.data,
            }, status=status.HTTP_200_OK)
        
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='check-username')
    def check_username(self, request):
        username = request.query_params.get('username', None)
        if not username:
            return Response({"error": "Se requiere un nombre de usuario."}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = CustomUser.objects.filter(username=username).exists()
        return Response({"exists": exists}, status=status.HTTP_200_OK)

    # Acción personalizada para registrar un nuevo usuario
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='register')
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"username": user.username}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Acción personalizada para el login
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='login')
    def login(self, request):
        serializer = ObtainAuthToken.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # Obtenemos las publicaciones del usuario para incluirlas en la respuesta
        user_publish = user.publicaciones.all()

        publish_serializer = PublicacionSerializer(user_publish, many=True)
        user_serializer = UserSerializer(user)

        return Response({
            'token': token.key,
            'user': user_serializer.data,
            'publish': publish_serializer.data,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='user-publications')
    def user_publications(self, request):
        user = request.user
        user_publish = user.publicaciones.all()
        publish_serializer = PublicacionSerializer(user_publish, many=True)
        return Response(publish_serializer.data, status=status.HTTP_200_OK)
