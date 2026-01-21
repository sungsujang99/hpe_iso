from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
    verbose_name = 'ISO 문서관리'
    
    def ready(self):
        import apps.documents.signals  # noqa
