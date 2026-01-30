"""
Inventory URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WarehouseViewSet, LocationViewSet, ItemCategoryViewSet,
    InventoryItemViewSet, StockTransactionViewSet,
    StockOperationView, BarcodeScanView,
    StockAlertViewSet, InventoryCountViewSet,
    InventoryDashboardView
)
from .views_excel import (
    ExcelMasterDocumentViewSet, ExcelUpdateLogViewSet
)

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'categories', ItemCategoryViewSet, basename='category')
router.register(r'items', InventoryItemViewSet, basename='item')
router.register(r'transactions', StockTransactionViewSet, basename='transaction')
router.register(r'alerts', StockAlertViewSet, basename='alert')
router.register(r'counts', InventoryCountViewSet, basename='count')
router.register(r'excel-documents', ExcelMasterDocumentViewSet, basename='excel-document')
router.register(r'excel-logs', ExcelUpdateLogViewSet, basename='excel-log')

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('dashboard/', InventoryDashboardView.as_view(), name='dashboard'),
    
    # Stock Operations
    path('stock/in/', StockOperationView.as_view(), {'operation_type': 'in'}, name='stock-in'),
    path('stock/out/', StockOperationView.as_view(), {'operation_type': 'out'}, name='stock-out'),
    path('stock/adjust/', StockOperationView.as_view(), {'operation_type': 'adjust'}, name='stock-adjust'),
    path('stock/transfer/', StockOperationView.as_view(), {'operation_type': 'transfer'}, name='stock-transfer'),
    
    # Barcode Scan
    path('scan/', BarcodeScanView.as_view(), name='barcode-scan'),
    
    # ViewSet routes
    path('', include(router.urls)),
]
