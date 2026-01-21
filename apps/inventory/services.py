"""
Inventory Services - Barcode Generation
"""
import io
import base64
import barcode
from barcode.writer import ImageWriter
import qrcode
from qrcode.image.pil import PilImage
import json


class BarcodeService:
    """바코드/QR 코드 생성 서비스"""
    
    def generate_barcode(self, code, label='', barcode_type='code128'):
        """
        바코드 생성
        
        Args:
            code: 바코드 값
            label: 라벨 텍스트
            barcode_type: 바코드 유형 (code128, ean13, etc.)
        
        Returns:
            dict: 바코드 이미지 데이터 (base64)
        """
        try:
            # 바코드 클래스 가져오기
            barcode_class = barcode.get_barcode_class(barcode_type)
            
            # 이미지 버퍼
            buffer = io.BytesIO()
            
            # 바코드 생성
            bc = barcode_class(str(code), writer=ImageWriter())
            bc.write(buffer, options={
                'module_width': 0.4,
                'module_height': 15.0,
                'font_size': 10,
                'text_distance': 5.0,
                'quiet_zone': 6.5,
            })
            
            buffer.seek(0)
            image_data = base64.b64encode(buffer.read()).decode('utf-8')
            
            return {
                'code': code,
                'label': label,
                'type': 'barcode',
                'format': barcode_type,
                'image': f'data:image/png;base64,{image_data}',
            }
            
        except Exception as e:
            return {
                'code': code,
                'label': label,
                'type': 'barcode',
                'error': str(e),
            }
    
    def generate_qr_code(self, code, additional_info=None, size=10):
        """
        QR 코드 생성
        
        Args:
            code: QR 코드 값
            additional_info: 추가 정보 (dict)
            size: 박스 크기
        
        Returns:
            dict: QR 코드 이미지 데이터 (base64)
        """
        try:
            # QR 코드 데이터 구성
            if additional_info:
                qr_data = json.dumps({
                    'code': code,
                    **additional_info
                }, ensure_ascii=False)
            else:
                qr_data = code
            
            # QR 코드 생성
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=size,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # 이미지 생성
            img = qr.make_image(fill_color='black', back_color='white')
            
            # 버퍼에 저장
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            image_data = base64.b64encode(buffer.read()).decode('utf-8')
            
            return {
                'code': code,
                'data': qr_data,
                'type': 'qr',
                'image': f'data:image/png;base64,{image_data}',
            }
            
        except Exception as e:
            return {
                'code': code,
                'type': 'qr',
                'error': str(e),
            }
    
    def generate_label(self, item, include_qr=True):
        """
        품목 라벨 생성 (바코드 + 정보)
        
        Args:
            item: InventoryItem 객체
            include_qr: QR 코드 포함 여부
        
        Returns:
            dict: 라벨 데이터
        """
        barcode_data = self.generate_barcode(
            item.barcode,
            item.name
        )
        
        label_data = {
            'item_code': item.item_code,
            'barcode': item.barcode,
            'name': item.name,
            'specification': item.specification,
            'unit': item.unit,
            'barcode_image': barcode_data.get('image'),
        }
        
        if include_qr:
            qr_data = self.generate_qr_code(
                item.barcode,
                {
                    'item_code': item.item_code,
                    'name': item.name,
                    'unit': item.unit,
                }
            )
            label_data['qr_image'] = qr_data.get('image')
        
        return label_data
    
    def batch_generate_labels(self, items, label_type='barcode'):
        """
        품목 라벨 일괄 생성
        
        Args:
            items: InventoryItem 목록
            label_type: 'barcode', 'qr', 'both'
        
        Returns:
            list: 라벨 데이터 목록
        """
        labels = []
        
        for item in items:
            label = {
                'item_code': item.item_code,
                'barcode': item.barcode,
                'name': item.name,
                'specification': item.specification,
                'unit': item.unit,
            }
            
            if label_type in ['barcode', 'both']:
                barcode_data = self.generate_barcode(item.barcode, item.name)
                label['barcode_image'] = barcode_data.get('image')
            
            if label_type in ['qr', 'both']:
                qr_data = self.generate_qr_code(
                    item.barcode,
                    {'item_code': item.item_code, 'name': item.name}
                )
                label['qr_image'] = qr_data.get('image')
            
            labels.append(label)
        
        return labels


class InventoryReportService:
    """재고 리포트 서비스"""
    
    def generate_stock_report(self, warehouse=None, category=None):
        """재고 현황 리포트"""
        from .models import InventoryItem
        from django.db.models import Sum, F
        
        queryset = InventoryItem.objects.filter(is_active=True)
        
        if warehouse:
            queryset = queryset.filter(default_location__warehouse=warehouse)
        if category:
            queryset = queryset.filter(category=category)
        
        report = {
            'generated_at': timezone.now(),
            'filters': {
                'warehouse': warehouse.name if warehouse else 'All',
                'category': category.name if category else 'All',
            },
            'summary': {
                'total_items': queryset.count(),
                'total_quantity': queryset.aggregate(Sum('current_quantity'))['current_quantity__sum'] or 0,
                'total_value': queryset.aggregate(
                    total=Sum(F('current_quantity') * F('unit_price'))
                )['total'] or 0,
                'low_stock_count': queryset.filter(
                    current_quantity__lte=F('safety_stock')
                ).count(),
            },
            'items': list(queryset.values(
                'item_code', 'name', 'current_quantity', 'safety_stock',
                'unit', 'unit_price', 'category__name'
            ))
        }
        
        return report
    
    def generate_transaction_report(self, date_from, date_to, transaction_type=None):
        """거래 내역 리포트"""
        from .models import StockTransaction
        
        queryset = StockTransaction.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )
        
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        report = {
            'generated_at': timezone.now(),
            'period': {
                'from': date_from,
                'to': date_to,
            },
            'summary': {
                'total_transactions': queryset.count(),
                'by_type': dict(
                    queryset.values('transaction_type').annotate(
                        count=Count('id'),
                        total_quantity=Sum('quantity')
                    ).values_list('transaction_type', 'count')
                ),
            },
            'transactions': list(queryset.values(
                'transaction_number', 'item__item_code', 'item__name',
                'transaction_type', 'quantity', 'created_at',
                'performed_by__first_name', 'performed_by__last_name'
            ))
        }
        
        return report


from django.utils import timezone
from django.db.models import Count
