"""
Document Background Tasks
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('hpe')


@shared_task
def send_pending_approval_reminders():
    """
    검토/승인 대기 중인 문서에 대해 리마인더 발송
    매일 아침 9시에 실행
    """
    from .models import Document
    from apps.accounts.models import User
    
    # 3일 이상 검토 대기 중인 문서
    pending_review_docs = Document.objects.filter(
        status='pending_review',
        submitted_at__lte=timezone.now() - timedelta(days=3)
    )
    
    if pending_review_docs.exists():
        reviewers = User.objects.filter(role__in=['admin', 'manager'], is_active=True)
        doc_list = '\n'.join([
            f"- {doc.document_number}: {doc.title} (작성자: {doc.created_by.get_full_name()})"
            for doc in pending_review_docs[:10]
        ])
        
        for reviewer in reviewers:
            try:
                send_mail(
                    subject='[HPE] 검토 대기 문서 알림',
                    message=f'''
안녕하세요, {reviewer.get_full_name()}님

다음 문서들이 3일 이상 검토 대기 중입니다:

{doc_list}

시스템에 로그인하여 검토해주세요.
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[reviewer.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f'Failed to send reminder to {reviewer.email}: {str(e)}')
    
    # 3일 이상 승인 대기 중인 문서
    pending_approval_docs = Document.objects.filter(
        status='pending_approval',
        reviewed_at__lte=timezone.now() - timedelta(days=3)
    )
    
    if pending_approval_docs.exists():
        admins = User.objects.filter(role='admin', is_active=True)
        doc_list = '\n'.join([
            f"- {doc.document_number}: {doc.title} (작성자: {doc.created_by.get_full_name()})"
            for doc in pending_approval_docs[:10]
        ])
        
        for admin in admins:
            try:
                send_mail(
                    subject='[HPE] 승인 대기 문서 알림',
                    message=f'''
안녕하세요, {admin.get_full_name()}님

다음 문서들이 3일 이상 승인 대기 중입니다:

{doc_list}

시스템에 로그인하여 승인해주세요.
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f'Failed to send reminder to {admin.email}: {str(e)}')
    
    logger.info(f'Sent reminders for {pending_review_docs.count()} review and {pending_approval_docs.count()} approval pending documents')


@shared_task
def generate_document_pdf_async(document_id):
    """비동기 PDF 생성"""
    from .models import Document
    from .services import PDFGenerator
    
    try:
        document = Document.objects.get(id=document_id)
        pdf_generator = PDFGenerator()
        pdf_file = pdf_generator.generate_document_pdf(document)
        document.pdf_file = pdf_file
        document.save(update_fields=['pdf_file'])
        logger.info(f'PDF generated for document {document.document_number}')
        return {'status': 'success', 'document_id': str(document_id)}
    except Document.DoesNotExist:
        logger.error(f'Document not found: {document_id}')
        return {'status': 'failed', 'error': 'Document not found'}
    except Exception as e:
        logger.error(f'PDF generation failed for {document_id}: {str(e)}')
        return {'status': 'failed', 'error': str(e)}
