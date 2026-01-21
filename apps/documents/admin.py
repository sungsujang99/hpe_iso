"""
Document Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    DocumentCategory, DocumentTemplate, Document,
    DocumentComment, DocumentHistory, DocumentAttachment
)


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'prefix', 'next_number', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'version', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']


class DocumentCommentInline(admin.TabularInline):
    model = DocumentComment
    extra = 0
    readonly_fields = ['user', 'comment_type', 'content', 'created_at']


class DocumentHistoryInline(admin.TabularInline):
    model = DocumentHistory
    extra = 0
    readonly_fields = ['user', 'action', 'from_status', 'to_status', 'comment', 'created_at']


class DocumentAttachmentInline(admin.TabularInline):
    model = DocumentAttachment
    extra = 0
    readonly_fields = ['filename', 'file_size', 'uploaded_by', 'uploaded_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'document_number', 'title', 'category', 'status_badge',
        'created_by', 'created_at', 'is_locked'
    ]
    list_filter = ['status', 'category', 'is_locked', 'created_at']
    search_fields = ['document_number', 'title']
    readonly_fields = [
        'document_number', 'created_by', 'reviewed_by', 'approved_by',
        'created_at', 'submitted_at', 'reviewed_at', 'approved_at',
        'is_locked', 'pdf_file'
    ]
    
    inlines = [DocumentCommentInline, DocumentHistoryInline, DocumentAttachmentInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('document_number', 'category', 'template', 'title', 'revision')
        }),
        ('문서 내용', {
            'fields': ('content_data',),
            'classes': ('wide',)
        }),
        ('워크플로우', {
            'fields': (
                'status', 'is_locked',
                ('created_by', 'created_at'),
                ('reviewed_by', 'reviewed_at'),
                ('approved_by', 'approved_at'),
            )
        }),
        ('파일', {
            'fields': ('pdf_file',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'pending_review': '#ffc107',
            'pending_approval': '#17a2b8',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'obsolete': '#343a40',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '상태'


@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'comment_type', 'created_at']
    list_filter = ['comment_type', 'created_at']
    search_fields = ['document__document_number', 'content']


@admin.register(DocumentHistory)
class DocumentHistoryAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'action', 'from_status', 'to_status', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['document__document_number']
    readonly_fields = ['document', 'user', 'action', 'from_status', 'to_status', 'comment', 'ip_address', 'created_at']
