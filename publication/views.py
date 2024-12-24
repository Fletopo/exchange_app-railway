from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.models import CustomUser
from .models import Publicacion, MediaPublicacion, Contrato, Calificacion, Favorite, Reporte
from .serializer import PublicacionSerializer, ContratoSerializer, CalificacionSerializer, FavoriteSerializer, ReporteSerializer


# Create your views here.

class PublicacionView(viewsets.ModelViewSet):
    serializer_class = PublicacionSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Permitir a todos ver la lista y los detalles de los juegos
            permission_classes = [permissions.AllowAny]
        else:
            # Solo el creador del juego puede editarlo
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Publicacion.objects.all()

        # Obtener parámetros de la query
        publish_type = self.request.query_params.get('publish_type', None)
        category = self.request.query_params.get('category', None)
        search_query = self.request.query_params.get('search', None)

        # Filtrado por tipo de publicación
        if publish_type:
            queryset = queryset.filter(publish_type__iexact=publish_type)

        # Filtrado por categoría
        if category and category != "Todos":
            queryset = queryset.filter(category__iexact=category)

        # Filtrado por nombre de publicación (búsqueda)
        if search_query:
            queryset = queryset.filter(publish_name__icontains=search_query)

        return queryset

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='create-publication')
    def create_publication(self, request):
        current_user = request.user  # Usuario actual obtenido desde el token

        # Serializar los datos recibidos para la publicación
        serializer = PublicacionSerializer(data=request.data)
        
        # Validar los datos
        if serializer.is_valid():
            # Guardar la publicación con el usuario actual como creador
            publicacion = serializer.save(user=current_user)

            # Verificar y actualizar latitud y longitud
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            if latitude and longitude:
                publicacion.latitude = latitude
                publicacion.longitude = longitude
                publicacion.save()

            # Guardar los archivos de medios (si los hay)
            files = request.FILES.getlist('media')
            if files:
                for file in files:
                    MediaPublicacion.objects.create(publicacion=publicacion, media=file)

            # Serializar la publicación y devolverla en la respuesta
            publicacion_serializer = PublicacionSerializer(publicacion)
            return Response(publicacion_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_update(self, serializer):
        # Obtener la publicación a actualizar
        publicacion = serializer.save(user=self.request.user)

        # Actualizar las coordenadas de la ubicación (si se proporcionan)
        latitude = self.request.data.get('latitude')
        longitude = self.request.data.get('longitude')

        # Si las coordenadas son válidas, actualizamos
        if latitude is not None and longitude is not None:
            publicacion.latitude = latitude
            publicacion.longitude = longitude
            publicacion.save()

        # Obtener las imágenes actuales de la publicación
        current_media = MediaPublicacion.objects.filter(publicacion=publicacion)

        # Obtener las imágenes existentes enviadas en la solicitud
        existing_images = self.request.data.getlist('existing_images')  # Esto debería contener los IDs de las imágenes existentes
        files = self.request.FILES.getlist('media')  # Nuevas imágenes enviadas

        # Eliminar las imágenes que no están en la lista de existentes
        for image in current_media:
            if str(image.id) not in existing_images:
                print(f"Eliminando imagen: {image.id}")  # Depuración: mostrar qué imágenes se eliminan
                image.delete()

        # Agregar las nuevas imágenes
        for file in files:
            print(f"Agregando imagen nueva: {file}")  # Depuración: mostrar qué imágenes se están agregando
            MediaPublicacion.objects.create(publicacion=publicacion, media=file)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        # Obtener las opciones de categoría definidas en el modelo
        categories = dict(Publicacion.CATEGORY_CHOICES)
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def products_condition(self, request):
        # Obtener las opciones de categoría definidas en el modelo
        products_condition = dict(Publicacion.PRODUCTSSS_CONDITION)
        return Response(products_condition)
    
    @action(detail=False, methods=['get'])
    def publish_types(self, request):
        # Obtener las opciones de categoría definidas en el modelo
        publish_types = dict(Publicacion.PUBLISH_CHOICES)
        return Response(publish_types)

    @action(detail=False, methods=['get'])
    def filter_by_tipo(self, request):
        tipo = request.query_params.get('tipo')  # Obtener el parámetro 'tipo' del query string
        if tipo not in ['Servicio', 'Articulo', 'Propiedad']:
            return Response({"error": "El tipo proporcionado no es válido."}, status=400)

        publicaciones = Publicacion.objects.filter(tipo=tipo, publish_state=True)  # Filtra por tipo y publicaciones activas
        serializer = self.get_serializer(publicaciones, many=True)
        return Response(serializer.data)
    
     # Agregar a favoritos
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_favorite(self, request, pk=None):
        """
        Agregar una publicación a los favoritos del usuario.
        """
        publicacion = self.get_object()  # Obtiene la publicación por su ID (pk)
        
        # Verificar si ya está marcada como favorita
        existing_favorite = Favorite.objects.filter(user=request.user, publication=publicacion).first()
        if existing_favorite:
            return Response({"detail": "Ya has marcado esta publicación como favorita"}, status=status.HTTP_400_BAD_REQUEST)

        # Crear un nuevo favorito
        favorite = Favorite.objects.create(user=request.user, publication=publicacion)
        serializer = FavoriteSerializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def remove_favorite(self, request, pk=None):
        """
        Eliminar una publicación de los favoritos del usuario.
        """
        publicacion = self.get_object()  # Obtiene la publicación por su ID (pk)
        
        # Eliminar el favorito
        # favorite = Favorite.objects.filter(user=request.user, publication=publicacion).first()

        exists = Favorite.objects.filter(user=request.user, publication=publicacion).exists()
        if not exists:
            return Response({"detail": "No es posible eliminar un favorito que no existe"}, status=status.HTTP_400_BAD_REQUEST)

        # Si existe, elimínalo
        Favorite.objects.filter(user=request.user, publication=publicacion).delete()
        return Response({"detail": "Favorito eliminado exitosamente"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def favorite_list(self, request):
        """
        Listar las publicaciones favoritas del usuario.
        """
        # Obtener las publicaciones favoritas del usuario autenticado
        favorites = Favorite.objects.filter(user=request.user)
        publicaciones_favoritas = [favorite.publication for favorite in favorites]
        
        # Serializar las publicaciones favoritas
        serializer = PublicacionSerializer(publicaciones_favoritas, many=True)
        return Response(serializer.data)

# Reportar una publicación
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def report(self, request, pk=None):
        """
        Permite a un usuario reportar una publicación.
        """
        publicacion = self.get_object()  

        
        existe_reporte = Reporte.objects.filter(publicacion=publicacion, usuario=request.user).exists()
        if existe_reporte:
            return Response({"detail": "Ya has reportado esta publicación."}, status=status.HTTP_400_BAD_REQUEST)

        # crear un nuevo reporte
        Reporte.objects.create(publicacion=publicacion, usuario=request.user)

        # contar los reportes y deshabilitar nuevas publicaciones del autor si alcanza el límite
        total_reportes = Reporte.objects.filter(publicacion=publicacion).count()
        if total_reportes >= 3:
            # obtener el autor de la publicación
            autor = publicacion.user
            autor.can_create_publications = False  # con este campo se valida que el socio pueda publicar o no
            autor.save()

        return Response({"detail": "La publicación ha sido reportada exitosamente."}, status=status.HTTP_201_CREATED)


    
class ContractView(viewsets.ModelViewSet):
    serializer_class = ContratoSerializer

    def get_queryset(self):
        return Contrato.objects.all()

    def perform_create(self, serializer):
        user_p_id = self.request.data.get('user_p')
        user_r_id = self.request.data.get('user_r')
        publish_id = self.request.data.get('publish')
        new_contract_state = self.request.data.get('contract_state')  # Estado por defecto

        # Obtener las instancias relacionadas
        user_p = CustomUser.objects.get(id=user_p_id)
        user_r = CustomUser.objects.get(id=user_r_id)
        publish = Publicacion.objects.get(id=publish_id)

        # Validar si ya existe un contrato activo con estos parámetros
        existing_active_contract = Contrato.objects.filter(
            user_p=user_p, user_r=user_r, publish=publish, contract_state="Activo"
        ).exists()

        if existing_active_contract and new_contract_state == "Activo":
            raise ValidationError("Ya existe un contrato activo con estos usuarios y publicación.")

        # Guardar el contrato si pasa la validación
        serializer.save(publish=publish, user_p=user_p, user_r=user_r)
        
class CalificacionView(viewsets.ModelViewSet):

    serializer_class = CalificacionSerializer

    def get_queryset(self):
        return Calificacion.objects.all()
    
    def perform_create(self, serializer):

        user_p_id = self.request.data.get('user_p')
        user_r_id = self.request.data.get('user_r')
        publish_id = self.request.data.get('publish')
        contract_id = self.request.data.get('contract')

        user_p_id = int(user_p_id)
        user_r_id = int(user_r_id)
        publish_id = int(publish_id)
        contract_id = int(contract_id)

        user_p = CustomUser.objects.get(id = user_p_id)
        user_r = CustomUser.objects.get(id = user_r_id)
        publish = Publicacion.objects.get(id = publish_id)
        contract = Contrato.objects.get(id=contract_id)

        serializer.save( user_p = user_p, user_r = user_r, publish = publish, contract=contract)
