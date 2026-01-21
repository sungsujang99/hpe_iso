#!/usr/bin/env python
"""
Add ISO 14001 Environmental Management System Procedures
ISO 14001 환경경영시스템 절차서 및 매뉴얼 추가
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.documents.models import DocumentCategory, DocumentTemplate


def create_iso14001_categories():
    """ISO 14001 카테고리 생성"""
    print("=" * 80)
    print("Creating ISO 14001 Categories")
    print("=" * 80)
    print()
    
    categories = [
        {
            'code': 'HP-EM',
            'name': '환경경영 매뉴얼',
            'description': 'Environmental Management Manual - ISO 14001 환경경영 매뉴얼',
            'prefix': 'HP-EM-',
            'next_number': 1,
        },
        {
            'code': 'HP-EP',
            'name': '환경경영 절차서',
            'description': 'Environmental Procedure - ISO 14001 환경경영시스템 절차서',
            'prefix': 'HP-EP-',
            'next_number': 410,
        },
        {
            'code': 'HP-EI',
            'name': '환경경영 지침서',
            'description': 'Environmental Instruction - ISO 14001 환경경영 지침서',
            'prefix': 'HP-EI-',
            'next_number': 741,
        },
    ]
    
    for cat_data in categories:
        cat, created = DocumentCategory.objects.get_or_create(
            code=cat_data['code'],
            defaults=cat_data
        )
        if created:
            print(f"  ✓ Created category: {cat.code} - {cat.name}")
        else:
            print(f"  ✓ Category already exists: {cat.code}")


def create_iso14001_procedure_templates():
    """ISO 14001 환경경영 절차서 템플릿 생성"""
    print()
    print("=" * 80)
    print("Creating ISO 14001 Procedure Templates")
    print("=" * 80)
    print()
    
    # Get categories
    ep_cat = DocumentCategory.objects.get(code='HP-EP')
    ei_cat = DocumentCategory.objects.get(code='HP-EI')
    
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
    
    # ISO 14001 환경경영 절차서 목록
    iso14001_procedures = [
        # 절차서 (HP-EP)
        {'category': ep_cat, 'code': '410', 'name': '상황이해 및 환경경영시스템 운영 절차서', 'doc_number': 'HP-EP-410', 'section': '4.0'},
        {'category': ep_cat, 'code': '510', 'name': '리더십 및 환경방침수립 절차서', 'doc_number': 'HP-EP-510', 'section': '5.0'},
        {'category': ep_cat, 'code': '520', 'name': '조직 및 업무분장 절차서', 'doc_number': 'HP-EP-520', 'section': '5.0'},
        {'category': ep_cat, 'code': '610', 'name': '환경경영시스템 기획 및 리스크 관리 절차서', 'doc_number': 'HP-EP-610', 'section': '6.0'},
        {'category': ep_cat, 'code': '710', 'name': '자원관리 절차서', 'doc_number': 'HP-EP-710', 'section': '7.0'},
        {'category': ep_cat, 'code': '720', 'name': '설비관리 절차서', 'doc_number': 'HP-EP-720', 'section': '7.0'},
        {'category': ep_cat, 'code': '730', 'name': '환경 측정장비 관리 절차서', 'doc_number': 'HP-EP-730', 'section': '7.0'},
        {'category': ep_cat, 'code': '740', 'name': '환경교육 및 훈련 관리 절차서', 'doc_number': 'HP-EP-740', 'section': '7.0'},
        {'category': ep_cat, 'code': '750', 'name': '환경인식 및 의사소통 절차서', 'doc_number': 'HP-EP-750', 'section': '7.0'},
        {'category': ep_cat, 'code': '760', 'name': '문서화 정보관리 절차서', 'doc_number': 'HP-EP-760', 'section': '7.0'},
        {'category': ep_cat, 'code': '810', 'name': '환경영향평가 절차서', 'doc_number': 'HP-EP-810', 'section': '8.0'},
        {'category': ep_cat, 'code': '820', 'name': '환경목표 수립 및 관리 절차서', 'doc_number': 'HP-EP-820', 'section': '8.0'},
        {'category': ep_cat, 'code': '830', 'name': '환경법규 준수 평가 절차서', 'doc_number': 'HP-EP-830', 'section': '8.0'},
        {'category': ep_cat, 'code': '840', 'name': '비상사태 대응 절차서', 'doc_number': 'HP-EP-840', 'section': '8.0'},
        {'category': ep_cat, 'code': '850', 'name': '폐기물관리 절차서', 'doc_number': 'HP-EP-850', 'section': '8.0'},
        {'category': ep_cat, 'code': '860', 'name': '에너지 관리 절차서', 'doc_number': 'HP-EP-860', 'section': '8.0'},
        {'category': ep_cat, 'code': '870', 'name': '환경오염 방지 절차서', 'doc_number': 'HP-EP-870', 'section': '8.0'},
        {'category': ep_cat, 'code': '910', 'name': '프로세스 성과관리 절차서', 'doc_number': 'HP-EP-910', 'section': '9.0'},
        {'category': ep_cat, 'code': '920', 'name': '환경점검 및 측정관리 절차서', 'doc_number': 'HP-EP-920', 'section': '9.0'},
        {'category': ep_cat, 'code': '930', 'name': '데이터 분석관리 절차서', 'doc_number': 'HP-EP-930', 'section': '9.0'},
        {'category': ep_cat, 'code': '940', 'name': '내부심사 절차서', 'doc_number': 'HP-EP-940', 'section': '9.0'},
        {'category': ep_cat, 'code': '950', 'name': '경영검토 절차서', 'doc_number': 'HP-EP-950', 'section': '9.0'},
        {'category': ep_cat, 'code': '1010', 'name': '부적합 및 시정조치 절차서', 'doc_number': 'HP-EP-1010', 'section': '10.0'},
        {'category': ep_cat, 'code': '1020', 'name': '지속적 개선 절차서', 'doc_number': 'HP-EP-1020', 'section': '10.0'},
        
        # 지침서 (HP-EI)
        {'category': ei_cat, 'code': '741', 'name': '환경자격인증관리 지침서', 'doc_number': 'HP-EI-741', 'section': '7.0'},
        {'category': ei_cat, 'code': '761', 'name': '문서작성 지침서', 'doc_number': 'HP-EI-761', 'section': '7.0'},
        {'category': ei_cat, 'code': '851', 'name': '환경측면 식별 및 평가 지침서', 'doc_number': 'HP-EI-851', 'section': '8.0'},
        {'category': ei_cat, 'code': '852', 'name': '오염물질 배출관리 지침서', 'doc_number': 'HP-EI-852', 'section': '8.0'},
    ]
    
    # 템플릿 생성
    created_count = 0
    for proc in iso14001_procedures:
        existing = DocumentTemplate.objects.filter(
            name__contains=proc['doc_number']
        ).first()
        
        if existing:
            print(f"  ○ Template already exists: {proc['doc_number']} - {proc['name']}")
            continue
        
        tmpl, created = DocumentTemplate.objects.get_or_create(
            category=proc['category'],
            name=f"{proc['name']} ({proc['doc_number']})",
            defaults={
                'description': f"ISO 14001:2015 환경경영시스템 - {proc['name']}\n매뉴얼 섹션: {proc['section']}",
                'fields_schema': standard_procedure_fields,
                'is_active': True,
                'version': '0',
            }
        )
        
        if created:
            print(f"  ✓ Created template: {proc['doc_number']} - {proc['name']}")
            created_count += 1
    
    return created_count


def create_iso14001_manual_template():
    """ISO 14001 환경경영 매뉴얼 템플릿 생성"""
    print()
    print("=" * 80)
    print("Creating ISO 14001 Environmental Manual Template")
    print("=" * 80)
    print()
    
    # HP-EM 카테고리 가져오기
    em_cat = DocumentCategory.objects.get(code='HP-EM')
    
    # 매뉴얼 템플릿 필드 스키마
    manual_fields_schema = {
        'fields': [
            # 0.3 환경경영 방침
            {
                'name': 'environmental_policy',
                'label': '0.3 환경경영 방침',
                'type': 'textarea',
                'required': True,
                'placeholder': '회사의 환경 방침을 기술합니다.',
                'default': '지속적 개선을 통한 고객만족 실현'
            },
            {
                'name': 'environmental_objectives',
                'label': '환경 목표',
                'type': 'textarea',
                'required': True,
                'placeholder': '환경 목표를 기술합니다 (각 줄마다 하나씩)',
                'default': '1. 오염방지의 지속적 노력\n2. 환경법규의 준수\n3. 지구환경 보전을 위한 지속적 실행'
            },
            
            # 1.0 적용범위
            {
                'name': 'scope',
                'label': '1.0 적용범위',
                'type': 'textarea',
                'required': True,
                'placeholder': '환경경영시스템의 적용범위를 기술합니다.'
            },
            
            # 2.0 인용 표준
            {
                'name': 'reference_standards',
                'label': '2.0 인용 표준',
                'type': 'textarea',
                'required': False,
                'placeholder': '참조하는 표준 문서를 기술합니다.',
                'default': 'ISO 14001:2015\nKS Q ISO 14001:2015'
            },
            
            # 3.0 용어의 정의
            {
                'name': 'terms_definitions',
                'label': '3.0 용어의 정의',
                'type': 'textarea',
                'required': False,
                'placeholder': '매뉴얼에서 사용되는 주요 용어를 정의합니다.'
            },
            
            # 4.0 조직의 상황
            {
                'name': 'organizational_context',
                'label': '4.0 조직의 상황',
                'type': 'textarea',
                'required': True,
                'placeholder': '조직의 내외부 상황을 기술합니다.\n참조: HP-EP-410'
            },
            
            # 5.0 리더십
            {
                'name': 'leadership',
                'label': '5.0 리더십',
                'type': 'textarea',
                'required': True,
                'placeholder': '최고경영자의 리더십과 환경 방침을 기술합니다.\n참조: HP-EP-510, HP-EP-520'
            },
            
            # 6.0 기획
            {
                'name': 'planning',
                'label': '6.0 기획',
                'type': 'textarea',
                'required': True,
                'placeholder': '환경경영시스템 기획 및 리스크 관리를 기술합니다.\n참조: HP-EP-610'
            },
            
            # 7.0 지원
            {
                'name': 'support',
                'label': '7.0 지원',
                'type': 'textarea',
                'required': True,
                'placeholder': '환경경영시스템 운영에 필요한 자원을 기술합니다.\n참조: HP-EP-710~760, HP-EI-741, 761'
            },
            
            # 8.0 운영
            {
                'name': 'operation',
                'label': '8.0 운영',
                'type': 'textarea',
                'required': True,
                'placeholder': '환경영향 평가 및 관리 프로세스를 기술합니다.\n참조: HP-EP-810~870, HP-EI-851~852'
            },
            
            # 9.0 성과평가
            {
                'name': 'performance_evaluation',
                'label': '9.0 성과평가',
                'type': 'textarea',
                'required': True,
                'placeholder': '모니터링, 측정, 분석 및 평가 활동을 기술합니다.\n참조: HP-EP-910~950'
            },
            
            # 10.0 개선
            {
                'name': 'improvement',
                'label': '10.0 개선',
                'type': 'textarea',
                'required': True,
                'placeholder': '부적합 처리 및 지속적 개선 활동을 기술합니다.\n참조: HP-EP-1010, 1020'
            },
        ]
    }
    
    # 매뉴얼 템플릿 생성
    template, created = DocumentTemplate.objects.update_or_create(
        category=em_cat,
        name='환경경영 매뉴얼 (HP-EM-01)',
        defaults={
            'description': 'ISO 14001:2015 환경경영시스템 매뉴얼\n\n이 매뉴얼은 관련 절차서들의 내용을 종합하여 작성됩니다.\n각 섹션은 해당하는 절차서들에서 자동으로 데이터를 가져올 수 있습니다.',
            'fields_schema': manual_fields_schema,
            'is_active': True,
            'version': '0',
        }
    )
    
    if created:
        print(f"  ✓ 매뉴얼 템플릿 생성: {template.name}")
    else:
        print(f"  ✓ 매뉴얼 템플릿 업데이트: {template.name}")
    
    return template


def main():
    print("=" * 80)
    print("ISO 14001 Environmental Management System Setup")
    print("=" * 80)
    print()
    
    # 1. 카테고리 생성
    create_iso14001_categories()
    
    # 2. 절차서 템플릿 생성
    procedure_count = create_iso14001_procedure_templates()
    
    # 3. 매뉴얼 템플릿 생성
    manual_template = create_iso14001_manual_template()
    
    print()
    print("=" * 80)
    print("ISO 14001 Setup Completed!")
    print("=" * 80)
    print()
    print(f"생성된 템플릿:")
    print(f"  - HP-EM (환경경영 매뉴얼): 1개")
    print(f"  - HP-EP (환경경영 절차서): {DocumentTemplate.objects.filter(category__code='HP-EP').count()}개")
    print(f"  - HP-EI (환경경영 지침서): {DocumentTemplate.objects.filter(category__code='HP-EI').count()}개")
    print()
    print("매뉴얼 섹션별 절차서:")
    print("  4.0 조직의 상황 → HP-EP-410")
    print("  5.0 리더십 → HP-EP-510, 520")
    print("  6.0 기획 → HP-EP-610")
    print("  7.0 지원 → HP-EP-710~760, HP-EI-741, 761")
    print("  8.0 운영 → HP-EP-810~870, HP-EI-851~852")
    print("  9.0 성과평가 → HP-EP-910~950")
    print("  10.0 개선 → HP-EP-1010, 1020")
    print()
    print("✅ ISO 9001과 동일하게 양방향 데이터 연동 지원!")


if __name__ == '__main__':
    main()
