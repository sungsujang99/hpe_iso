"""
Inventory Management Models
바코드 기반 재고관리 시스템
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
import uuid


class Warehouse(models.Model):
    """창고"""
    
    code = models.CharField(_('창고 코드'), max_length=20, unique=True)
    name = models.CharField(_('창고명'), max_length=100)
    address = models.TextField(_('주소'), blank=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_warehouses',
        verbose_name=_('담당자')
    )
    is_active = models.BooleanField(_('활성화'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('창고')
        verbose_name_plural = _('창고')
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Location(models.Model):
    """창고 내 위치 (구역)"""
    
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name=_('창고')
    )
    code = models.CharField(_('위치 코드'), max_length=30)
    name = models.CharField(_('위치명'), max_length=100)
    description = models.TextField(_('설명'), blank=True)
    barcode = models.CharField(_('바코드'), max_length=50, unique=True, blank=True, null=True)
    is_active = models.BooleanField(_('활성화'), default=True)
    
    class Meta:
        verbose_name = _('위치')
        verbose_name_plural = _('위치')
        ordering = ['warehouse', 'code']
        unique_together = ['warehouse', 'code']
    
    def __str__(self):
        return f"{self.warehouse.code}-{self.code}"
    
    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = f"LOC-{self.warehouse.code}-{self.code}"
        super().save(*args, **kwargs)


class ItemCategory(models.Model):
    """품목 카테고리"""
    
    code = models.CharField(_('카테고리 코드'), max_length=20, unique=True)
    name = models.CharField(_('카테고리명'), max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('상위 카테고리')
    )
    description = models.TextField(_('설명'), blank=True)
    is_active = models.BooleanField(_('활성화'), default=True)
    
    class Meta:
        verbose_name = _('품목 카테고리')
        verbose_name_plural = _('품목 카테고리')
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class InventoryItem(models.Model):
    """재고 품목"""
    
    class ItemType(models.TextChoices):
        MATERIAL = 'material', _('자재')
        PRODUCT = 'product', _('제품')
        CONSUMABLE = 'consumable', _('소모품')
        EQUIPMENT = 'equipment', _('장비')
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item_code = models.CharField(_('품목 코드'), max_length=50, unique=True)
    barcode = models.CharField(_('바코드'), max_length=100, unique=True, blank=True, null=True)
    
    # Basic Info
    name = models.CharField(_('품목명'), max_length=200)
    description = models.TextField(_('설명'), blank=True)
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
        verbose_name=_('카테고리')
    )
    item_type = models.CharField(
        _('품목 유형'),
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.MATERIAL,
    )
    
    # Specifications
    unit = models.CharField(_('단위'), max_length=20, default='EA')  # EA, KG, M, L, etc.
    specification = models.CharField(_('규격'), max_length=200, blank=True)
    manufacturer = models.CharField(_('제조사'), max_length=100, blank=True)
    supplier = models.CharField(_('공급업체'), max_length=100, blank=True)
    
    # Serial & Inspection
    serial_number = models.CharField(_('시리얼번호'), max_length=100, blank=True)
    inspection_required = models.BooleanField(_('점검여부'), default=False)
    inspection_due_date = models.DateField(_('점검예정일자'), null=True, blank=True)
    
    # Inventory
    current_quantity = models.DecimalField(
        _('현재 수량'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    safety_stock = models.DecimalField(
        _('안전재고'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Location
    default_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
        verbose_name=_('기본 위치')
    )
    
    # Pricing
    unit_price = models.DecimalField(
        _('단가'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Image
    image = models.ImageField(_('이미지'), upload_to='inventory/items/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(_('활성화'), default=True)
    
    # ISO Connection (HP-QP-710)
    iso_document = models.CharField(_('ISO 문서번호'), max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_items',
        verbose_name=_('등록자')
    )
    
    class Meta:
        verbose_name = _('재고 품목')
        verbose_name_plural = _('재고 품목')
        ordering = ['item_code']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['item_code']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.item_code} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = f"ITM-{self.item_code}"
        super().save(*args, **kwargs)
    
    @property
    def is_low_stock(self):
        """안전재고 미달 여부"""
        return self.current_quantity <= self.safety_stock
    
    @property
    def stock_status(self):
        """재고 상태"""
        if self.current_quantity <= 0:
            return 'out_of_stock'
        elif self.is_low_stock:
            return 'low_stock'
        return 'in_stock'


class StockTransaction(models.Model):
    """재고 입/출고 거래"""
    
    class TransactionType(models.TextChoices):
        IN = 'in', _('입고')
        OUT = 'out', _('출고')
        ADJUST = 'adjust', _('조정')
        TRANSFER = 'transfer', _('이동')
        RETURN = 'return', _('반품')
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_number = models.CharField(_('거래번호'), max_length=50, unique=True)
    
    # Transaction Info
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name=_('품목')
    )
    transaction_type = models.CharField(
        _('거래 유형'),
        max_length=20,
        choices=TransactionType.choices,
    )
    
    # Quantity
    quantity = models.DecimalField(
        _('수량'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    before_quantity = models.DecimalField(
        _('거래 전 수량'),
        max_digits=12,
        decimal_places=2,
    )
    after_quantity = models.DecimalField(
        _('거래 후 수량'),
        max_digits=12,
        decimal_places=2,
    )
    
    # Location
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('위치')
    )
    to_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfer_transactions',
        verbose_name=_('이동 위치')
    )
    
    # Reference
    reference_number = models.CharField(_('참조번호'), max_length=100, blank=True)  # PO번호, 출고요청번호 등
    remarks = models.TextField(_('비고'), blank=True)
    
    # User & Time
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='stock_transactions',
        verbose_name=_('담당자')
    )
    created_at = models.DateTimeField(_('거래일시'), auto_now_add=True)
    
    # Scan Info
    scanned_barcode = models.CharField(_('스캔된 바코드'), max_length=100, blank=True)
    scan_device = models.CharField(_('스캔 장치'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('재고 거래')
        verbose_name_plural = _('재고 거래')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_number']),
            models.Index(fields=['item', 'created_at']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_number} - {self.item.name} ({self.transaction_type})"
    
    def save(self, *args, **kwargs):
        if not self.transaction_number:
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.transaction_number = f"TRX-{timestamp}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)


class StockAlert(models.Model):
    """재고 알림"""
    
    class AlertType(models.TextChoices):
        LOW_STOCK = 'low_stock', _('안전재고 미달')
        OUT_OF_STOCK = 'out_of_stock', _('재고 소진')
        OVERSTOCK = 'overstock', _('과잉 재고')
    
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_('품목')
    )
    alert_type = models.CharField(
        _('알림 유형'),
        max_length=20,
        choices=AlertType.choices,
    )
    message = models.TextField(_('알림 메시지'))
    current_quantity = models.DecimalField(_('현재 수량'), max_digits=12, decimal_places=2)
    threshold_quantity = models.DecimalField(_('기준 수량'), max_digits=12, decimal_places=2)
    
    is_resolved = models.BooleanField(_('해결됨'), default=False)
    resolved_at = models.DateTimeField(_('해결일시'), null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        verbose_name=_('해결자')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('재고 알림')
        verbose_name_plural = _('재고 알림')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.item.name} - {self.get_alert_type_display()}"


class InventoryCount(models.Model):
    """재고 실사"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('작성중')
        IN_PROGRESS = 'in_progress', _('진행중')
        COMPLETED = 'completed', _('완료')
        CANCELLED = 'cancelled', _('취소')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    count_number = models.CharField(_('실사번호'), max_length=50, unique=True)
    
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='inventory_counts',
        verbose_name=_('창고')
    )
    
    status = models.CharField(
        _('상태'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    
    count_date = models.DateField(_('실사일'))
    remarks = models.TextField(_('비고'), blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_counts',
        verbose_name=_('생성자')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_counts',
        verbose_name=_('승인자')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(_('완료일시'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('재고 실사')
        verbose_name_plural = _('재고 실사')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.count_number} - {self.warehouse.name}"


class InventoryCountItem(models.Model):
    """재고 실사 품목"""
    
    inventory_count = models.ForeignKey(
        InventoryCount,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('실사')
    )
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        verbose_name=_('품목')
    )
    
    system_quantity = models.DecimalField(_('시스템 수량'), max_digits=12, decimal_places=2)
    counted_quantity = models.DecimalField(
        _('실사 수량'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    difference = models.DecimalField(
        _('차이'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    remarks = models.TextField(_('비고'), blank=True)
    
    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('실사자')
    )
    counted_at = models.DateTimeField(_('실사일시'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('실사 품목')
        verbose_name_plural = _('실사 품목')
        unique_together = ['inventory_count', 'item']
    
    def save(self, *args, **kwargs):
        if self.counted_quantity is not None:
            self.difference = self.counted_quantity - self.system_quantity
        super().save(*args, **kwargs)
