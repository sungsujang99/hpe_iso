"""
ISO Document Management Models
HP-QP (Quality Procedure) / HP-EP (Engineering Procedure) 시리즈 문서 관리
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
import uuid


class DocumentCategory(models.Model):
    """문서 카테고리 (HP-QP, HP-EP 등)"""
    
    code = models.CharField(_('코드'), max_length=20, unique=True)  # HP-QP, HP-EP
    name = models.CharField(_('이름'), max_length=100)
    description = models.TextField(_('설명'), blank=True)
    prefix = models.CharField(_('문서번호 접두사'), max_length=20)  # HP-QP-
    next_number = models.IntegerField(_('다음 문서번호'), default=1000)
    is_active = models.BooleanField(_('활성화'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('문서 카테고리')
        verbose_name_plural = _('문서 카테고리')
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_next_document_number(self):
        """다음 문서번호 발급"""
        number = f"{self.prefix}{self.next_number}"
        self.next_number += 1
        self.save(update_fields=['next_number'])
        return number


class DocumentTemplate(models.Model):
    """문서 템플릿 (양식)"""
    
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name='templates',
        verbose_name=_('카테고리')
    )
    name = models.CharField(_('템플릿명'), max_length=200)
    description = models.TextField(_('설명'), blank=True)
    
    # 템플릿 필드 정의 (JSON)
    fields_schema = models.JSONField(
        _('필드 스키마'),
        default=dict,
        help_text='문서에 필요한 필드 정의 (JSON 형식)'
    )
    
    # 템플릿 파일 (선택적)
    template_file = models.FileField(
        _('템플릿 파일'),
        upload_to='document_templates/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['html', 'docx'])]
    )
    
    is_active = models.BooleanField(_('활성화'), default=True)
    version = models.CharField(_('버전'), max_length=20, default='1.0')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('문서 템플릿')
        verbose_name_plural = _('문서 템플릿')
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.category.code} - {self.name}"


class Document(models.Model):
    """ISO 문서"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('작성중')
        PENDING_REVIEW = 'pending_review', _('검토 대기')
        PENDING_APPROVAL = 'pending_approval', _('승인 대기')
        APPROVED = 'approved', _('승인 완료')
        REJECTED = 'rejected', _('반려')
        OBSOLETE = 'obsolete', _('폐기')
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_number = models.CharField(_('문서번호'), max_length=50, unique=True)
    
    # Classification
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name='documents',
        verbose_name=_('카테고리')
    )
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_('템플릿')
    )
    
    # Content
    title = models.CharField(_('제목'), max_length=300)
    revision = models.CharField(_('개정번호'), max_length=10, default='0')
    
    # 동적 필드 데이터 (템플릿 기반)
    content_data = models.JSONField(
        _('문서 내용'),
        default=dict,
        help_text='템플릿 필드에 대응하는 데이터'
    )
    
    # Workflow Status
    status = models.CharField(
        _('상태'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    
    # 데이터 무결성: 승인 완료된 문서는 수정 불가
    is_locked = models.BooleanField(_('잠금'), default=False)
    
    # Workflow Users
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_documents',
        verbose_name=_('작성자')
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_documents',
        verbose_name=_('검토자')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_documents',
        verbose_name=_('승인자')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('작성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)
    submitted_at = models.DateTimeField(_('제출일'), null=True, blank=True)
    reviewed_at = models.DateTimeField(_('검토일'), null=True, blank=True)
    approved_at = models.DateTimeField(_('승인일'), null=True, blank=True)
    
    # Generated Files
    pdf_file = models.FileField(
        _('PDF 파일'),
        upload_to='documents/pdf/%Y/%m/',
        blank=True,
        null=True,
    )
    
    class Meta:
        verbose_name = _('문서')
        verbose_name_plural = _('문서')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_by', 'status']),
        ]
    
    def __str__(self):
        return f"{self.document_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        # 승인된 문서는 수정 불가 (단, 승인 처리 시에는 예외)
        if self.pk:
            # DB에서 현재 문서 상태 가져오기
            try:
                old_doc = Document.objects.get(pk=self.pk)
                # 이미 잠긴 문서인 경우에만 체크
                if old_doc.is_locked:
                    update_fields = kwargs.get('update_fields')
                    if update_fields:
                        # 승인/검토 관련 필드와 상태 변경, PDF 생성만 허용
                        allowed_fields = {
                            'pdf_file', 'status', 'is_locked',
                            'approved_by', 'approved_at',
                            'reviewed_by', 'reviewed_at'
                        }
                        if not set(update_fields).issubset(allowed_fields):
                            raise ValueError('승인된 문서는 수정할 수 없습니다.')
                    else:
                        raise ValueError('승인된 문서는 수정할 수 없습니다.')
            except Document.DoesNotExist:
                pass  # 새 문서인 경우 체크하지 않음
        super().save(*args, **kwargs)
    
    @property
    def can_edit(self):
        """수정 가능 여부"""
        return self.status == self.Status.DRAFT and not self.is_locked
    
    @property
    def can_submit(self):
        """제출 가능 여부"""
        return self.status == self.Status.DRAFT
    
    @property
    def can_review(self):
        """검토 가능 여부"""
        return self.status == self.Status.PENDING_REVIEW
    
    @property
    def can_approve(self):
        """승인 가능 여부"""
        return self.status == self.Status.PENDING_APPROVAL


class DocumentComment(models.Model):
    """문서 코멘트 (검토/반려 사유 등)"""
    
    class CommentType(models.TextChoices):
        GENERAL = 'general', _('일반')
        REVIEW = 'review', _('검토')
        REJECTION = 'rejection', _('반려 사유')
        APPROVAL = 'approval', _('승인')
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('문서')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='document_comments',
        verbose_name=_('작성자')
    )
    comment_type = models.CharField(
        _('유형'),
        max_length=20,
        choices=CommentType.choices,
        default=CommentType.GENERAL,
    )
    content = models.TextField(_('내용'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('문서 코멘트')
        verbose_name_plural = _('문서 코멘트')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.document.document_number} - {self.user} ({self.comment_type})"


class DocumentHistory(models.Model):
    """문서 이력 (워크플로우 추적)"""
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('문서')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('사용자')
    )
    action = models.CharField(_('동작'), max_length=100)
    from_status = models.CharField(_('이전 상태'), max_length=30, blank=True)
    to_status = models.CharField(_('이후 상태'), max_length=30, blank=True)
    comment = models.TextField(_('비고'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP 주소'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('문서 이력')
        verbose_name_plural = _('문서 이력')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document.document_number} - {self.action} ({self.created_at})"


class DocumentAttachment(models.Model):
    """문서 첨부파일"""
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('문서')
    )
    file = models.FileField(_('파일'), upload_to='documents/attachments/%Y/%m/')
    filename = models.CharField(_('파일명'), max_length=255)
    file_size = models.IntegerField(_('파일 크기'), default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('업로더')
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('첨부파일')
        verbose_name_plural = _('첨부파일')
    
    def __str__(self):
        return self.filename
    
    def save(self, *args, **kwargs):
        if self.file:
            self.filename = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)
