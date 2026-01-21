"""
Account Admin Configuration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, LoginHistory, ActivityLog, Department


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'department', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'department', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'employee_id']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('개인정보'), {'fields': ('first_name', 'last_name', 'employee_id', 'phone')}),
        (_('소속정보'), {'fields': ('department', 'position')}),
        (_('권한'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('서명'), {'fields': ('signature_image',)}),
        (_('접속정보'), {'fields': ('last_login', 'last_login_ip')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_at', 'ip_address', 'success']
    list_filter = ['success', 'login_at']
    search_fields = ['user__email', 'ip_address']
    ordering = ['-login_at']
    readonly_fields = ['user', 'login_at', 'ip_address', 'user_agent', 'success', 'failure_reason']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    search_fields = ['user__email', 'object_repr']
    ordering = ['-created_at']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr', 'changes', 'ip_address', 'created_at']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'member_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['name']
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = '소속 인원'
