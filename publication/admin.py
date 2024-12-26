from django.contrib import admin
from .models import Publicacion, MediaPublicacion, Contrato, Calificacion, Favorite, Reporte
from users.models import CustomUser, Follower
from chat.models import Message, MessageMedia
from django.utils.timezone import localtime

# ver publicaciones que tiene un usuario en el panel de admin 
class PublishInLine(admin.TabularInline):
    model = Publicacion
    extra = 0
    fields = ('publish_name', 'category')

class CustomUserModel(admin.ModelAdmin):
    inlines=[PublishInLine]
    list_display = ('username', 'email')

#ver las imagenes que tiene una publicacion en el panel de django

class MediaPublicacionInline(admin.TabularInline):
    model = MediaPublicacion
    extra = 1

class PublicacionModel(admin.ModelAdmin):
    inlines = [MediaPublicacionInline]
    list_display = ('publish_name', 'user', 'category', 'created_at', 'publish_state')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'publication', 'created_at')  
    list_filter = ('user',)  
    search_fields = ('user__username', 'publication__publish_name') 

class ReporteAdmin(admin.ModelAdmin):
    list_display = ('id', 'publicacion', 'usuario', 'fecha') 
    list_filter = ('fecha',)  
    ordering = ('-fecha',)  
    search_fields = ('publicacion__publish_name', 'usuario__username')
#MARCELO

class ContratoAdmin(admin.ModelAdmin):
    list_display = ('publish', 'user_p', 'user_r', 'contract_state', 'user_p_state', 'user_r_state', 'created_at', 'completed_at')
    list_filter = ('contract_state', 'created_at', 'completed_at')
    search_fields = ('publish__publish_name', 'user_p__username', 'user_r__username')

    def formatted_meeting_date(self, obj):
        # Asegúrate de que obj.meeting_date sea un datetime con tzinfo
        if obj.meeting_date:
            return localtime(obj.meeting_date).strftime('%Y-%m-%d %H:%M:%S')
        return "-"
    formatted_meeting_date.short_description = "Fecha de Reunión"

admin.site.register(Contrato, ContratoAdmin)



# Register your models here.
admin.site.register(Publicacion, PublicacionModel)
admin.site.register(CustomUser, CustomUserModel)
admin.site.register(MediaPublicacion)
admin.site.register(Message)
admin.site.register(MessageMedia)
admin.site.register(Calificacion)
admin.site.register(Favorite)
admin.site.register(Follower)
admin.site.register(Reporte, ReporteAdmin)
