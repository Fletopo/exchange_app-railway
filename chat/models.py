from django.db import models
from users.models import CustomUser
from django.core.validators import FileExtensionValidator

# Create your models here.
class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')#Objeto con usuario que envio el mensaje
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')#Objeto con usuario que recivio el mensaje
    content = models.TextField(blank=True,null=True)#Contenido del mensaje que se envia
    timestamp = models.DateTimeField(auto_now_add=True)#Fecha y hora exacta de cuando se envia el mensaje
    is_read = models.BooleanField(default=False) #estado para saber si se leyó el mensaje

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.content[:50]}"

class MessageMedia(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="media")
    media = models.FileField(upload_to='messages/', null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'mp4', 'mov'])])

    def get_media_type(self):
        if self.media.name.endswith(('jpg', 'jpeg', 'png')):
            return 'image'
        elif self.media.name.endswith(('mp4', 'mov')):
            return 'video'
        return 'unknown'

    def __str__(self):
        return f'Media for Message ID {self.message.id} ({self.get_media_type()})'