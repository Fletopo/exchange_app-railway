from rest_framework import serializers
from .models import ResponseTime

class ResponseTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseTime
        fields = ['event_name', 'duration_ms', 'timestamp']
