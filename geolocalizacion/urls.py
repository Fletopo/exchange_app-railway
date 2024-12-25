from django.urls import path
from . import views

urlpatterns = [
    path('user/locations/', views.user_location),  # Ruta para ver y crear ubicaciones
    path('get_other_user_location/<str:username>/', views.get_other_user_location),
]
