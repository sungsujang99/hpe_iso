from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import connection, models
from django.utils import timezone


class DashboardView(APIView):
    """메인 대시보드 API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from apps.documents.models import Document
        from apps.inventory.models import InventoryItem, StockTransaction
        
        user = request.user
        
        # 문서 통계
        document_stats = {
            'total': Document.objects.count(),
            'pending_review': Document.objects.filter(status='pending_review').count(),
            'pending_approval': Document.objects.filter(status='pending_approval').count(),
            'approved_today': Document.objects.filter(
                status='approved',
                approved_at__date=timezone.now().date()
            ).count(),
        }
        
        # 사용자별 문서 (본인이 작성한 것)
        if user.role == 'user':
            document_stats['my_drafts'] = Document.objects.filter(
                created_by=user, status='draft'
            ).count()
            document_stats['my_pending'] = Document.objects.filter(
                created_by=user, status__in=['pending_review', 'pending_approval']
            ).count()
        
        # 재고 통계
        inventory_stats = {
            'total_items': InventoryItem.objects.count(),
            'low_stock_alerts': InventoryItem.objects.filter(
                current_quantity__lte=models.F('safety_stock')
            ).count() if hasattr(InventoryItem, 'safety_stock') else 0,
            'transactions_today': StockTransaction.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
        }
        
        return Response({
            'user': {
                'name': user.get_full_name(),
                'role': user.role,
                'department': user.department,
            },
            'documents': document_stats,
            'inventory': inventory_stats,
            'server_time': timezone.now(),
        })


class HealthCheckView(APIView):
    """시스템 상태 확인 API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Database connection check
        db_status = 'ok'
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return Response({
            'status': 'healthy' if db_status == 'ok' else 'unhealthy',
            'database': db_status,
            'timestamp': timezone.now(),
        })
