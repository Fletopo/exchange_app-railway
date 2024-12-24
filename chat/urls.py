from django.urls import path, include
from rest_framework.routers import DefaultRouter
from chat.views import ChatViewSet

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')

urlpatterns = [
    path('api/', include(router.urls)),
]
