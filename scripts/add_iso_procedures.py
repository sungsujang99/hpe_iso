#!/usr/bin/env python
"""
Add ISO 9001 Quality Management System Procedures
Based on HP Engineering ISO 9001 Procedure Manual
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.documents.models import DocumentCategory, DocumentTemplate
from apps.accounts.models import Department


def ensure_departments():
    """부서가 없으면 기본 부서 생성"""
    print("Checking departments...")
    
    default_departments = [
        {'name': '경영지원', 'code': 'MGMT', 'description': '경영 지원 부서'},
        {'name': '품질관리', 'code': 'QA', 'description': '품질 관리 부서'},
        {'name': '생산', 'code': 'PROD', 'description': '생산 부서'},
        {'name': '기술', 'code': 'TECH', 'description': '기술 부서'},
    ]
    
    for dept_data in default_departments:
        dept, created = Department.objects.get_or_create(
            name=dept_data['name'],
            defaults=dept_data
        )
        if created:
            print(f"  Created department: {dept.name}")


def create_iso_procedure_templates():
    """ISO 9001 절차서 템플릿 생성"""
    print("Creating ISO 9001 procedure templates...")
    
    # Get or create HP-QP category
    qp_cat, created = DocumentCategory.objects.get_or_create(
        code='HP-QP',
        defaults={
            'name': '품질경영시스템 매뉴얼/절차서',
            'description': 'Quality Management System Manual/Procedure - ISO 9001 품질경영시스템 절차서',
            'prefix': 'HP-QP-',
            'next_number': 410,
        }
    )
    if created:
        print(f"  Created category: {qp_cat.code}")
    
    # Get or create HP-QM category (매뉴얼)
    qm_cat, created = DocumentCategory.objects.get_or_create(
        code='HP-QM',
        defaults={
            'name': '품질경영 매뉴얼',
            'description': 'Quality Manual - ISO 9001 품질경영 매뉴얼',
            'prefix': 'HP-QM-',
            'next_number': 1,
        }
    )
    if created:
        print(f"  Created category: {qm_cat.code}")
    
    # Get or create HP-QI category (지침서)
    qi_cat, created = DocumentCategory.objects.get_or_create(
        code='HP-QI',
        defaults={
            'name': '품질경영 지침서',
            'description': 'Quality Instruction - ISO 9001 품질경영 지침서',
            'prefix': 'HP-QI-',
            'next_number': 741,
        }
    )
    if created:
        print(f"  Created category: {qi_cat.code}")
    
    # ISO 절차서 표준 필드 스키마
    standard_procedure_fields = {
        'fields': [
            {'name': 'purpose', 'label': '1. 목적', 'type': 'textarea', 'required': True, 
             'placeholder': '이 절차서의 목적을 기술합니다.'},
            {'name': 'scope', 'label': '2. 적용범위', 'type': 'textarea', 'required': True,
             'placeholder': '이 절차가 적용되는 범위를 명시합니다.'},
            {'name': 'terms', 'label': '3. 용어의 정의', 'type': 'textarea', 'required': False,
             'placeholder': '절차서에서 사용되는 주요 용어를 정의합니다.'},
            {'name': 'responsibility', 'label': '4. 책임과 권한', 'type': 'textarea', 'required': True,
             'placeholder': '각 직책별 책임과 권한을 명시합니다.'},
            {'name': 'procedure', 'label': '5. 업무절차', 'type': 'textarea', 'required': True,
             'placeholder': '상세한 업무 수행 절차를 단계별로 기술합니다.'},
            {'name': 'related_documents', 'label': '6. 관련 문서', 'type': 'textarea', 'required': False,
             'placeholder': '관련된 다른 문서의 번호와 명칭을 나열합니다.'},
            {'name': 'records', 'label': '7. 기록', 'type': 'textarea', 'required': False,
             'placeholder': '이 절차에서 발생하는 기록물의 명칭과 보관방법을 명시합니다.'},
            {'name': 'attachments', 'label': '8. 첨부', 'type': 'textarea', 'required': False,
             'placeholder': '절차서에 첨부되는 양식이나 참고자료를 나열합니다.'},
        ]
    }
    
    # ISO 9001 절차서 목록 (PDF 기준)
    iso_procedures = [
        # 매뉴얼
        {'category': qm_cat, 'code': '01', 'name': '품질 경영 매뉴얼', 'doc_number': 'HP-QM-01'},
        
        # 절차서 (HP-QP)
        {'category': qp_cat, 'code': '410', 'name': '상황이해 및 품질경영시스템 운영 절차서', 'doc_number': 'HP-QP-410'},
        {'category': qp_cat, 'code': '510', 'name': '리더십 및 방침수립 절차서', 'doc_number': 'HP-QP-510'},
        {'category': qp_cat, 'code': '520', 'name': '조직 및 업무분장 절차서', 'doc_number': 'HP-QP-520'},
        {'category': qp_cat, 'code': '610', 'name': '품질 경영시스템 기획 및 리스크 관리 절차서', 'doc_number': 'HP-QP-610'},
        {'category': qp_cat, 'code': '710', 'name': '자원관리 절차서', 'doc_number': 'HP-QP-710'},
        {'category': qp_cat, 'code': '720', 'name': '설비관리 절차서', 'doc_number': 'HP-QP-720'},
        {'category': qp_cat, 'code': '730', 'name': '시험 및 측정장비 관리 절차서', 'doc_number': 'HP-QP-730'},
        {'category': qp_cat, 'code': '740', 'name': '교육 및 훈련 관리 절차서', 'doc_number': 'HP-QP-740'},
        {'category': qp_cat, 'code': '750', 'name': '인식 및 의사소통 절차서', 'doc_number': 'HP-QP-750'},
        {'category': qp_cat, 'code': '760', 'name': '문서화 정보관리 절차서', 'doc_number': 'HP-QP-760'},
        {'category': qp_cat, 'code': '810', 'name': '제품 및 서비스 요구사항 검토 절차서', 'doc_number': 'HP-QP-810'},
        {'category': qp_cat, 'code': '820', 'name': '설계 및 개발관리 절차서', 'doc_number': 'HP-QP-820'},
        {'category': qp_cat, 'code': '830', 'name': '구매관리 절차서', 'doc_number': 'HP-QP-830'},
        {'category': qp_cat, 'code': '840', 'name': '공급자관리 절차서', 'doc_number': 'HP-QP-840'},
        {'category': qp_cat, 'code': '850', 'name': '생산관리 절차서', 'doc_number': 'HP-QP-850'},
        {'category': qp_cat, 'code': '860', 'name': '검사 및 시험 절차서', 'doc_number': 'HP-QP-860'},
        {'category': qp_cat, 'code': '870', 'name': '부적합품 관리 절차서', 'doc_number': 'HP-QP-870'},
        {'category': qp_cat, 'code': '910', 'name': '프로세스 성과관리 절차서', 'doc_number': 'HP-QP-910'},
        {'category': qp_cat, 'code': '920', 'name': '고객만족관리 절차서', 'doc_number': 'HP-QP-920'},
        {'category': qp_cat, 'code': '930', 'name': '데이터 분석관리 절차서', 'doc_number': 'HP-QP-930'},
        {'category': qp_cat, 'code': '940', 'name': '내부심사 절차서', 'doc_number': 'HP-QP-940'},
        {'category': qp_cat, 'code': '950', 'name': '경영검토 절차서', 'doc_number': 'HP-QP-950'},
        {'category': qp_cat, 'code': '1010', 'name': '부적합 및 시정조치 절차서', 'doc_number': 'HP-QP-1010'},
        {'category': qp_cat, 'code': '1020', 'name': '지속적 개선 절차서', 'doc_number': 'HP-QP-1020'},
        
        # 지침서 (HP-QI)
        {'category': qi_cat, 'code': '741', 'name': '자격인증관리 지침서', 'doc_number': 'HP-QI-741'},
        {'category': qi_cat, 'code': '761', 'name': '문서작성 지침서', 'doc_number': 'HP-QI-761'},
        {'category': qi_cat, 'code': '851', 'name': '식별 및 추적성 관리 지침서', 'doc_number': 'HP-QI-851'},
        {'category': qi_cat, 'code': '852', 'name': '고객 및 외부공급자 자산관리 지침서', 'doc_number': 'HP-QI-852'},
        {'category': qi_cat, 'code': '853', 'name': '제품 보존관리 지침서', 'doc_number': 'HP-QI-853'},
        {'category': qi_cat, 'code': '854', 'name': '인도 후 활동 지침서', 'doc_number': 'HP-QI-854'},
    ]
    
    # 템플릿 생성
    for proc in iso_procedures:
        # 템플릿이 이미 존재하는지 확인 (문서번호로)
        existing = DocumentTemplate.objects.filter(
            name__contains=proc['doc_number']
        ).first()
        
        if existing:
            print(f"  Template already exists: {proc['doc_number']} - {proc['name']}")
            continue
        
        tmpl, created = DocumentTemplate.objects.get_or_create(
            category=proc['category'],
            name=f"{proc['name']} ({proc['doc_number']})",
            defaults={
                'description': f"ISO 9001:2015 품질경영시스템 - {proc['name']}",
                'fields_schema': standard_procedure_fields,
                'is_active': True,
                'version': '0',
            }
        )
        
        if created:
            print(f"  Created template: {proc['doc_number']} - {proc['name']}")


def main():
    print("=" * 80)
    print("ISO 9001 Quality Management System Procedures Setup")
    print("=" * 80)
    print()
    
    ensure_departments()
    print()
    
    create_iso_procedure_templates()
    print()
    
    print("=" * 80)
    print("ISO 9001 procedures setup completed!")
    print()
    print("Total templates created:")
    print(f"  - HP-QM (매뉴얼): {DocumentTemplate.objects.filter(category__code='HP-QM').count()}")
    print(f"  - HP-QP (절차서): {DocumentTemplate.objects.filter(category__code='HP-QP').count()}")
    print(f"  - HP-QI (지침서): {DocumentTemplate.objects.filter(category__code='HP-QI').count()}")
    print("=" * 80)


if __name__ == '__main__':
    main()
