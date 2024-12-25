from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ResponseTime
from .serializer import ResponseTimeSerializer
from django.shortcuts import render
from django.db.models import Avg
from rest_framework.permissions import AllowAny
from publication.models import Publicacion  # Importa el modelo Publicacion
from users.models import CustomUser  # Importa el modelo de usuario
class LogResponseTime(APIView):
    permission_classes = [AllowAny]  # Permite acceso sin autenticación

    def post(self, request):
        # Lógica de tu vista
        serializer = ResponseTimeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



def response_times_page(request):
    events = ResponseTime.objects.values('event_name').distinct()  # Obtener eventos únicos
    grouped_data = {}
    averages = {}

    # Agrupar y escalar los valores de duration_ms
    for event in events:
        event_name = event['event_name']
        event_data = ResponseTime.objects.filter(event_name=event_name, duration_ms__gt=0).order_by('timestamp')

        # Calcular promedio de duración por categoría
        avg_duration = ResponseTime.objects.filter(event_name=event_name).aggregate(Avg('duration_ms'))['duration_ms__avg']
        averages[event_name] = round(avg_duration, 2) if avg_duration else 0

        scaled_data = []
        for item in event_data:
            scaled_data.append({
                'event_name': item.event_name,
                'duration_ms': item.duration_ms,
                'percentage': min((item.duration_ms / 1000) * 100, 100),
                'timestamp': item.timestamp,
                'bar_class': 'red' if item.duration_ms > 1000 else 'green',
            })
        grouped_data[event_name] = scaled_data

    # Obtener la cantidad de publicaciones
    publicaciones_count = Publicacion.objects.count()

    # Obtener la cantidad de usuarios
    usuarios_count = CustomUser.objects.count()

    return render(request, 'monitoreo/response_times.html', {
        'grouped_data': grouped_data,
        'averages': averages,
        'publicaciones_count': publicaciones_count,  # Cantidad de publicaciones
        'usuarios_count': usuarios_count,  # Cantidad de usuarios
    })