from django.contrib import admin
from .models import KSCertificationItem, KSCertificationHistory


@admin.register(KSCertificationItem)
class KSCertificationItemAdmin(admin.ModelAdmin):
    list_display = [
        'barcode', 'name', 'status', 'manufacturer',
        'certification_date', 'expiry_date', 'quantity', 'unit',
        'inspection_required', 'created_at'
    ]
    list_filter = ['status', 'inspection_required', 'certification_body', 'created_at']
    search_fields = ['barcode', 'name', 'serial_number', 'manufacturer', 'ks_standard_number']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('barcode', 'name', 'serial_number', 'status')
        }),
        ('KS 인증 정보', {
            'fields': ('ks_standard_number', 'certification_date', 'expiry_date', 'certification_body')
        }),
        ('제조사 정보', {
            'fields': ('manufacturer', 'manufacturer_country')
        }),
        ('재고 정보', {
            'fields': ('quantity', 'unit', 'location')
        }),
        ('점검 정보', {
            'fields': ('inspection_required', 'last_inspection_date', 'next_inspection_date')
        }),
        ('비고', {
            'fields': ('remarks',)
        }),
        ('메타 정보', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(KSCertificationHistory)
class KSCertificationHistoryAdmin(admin.ModelAdmin):
    list_display = ['item', 'action_type', 'created_at', 'created_by']
    list_filter = ['action_type', 'created_at']
    search_fields = ['item__barcode', 'item__name', 'action_description']
    readonly_fields = ['id', 'item', 'action_type', 'action_description', 
                      'previous_value', 'new_value', 'created_at', 'created_by']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
