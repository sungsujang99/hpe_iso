from django.db import models
from django.utils import timezone
import uuid


class KSCertificationItem(models.Model):
    """KS 인증 사내문서 관리대장 품목"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', '사용중'
        EXPIRED = 'expired', '만료'
        SUSPENDED = 'suspended', '중지'
        DISCARDED = 'discarded', '폐기'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 기본 정보
    barcode = models.CharField('관리번호(바코드)', max_length=50, unique=True, db_index=True)
    name = models.TextField('한국산업표준명')
    serial_number = models.CharField('시리얼번호', max_length=100, blank=True)
    
    # KS 인증 정보
    ks_standard_number = models.CharField('KS 규격번호', max_length=50, blank=True)
    certification_date = models.DateField('인증일자', null=True, blank=True)
    expiry_date = models.DateField('만료일자', null=True, blank=True)
    certification_body = models.CharField('인증기관', max_length=100, blank=True, default='한국표준협회')
    
    # 제조사 정보
    manufacturer = models.CharField('제조사', max_length=200, blank=True)
    manufacturer_country = models.CharField('제조국', max_length=50, blank=True)
    
    # 관리 정보
    status = models.CharField('상태', max_length=20, choices=Status.choices, default=Status.ACTIVE)
    location = models.CharField('보관위치', max_length=200, blank=True)
    quantity = models.DecimalField('수량', max_digits=10, decimal_places=2, default=0)
    unit = models.CharField('단위', max_length=20, default='EA')
    
    # 점검 정보
    inspection_required = models.BooleanField('점검필요', default=False)
    last_inspection_date = models.DateField('최근점검일', null=True, blank=True)
    next_inspection_date = models.DateField('다음점검일', null=True, blank=True)
    
    # 비고
    remarks = models.TextField('비고', blank=True)
    
    # 메타 정보
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_ks_items',
        verbose_name='등록자'
    )
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_ks_items',
        verbose_name='수정자'
    )
    
    class Meta:
        db_table = 'ks_certification_items'
        verbose_name = 'KS 인증 품목'
        verbose_name_plural = 'KS 인증 품목'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['status']),
            models.Index(fields=['certification_date']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.barcode} - {self.name}"
    
    @property
    def is_expired(self):
        """인증 만료 여부"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False
    
    @property
    def is_inspection_due(self):
        """점검 기한 도래 여부"""
        if self.next_inspection_date:
            return self.next_inspection_date <= timezone.now().date()
        return False


class KSCertificationHistory(models.Model):
    """KS 인증 품목 이력"""
    
    class ActionType(models.TextChoices):
        REGISTER = 'register', '등록'
        UPDATE = 'update', '수정'
        SCAN = 'scan', '스캔'
        INSPECTION = 'inspection', '점검'
        STATUS_CHANGE = 'status_change', '상태변경'
        QUANTITY_CHANGE = 'quantity_change', '수량변경'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        KSCertificationItem,
        on_delete=models.CASCADE,
        related_name='histories',
        verbose_name='품목'
    )
    action_type = models.CharField('작업유형', max_length=20, choices=ActionType.choices)
    action_description = models.TextField('작업내용')
    previous_value = models.JSONField('이전값', null=True, blank=True)
    new_value = models.JSONField('새값', null=True, blank=True)
    
    created_at = models.DateTimeField('작업일시', auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='작업자'
    )
    
    class Meta:
        db_table = 'ks_certification_histories'
        verbose_name = 'KS 인증 이력'
        verbose_name_plural = 'KS 인증 이력'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['item', '-created_at']),
            models.Index(fields=['action_type']),
        ]
    
    def __str__(self):
        return f"{self.item.barcode} - {self.action_type} - {self.created_at}"
