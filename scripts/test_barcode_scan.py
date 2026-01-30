#!/usr/bin/env python
"""
바코드 스캔 API 테스트 스크립트
"""
import os
import sys
import django
import requests
import json

# Django 설정
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

BASE_URL = 'http://localhost:8000/api/v1'

def login():
    """로그인하여 토큰 받기"""
    response = requests.post(f'{BASE_URL}/auth/login/', json={
        'username': 'admin',
        'password': 'admin123!'
    })
    if response.status_code == 200:
        data = response.json()
        return data['access']
    else:
        print(f"❌ 로그인 실패: {response.text}")
        return None

def get_headers(token):
    """인증 헤더 생성"""
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

def list_excel_documents(token):
    """엑셀 문서 목록 조회"""
    print("\n" + "="*80)
    print("📄 엑셀 문서 목록")
    print("="*80)
    
    response = requests.get(
        f'{BASE_URL}/inventory/excel-documents/',
        headers=get_headers(token)
    )
    
    if response.status_code == 200:
        data = response.json()
        docs = data.get('results', [])
        
        for doc in docs:
            print(f"\n📄 {doc['title']}")
            print(f"   ID: {doc['id']}")
            print(f"   유형: {doc['doc_type_display']}")
            print(f"   파일: {doc['file_name']}")
            print(f"   총 항목: {doc.get('total_items', 0)}개")
        
        return docs
    else:
        print(f"❌ 문서 목록 조회 실패: {response.text}")
        return []

def get_document_items(token, doc_id):
    """특정 문서의 항목 조회"""
    response = requests.get(
        f'{BASE_URL}/inventory/excel-documents/{doc_id}/items/',
        headers=get_headers(token)
    )
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        print(f"\n📊 항목 수: {len(items)}개")
        
        # 처음 3개만 표시
        for item in items[:3]:
            print(f"   - {item['barcode']}: {item['name']}")
        
        if len(items) > 3:
            print(f"   ... 외 {len(items) - 3}개")
        
        return items
    else:
        print(f"❌ 항목 조회 실패: {response.text}")
        return []

def scan_barcode(token, barcode, action='scan', quantity=1):
    """바코드 스캔"""
    print("\n" + "="*80)
    print(f"🔍 바코드 스캔: {barcode} (action: {action}, quantity: {quantity})")
    print("="*80)
    
    payload = {
        'barcode': barcode,
        'action': action,
        'quantity': quantity
    }
    
    response = requests.post(
        f'{BASE_URL}/inventory/excel-documents/scan_barcode/',
        headers=get_headers(token),
        json=payload
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ {data.get('message', '성공')}")
        print(f"문서: {data.get('document', 'N/A')}")
        
        if 'item' in data:
            print(f"\n📦 항목 정보:")
            item = data['item']
            print(f"   이름: {item.get('name', 'N/A')}")
            print(f"   입고: {item.get('received', 0)}")
            print(f"   출고: {item.get('issued', 0)}")
            print(f"   현재: {item.get('current', 0)}")
        
        if 'previous' in data and 'updated' in data:
            print(f"\n📊 변경 사항:")
            prev = data['previous']
            updated = data['updated']
            print(f"   이전 - 입고: {prev.get('received', 0)}, 현재: {prev.get('current', 0)}")
            print(f"   변경 - 입고: {updated.get('received', 0)}, 현재: {updated.get('current', 0)}")
        
        return data
    else:
        try:
            error_data = response.json()
            print(f"❌ 스캔 실패:")
            print(json.dumps(error_data, indent=2, ensure_ascii=False))
        except:
            print(f"❌ 스캔 실패: {response.text}")
        return None

def view_update_logs(token, barcode=None):
    """업데이트 로그 조회"""
    print("\n" + "="*80)
    print(f"📝 업데이트 로그" + (f" (바코드: {barcode})" if barcode else ""))
    print("="*80)
    
    url = f'{BASE_URL}/inventory/excel-logs/'
    if barcode:
        url += f'?barcode={barcode}'
    
    response = requests.get(url, headers=get_headers(token))
    
    if response.status_code == 200:
        data = response.json()
        logs = data.get('results', [])
        
        print(f"\n총 {len(logs)}개 로그")
        
        for log in logs[:5]:
            print(f"\n- {log['created_at']}")
            print(f"  바코드: {log['barcode']}")
            print(f"  작업: {log['action']}")
            print(f"  문서: {log['document_title']}")
            print(f"  작업자: {log['created_by_username']}")
            if log['updates']:
                print(f"  변경: {log['updates']}")
        
        return logs
    else:
        print(f"❌ 로그 조회 실패: {response.text}")
        return []

def main():
    """메인 테스트 시나리오"""
    print("\n🚀 바코드 스캔 API 테스트 시작")
    print("="*80)
    
    # 1. 로그인
    token = login()
    if not token:
        print("❌ 로그인 실패. 테스트 중단.")
        return
    
    print("✅ 로그인 성공")
    
    # 2. 엑셀 문서 목록 조회
    docs = list_excel_documents(token)
    if not docs:
        print("❌ 문서가 없습니다. setup_excel_documents.py를 먼저 실행하세요.")
        return
    
    # 3. 각 문서의 항목 조회
    for doc in docs:
        print(f"\n{'='*80}")
        print(f"📄 {doc['title']} 항목 조회")
        print(f"{'='*80}")
        items = get_document_items(token, doc['id'])
        
        # 첫 번째 항목으로 스캔 테스트
        if items:
            first_item = items[0]
            barcode = first_item['barcode']
            
            # 3-1. 스캔만
            scan_barcode(token, barcode, action='scan')
            
            # 3-2. 입고 (PRT/SUP만)
            if doc['doc_type'] in ['parts', 'supplies']:
                scan_barcode(token, barcode, action='stock_in', quantity=10)
                
                # 3-3. 출고
                scan_barcode(token, barcode, action='stock_out', quantity=3)
            
            # 3-4. 로그 확인
            view_update_logs(token, barcode)
    
    print("\n" + "="*80)
    print("✅ 테스트 완료")
    print("="*80)

if __name__ == '__main__':
    main()
