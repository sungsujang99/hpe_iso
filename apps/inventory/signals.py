"""
Inventory Signals
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import StockAlert, InventoryItem


@receiver(post_save, sender=StockAlert)
def notify_low_stock_alert(sender, instance, created, **kwargs):
    """안전재고 알림 발생 시 관리자에게 이메일 발송"""
    if not created or instance.alert_type not in ['low_stock', 'out_of_stock']:
        return
    
    if not getattr(settings, 'SAFETY_STOCK_ALERT_ENABLED', True):
        return
    
    from django.core.mail import send_mail
    from apps.accounts.models import User
    
    # 관리자 및 매니저에게 알림
    recipients = User.objects.filter(
        role__in=['admin', 'manager'],
        is_active=True
    ).values_list('email', flat=True)
    
    if not recipients:
        return
    
    subject = f'[HPE 재고관리] {instance.get_alert_type_display()} 알림'
    message = f'''
재고 알림이 발생했습니다.

품목코드: {instance.item.item_code}
품목명: {instance.item.name}
알림유형: {instance.get_alert_type_display()}
현재수량: {instance.current_quantity} {instance.item.unit}
안전재고: {instance.threshold_quantity} {instance.item.unit}

시스템에서 확인해주세요.
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(recipients),
            fail_silently=True,
        )
    except Exception:
        pass
