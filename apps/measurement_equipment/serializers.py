from rest_framework import serializers
from .models import MeasurementEquipment, MeasurementEquipmentHistory
from apps.accounts.serializers import UserSerializer


class MeasurementEquipmentListSerializer(serializers.ModelSerializer):
    """계측장비 목록 시리얼라이저"""
    is_calibration_due = serializers.BooleanField(read_only=True)
    is_calibration_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MeasurementEquipment
        fields = [
            'id', 'barcode', 'name', 'equipment_type', 'status',
            'manufacturer', 'location', 'responsible_person', 'department',
            'calibration_required', 'next_calibration_date',
            'is_calibration_due', 'is_calibration_overdue',
            'created_at', 'updated_at'
        ]


class MeasurementEquipmentDetailSerializer(serializers.ModelSerializer):
    """계측장비 상세 시리얼라이저"""
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    updated_by_detail = UserSerializer(source='updated_by', read_only=True)
    is_calibration_due = serializers.BooleanField(read_only=True)
    is_calibration_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MeasurementEquipment
        fields = '__all__'


class MeasurementEquipmentCreateSerializer(serializers.ModelSerializer):
    """계측장비 생성 시리얼라이저"""
    
    class Meta:
        model = MeasurementEquipment
        fields = [
            'barcode', 'name', 'equipment_type', 'model_number', 'serial_number',
            'manufacturer', 'specifications', 'measurement_range', 'accuracy',
            'status', 'location', 'responsible_person', 'department',
            'purchase_date', 'purchase_price', 'warranty_expiry',
            'calibration_required', 'last_calibration_date', 'next_calibration_date',
            'calibration_cycle_months', 'calibration_agency', 'remarks'
        ]
    
    def validate_barcode(self, value):
        """바코드 유효성 검증"""
        if not (value.startswith('HP-P10-') or value.startswith('HP-P20-')):
            raise serializers.ValidationError('계측장비의 관리번호는 HP-P10- 또는 HP-P20-으로 시작해야 합니다.')
        return value
    
    def create(self, validated_data):
        # 생성자 설정
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        
        equipment = super().create(validated_data)
        
        # 이력 기록
        MeasurementEquipmentHistory.objects.create(
            equipment=equipment,
            action_type=MeasurementEquipmentHistory.ActionType.REGISTER,
            action_description=f'계측장비 등록: {equipment.name}',
            new_value={'barcode': equipment.barcode, 'name': equipment.name},
            created_by=self.context['request'].user
        )
        
        return equipment


class MeasurementEquipmentUpdateSerializer(serializers.ModelSerializer):
    """계측장비 수정 시리얼라이저"""
    
    class Meta:
        model = MeasurementEquipment
        fields = [
            'name', 'equipment_type', 'model_number', 'serial_number',
            'manufacturer', 'specifications', 'measurement_range', 'accuracy',
            'status', 'location', 'responsible_person', 'department',
            'purchase_date', 'purchase_price', 'warranty_expiry',
            'calibration_required', 'last_calibration_date', 'next_calibration_date',
            'calibration_cycle_months', 'calibration_agency', 'remarks'
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
        
        equipment = super().update(instance, validated_data)
        
        # 이력 기록
        if previous_value:
            MeasurementEquipmentHistory.objects.create(
                equipment=equipment,
                action_type=MeasurementEquipmentHistory.ActionType.UPDATE,
                action_description=f'계측장비 정보 수정',
                previous_value=previous_value,
                new_value=new_value,
                created_by=self.context['request'].user
            )
        
        return equipment


class MeasurementEquipmentHistorySerializer(serializers.ModelSerializer):
    """계측장비 이력 시리얼라이저"""
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    equipment_barcode = serializers.CharField(source='equipment.barcode', read_only=True)
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    
    class Meta:
        model = MeasurementEquipmentHistory
        fields = '__all__'


class MeasurementScanSerializer(serializers.Serializer):
    """계측장비 스캔 시리얼라이저"""
    barcode = serializers.CharField(max_length=50)
    action = serializers.ChoiceField(choices=['use', 'return', 'scan'], default='scan')
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate_barcode(self, value):
        """바코드 유효성 검증"""
        if not (value.startswith('HP-P10-') or value.startswith('HP-P20-')):
            raise serializers.ValidationError('계측장비의 관리번호는 HP-P10- 또는 HP-P20-으로 시작해야 합니다.')
        return value
