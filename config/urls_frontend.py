"""
Frontend URLs - HTML Page Routes
"""
from django.urls import path
from apps.core.views_frontend import (
    LoginPageView, DashboardPageView,
    DocumentListPageView, DocumentCreatePageView,
    DocumentDetailPageView, DocumentPendingPageView,
    InventoryListPageView, InventoryScanPageView,
    InventoryInPageView, InventoryOutPageView, InventoryAlertsPageView,
    UserManagementPageView, DepartmentManagementPageView,
    ISO9001PageView, ISO14001PageView,
    ExcelDocumentsPageView, ExcelDocumentViewPageView
)

urlpatterns = [
    # Auth
    path('login/', LoginPageView.as_view(), name='login'),
    
    # Dashboard
    path('', DashboardPageView.as_view(), name='home'),
    path('dashboard/', DashboardPageView.as_view(), name='dashboard'),
    
    # Documents
    path('documents/', DocumentListPageView.as_view(), name='document-list'),
    path('documents/new/', DocumentCreatePageView.as_view(), name='document-create'),
    path('documents/pending/', DocumentPendingPageView.as_view(), name='document-pending'),
    path('documents/<uuid:pk>/', DocumentDetailPageView.as_view(), name='document-detail'),
    
    # Inventory
    path('inventory/', InventoryListPageView.as_view(), name='inventory-list'),
    path('inventory/scan/', InventoryScanPageView.as_view(), name='inventory-scan'),
    path('inventory/in/', InventoryInPageView.as_view(), name='inventory-in'),
    path('inventory/out/', InventoryOutPageView.as_view(), name='inventory-out'),
    path('inventory/alerts/', InventoryAlertsPageView.as_view(), name='inventory-alerts'),
    path('inventory/excel-documents/', ExcelDocumentsPageView.as_view(), name='excel-documents'),
    path('inventory/excel-documents/<uuid:pk>/view/', ExcelDocumentViewPageView.as_view(), name='excel-document-view'),
    
    # Users (Admin only)
    path('users/', UserManagementPageView.as_view(), name='user-list'),
    
    # Departments (Admin only)
    path('departments/', DepartmentManagementPageView.as_view(), name='department-list'),
    
    # ISO Manuals
    path('iso/9001/', ISO9001PageView.as_view(), name='iso-9001'),
    path('iso/14001/', ISO14001PageView.as_view(), name='iso-14001'),
]
