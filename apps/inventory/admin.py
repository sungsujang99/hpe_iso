"""
Inventory Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Warehouse, Location, ItemCategory, InventoryItem,
    StockTransaction, StockAlert, InventoryCount, InventoryCountItem,
    ExcelMasterDocument, ExcelUpdateLog
)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'manager', 'location_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    
    def location_count(self, obj):
        return obj.locations.count()
    location_count.short_description = '위치 수'


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'warehouse', 'barcode', 'is_active']
    list_filter = ['warehouse', 'is_active']
    search_fields = ['code', 'name', 'barcode']


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['code', 'name']


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = [
        'item_code', 'name', 'category', 'item_type',
        'current_quantity', 'safety_stock', 'stock_status_badge',
        'unit', 'is_active'
    ]
    list_filter = ['item_type', 'category', 'is_active']
    search_fields = ['item_code', 'name', 'barcode']
    readonly_fields = ['barcode', 'current_quantity', 'created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('item_code', 'barcode', 'name', 'description', 'category', 'item_type')
        }),
        ('규격', {
            'fields': ('unit', 'specification', 'manufacturer', 'supplier')
        }),
        ('재고', {
            'fields': ('current_quantity', 'safety_stock', 'default_location')
        }),
        ('가격', {
            'fields': ('unit_price',)
        }),
        ('기타', {
            'fields': ('image', 'iso_document', 'is_active', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    def stock_status_badge(self, obj):
        if obj.current_quantity <= 0:
            color = '#dc3545'
            text = '재고없음'
        elif obj.is_low_stock:
            color = '#ffc107'
            text = '부족'
        else:
            color = '#28a745'
            text = '정상'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, text
        )
    stock_status_badge.short_description = '재고상태'


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_number', 'item', 'transaction_type',
        'quantity', 'before_quantity', 'after_quantity',
        'performed_by', 'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['transaction_number', 'item__item_code', 'item__name']
    readonly_fields = [
        'transaction_number', 'item', 'transaction_type', 'quantity',
        'before_quantity', 'after_quantity', 'location', 'to_location',
        'reference_number', 'remarks', 'performed_by', 'created_at',
        'scanned_barcode', 'scan_device'
    ]
    
    def has_add_permission(self, request):
        return False  # 거래는 API를 통해서만 생성
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = [
        'item', 'alert_type', 'current_quantity', 'threshold_quantity',
        'is_resolved', 'created_at'
    ]
    list_filter = ['alert_type', 'is_resolved', 'created_at']
    search_fields = ['item__item_code', 'item__name']
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_resolved=True, resolved_at=timezone.now(), resolved_by=request.user)
    mark_resolved.short_description = '선택된 알림 해결 처리'


class InventoryCountItemInline(admin.TabularInline):
    model = InventoryCountItem
    extra = 0
    readonly_fields = ['system_quantity', 'difference']


@admin.register(InventoryCount)
class InventoryCountAdmin(admin.ModelAdmin):
    list_display = ['count_number', 'warehouse', 'status', 'count_date', 'created_by', 'created_at']
    list_filter = ['status', 'warehouse', 'count_date']
    search_fields = ['count_number']
    inlines = [InventoryCountItemInline]


@admin.register(ExcelMasterDocument)
class ExcelMasterDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'doc_type', 'total_items', 'last_updated']
    list_filter = ['doc_type']
    search_fields = ['title', 'file_path']
    readonly_fields = ['total_items', 'last_updated', 'created_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('doc_type', 'title', 'file_path', 'sheet_name')
        }),
        ('엑셀 구조', {
            'fields': ('header_row', 'data_start_row', 'barcode_column', 'name_column', 'extra_columns')
        }),
        ('통계', {
            'fields': ('total_items', 'last_updated', 'created_at')
        }),
    )


@admin.register(ExcelUpdateLog)
class ExcelUpdateLogAdmin(admin.ModelAdmin):
    list_display = ['barcode', 'document', 'action', 'created_by', 'created_at']
    list_filter = ['action', 'document', 'created_at']
    search_fields = ['barcode']
    readonly_fields = ['document', 'barcode', 'action', 'updates', 'previous_values', 'created_at', 'created_by']
    
    def has_add_permission(self, request):
        return False  # 로그는 자동으로만 생성
    
    def has_change_permission(self, request, obj=None):
        return False  # 로그는 수정 불가
