"""
엑셀 기반 문서 관리 Views
바코드 스캔 시 엑셀 파일 직접 업데이트
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import ExcelMasterDocument, ExcelUpdateLog
from .serializers_excel import (
    ExcelMasterDocumentSerializer,
    ExcelUpdateLogSerializer,
    BarcodeScanSerializer
)


class ExcelMasterDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """엑셀 마스터 문서 ViewSet (읽기 전용)"""
    queryset = ExcelMasterDocument.objects.all()
    serializer_class = ExcelMasterDocumentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def list_all_items(self, request):
        """모든 문서의 항목 통합 조회"""
        all_items = []
        
        for doc in ExcelMasterDocument.objects.all():
            items = doc.read_all_items()
            for item in items:
                item['document_id'] = str(doc.id)
                item['document_title'] = doc.title
                item['document_type'] = doc.doc_type
                all_items.append(item)
        
        return Response({
            'count': len(all_items),
            'results': all_items
        })
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """특정 문서의 항목 조회"""
        document = self.get_object()
        items = document.read_all_items()
        
        return Response({
            'document': ExcelMasterDocumentSerializer(document).data,
            'count': len(items),
            'items': items
        })
    
    @action(detail=False, methods=['post'])
    def scan_barcode(self, request):
        """
        바코드 스캔 처리
        - 바코드 패턴으로 문서 자동 판별
        - 해당 엑셀 파일 업데이트
        """
        serializer = BarcodeScanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        barcode = serializer.validated_data['barcode']
        action_type = serializer.validated_data['action']
        quantity = serializer.validated_data.get('quantity', 1)
        remarks = serializer.validated_data.get('remarks', '')
        
        # 1. 바코드 패턴으로 문서 유형 판별
        document = self._get_document_by_barcode(barcode)
        if not document:
            return Response({
                'error': f'바코드 "{barcode}"에 해당하는 문서를 찾을 수 없습니다.',
                'barcode': barcode
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 2. 엑셀 파일에서 항목 찾기
        items = document.read_all_items()
        existing_item = next((item for item in items if item['barcode'] == barcode), None)
        
        if not existing_item:
            # 새 항목 추가 (PRT, SUP만 가능)
            if document.doc_type in [ExcelMasterDocument.DocType.PARTS, ExcelMasterDocument.DocType.SUPPLIES]:
                return self._add_new_item(document, barcode, quantity, remarks, request.user)
            else:
                return Response({
                    'error': f'바코드 "{barcode}"가 {document.title}에 등록되어 있지 않습니다.',
                    'barcode': barcode,
                    'document': document.title
                }, status=status.HTTP_404_NOT_FOUND)
        
        # 3. 기존 항목 업데이트
        if action_type == 'stock_in':
            return self._handle_stock_in(document, barcode, existing_item, quantity, remarks, request.user)
        elif action_type == 'stock_out':
            return self._handle_stock_out(document, barcode, existing_item, quantity, remarks, request.user)
        else:  # scan
            return self._handle_scan(document, barcode, existing_item, request.user)
    
    def _get_document_by_barcode(self, barcode):
        """바코드 패턴으로 문서 판별"""
        if barcode.startswith('HP-KSTC-'):
            return ExcelMasterDocument.objects.filter(doc_type=ExcelMasterDocument.DocType.KS_CERT).first()
        elif barcode.startswith('HP-P10-') or barcode.startswith('HP-P20-'):
            return ExcelMasterDocument.objects.filter(doc_type=ExcelMasterDocument.DocType.MEASUREMENT).first()
        elif barcode.startswith('HP-PRT-'):
            return ExcelMasterDocument.objects.filter(doc_type=ExcelMasterDocument.DocType.PARTS).first()
        elif barcode.startswith('HP-SUP-'):
            return ExcelMasterDocument.objects.filter(doc_type=ExcelMasterDocument.DocType.SUPPLIES).first()
        return None
    
    def _handle_scan(self, document, barcode, item, user):
        """스캔만 (정보 조회)"""
        # 로그 기록
        ExcelUpdateLog.objects.create(
            document=document,
            barcode=barcode,
            action='scan',
            updates={'scanned': True},
            created_by=user
        )
        
        return Response({
            'message': '스캔 완료',
            'barcode': barcode,
            'document': document.title,
            'item': item
        })
    
    def _handle_stock_in(self, document, barcode, item, quantity, remarks, user):
        """입고 처리"""
        if 'received' not in document.extra_columns:
            return Response({
                'error': f'{document.title}는 입고 처리를 지원하지 않습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 현재 값 읽기
        current_received = float(item.get('received', 0) or 0)
        current_issued = float(item.get('issued', 0) or 0)
        
        # 새 값 계산
        new_received = current_received + float(quantity)
        new_current = new_received - current_issued
        
        # 엑셀 파일 업데이트
        updates = {
            'received': new_received,
            'current': new_current
        }
        
        success = document.update_item(barcode, updates)
        
        if success:
            # 로그 기록
            ExcelUpdateLog.objects.create(
                document=document,
                barcode=barcode,
                action='stock_in',
                updates={'quantity': float(quantity), 'new_received': new_received, 'new_current': new_current},
                previous_values={'received': current_received, 'current': current_received - current_issued},
                created_by=user
            )
            
            return Response({
                'message': '입고 처리 완료',
                'barcode': barcode,
                'quantity': quantity,
                'document': document.title,
                'previous': {
                    'received': current_received,
                    'current': current_received - current_issued
                },
                'updated': {
                    'received': new_received,
                    'current': new_current
                }
            })
        else:
            return Response({
                'error': '엑셀 파일 업데이트 실패'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_stock_out(self, document, barcode, item, quantity, remarks, user):
        """출고 처리"""
        if 'issued' not in document.extra_columns:
            return Response({
                'error': f'{document.title}는 출고 처리를 지원하지 않습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 현재 값 읽기
        current_received = float(item.get('received', 0) or 0)
        current_issued = float(item.get('issued', 0) or 0)
        current_stock = current_received - current_issued
        
        # 재고 부족 확인
        if current_stock < float(quantity):
            return Response({
                'error': f'재고 부족: 현재 {current_stock}, 출고 요청 {quantity}',
                'barcode': barcode,
                'current_stock': current_stock,
                'requested_quantity': float(quantity)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 새 값 계산
        new_issued = current_issued + float(quantity)
        new_current = current_received - new_issued
        
        # 엑셀 파일 업데이트
        updates = {
            'issued': new_issued,
            'current': new_current
        }
        
        success = document.update_item(barcode, updates)
        
        if success:
            # 로그 기록
            ExcelUpdateLog.objects.create(
                document=document,
                barcode=barcode,
                action='stock_out',
                updates={'quantity': float(quantity), 'new_issued': new_issued, 'new_current': new_current},
                previous_values={'issued': current_issued, 'current': current_stock},
                created_by=user
            )
            
            return Response({
                'message': '출고 처리 완료',
                'barcode': barcode,
                'quantity': quantity,
                'document': document.title,
                'previous': {
                    'issued': current_issued,
                    'current': current_stock
                },
                'updated': {
                    'issued': new_issued,
                    'current': new_current
                }
            })
        else:
            return Response({
                'error': '엑셀 파일 업데이트 실패'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _add_new_item(self, document, barcode, quantity, remarks, user):
        """새 항목 추가 (엑셀에 새 행 추가)"""
        # TODO: 엑셀에 새 행 추가하는 로직 구현
        return Response({
            'error': '새 항목 추가 기능은 아직 구현되지 않았습니다. 엑셀 파일에서 직접 추가해주세요.',
            'barcode': barcode
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class ExcelUpdateLogViewSet(viewsets.ReadOnlyModelViewSet):
    """엑셀 업데이트 로그 ViewSet (읽기 전용)"""
    queryset = ExcelUpdateLog.objects.all()
    serializer_class = ExcelUpdateLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 문서별 필터
        document_id = self.request.query_params.get('document_id')
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        
        # 바코드별 필터
        barcode = self.request.query_params.get('barcode')
        if barcode:
            queryset = queryset.filter(barcode=barcode)
        
        # 작업 유형별 필터
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        return queryset
