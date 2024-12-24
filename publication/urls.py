from django.urls import path, include
from rest_framework.routers import DefaultRouter
from publication import views

router = DefaultRouter()
router.register(r'publication', views.PublicacionView, basename='publication')
router.register(r'contracts', views.ContractView, basename='contracts')
router.register(r'calification', views.CalificacionView, basename='calification')

urlpatterns = [
    path("api/", include(router.urls)),
]

