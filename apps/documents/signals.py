"""
Document Signals
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Document


@receiver(post_save, sender=Document)
def notify_on_status_change(sender, instance, created, **kwargs):
    """문서 상태 변경 시 알림"""
    if created:
        return
    
    # 검토 요청 시 검토자들에게 알림
    if instance.status == 'pending_review':
        # 검토 권한이 있는 사용자들에게 이메일 발송
        from apps.accounts.models import User
        reviewers = User.objects.filter(
            role__in=['admin', 'manager'],
            is_active=True
        )
        
        for reviewer in reviewers:
            try:
                send_mail(
                    subject=f'[HPE] 문서 검토 요청: {instance.document_number}',
                    message=f'''
새로운 문서 검토 요청이 있습니다.

문서번호: {instance.document_number}
제목: {instance.title}
작성자: {instance.created_by.get_full_name()}

시스템에 로그인하여 검토해주세요.
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[reviewer.email],
                    fail_silently=True,
                )
            except Exception:
                pass
    
    # 승인 요청 시 관리자에게 알림
    elif instance.status == 'pending_approval':
        from apps.accounts.models import User
        admins = User.objects.filter(role='admin', is_active=True)
        
        for admin in admins:
            try:
                send_mail(
                    subject=f'[HPE] 문서 승인 요청: {instance.document_number}',
                    message=f'''
문서 최종 승인 요청이 있습니다.

문서번호: {instance.document_number}
제목: {instance.title}
작성자: {instance.created_by.get_full_name()}
검토자: {instance.reviewed_by.get_full_name() if instance.reviewed_by else '-'}

시스템에 로그인하여 승인해주세요.
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin.email],
                    fail_silently=True,
                )
            except Exception:
                pass
    
    # 반려 시 작성자에게 알림
    elif instance.status == 'rejected':
        try:
            send_mail(
                subject=f'[HPE] 문서 반려: {instance.document_number}',
                message=f'''
문서가 반려되었습니다.

문서번호: {instance.document_number}
제목: {instance.title}

반려 사유를 확인하고 수정 후 다시 제출해주세요.
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.created_by.email],
                fail_silently=True,
            )
        except Exception:
            pass
    
    # 승인 완료 시 작성자에게 알림
    elif instance.status == 'approved':
        try:
            send_mail(
                subject=f'[HPE] 문서 승인 완료: {instance.document_number}',
                message=f'''
문서가 최종 승인되었습니다.

문서번호: {instance.document_number}
제목: {instance.title}
승인자: {instance.approved_by.get_full_name() if instance.approved_by else '-'}
승인일: {instance.approved_at.strftime('%Y-%m-%d %H:%M') if instance.approved_at else '-'}

PDF 문서가 생성되어 시스템에 보관됩니다.
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.created_by.email],
                fail_silently=True,
            )
        except Exception:
            pass
