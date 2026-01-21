"""
Inventory Serializers
"""
from rest_framework import serializers
from django.utils import timezone
from .models import (
    Warehouse, Location, ItemCategory, InventoryItem,
    StockTransaction, StockAlert, InventoryCount, InventoryCountItem
)


class WarehouseSerializer(serializers.ModelSerializer):
    """창고 시리얼라이저"""
    
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    location_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Warehouse
        fields = ['id', 'code', 'name', 'address', 'manager', 'manager_name', 
                  'location_count', 'is_active', 'created_at']
    
    def get_location_count(self, obj):
        return obj.locations.filter(is_active=True).count()


class LocationSerializer(serializers.ModelSerializer):
    """위치 시리얼라이저"""
    
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    full_code = serializers.SerializerMethodField()
    
    class Meta:
        model = Location
        fields = ['id', 'warehouse', 'warehouse_name', 'code', 'name', 
                  'description', 'barcode', 'full_code', 'is_active']
    
    def get_full_code(self, obj):
        return f"{obj.warehouse.code}-{obj.code}"


class ItemCategorySerializer(serializers.ModelSerializer):
    """품목 카테고리 시리얼라이저"""
    
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemCategory
        fields = ['id', 'code', 'name', 'parent', 'parent_name', 'description', 
                  'children', 'is_active']
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return ItemCategorySerializer(children, many=True).data


