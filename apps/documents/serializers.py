"""
Document Serializers
"""
from rest_framework import serializers
from django.utils import timezone
from .models import (
    DocumentCategory, DocumentTemplate, Document,
    DocumentComment, DocumentHistory, DocumentAttachment
)


class DocumentCategorySerializer(serializers.ModelSerializer):
    """문서 카테고리 시리얼라이저"""
    
    class Meta:
        model = DocumentCategory
        fields = ['id', 'code', 'name', 'description', 'prefix', 'is_active']


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """문서 템플릿 시리얼라이저"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'category', 'category_name', 'name', 'description',
            'fields_schema', 'is_active', 'version', 'created_at'
        ]


class DocumentCommentSerializer(serializers.ModelSerializer):
    """문서 코멘트 시리얼라이저"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = DocumentComment
        fields = ['id', 'user', 'user_name', 'comment_type', 'content', 'created_at']
        read_only_fields = ['user']


class DocumentHistorySerializer(serializers.ModelSerializer):
    """문서 이력 시리얼라이저"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = DocumentHistory
        fields = [
            'id', 'user', 'user_name', 'action',
            'from_status', 'to_status', 'comment', 'created_at'
        ]


class DocumentAttachmentSerializer(serializers.ModelSerializer):
    """첨부파일 시리얼라이저"""
    
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = DocumentAttachment
        fields = ['id', 'file', 'filename', 'file_size', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']
        read_only_fields = ['filename', 'file_size', 'uploaded_by']


class DocumentListSerializer(serializers.ModelSerializer):
    """문서 목록 시리얼라이저"""
    
    category_code = serializers.CharField(source='category.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'document_number', 'category', 'category_code',
            'title', 'revision', 'status', 'status_display',
            'created_by', 'created_by_name', 'created_at',
            'is_locked', 'can_edit'
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):
    """문서 상세 시리얼라이저"""
    
    category_detail = DocumentCategorySerializer(source='category', read_only=True)
    template_detail = DocumentTemplateSerializer(source='template', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    comments = DocumentCommentSerializer(many=True, read_only=True)
    history = DocumentHistorySerializer(many=True, read_only=True)
    attachments = DocumentAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'document_number', 'category', 'category_detail',
            'template', 'template_detail', 'title', 'revision',
            'content_data', 'status', 'status_display', 'is_locked',
            'created_by', 'created_by_name',
            'reviewed_by', 'reviewed_by_name',
            'approved_by', 'approved_by_name',
            'created_at', 'updated_at', 'submitted_at',
            'reviewed_at', 'approved_at',
            'pdf_file', 'can_edit', 'can_submit', 'can_review', 'can_approve',
            'comments', 'history', 'attachments'
        ]


class DocumentCreateSerializer(serializers.ModelSerializer):
    """문서 생성 시리얼라이저 (문서번호, 제목 자동 생성)"""
    
    # title은 선택사항으로 변경 (없으면 자동 생성)
    title = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Document
        fields = ['id', 'category', 'template', 'title', 'content_data', 'document_number', 'status']
        read_only_fields = ['id', 'document_number', 'status']
    
    def create(self, validated_data):
        # 문서번호 자동 생성
        category = validated_data['category']
        validated_data['document_number'] = category.get_next_document_number()
        validated_data['created_by'] = self.context['request'].user
        
        # 제목이 없으면 카테고리 기반으로 자동 생성
        if not validated_data.get('title'):
            template = validated_data.get('template')
            if template:
                validated_data['title'] = f"{category.name} - {template.name}"
            else:
                validated_data['title'] = f"{category.name} 문서"
        
        return super().create(validated_data)


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """문서 수정 시리얼라이저 (내부 내용만 수정 가능)"""
    
    # title은 읽기 전용 (수정 불가)
    title = serializers.CharField(read_only=True)
    
    class Meta:
        model = Document
        fields = ['title', 'content_data']
    
    def validate(self, attrs):
        instance = self.instance
        if instance and not instance.can_edit:
            raise serializers.ValidationError('이 문서는 수정할 수 없습니다.')
        return attrs


class DocumentSubmitSerializer(serializers.Serializer):
    """문서 제출(승인 요청) 시리얼라이저"""
    
    comment = serializers.CharField(required=False, allow_blank=True)


class DocumentReviewSerializer(serializers.Serializer):
    """문서 검토 시리얼라이저"""
    
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    comment = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        if attrs['action'] == 'reject' and not attrs.get('comment'):
            raise serializers.ValidationError({'comment': '반려 시 사유를 입력해야 합니다.'})
        return attrs


class DocumentApprovalSerializer(serializers.Serializer):
    """문서 최종 승인 시리얼라이저"""
    
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    comment = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        if attrs['action'] == 'reject' and not attrs.get('comment'):
            raise serializers.ValidationError({'comment': '반려 시 사유를 입력해야 합니다.'})
        return attrs


class BulkDocumentStatusSerializer(serializers.Serializer):
    """문서 일괄 상태 변경 시리얼라이저"""
    
    document_ids = serializers.ListField(child=serializers.UUIDField())
    action = serializers.ChoiceField(choices=['submit', 'review_approve', 'review_reject', 'approve', 'reject'])
    comment = serializers.CharField(required=False, allow_blank=True)
