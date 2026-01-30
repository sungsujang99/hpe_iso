from rest_framework import serializers
from .models import KSCertificationItem, KSCertificationHistory
from apps.accounts.serializers import UserSerializer


class KSCertificationItemListSerializer(serializers.ModelSerializer):
    """KS 인증 품목 목록 시리얼라이저"""
    is_expired = serializers.BooleanField(read_only=True)
    is_inspection_due = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = KSCertificationItem
        fields = [
            'id', 'barcode', 'name', 'serial_number', 'status',
            'manufacturer', 'quantity', 'unit', 'location',
            'certification_date', 'expiry_date', 'is_expired',
            'inspection_required', 'next_inspection_date', 'is_inspection_due',
            'created_at', 'updated_at'
        ]


class KSCertificationItemDetailSerializer(serializers.ModelSerializer):
    """KS 인증 품목 상세 시리얼라이저"""
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    updated_by_detail = UserSerializer(source='updated_by', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_inspection_due = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = KSCertificationItem
        fields = '__all__'


class KSCertificationItemCreateSerializer(serializers.ModelSerializer):
    """KS 인증 품목 생성 시리얼라이저"""
    
    class Meta:
        model = KSCertificationItem
        fields = [
            'barcode', 'name', 'serial_number', 'ks_standard_number',
            'certification_date', 'expiry_date', 'certification_body',
            'manufacturer', 'manufacturer_country', 'status',
            'location', 'quantity', 'unit',
            'inspection_required', 'last_inspection_date', 'next_inspection_date',
            'remarks'
        ]
    
    def validate_barcode(self, value):
        """바코드 유효성 검증"""
        if not value.startswith('HP-KSTC-'):
            raise serializers.ValidationError('KS 인증 품목의 관리번호는 HP-KSTC-로 시작해야 합니다.')
        return value
    
    def create(self, validated_data):
        # 생성자 설정
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        
        item = super().create(validated_data)
        
        # 이력 기록
        KSCertificationHistory.objects.create(
            item=item,
            action_type=KSCertificationHistory.ActionType.REGISTER,
            action_description=f'KS 인증 품목 등록: {item.name}',
            new_value={'barcode': item.barcode, 'name': item.name},
            created_by=self.context['request'].user
        )
        
        return item


class KSCertificationItemUpdateSerializer(serializers.ModelSerializer):
    """KS 인증 품목 수정 시리얼라이저"""
    
    class Meta:
        model = KSCertificationItem
        fields = [
            'name', 'serial_number', 'ks_standard_number',
            'certification_date', 'expiry_date', 'certification_body',
            'manufacturer', 'manufacturer_country', 'status',
            'location', 'quantity', 'unit',
            'inspection_required', 'last_inspection_date', 'next_inspection_date',
            'remarks'
        ]
    
    def update(self, instance, validated_data):
        # 수정자 설정
        validated_data['updated_by'] = self.context['request'].user
        
        # 변경 사항 추적
        previous_value = {}
        new_value = {}
        for field, value in validated_data.items():
            old_value = getattr(instance, field)
            if old_value != value:
                previous_value[field] = str(old_value) if old_value else None
                new_value[field] = str(value) if value else None
        
        item = super().update(instance, validated_data)
        
        # 이력 기록
        if previous_value:
            KSCertificationHistory.objects.create(
                item=item,
                action_type=KSCertificationHistory.ActionType.UPDATE,
                action_description=f'KS 인증 품목 정보 수정',
                previous_value=previous_value,
                new_value=new_value,
                created_by=self.context['request'].user
            )
        
        return item


class KSCertificationHistorySerializer(serializers.ModelSerializer):
    """KS 인증 이력 시리얼라이저"""
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    item_barcode = serializers.CharField(source='item.barcode', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    
    class Meta:
        model = KSCertificationHistory
        fields = '__all__'


class KSScanSerializer(serializers.Serializer):
    """KS 인증 품목 스캔 시리얼라이저"""
    barcode = serializers.CharField(max_length=50)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, default=1, required=False)
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate_barcode(self, value):
        """바코드 유효성 검증"""
        if not value.startswith('HP-KSTC-'):
            raise serializers.ValidationError('KS 인증 품목의 관리번호는 HP-KSTC-로 시작해야 합니다.')
        return value