class InventoryItemListSerializer(serializers.ModelSerializer):
    """품목 목록 시리얼라이저"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    location_name = serializers.CharField(source='default_location.name', read_only=True)
    stock_status = serializers.CharField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'item_code', 'barcode', 'name', 'serial_number', 'category', 'category_name',
            'item_type', 'unit', 'current_quantity', 'safety_stock',
            'default_location', 'location_name', 'stock_status', 'is_low_stock',
            'manufacturer', 'inspection_required', 'inspection_due_date', 'is_active'
        ]


class InventoryItemDetailSerializer(serializers.ModelSerializer):
    """품목 상세 시리얼라이저"""
    
    category_detail = ItemCategorySerializer(source='category', read_only=True)
    location_detail = LocationSerializer(source='default_location', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    stock_status = serializers.CharField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'item_code', 'barcode', 'name', 'serial_number', 'description',
            'category', 'category_detail', 'item_type', 'unit', 'specification',
            'manufacturer', 'supplier', 'current_quantity', 'safety_stock',
            'default_location', 'location_detail', 'unit_price', 'image',
            'iso_document', 'stock_status', 'is_low_stock', 'is_active',
            'inspection_required', 'inspection_due_date',
            'created_at', 'updated_at', 'created_by', 'created_by_name'
        ]


class InventoryItemCreateSerializer(serializers.ModelSerializer):
    """품목 생성 시리얼라이저 - 필수 필드만"""
    
    # 필수 필드
    barcode = serializers.CharField(required=True, max_length=100, help_text='관리번호(바코드)')
    name = serializers.CharField(required=True, max_length=200, help_text='품목명')
    serial_number = serializers.CharField(required=True, max_length=100, help_text='시리얼번호')
    
    # 선택 필드
    manufacturer = serializers.CharField(required=False, allow_blank=True, max_length=100, help_text='제작사')
    inspection_required = serializers.BooleanField(required=False, default=False, help_text='점검여부')
    inspection_due_date = serializers.DateField(required=False, allow_null=True, help_text='점검예정일자')
    
    # item_code는 자동 생성 (read_only)
    item_code = serializers.CharField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'barcode', 'item_code', 'name', 'serial_number', 
            'manufacturer', 'inspection_required', 'inspection_due_date'
        ]
    
    def validate_barcode(self, value):
        """바코드 중복 체크"""
        if InventoryItem.objects.filter(barcode=value).exists():
            raise serializers.ValidationError('이미 등록된 관리번호(바코드)입니다.')
        return value
    
    def create(self, validated_data):
        # item_code는 barcode와 동일하게 설정
        barcode = validated_data.get('barcode', '')
        validated_data['item_code'] = barcode
        
        # 기본값 설정
        validated_data['unit'] = 'EA'
        validated_data['item_type'] = InventoryItem.ItemType.EQUIPMENT
        validated_data['current_quantity'] = 0
        
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class StockTransactionSerializer(serializers.ModelSerializer):
    """재고 거래 시리얼라이저"""
    
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.item_code', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = StockTransaction
        fields = [
            'id', 'transaction_number', 'item', 'item_name', 'item_code',
            'transaction_type', 'transaction_type_display', 'quantity',
            'before_quantity', 'after_quantity', 'location', 'location_name',
            'to_location', 'reference_number', 'remarks',
            'performed_by', 'performed_by_name', 'created_at',
            'scanned_barcode', 'scan_device'
        ]
        read_only_fields = [
            'transaction_number', 'before_quantity', 'after_quantity', 'performed_by'
        ]


class StockInSerializer(serializers.Serializer):
    """입고 시리얼라이저 (바코드 기반) - 자동 품목 생성"""
    
    item_id = serializers.UUIDField(required=False, allow_null=True)
    barcode = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    location_id = serializers.IntegerField(required=False, allow_null=True)
    reference_number = serializers.CharField(required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
    scanned_barcode = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """item_id 또는 barcode 중 하나는 필수, 새 바코드면 자동 생성"""
        item_id = attrs.get('item_id')
        barcode = attrs.get('barcode')
        
        if not item_id and not barcode:
            raise serializers.ValidationError('item_id 또는 barcode 중 하나는 필수입니다.')
        
        # barcode로 item 찾기 또는 자동 생성 (입고 시에만)
        if barcode and not item_id:
            try:
                item = InventoryItem.objects.get(barcode=barcode)
                attrs['item_id'] = item.id
            except InventoryItem.DoesNotExist:
                # 새로운 바코드인 경우 자동으로 품목 생성
                item = InventoryItem.objects.create(
                    barcode=barcode,
                    item_code=barcode,  # item_code는 barcode와 동일하게 자동 생성
                    name=f'품목-{barcode}',  # 기본 이름 (나중에 수정 가능)
                    serial_number=barcode,  # serial_number도 barcode로 설정
                    unit='EA',
                    item_type=InventoryItem.ItemType.EQUIPMENT,
                    current_quantity=0,
                    created_by=self.context['request'].user
                )
                attrs['item_id'] = item.id
                attrs['_new_item_created'] = True  # 새 품목 생성 플래그
        
        return attrs


class StockOutSerializer(serializers.Serializer):
    """출고 시리얼라이저 (바코드 기반)"""
    
    item_id = serializers.UUIDField(required=False, allow_null=True)
    barcode = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    location_id = serializers.IntegerField(required=False, allow_null=True)
    reference_number = serializers.CharField(required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
    scanned_barcode = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """item_id 또는 barcode 중 하나는 필수"""
        item_id = attrs.get('item_id')
        barcode = attrs.get('barcode')
        
        if not item_id and not barcode:
            raise serializers.ValidationError('item_id 또는 barcode 중 하나는 필수입니다.')
        
        # barcode로 item 찾기
        if barcode and not item_id:
            try:
                item = InventoryItem.objects.get(barcode=barcode)
                attrs['item_id'] = item.id
            except InventoryItem.DoesNotExist:
                raise serializers.ValidationError(f'바코드 "{barcode}"에 해당하는 품목을 찾을 수 없습니다.')
        
        return attrs


class StockTransferSerializer(serializers.Serializer):
    """재고 이동 시리얼라이저"""
    
    item_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    from_location_id = serializers.IntegerField()
    to_location_id = serializers.IntegerField()
    remarks = serializers.CharField(required=False, allow_blank=True)


class StockAdjustSerializer(serializers.Serializer):
    """재고 조정 시리얼라이저"""
    
    item_id = serializers.UUIDField()
    new_quantity = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    reason = serializers.CharField()


class BarcodeScanSerializer(serializers.Serializer):
    """바코드 스캔 시리얼라이저"""
    
    barcode = serializers.CharField(max_length=100)
    scan_type = serializers.ChoiceField(choices=['item', 'location', 'any'], default='any')


class StockAlertSerializer(serializers.ModelSerializer):
    """재고 알림 시리얼라이저"""
    
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.item_code', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    
    class Meta:
        model = StockAlert
        fields = [
            'id', 'item', 'item_name', 'item_code', 'alert_type', 'alert_type_display',
            'message', 'current_quantity', 'threshold_quantity',
            'is_resolved', 'resolved_at', 'resolved_by', 'created_at'
        ]


class InventoryCountSerializer(serializers.ModelSerializer):
    """재고 실사 시리얼라이저"""
    
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryCount
        fields = [
            'id', 'count_number', 'warehouse', 'warehouse_name', 'status',
            'count_date', 'remarks', 'created_by', 'created_by_name',
            'approved_by', 'created_at', 'completed_at', 'item_count'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()


class InventoryCountItemSerializer(serializers.ModelSerializer):
    """재고 실사 품목 시리얼라이저"""
    
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.item_code', read_only=True)
    item_barcode = serializers.CharField(source='item.barcode', read_only=True)
    
    class Meta:
        model = InventoryCountItem
        fields = [
            'id', 'inventory_count', 'item', 'item_name', 'item_code', 'item_barcode',
            'system_quantity', 'counted_quantity', 'difference', 'remarks',
            'counted_by', 'counted_at'
        ]
        read_only_fields = ['system_quantity', 'difference']


class DashboardStatsSerializer(serializers.Serializer):
    """대시보드 통계 시리얼라이저"""
    
    total_items = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    transactions_today = serializers.IntegerField()
    pending_alerts = serializers.IntegerField()
