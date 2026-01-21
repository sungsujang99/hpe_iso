"""
Core Background Tasks
"""
import os
import subprocess
import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings

logger = logging.getLogger('hpe')


@shared_task
def daily_backup():
    """
    매일 자동 백업 수행
    - PostgreSQL 데이터베이스 덤프
    - 미디어 파일 백업
    - 오래된 백업 파일 정리
    """
    if not settings.BACKUP_ENABLED:
        logger.info('Backup is disabled in settings')
        return
    
    backup_path = getattr(settings, 'BACKUP_PATH', '/backup')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # Create backup directory
        backup_dir = os.path.join(backup_path, timestamp)
        os.makedirs(backup_dir, exist_ok=True)
        
        # Database backup
        db_settings = settings.DATABASES['default']
        if db_settings['ENGINE'] == 'django.db.backends.postgresql':
            db_backup_file = os.path.join(backup_dir, 'database.sql')
            
            env = os.environ.copy()
            env['PGPASSWORD'] = db_settings.get('PASSWORD', '')
            
            cmd = [
                'pg_dump',
                '-h', db_settings.get('HOST', 'localhost'),
                '-p', str(db_settings.get('PORT', '5432')),
                '-U', db_settings.get('USER', 'postgres'),
                '-d', db_settings.get('NAME', 'hpe_db'),
                '-f', db_backup_file,
            ]
            
            subprocess.run(cmd, env=env, check=True)
            logger.info(f'Database backup completed: {db_backup_file}')
        
        # Media files backup
        media_backup_file = os.path.join(backup_dir, 'media.tar.gz')
        media_path = str(settings.MEDIA_ROOT)
        
        if os.path.exists(media_path):
            subprocess.run([
                'tar', '-czf', media_backup_file, '-C', 
                os.path.dirname(media_path), 
                os.path.basename(media_path)
            ], check=True)
            logger.info(f'Media backup completed: {media_backup_file}')
        
        # Clean up old backups
        cleanup_old_backups(backup_path, settings.BACKUP_RETENTION_DAYS)
        
        logger.info(f'Daily backup completed successfully: {backup_dir}')
        return {'status': 'success', 'backup_dir': backup_dir}
        
    except Exception as e:
        logger.error(f'Backup failed: {str(e)}')
        return {'status': 'failed', 'error': str(e)}


def cleanup_old_backups(backup_path, retention_days):
    """오래된 백업 파일 정리"""
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    for item in os.listdir(backup_path):
        item_path = os.path.join(backup_path, item)
        if os.path.isdir(item_path):
            try:
                # Parse directory name as timestamp
                dir_date = datetime.strptime(item[:8], '%Y%m%d')
                if dir_date < cutoff_date:
                    subprocess.run(['rm', '-rf', item_path], check=True)
                    logger.info(f'Removed old backup: {item_path}')
            except ValueError:
                continue


@shared_task
def send_email_notification(to_email, subject, message, html_message=None):
    """이메일 알림 발송"""
    from django.core.mail import send_mail
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Email sent to {to_email}: {subject}')
        return {'status': 'sent', 'to': to_email}
    except Exception as e:
        logger.error(f'Failed to send email to {to_email}: {str(e)}')
        return {'status': 'failed', 'error': str(e)}
