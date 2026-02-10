from django.db import migrations


def seed_categories(apps, schema_editor):
    DocumentCategory = apps.get_model('documents', 'DocumentCategory')
    
    categories = [
        ('HP-QM', '품질경영 매뉴얼'),
        ('HP-QP', '품질절차서'),
        ('HP-QI', '품질경영 지침서'),
        ('HP-QR', '품질기록'),
        ('HP-EM', '환경경영 매뉴얼'),
        ('HP-EP', '기술절차서'),
        ('HP-EI', '환경경영 지침서'),
        ('HP-WI', '작업지시서'),
    ]
    
    for code, name in categories:
        DocumentCategory.objects.get_or_create(
            code=code,
            defaults={'name': name}
        )


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_document_excel_file'),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_seed),
    ]
