"""
Account URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView, UserViewSet, LogoutView,
    ReviewerListView, ApproverListView, DepartmentViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'departments', DepartmentViewSet, basename='department')

app_name = 'accounts'

urlpatterns = [
    # JWT Authentication
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # User Lists for Document Workflow
    path('reviewers/', ReviewerListView.as_view(), name='reviewer-list'),
    path('approvers/', ApproverListView.as_view(), name='approver-list'),
    
    # ViewSet routes
    path('', include(router.urls)),
]
