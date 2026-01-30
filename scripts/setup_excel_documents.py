#!/usr/bin/env python
"""
엑셀 마스터 문서 초기 설정
4개의 엑셀 파일을 문서로 등록
"""
import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.inventory.models import ExcelMasterDocument


def setup_excel_documents():
    """4개의 엑셀 파일을 마스터 문서로 등록"""
    
    print("\n" + "="*80)
    print("📄 엑셀 마스터 문서 등록 시작...")
    print("="*80)
    
    documents = [
        {
            'doc_type': ExcelMasterDocument.DocType.KS_CERT,
            'title': 'KS 인증 사내문서 관리대장',
            'file_path': 'KS 인증 사내문서 관리대장_251226.xlsx',
            'sheet_name': 'Sheet1',
            'header_row': 6,
            'data_start_row': 8,
            'barcode_column': 3,  # C열 (관리번호)
            'name_column': 6,     # F열 (한국산업표준명)
            'extra_columns': {}
        },
        {
            'doc_type': ExcelMasterDocument.DocType.MEASUREMENT,
            'title': '계측장비 재고조사 관리대장',
            'file_path': '계측장비 재고조사 관리대장_251224.xlsx',
            'sheet_name': '계측장비관리대장',
            'header_row': 6,
            'data_start_row': 8,
            'barcode_column': 2,  # B열 (관리번호)
            'name_column': 5,     # E열 (장비이름)
            'extra_columns': {}
        },
        {
            'doc_type': ExcelMasterDocument.DocType.PARTS,
            'title': '재고관리 리스트 (PRT) - 사내부품',
            'file_path': '재고관리 리스트 (PRT).xlsx',
            'sheet_name': '사내부품(PRT)-001',
            'header_row': 12,
            'data_start_row': 14,
            'barcode_column': 4,  # D열 (관리번호)
            'name_column': 6,     # F열 (부품이름)
            'extra_columns': {
                'received': 8,     # H열 (입고수량)
                'issued': 9,       # I열 (출고수량)
                'current': 10      # J열 (현재수량)
            }
        },
        {
            'doc_type': ExcelMasterDocument.DocType.SUPPLIES,
            'title': '재고관리 리스트 (SUP) - 사내소모품',
            'file_path': '재고관리 리스트 (SUP).xlsx',
            'sheet_name': '사내부품(PRT)-001',  # SUP 파일도 시트명이 같음
            'header_row': 12,
            'data_start_row': 14,
            'barcode_column': 4,  # D열 (관리번호)
            'name_column': 6,     # F열 (소모품이름)
            'extra_columns': {
                'received': 8,     # H열 (입고수량)
                'issued': 9,       # I열 (출고수량)
                'current': 10      # J열 (현재수량)
            }
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for doc_data in documents:
        doc, created = ExcelMasterDocument.objects.update_or_create(
            doc_type=doc_data['doc_type'],
            defaults=doc_data
        )
        
        if created:
            created_count += 1
            print(f"✅ 생성: {doc.title}")
        else:
            updated_count += 1
            print(f"🔄 업데이트: {doc.title}")
        
        # 항목 수 읽기
        items = doc.read_all_items()
        print(f"   → 총 {len(items)}개 항목")
    
    print("\n" + "="*80)
    print(f"✅ 완료! 생성: {created_count}개, 업데이트: {updated_count}개")
    print("="*80)
    
    # 등록된 문서 목록 출력
    print("\n📋 등록된 엑셀 마스터 문서:")
    for doc in ExcelMasterDocument.objects.all():
        print(f"  - {doc.title}: {doc.total_items}개 항목")


if __name__ == '__main__':
    setup_excel_documents()
