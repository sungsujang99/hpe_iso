from django.db import models
from django.utils import timezone
import uuid


class MeasurementEquipment(models.Model):
    """계측장비 재고조사 관리대장"""
    
    class Status(models.TextChoices):
        IN_USE = 'in_use', '사용중'
        MAINTENANCE = 'maintenance', '정비중'
        CALIBRATION = 'calibration', '검정중'
        BROKEN = 'broken', '고장'
        DISCARDED = 'discarded', '폐기'
        STORED = 'stored', '보관중'
    
    class EquipmentType(models.TextChoices):
        PRESSURE = 'pressure', '압력계'
        TEMPERATURE = 'temperature', '온도계'
        FLOW = 'flow', '유량계'
        LEVEL = 'level', '레벨계'
        MULTIMETER = 'multimeter', '멀티미터'
        OSCILLOSCOPE = 'oscilloscope', '오실로스코프'
        CALIPER = 'caliper', '캘리퍼스'
        MICROMETER = 'micrometer', '마이크로미터'
        TORQUE_WRENCH = 'torque_wrench', '토크렌치'
        OTHER = 'other', '기타'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 기본 정보
    barcode = models.CharField('관리번호(바코드)', max_length=50, unique=True, db_index=True)
    name = models.CharField('장비명', max_length=200)
    equipment_type = models.CharField('장비유형', max_length=20, choices=EquipmentType.choices, default=EquipmentType.OTHER)
    
    # 제품 정보
    model_number = models.CharField('모델번호', max_length=100, blank=True)
    serial_number = models.CharField('시리얼번호', max_length=100, blank=True)
    manufacturer = models.CharField('제조사', max_length=100, blank=True)
    
    # 사양 정보
    specifications = models.TextField('사양', blank=True)  # 예: 1000kgf/cm2, 700BAR 등
    measurement_range = models.CharField('측정범위', max_length=100, blank=True)
    accuracy = models.CharField('정확도', max_length=50, blank=True)
    
    # 관리 정보
    status = models.CharField('상태', max_length=20, choices=Status.choices, default=Status.IN_USE)
    location = models.CharField('보관위치', max_length=200, blank=True)
    responsible_person = models.CharField('담당자', max_length=50, blank=True)
    department = models.CharField('사용부서', max_length=100, blank=True)
    
    # 구매 정보
    purchase_date = models.DateField('구매일', null=True, blank=True)
    purchase_price = models.DecimalField('구매가격', max_digits=12, decimal_places=2, null=True, blank=True)
    warranty_expiry = models.DateField('보증만료일', null=True, blank=True)
    
    # 검정/교정 정보
    calibration_required = models.BooleanField('검정필요', default=True)
    last_calibration_date = models.DateField('최근검정일', null=True, blank=True)
    next_calibration_date = models.DateField('다음검정일', null=True, blank=True)
    calibration_cycle_months = models.IntegerField('검정주기(개월)', default=12)
    calibration_agency = models.CharField('검정기관', max_length=100, blank=True)
    
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
        related_name='created_equipment',
        verbose_name='등록자'
    )
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_equipment',
        verbose_name='수정자'
    )
    
    class Meta:
        db_table = 'measurement_equipment'
        verbose_name = '계측장비'
        verbose_name_plural = '계측장비'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['status']),
            models.Index(fields=['equipment_type']),
            models.Index(fields=['next_calibration_date']),
        ]
    
    def __str__(self):
        return f"{self.barcode} - {self.name}"
    
    @property
    def is_calibration_due(self):
        """검정 기한 도래 여부"""
        if self.next_calibration_date:
            return self.next_calibration_date <= timezone.now().date()
        return False
    
    @property
    def is_calibration_overdue(self):
        """검정 기한 초과 여부"""
        if self.next_calibration_date:
            return self.next_calibration_date < timezone.now().date()
        return False


class MeasurementEquipmentHistory(models.Model):
    """계측장비 이력"""
    
    class ActionType(models.TextChoices):
        REGISTER = 'register', '등록'
        UPDATE = 'update', '수정'
        SCAN = 'scan', '스캔'
        USE = 'use', '사용'
        RETURN = 'return', '반납'
        CALIBRATION = 'calibration', '검정'
        REPAIR = 'repair', '수리'
        STATUS_CHANGE = 'status_change', '상태변경'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipment = models.ForeignKey(
        MeasurementEquipment,
        on_delete=models.CASCADE,
        related_name='histories',
        verbose_name='장비'
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
        db_table = 'measurement_equipment_histories'
        verbose_name = '계측장비 이력'
        verbose_name_plural = '계측장비 이력'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['equipment', '-created_at']),
            models.Index(fields=['action_type']),
        ]
    
    def __str__(self):
        return f"{self.equipment.barcode} - {self.action_type} - {self.created_at}"
