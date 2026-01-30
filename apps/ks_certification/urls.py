from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'items', views.KSCertificationItemViewSet, basename='ks-item')
router.register(r'histories', views.KSCertificationHistoryViewSet, basename='ks-history')

urlpatterns = [
    path('', include(router.urls)),
]
