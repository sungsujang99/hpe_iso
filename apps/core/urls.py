from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]
