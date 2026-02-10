import json
import os
from django.db import migrations


def seed_categories(apps, schema_editor):
    DocumentCategory = apps.get_model('documents', 'DocumentCategory')
    
    categories = [
        ('HP-QM', '품질경영 매뉴얼', 'HP-QM-'),
        ('HP-QP', '품질절차서', 'HP-QP-'),
        ('HP-QI', '품질경영 지침서', 'HP-QI-'),
        # HP-QR 삭제됨 - 모든 서식은 HP-QM에 통합
        ('HP-EM', '환경경영 매뉴얼', 'HP-EM-'),
        ('HP-EP', '기술절차서', 'HP-EP-'),
        ('HP-EI', '환경경영 지침서', 'HP-EI-'),
        ('HP-WI', '작업지시서', 'HP-WI-'),
    ]
    
    for code, name, prefix in categories:
        DocumentCategory.objects.get_or_create(
            code=code,
            defaults={'name': name, 'prefix': prefix}
        )


def seed_templates(apps, schema_editor):
    DocumentTemplate = apps.get_model('documents', 'DocumentTemplate')
    DocumentCategory = apps.get_model('documents', 'DocumentCategory')
    
    # 이미 템플릿이 있으면 스킵
    if DocumentTemplate.objects.exists():
        return
    
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'fixtures', 'templates.json'
    )
    
    if not os.path.exists(fixture_path):
        return
    
    with open(fixture_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # category code -> obj 매핑
    cat_map = {c.code: c for c in DocumentCategory.objects.all()}
    
    for item in data:
        category_code = item.get('category_code', '')
        category = cat_map.get(category_code)
        if not category:
            continue
        
        DocumentTemplate.objects.get_or_create(
            category=category,
            name=item['name'],
            defaults={
                'description': item.get('description', ''),
                'fields_schema': item.get('fields_schema', {}),
                'template_file': item.get('template_file', ''),
                'is_active': item.get('is_active', True),
                'version': item.get('version', '1.0'),
            }
        )


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_document_excel_file'),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_seed),
        migrations.RunPython(seed_templates, reverse_seed),
    ]
