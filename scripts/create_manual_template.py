#!/usr/bin/env python
"""
Create ISO 9001 Quality Manual Template
품질경영 매뉴얼 템플릿 생성
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.documents.models import DocumentCategory, DocumentTemplate


def create_manual_template():
    """품질경영 매뉴얼 템플릿 생성"""
    print("=" * 80)
    print("Creating ISO 9001 Quality Manual Template")
    print("=" * 80)
    print()
    
    # HP-QM 카테고리 가져오기
    qm_cat = DocumentCategory.objects.get(code='HP-QM')
    
    # 매뉴얼 템플릿 필드 스키마
    manual_fields_schema = {
        'fields': [
            # 0.3 품질 방침
            {
                'name': 'quality_policy',
                'label': '0.3 품질 방침',
                'type': 'textarea',
                'required': True,
                'placeholder': '회사의 품질 방침을 기술합니다.',
                'default': '고객 요구사항 준수를 통한 고객만족 실현'
            },
            {
                'name': 'quality_objectives',
                'label': '품질 목표',
                'type': 'textarea',
                'required': True,
                'placeholder': '품질 목표를 기술합니다 (각 줄마다 하나씩)',
                'default': '1. 고객과 소통하는 경영\n2. 실행중심·고객중심·인간중심\n3. 고객약속 최우선'
            },
            
            # 1.0 적용범위
            {
                'name': 'scope',
                'label': '1.0 적용범위',
                'type': 'textarea',
                'required': True,
                'placeholder': '품질경영시스템의 적용범위를 기술합니다.'
            },
            
            # 2.0 인용 표준
            {
                'name': 'reference_standards',
                'label': '2.0 인용 표준',
                'type': 'textarea',
                'required': False,
                'placeholder': '참조하는 표준 문서를 기술합니다.',
                'default': 'ISO 9001:2015\nKS Q ISO 9001:2015'
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
                'placeholder': '조직의 내외부 상황을 기술합니다.\n참조: HP-QP-410'
            },
            
            # 5.0 리더십
            {
                'name': 'leadership',
                'label': '5.0 리더십',
                'type': 'textarea',
                'required': True,
                'placeholder': '최고경영자의 리더십과 품질 방침을 기술합니다.\n참조: HP-QP-510, HP-QP-520'
            },
            
            # 6.0 기획
            {
                'name': 'planning',
                'label': '6.0 기획',
                'type': 'textarea',
                'required': True,
                'placeholder': '품질경영시스템 기획 및 리스크 관리를 기술합니다.\n참조: HP-QP-610'
            },
            
            # 7.0 자원
            {
                'name': 'support',
                'label': '7.0 지원 (자원)',
                'type': 'textarea',
                'required': True,
                'placeholder': '품질경영시스템 운영에 필요한 자원을 기술합니다.\n참조: HP-QP-710~760, HP-QI-741, 761'
            },
            
            # 8.0 운영
            {
                'name': 'operation',
                'label': '8.0 운영',
                'type': 'textarea',
                'required': True,
                'placeholder': '제품 및 서비스 제공 프로세스를 기술합니다.\n참조: HP-QP-810~870, HP-QI-851~854'
            },
            
            # 9.0 성과평가
            {
                'name': 'performance_evaluation',
                'label': '9.0 성과평가',
                'type': 'textarea',
                'required': True,
                'placeholder': '모니터링, 측정, 분석 및 평가 활동을 기술합니다.\n참조: HP-QP-910~950'
            },
            
            # 10.0 개선
            {
                'name': 'improvement',
                'label': '10.0 개선',
                'type': 'textarea',
                'required': True,
                'placeholder': '부적합 처리 및 지속적 개선 활동을 기술합니다.\n참조: HP-QP-1010, 1020'
            },
        ]
    }
    
    # 매뉴얼 템플릿 생성
    template, created = DocumentTemplate.objects.update_or_create(
        category=qm_cat,
        name='품질 경영 매뉴얼 (HP-QM-01)',
        defaults={
            'description': 'ISO 9001:2015 품질경영시스템 매뉴얼\n\n이 매뉴얼은 관련 절차서들의 내용을 종합하여 작성됩니다.\n각 섹션은 해당하는 절차서들에서 자동으로 데이터를 가져올 수 있습니다.',
            'fields_schema': manual_fields_schema,
            'is_active': True,
            'version': '0',
        }
    )
    
    if created:
        print(f"  ✓ 매뉴얼 템플릿 생성: {template.name}")
    else:
        print(f"  ✓ 매뉴얼 템플릿 업데이트: {template.name}")
    
    print()
    print("=" * 80)
    print("Manual Template Created!")
    print("=" * 80)
    print()
    print(f"템플릿: {template.name}")
    print(f"필드 수: {len(manual_fields_schema['fields'])}개")
    print()
    print("매뉴얼 섹션:")
    print("  0.3 품질 방침")
    print("  1.0 적용범위")
    print("  2.0 인용 표준")
    print("  3.0 용어의 정의")
    print("  4.0 조직의 상황 → HP-QP-410")
    print("  5.0 리더십 → HP-QP-510, 520")
    print("  6.0 기획 → HP-QP-610")
    print("  7.0 자원 → HP-QP-710~760, HP-QI-741, 761")
    print("  8.0 운영 → HP-QP-810~870, HP-QI-851~854")
    print("  9.0 성과평가 → HP-QP-910~950")
    print("  10.0 개선 → HP-QP-1010, 1020")


if __name__ == '__main__':
    create_manual_template()
