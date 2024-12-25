from django.urls import path
from .views import LogResponseTime
from .views import response_times_page

urlpatterns = [
    path('log-response-time/', LogResponseTime.as_view(), name='log_response_time'),
     path('monitoreo-app/', response_times_page, name='response_times_page'),
]

# from django.urls import path
# from . import views

# urlpatterns = [
#     path('user/locations/', views.user_location),  # Ruta para ver y crear ubicaciones
#     path('get_other_user_location/<str:username>/', views.get_other_user_location),
# ]
