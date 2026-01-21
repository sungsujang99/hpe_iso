"""
Document URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DocumentCategoryViewSet, DocumentTemplateViewSet,
    DocumentViewSet, DocumentAttachmentViewSet,
    PendingReviewListView, PendingApprovalListView
)

router = DefaultRouter()
router.register(r'categories', DocumentCategoryViewSet, basename='category')
router.register(r'templates', DocumentTemplateViewSet, basename='template')
router.register(r'items', DocumentViewSet, basename='document')

app_name = 'documents'

urlpatterns = [
    # Workflow endpoints
    path('pending-review/', PendingReviewListView.as_view(), name='pending-review'),
    path('pending-approval/', PendingApprovalListView.as_view(), name='pending-approval'),
    
    # Document attachments (manual nested route)
    path('items/<uuid:document_pk>/attachments/', 
         DocumentAttachmentViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='document-attachment-list'),
    path('items/<uuid:document_pk>/attachments/<int:pk>/',
         DocumentAttachmentViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}),
         name='document-attachment-detail'),
    
    # ViewSet routes
    path('', include(router.urls)),
]
