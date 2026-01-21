"""
User Model and Authentication
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """부서 모델"""
    
    name = models.CharField(_('부서명'), max_length=100, unique=True)
    code = models.CharField(_('부서코드'), max_length=20, unique=True, blank=True, null=True)
    description = models.TextField(_('설명'), blank=True)
    is_active = models.BooleanField(_('활성화'), default=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)
    
    class Meta:
        verbose_name = _('부서')
        verbose_name_plural = _('부서')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.name[:20].upper().replace(' ', '_')
        super().save(*args, **kwargs)


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError(_('아이디는 필수입니다'))
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(username, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User Model for HPE System
    
    Roles:
    - admin: 최종 관리자 (대표이사급) - 최종 승인 권한
    - manager: 중간 관리자 (부서장급) - 검토 권한
    - user: 일반 사용자 - 작성 권한
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('관리자')
        MANAGER = 'manager', _('검토자')
        USER = 'user', _('사용자')
    
    # username 필드 사용 (AbstractUser 기본 제공)
    email = models.EmailField(_('이메일'), blank=True)
    
    # Profile Information
    employee_id = models.CharField(_('사번'), max_length=20, unique=True, blank=True, null=True)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name=_('부서')
    )
    position = models.CharField(_('직책'), max_length=100, blank=True)
    phone = models.CharField(_('연락처'), max_length=20, blank=True)
    is_department_head = models.BooleanField(_('부서장 여부'), default=False)
    
    # Role and Permissions
    role = models.CharField(
        _('역할'),
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )
    
    # Digital Signature (for document approval)
    signature_image = models.ImageField(
        _('서명 이미지'),
        upload_to='signatures/',
        blank=True,
        null=True,
    )
    
    # Status
    is_active = models.BooleanField(_('활성화'), default=True)
    last_login_ip = models.GenericIPAddressField(_('마지막 접속 IP'), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('사용자')
        verbose_name_plural = _('사용자들')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """성명 반환 (한국식: 성 + 이름)"""
        return f"{self.last_name}{self.first_name}".strip() or self.email
    
    def get_short_name(self):
        return self.first_name or self.email.split('@')[0]
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser
    
    @property
    def is_manager(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER]
    
    @property
    def can_approve(self):
        """최종 승인 권한 여부"""
        return self.role == self.Role.ADMIN
    
    @property
    def can_review(self):
        """검토 권한 여부"""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER]
    
    @property
    def display_role(self):
        """역할 표시명"""
        return dict(self.Role.choices).get(self.role, self.role)
    
    def save(self, *args, **kwargs):
        """사용자 저장 시 역할 자동 설정"""
        # 관리자는 역할 변경 불가
        if not self.is_admin and not self.is_superuser:
            # 부서장이면 중간관리자(manager), 아니면 일반 사용자(user)
            if self.is_department_head:
                self.role = self.Role.MANAGER
            else:
                self.role = self.Role.USER
        super().save(*args, **kwargs)


class LoginHistory(models.Model):
    """로그인 이력 (Audit Trail)"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history',
        verbose_name=_('사용자')
    )
    login_at = models.DateTimeField(_('로그인 시간'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP 주소'), blank=True, null=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    success = models.BooleanField(_('성공 여부'), default=True)
    failure_reason = models.CharField(_('실패 사유'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('로그인 이력')
        verbose_name_plural = _('로그인 이력')
        ordering = ['-login_at']
    
    def __str__(self):
        status = '성공' if self.success else '실패'
        return f"{self.user.email} - {self.login_at} ({status})"


class ActivityLog(models.Model):
    """사용자 활동 로그"""
    
    class ActionType(models.TextChoices):
        CREATE = 'create', _('생성')
        UPDATE = 'update', _('수정')
        DELETE = 'delete', _('삭제')
        VIEW = 'view', _('조회')
        APPROVE = 'approve', _('승인')
        REJECT = 'reject', _('반려')
        EXPORT = 'export', _('내보내기')
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs',
        verbose_name=_('사용자')
    )
    action = models.CharField(
        _('동작'),
        max_length=20,
        choices=ActionType.choices
    )
    model_name = models.CharField(_('모델명'), max_length=100)
    object_id = models.CharField(_('객체 ID'), max_length=100, blank=True)
    object_repr = models.TextField(_('객체 표현'), blank=True)
    changes = models.JSONField(_('변경 내용'), default=dict, blank=True)
    ip_address = models.GenericIPAddressField(_('IP 주소'), blank=True, null=True)
    created_at = models.DateTimeField(_('발생 시간'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('활동 로그')
        verbose_name_plural = _('활동 로그')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['model_name', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"
