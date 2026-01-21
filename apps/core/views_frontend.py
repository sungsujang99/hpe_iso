"""
Frontend Views - HTML Template Rendering
토큰 인증은 JavaScript에서 처리하므로 Django 세션 인증 불필요
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView


class LoginPageView(TemplateView):
    """로그인 페이지"""
    template_name = 'login.html'


class DashboardPageView(TemplateView):
    """대시보드 페이지"""
    template_name = 'dashboard.html'


class DocumentListPageView(TemplateView):
    """문서 목록 페이지"""
    template_name = 'documents/list.html'


class DocumentCreatePageView(TemplateView):
    """문서 작성 페이지"""
    template_name = 'documents/create.html'


class DocumentDetailPageView(TemplateView):
    """문서 상세 페이지"""
    template_name = 'documents/detail.html'


class DocumentPendingPageView(TemplateView):
    """승인 대기 문서 페이지"""
    template_name = 'documents/pending.html'


class InventoryListPageView(TemplateView):
    """재고 목록 페이지"""
    template_name = 'inventory/list.html'


class InventoryScanPageView(TemplateView):
    """바코드 스캔 페이지"""
    template_name = 'inventory/scan.html'


class InventoryInPageView(TemplateView):
    """입고 처리 페이지"""
    template_name = 'inventory/stock_in.html'


class InventoryOutPageView(TemplateView):
    """출고 처리 페이지"""
    template_name = 'inventory/stock_out.html'


class InventoryAlertsPageView(TemplateView):
    """재고 알림 페이지"""
    template_name = 'inventory/alerts.html'


class UserManagementPageView(TemplateView):
    """사용자 관리 페이지 (관리자 전용)"""
    template_name = 'users/list.html'


class DepartmentManagementPageView(TemplateView):
    """부서 관리 페이지 (관리자 전용)"""
    template_name = 'departments/list.html'


class ISO9001PageView(TemplateView):
    """ISO 9001 매뉴얼 및 관련 문서 페이지"""
    template_name = 'iso/9001.html'


class ISO14001PageView(TemplateView):
    """ISO 14001 매뉴얼 및 관련 문서 페이지"""
    template_name = 'iso/14001.html'
