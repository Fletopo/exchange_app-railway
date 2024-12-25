from django.db import models
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image
from users.models import CustomUser
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Publicacion(models.Model):

    CATEGORY_CHOICES = [
        ('Tecnologico', 'Tecnologico'),
        ('Deportes', 'Deportes'),
        ('Juegos', 'Juegos'),
        ('Electrodomesticos', 'Electrodomesticos'),
        ('Automoviles', 'Automoviles'),
        ('Electrónica', 'Electrónica'),
        ('Muebles', 'Muebles'),
        ('Ropa y Accesorios', 'Ropa y Accesorios'),
        ('Vehículos', 'Vehículos'),
        ('Inmuebles', 'Inmuebles'),
        ('Servicios', 'Servicios'),
        ('Alimentos y Bebidas', 'Alimentos y Bebidas'),
        ('Salud y Bienestar', 'Salud y Bienestar'),
        ('Deportes y Ocio', 'Deportes y Ocio'),
        ('Hogar', 'Hogar'),
        ('Arte y Entretenimiento', 'Arte y Entretenimiento'),
        ('Mascotas', 'Mascotas'),
        ('Jardinería', 'Jardinería'),
        ('Herramientas y Equipos', 'Herramientas y Equipos'),
        ('Libros y Literatura', 'Libros y Literatura'),
        ('Educación y Formación', 'Educación y Formación'),
        ('Música', 'Música'),
        ('Viajes y Turismo', 'Viajes y Turismo'),
        ('Fotografía y Video', 'Fotografía y Video'),
        ('Coleccionables', 'Coleccionables'),
        ('Seguros', 'Seguros'),
        ('Servicios Profesionales', 'Servicios Profesionales')
        # Agregar más categorías
    ]

    # esto representa el tipo de publicación (artículo, servicio, bienes)
    PUBLISH_CHOICES = [
        ('Articulos', 'Articulos'),
        ('Servicios', 'Servicios'),
        ('Bienes', 'Bienes'),
    ]

    PRODUCTSSS_CONDITION = [
        ('Nuevo', 'Nuevo'),
        ('Casi nuevo', 'Casi nuevo'),
        ('Poco uso', 'Poco uso'),
        ('Usado', 'Usado'),
        ('Desgastado', 'Desgastado'),
    ]

    user = models.ForeignKey(CustomUser , related_name="publicaciones", on_delete=models.CASCADE)#Objeto con datos del usuario publicador.
    publish_name = models.CharField(max_length=100)#el nombre de la publicacion.
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)#categoria del producto Ej:Tecnologico, Deportes, Juegos, Electrodomesticos, Automoviles, etc.
    description = models.TextField(blank=True)#descripcion detallando el producto a intercambiar
    product_condition = models.CharField(max_length=255, choices=PRODUCTSSS_CONDITION, default="Usado", blank=True, null=True)   
    publish_state = models.BooleanField(default=True, blank=True)#Estado de la publicacion True(Publicado/No Oculto)/False(Oculto/Intercambiado)
    created_at = models.DateTimeField(auto_now_add=True)#Fecha de creacion de la Publicacion
    publish_type = models.CharField(max_length=255, choices=PUBLISH_CHOICES, default="Articulos")  
    valor_estimado = models.IntegerField(blank=True, default=0, null=True)

    # esto es del meeting spot coqueto
    latitude = models.FloatField(null=True, blank=True)  # Latitud
    longitude = models.FloatField(null=True, blank=True)  # Longitud


    def __str__(self):
        return self.publish_name

class MediaPublicacion(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='media')
    media = models.FileField(upload_to='publication/', null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'mp4', 'mov'])])

    def get_media_type(self):
        if self.media.name.endswith(('jpg', 'jpeg', 'png')):
            return 'image'
        elif self.media.name.endswith(('mp4', 'mov')):
            return 'video'
        return 'unknown'
        
class Contrato(models.Model):

    CONTRACT_STATE_CHOICES = [
    ('Por confirmar', 'Por confirmar'),
    ('Activo', 'Activo'),
    ('Completado', 'Completado'),
    ('Cancelado', 'Cancelado'),
    ]

    publish = models.ForeignKey(Publicacion, on_delete=models.CASCADE)#Objeto con datos de una publicacion en especifico 
    user_p = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_provider')#Objeto con datos del usuario que publico el producto 
    user_r = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_recieving')#Objeto con datos del usuario que recive el intercambio
    qr_code = models.ImageField(blank=True, upload_to='qrcodes/')
    user_p_state = models.BooleanField(default=False)  # Confirmación del usuario que publicó
    user_r_state = models.BooleanField(default=False)  # Confirmación del usuario que recibe
    contract_state = models.CharField(max_length=100, choices=CONTRACT_STATE_CHOICES, blank=True)  #Estado de contrato Ej: Por confirmar, activo, completado, cancelado
    meeting_date = models.DateTimeField(blank=True, null=True)#Fecha acordada para un encuentro
    created_at = models.DateTimeField(auto_now_add=True) #Fecha de creacion de contrato
    completed_at = models.DateTimeField(blank=True, null=True)# Fecha de cuando se llevo a cabo el intercambio

    def __str__(self):
        return str(f"id_publish:{self.publish.id}, name:{self.publish.publish_name}")
    
    def save(self, *args, **kwargs):

        if not self.qr_code and self.contract_state == 'Activo':
                qrcode_img = qrcode.make(self.publish.id)
                qrcode_img = qrcode_img.convert("RGB")
                canvas = Image.new('RGB', qrcode_img.size, 'white')
                canvas.paste(qrcode_img)
                fname = f'qr_code-{self.publish.id}.png'
                buffer = BytesIO()
                canvas.save(buffer, 'PNG')
                self.qr_code.save(fname, ContentFile(buffer.getvalue()), save=False)
                buffer.close()
                
        super().save(*args, **kwargs)

class Calificacion(models.Model):
    user_p = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_p')
    user_r = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_r')#Objeto con datos del usuario que recivio el intercambio
    publish = models.ForeignKey(Publicacion, on_delete=models.CASCADE)#Objeto con los datos de la publicacion que fue seleccionada para el intercambio
    contract = models.ForeignKey(Contrato, on_delete=models.CASCADE)#Objeto con los datos del contrato
    comment = models.TextField(blank=True, null=True)#Campo que contiene el comentario del usuario
    calificacion = models.FloatField(blank=True)  # Número de calificación (1-5, por ejemplo)
    created_at = models.DateTimeField(auto_now_add=True)#Fecha de creacion de la calificacion

@receiver(post_save, sender=Calificacion)
def actualizar_trade_score(sender, instance, **kwargs):
        """Actualiza el trade_score del usuario receptor cuando se guarda una calificación."""
        instance.user_p.calcular_trade_score()


class Favorite(models.Model):
    user = models.ForeignKey(CustomUser, related_name="favorites", on_delete=models.CASCADE)
    publication = models.ForeignKey(Publicacion, related_name="favorites", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'publication')  # Evita duplicados
        indexes = [
                models.Index(fields=['user', 'publication']),  # Índice combinado para optimizar consultas
            ]

    def __str__(self):
        return f"Favorite: {self.user.username} - {self.publication.publish_name}"

class Reporte(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name="reportes")
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reportes")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('publicacion', 'usuario')  # con esto se válida que un usuario no puede reportar una publicación más de una vez
        indexes = [
            models.Index(fields=['publicacion', 'usuario']),  
        ]

    def __str__(self):
        return f"Reporte: {self.publicacion.publish_name} por {self.usuario.username}"
