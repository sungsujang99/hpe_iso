"""
엑셀 기반 문서 관리 Serializers
"""
from rest_framework import serializers
from .models import ExcelMasterDocument, ExcelUpdateLog


class ExcelMasterDocumentSerializer(serializers.ModelSerializer):
    """엑셀 마스터 문서 Serializer"""
    doc_type_display = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ExcelMasterDocument
        fields = [
            'id', 'title', 'doc_type', 'doc_type_display',
            'file_path', 'file_name', 'extra_columns', 'total_items',
            'last_updated', 'created_at'
        ]
        read_only_fields = ['id', 'total_items', 'last_updated', 'created_at']
    
    def get_doc_type_display(self, obj):
        return obj.get_doc_type_display()
    
    def get_file_name(self, obj):
        import os
        return os.path.basename(obj.file_path)


class ExcelUpdateLogSerializer(serializers.ModelSerializer):
    """엑셀 업데이트 로그 Serializer"""
    document_title = serializers.CharField(source='document.title', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ExcelUpdateLog
        fields = [
            'id', 'document', 'document_title', 'barcode', 'action',
            'updates', 'previous_values', 'created_at', 'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'created_at']


class BarcodeScanSerializer(serializers.Serializer):
    """바코드 스캔 Serializer"""
    barcode = serializers.CharField(required=True, max_length=100)
    action = serializers.ChoiceField(
        choices=['scan', 'stock_in', 'stock_out'],
        default='scan'
    )
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        required=False, default=1,
        min_value=0
    )
    remarks = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_barcode(self, value):
        """바코드 형식 검증"""
        value = value.strip().upper()
        
        # 지원하는 바코드 패턴
        supported_patterns = ['HP-KSTC-', 'HP-P10-', 'HP-P20-', 'HP-PRT-', 'HP-SUP-']
        
        if not any(value.startswith(pattern) for pattern in supported_patterns):
            raise serializers.ValidationError(
                f'지원하지 않는 바코드 형식입니다. ({", ".join(supported_patterns)})'
            )
        
        return value
    
    def validate_quantity(self, value):
        """수량 검증"""
        if value <= 0:
            raise serializers.ValidationError('수량은 0보다 커야 합니다.')
        return value
