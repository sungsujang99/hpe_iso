"""
Custom Permissions for HPE System
"""
from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """관리자(Admin) 역할만 허용"""
    
    message = '관리자 권한이 필요합니다.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin
        )


class IsManagerOrAdmin(BasePermission):
    """검토자(Manager) 또는 관리자(Admin) 역할만 허용"""
    
    message = '검토자 이상의 권한이 필요합니다.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_manager
        )


class IsOwnerOrAdmin(BasePermission):
    """본인 또는 관리자만 허용"""
    
    message = '본인 또는 관리자만 접근 가능합니다.'
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        
        # obj에 created_by 또는 user 필드가 있는 경우
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class CanApproveDocument(BasePermission):
    """문서 최종 승인 권한"""
    
    message = '문서 승인 권한이 없습니다.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_approve
        )


class CanReviewDocument(BasePermission):
    """문서 검토 권한"""
    
    message = '문서 검토 권한이 없습니다.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_review
        )


class ReadOnly(BasePermission):
    """읽기 전용 접근"""
    
    def has_permission(self, request, view):
        return request.method in ['GET', 'HEAD', 'OPTIONS']
