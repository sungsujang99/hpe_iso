"""
Inventory Background Tasks
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import F

logger = logging.getLogger('hpe')


@shared_task
def check_safety_stock_levels():
    """
    안전재고 미달 품목 확인 및 알림 생성
    매시간 실행
    """
    from .models import InventoryItem, StockAlert
    
    # 안전재고 미달 품목 조회
    low_stock_items = InventoryItem.objects.filter(
        current_quantity__lte=F('safety_stock'),
        current_quantity__gt=0,
        is_active=True
    )
    
    out_of_stock_items = InventoryItem.objects.filter(
        current_quantity__lte=0,
        is_active=True
    )
    
    created_alerts = 0
    
    # 안전재고 미달 알림 생성
    for item in low_stock_items:
        alert, created = StockAlert.objects.get_or_create(
            item=item,
            alert_type='low_stock',
            is_resolved=False,
            defaults={
                'message': f'{item.name}의 재고({item.current_quantity})가 안전재고({item.safety_stock}) 이하입니다.',
                'current_quantity': item.current_quantity,
                'threshold_quantity': item.safety_stock,
            }
        )
        if created:
            created_alerts += 1
    
    # 재고 소진 알림 생성
    for item in out_of_stock_items:
        alert, created = StockAlert.objects.get_or_create(
            item=item,
            alert_type='out_of_stock',
            is_resolved=False,
            defaults={
                'message': f'{item.name}의 재고가 소진되었습니다.',
                'current_quantity': item.current_quantity,
                'threshold_quantity': 0,
            }
        )
        if created:
            created_alerts += 1
    
    # 재고가 복구된 품목의 알림 해결
    from django.utils import timezone
    StockAlert.objects.filter(
        item__current_quantity__gt=F('item__safety_stock'),
        is_resolved=False
    ).update(is_resolved=True, resolved_at=timezone.now())
    
    logger.info(f'Safety stock check completed. Created {created_alerts} new alerts.')
    return {
        'low_stock_count': low_stock_items.count(),
        'out_of_stock_count': out_of_stock_items.count(),
        'new_alerts': created_alerts
    }


@shared_task
def send_daily_inventory_report():
    """
    일일 재고 현황 리포트 발송
    """
    from .models import InventoryItem, StockTransaction, StockAlert
    from apps.accounts.models import User
    from django.db.models import Sum, Count
    from datetime import date, timedelta
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # 통계 수집
    total_items = InventoryItem.objects.filter(is_active=True).count()
    low_stock_count = InventoryItem.objects.filter(
        current_quantity__lte=F('safety_stock'),
        is_active=True
    ).count()
    
    transactions_today = StockTransaction.objects.filter(
        created_at__date=today
    ).aggregate(
        count=Count('id'),
        in_count=Count('id', filter=models.Q(transaction_type='in')),
        out_count=Count('id', filter=models.Q(transaction_type='out')),
    )
    
    pending_alerts = StockAlert.objects.filter(is_resolved=False).count()
    
    # 이메일 내용 구성
    subject = f'[HPE 재고관리] 일일 현황 리포트 - {today}'
    message = f'''
안녕하세요,

{today} 재고 현황 리포트입니다.

===== 재고 현황 =====
총 품목 수: {total_items}개
안전재고 미달: {low_stock_count}개
미해결 알림: {pending_alerts}건

===== 오늘의 거래 =====
총 거래: {transactions_today['count']}건
입고: {transactions_today['in_count']}건
출고: {transactions_today['out_count']}건

자세한 내용은 시스템에서 확인해주세요.

HPE 재고관리 시스템
    '''
    
    # 관리자에게 발송
    recipients = User.objects.filter(
        role='admin',
        is_active=True
    ).values_list('email', flat=True)
    
    if recipients:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(recipients),
                fail_silently=True,
            )
            logger.info(f'Daily inventory report sent to {len(recipients)} recipients')
        except Exception as e:
            logger.error(f'Failed to send daily report: {str(e)}')
    
    return {'sent_to': list(recipients)}


@shared_task
def cleanup_resolved_alerts(days=30):
    """
    오래된 해결된 알림 정리
    """
    from .models import StockAlert
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    deleted_count, _ = StockAlert.objects.filter(
        is_resolved=True,
        resolved_at__lt=cutoff_date
    ).delete()
    
    logger.info(f'Cleaned up {deleted_count} old resolved alerts')
    return {'deleted_count': deleted_count}


from django.db import models
