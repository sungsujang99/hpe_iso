#!/usr/bin/env python
"""
Initial Data Setup Script
Creates default categories, templates, and sample data for HPE System
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.documents.models import DocumentCategory, DocumentTemplate
from apps.inventory.models import Warehouse, Location, ItemCategory

User = get_user_model()


def create_users():
    """Create default users"""
    print("Creating users...")
    
    # Admin user
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': '관리자',
            'last_name': '시스템',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
            'department': '경영지원',
            'position': '대표이사',
        }
    )
    if created:
        admin.set_password('admin123!')
        admin.save()
        print(f"  Created admin: {admin.username}")
    
    # Manager user
    manager, created = User.objects.get_or_create(
        username='manager',
        defaults={
            'first_name': '검토자',
            'last_name': '부서장',
            'role': 'manager',
            'is_staff': True,
            'department': '품질관리',
            'position': '팀장',
        }
    )
    if created:
        manager.set_password('manager123!')
        manager.save()
        print(f"  Created manager: {manager.username}")
    
    # Regular user
    user, created = User.objects.get_or_create(
        username='user',
        defaults={
            'first_name': '홍길동',
            'last_name': '',
            'role': 'user',
            'is_staff': True,
            'department': '생산',
            'position': '사원',
        }
    )
    if created:
        user.set_password('user123!')
        user.save()
        print(f"  Created user: {user.username}")
    
    return admin, manager, user


def create_document_categories():
    """Create ISO document categories"""
    print("Creating document categories...")
    
    categories = [
        {
            'code': 'HP-QP',
            'name': '품질절차서',
            'description': 'Quality Procedure - ISO 9001 품질경영시스템 절차서',
            'prefix': 'HP-QP-',
            'next_number': 1001,
        },
        {
            'code': 'HP-EP',
            'name': '기술절차서',
            'description': 'Engineering Procedure - 기술 업무 절차서',
            'prefix': 'HP-EP-',
            'next_number': 1001,
        },
        # HP-QR 삭제됨 - 모든 서식은 HP-QM에 통합
        {
            'code': 'HP-WI',
            'name': '작업지시서',
            'description': 'Work Instruction - 상세 작업 지침',
            'prefix': 'HP-WI-',
            'next_number': 1001,
        },
    ]
    
    for cat_data in categories:
        cat, created = DocumentCategory.objects.get_or_create(
            code=cat_data['code'],
            defaults=cat_data
        )
        if created:
            print(f"  Created category: {cat.code}")


def create_document_templates():
    """Create document templates"""
    print("Creating document templates...")
    
    # Get categories
    try:
        qp_cat = DocumentCategory.objects.get(code='HP-QP')
        qm_cat = DocumentCategory.objects.get(code='HP-QM')
    except DocumentCategory.DoesNotExist:
        print("  Categories not found, skipping templates")
        return
    
    templates = [
        {
            'category': qm_cat,
            'name': '부적합보고서',
            'description': '품질 부적합 발생 시 작성하는 보고서',
            'fields_schema': {
                'fields': [
                    {'name': 'occurrence_date', 'label': '발생 일시', 'type': 'datetime', 'required': True},
                    {'name': 'location', 'label': '발생 장소', 'type': 'text', 'required': True},
                    {'name': 'nonconformity_content', 'label': '부적합 내용', 'type': 'textarea', 'required': True},
                    {'name': 'cause_analysis', 'label': '원인 분석', 'type': 'textarea', 'required': True},
                    {'name': 'corrective_action', 'label': '시정 조치 계획', 'type': 'textarea', 'required': True},
                    {'name': 'preventive_action', 'label': '예방 조치', 'type': 'textarea', 'required': False},
                    {'name': 'target_date', 'label': '목표 완료일', 'type': 'date', 'required': True},
                    {'name': 'remarks', 'label': '비고', 'type': 'textarea', 'required': False},
                ]
            },
        },
        {
            'category': qp_cat,
            'name': '자원관리절차서 (HP-QP-710)',
            'description': 'ISO 9001 7.1 자원관리 절차서',
            'fields_schema': {
                'fields': [
                    {'name': 'purpose', 'label': '목적', 'type': 'textarea', 'required': True},
                    {'name': 'scope', 'label': '적용범위', 'type': 'textarea', 'required': True},
                    {'name': 'responsibility', 'label': '책임과 권한', 'type': 'textarea', 'required': True},
                    {'name': 'procedure', 'label': '절차', 'type': 'textarea', 'required': True},
                    {'name': 'related_documents', 'label': '관련문서', 'type': 'textarea', 'required': False},
                    {'name': 'records', 'label': '기록', 'type': 'textarea', 'required': False},
                ]
            },
        },
        {
            'category': qm_cat,
            'name': '시정조치요청서',
            'description': '시정 조치 요청 및 이행 확인 기록',
            'fields_schema': {
                'fields': [
                    {'name': 'request_date', 'label': '요청일', 'type': 'date', 'required': True},
                    {'name': 'requester', 'label': '요청자', 'type': 'text', 'required': True},
                    {'name': 'department', 'label': '관련 부서', 'type': 'text', 'required': True},
                    {'name': 'issue_description', 'label': '문제 사항', 'type': 'textarea', 'required': True},
                    {'name': 'root_cause', 'label': '근본 원인', 'type': 'textarea', 'required': True},
                    {'name': 'corrective_action', 'label': '시정 조치', 'type': 'textarea', 'required': True},
                    {'name': 'verification', 'label': '이행 확인', 'type': 'textarea', 'required': False},
                    {'name': 'due_date', 'label': '완료 기한', 'type': 'date', 'required': True},
                ]
            },
        },
    ]
    
    for tmpl_data in templates:
        tmpl, created = DocumentTemplate.objects.get_or_create(
            category=tmpl_data['category'],
            name=tmpl_data['name'],
            defaults=tmpl_data
        )
        if created:
            print(f"  Created template: {tmpl.name}")


def create_warehouses():
    """Create warehouses and locations"""
    print("Creating warehouses...")
    
    warehouses = [
        {
            'code': 'WH-MAIN',
            'name': '본사 창고',
            'address': '서울시 강남구 테헤란로 123',
            'locations': [
                {'code': 'A-01', 'name': 'A구역 1열'},
                {'code': 'A-02', 'name': 'A구역 2열'},
                {'code': 'A-03', 'name': 'A구역 3열'},
                {'code': 'B-01', 'name': 'B구역 1열'},
                {'code': 'B-02', 'name': 'B구역 2열'},
                {'code': 'C-01', 'name': '불량품 구역'},
            ]
        },
        {
            'code': 'WH-PROD',
            'name': '생산 창고',
            'address': '서울시 강남구 테헤란로 125',
            'locations': [
                {'code': 'R-01', 'name': '원자재 구역'},
                {'code': 'F-01', 'name': '완제품 구역'},
                {'code': 'T-01', 'name': '임시 보관'},
            ]
        },
    ]
    
    for wh_data in warehouses:
        locations = wh_data.pop('locations')
        wh, created = Warehouse.objects.get_or_create(
            code=wh_data['code'],
            defaults=wh_data
        )
        if created:
            print(f"  Created warehouse: {wh.code}")
        
        for loc_data in locations:
            loc, loc_created = Location.objects.get_or_create(
                warehouse=wh,
                code=loc_data['code'],
                defaults={
                    'name': loc_data['name'],
                }
            )
            if loc_created:
                print(f"    Created location: {loc}")


def create_item_categories():
    """Create inventory item categories"""
    print("Creating item categories...")
    
    categories = [
        {'code': 'RAW', 'name': '원자재', 'description': '생산에 사용되는 원자재'},
        {'code': 'PART', 'name': '부품', 'description': '제품 조립용 부품'},
        {'code': 'CONS', 'name': '소모품', 'description': '사무용품 및 소모품'},
        {'code': 'EQUIP', 'name': '장비', 'description': '측정장비 및 공구'},
        {'code': 'PROD', 'name': '완제품', 'description': '완성된 제품'},
    ]
    
    for cat_data in categories:
        cat, created = ItemCategory.objects.get_or_create(
            code=cat_data['code'],
            defaults=cat_data
        )
        if created:
            print(f"  Created item category: {cat.code}")


def main():
    print("=" * 50)
    print("HPE System Initial Data Setup")
    print("=" * 50)
    print()
    
    create_users()
    print()
    
    create_document_categories()
    print()
    
    create_document_templates()
    print()
    
    create_warehouses()
    print()
    
    create_item_categories()
    print()
    
    print("=" * 50)
    print("Setup completed!")
    print()
    print("Default credentials:")
    print("  Admin: admin / admin123!")
    print("  Manager: manager / manager123!")
    print("  User: user / user123!")
    print("=" * 50)


if __name__ == '__main__':
    main()
