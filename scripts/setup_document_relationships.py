#!/usr/bin/env python
"""
Setup Document Relationships between Manual and Procedures
ISO 9001 매뉴얼과 절차서 간의 관계 설정
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.documents.models import DocumentTemplate


def setup_document_relationships():
    """매뉴얼과 절차서 간의 관계 설정"""
    print("=" * 80)
    print("Setting up Document Relationships")
    print("=" * 80)
    print()
    
    # 매뉴얼 섹션별 관련 절차서 매핑
    manual_procedure_mapping = {
        '4.0': [  # 조직의 상황
            'HP-QP-410',  # 상황이해 및 품질경영시스템 운영 절차서
        ],
        '5.0': [  # 리더십
            'HP-QP-510',  # 리더십 및 방침수립 절차서
            'HP-QP-520',  # 조직 및 업무분장 절차서
        ],
        '6.0': [  # 기획
            'HP-QP-610',  # 품질 경영시스템 기획 및 리스크 관리 절차서
        ],
        '7.0': [  # 자원
            'HP-QP-710',  # 자원관리 절차서
            'HP-QP-720',  # 설비관리 절차서
            'HP-QP-730',  # 시험 및 측정장비 관리 절차서
            'HP-QP-740',  # 교육 및 훈련 관리 절차서
            'HP-QI-741',  # 자격인증관리 지침서
            'HP-QP-750',  # 인식 및 의사소통 절차서
            'HP-QP-760',  # 문서화 정보관리 절차서
            'HP-QI-761',  # 문서작성 지침서
        ],
        '8.0': [  # 운영
            'HP-QP-810',  # 제품 및 서비스 요구사항 검토 절차서
            'HP-QP-820',  # 설계 및 개발관리 절차서
            'HP-QP-830',  # 구매관리 절차서
            'HP-QP-840',  # 공급자관리 절차서
            'HP-QP-850',  # 생산관리 절차서
            'HP-QI-851',  # 식별 및 추적성 관리 지침서
            'HP-QI-852',  # 고객 및 외부공급자 자산관리 지침서
            'HP-QI-853',  # 제품 보존관리 지침서
            'HP-QI-854',  # 인도 후 활동 지침서
            'HP-QP-860',  # 검사 및 시험 절차서
            'HP-QP-870',  # 부적합품 관리 절차서
        ],
        '9.0': [  # 성과평가
            'HP-QP-910',  # 프로세스 성과관리 절차서
            'HP-QP-920',  # 고객만족관리 절차서
            'HP-QP-930',  # 데이터 분석관리 절차서
            'HP-QP-940',  # 내부심사 절차서
            'HP-QP-950',  # 경영검토 절차서
        ],
        '10.0': [  # 개선
            'HP-QP-1010',  # 부적합 및 시정조치 절차서
            'HP-QP-1020',  # 지속적 개선 절차서
        ],
    }
    
    # 템플릿에 description에 섹션 정보 추가
    for section, doc_numbers in manual_procedure_mapping.items():
        for doc_number in doc_numbers:
            try:
                # 문서번호로 템플릿 찾기
                template = DocumentTemplate.objects.filter(name__contains=doc_number).first()
                if template:
                    # description에 매뉴얼 섹션 정보 추가
                    if f"매뉴얼 섹션: {section}" not in template.description:
                        template.description += f"\n매뉴얼 섹션: {section}"
                        template.save()
                        print(f"  ✓ {doc_number} → 매뉴얼 섹션 {section} 연결")
                else:
                    print(f"  ✗ {doc_number} 템플릿을 찾을 수 없습니다")
            except Exception as e:
                print(f"  ✗ {doc_number} 처리 중 오류: {e}")
    
    print()
    print("=" * 80)
    print("Document Relationships Setup Completed!")
    print("=" * 80)
    print()
    print("매뉴얼 섹션별 관련 절차서:")
    for section, procedures in manual_procedure_mapping.items():
        print(f"  {section}: {len(procedures)}개 절차서")


def create_shared_fields_config():
    """
    매뉴얼과 절차서 간 공유 필드 설정
    매뉴얼에서 가져올 수 있는 공통 정보
    """
    shared_config = {
        'company_info': {
            'company_name': '주식회사 에이치피엔지니어링',
            'company_name_en': 'HP Engineering Co., Ltd',
            'company_address': '경상남도 창원시 의창구 원이대로 271, 3층 322호(봉곡동, 한마음타워)',
        },
        'quality_policy': {
            'policy': '고객 요구사항 준수를 통한 고객만족 실현',
            'objectives': [
                '고객과 소통하는 경영',
                '실행중심·고객중심·인간중심',
                '고객약속 최우선'
            ]
        },
        'common_fields': [
            'purpose',  # 목적 - 매뉴얼의 해당 섹션 목적 참조
            'scope',  # 적용범위 - 매뉴얼의 해당 섹션 범위 참조
            'terms',  # 용어의 정의 - 매뉴얼의 3.0 용어 참조
        ]
    }
    
    return shared_config


if __name__ == '__main__':
    setup_document_relationships()
    
    print("\n공유 필드 설정:")
    config = create_shared_fields_config()
    print(f"  - 회사 정보: {len(config['company_info'])}개 필드")
    print(f"  - 품질 방침: {len(config['quality_policy'])}개 섹션")
    print(f"  - 공통 필드: {len(config['common_fields'])}개 필드")
