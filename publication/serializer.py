from rest_framework import serializers
from .models import Publicacion, MediaPublicacion, Contrato, Calificacion, Favorite, Reporte
from users.models import CustomUser, Follower
from chat.models import Message
from django.utils import timezone
from datetime import datetime, date, time
from django.utils.timezone import make_aware

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'password', 'email', 'birthday', 'profile_picture', 'trade_score', 'date_joined', 'user_state', 'user_verified', 'account_creation', 'bio', 'trade', 'can_create_publications', 'cant_trade_time', 'can_trade')

    def create(self, validated_data):

        validated_data['can_create_publications'] = True
        validated_data['can_trade'] = True

        user = CustomUser(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    receiver = UserSerializer()

    class Meta:
        model = Message
        fields = ['sender', 'receiver', 'content', 'timestamp']

class FollowerSerializer(serializers.ModelSerializer):
    follower = UserSerializer()  # Mostrar el username o el campo que desees
    user = UserSerializer()

    class Meta:
        model = Follower
        fields = ['user', 'follower']

class MediaPublicacionSerializer(serializers.ModelSerializer):
    
    media_type = serializers.SerializerMethodField()

    class Meta:
        model = MediaPublicacion
        fields = ('id', 'media', 'media_type')

    def get_media_type(self, obj):
        return obj.get_media_type()

class PublicacionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    media = MediaPublicacionSerializer(many=True, read_only=True)

    class Meta:
        model = Publicacion
        fields = '__all__'
        

class ContratoSerializer(serializers.ModelSerializer):
    
    publish = PublicacionSerializer(read_only=True)
    user_p = UserSerializer(read_only=True)
    user_r = UserSerializer(read_only=True)

    class Meta:
        model = Contrato
        fields = ['id', 'publish', 'user_p', 'user_r', 'qr_code', 'contract_state', 'meeting_date','created_at','user_p_state','user_r_state', 'completed_at']

    def validate_meeting_date(self, value):
        # Validar que el valor sea un date y no un datetime
        if isinstance(value, date) and not isinstance(value, datetime):
            # Convertir a datetime si solo es una fecha
            return datetime.combine(value, time(hour=12))  # Hora por defecto: mediodía
        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        meeting_date = representation.get('meeting_date')
        
        # Si `meeting_date` es solo una fecha, conviértelo a un datetime
        if isinstance(meeting_date, date) and not isinstance(meeting_date, datetime):
            representation['meeting_date'] = make_aware(datetime.combine(meeting_date, time.min))
        
        return representation

    def update(self, instance, validated_data):
        # Si el estado del contrato es 'Completado', actualizamos 'completed_at'
        if validated_data.get('contract_state') == 'Completado' and instance.contract_state != 'Completado':
            validated_data['completed_at'] = timezone.now()  # Agregar la fecha actual al completar el contrato

        return super().update(instance, validated_data)

class CalificacionSerializer(serializers.ModelSerializer):
    publish = PublicacionSerializer(read_only=True)
    user_p = UserSerializer(read_only=True)
    user_r = UserSerializer(read_only=True)
    contract = ContratoSerializer(read_only=True)

    class Meta:
        model = Calificacion
        fields = ['id', 'user_p', 'user_r', 'publish', 'contract', 'comment', 'calificacion', 'created_at']

class FavoriteSerializer(serializers.ModelSerializer):
    publication = serializers.PrimaryKeyRelatedField(queryset=Publicacion.objects.all())
    
    class Meta:
        model = Favorite
        fields = '__all__'
        read_only_fields = ['created_at']  # No dejamos que el campo created_at sea modificable

    def create(self, validated_data):
        return Favorite.objects.create(**validated_data)

class ReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporte
        fields = ['id', 'publicacion', 'usuario', 'fecha']
        read_only_fields = ['fecha']