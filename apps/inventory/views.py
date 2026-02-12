"""
Inventory Views
"""
from rest_framework import viewsets, status, generics, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction, models
from django.db.models import F, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import IsAdminRole, IsManagerOrAdmin
from .models import (
    Warehouse, Location, ItemCategory, InventoryItem,
    StockTransaction, StockAlert, InventoryCount, InventoryCountItem,
    ExcelMasterDocument, ExcelUpdateLog
)
from .serializers import (
    WarehouseSerializer, LocationSerializer, ItemCategorySerializer,
    InventoryItemListSerializer, InventoryItemDetailSerializer,
    InventoryItemCreateSerializer, InventoryItemUpdateSerializer,
    StockTransactionSerializer,
    StockInSerializer, StockOutSerializer, StockTransferSerializer,
    StockAdjustSerializer, BarcodeScanSerializer, StockAlertSerializer,
    InventoryCountSerializer, InventoryCountItemSerializer,
    DashboardStatsSerializer
)
from .services import BarcodeService


class WarehouseViewSet(viewsets.ModelViewSet):
    """창고 관리 ViewSet"""
    
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]


class LocationViewSet(viewsets.ModelViewSet):
    """위치 관리 ViewSet"""
    
    queryset = Location.objects.select_related('warehouse')
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        warehouse_id = self.request.query_params.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        return queryset
    
    @action(detail=True, methods=['get'])
    def barcode(self, request, pk=None):
        """위치 바코드 생성"""
        location = self.get_object()
        barcode_service = BarcodeService()
        barcode_data = barcode_service.generate_barcode(
            location.barcode,
            f"{location.warehouse.name} - {location.name}"
        )
        return Response(barcode_data)


class ItemCategoryViewSet(viewsets.ModelViewSet):
    """품목 카테고리 ViewSet"""
    
    queryset = ItemCategory.objects.filter(is_active=True)
    serializer_class = ItemCategorySerializer
    permission_classes = [IsAuthenticated]


class InventoryItemViewSet(viewsets.ModelViewSet):
    """재고 품목 ViewSet"""
    
    queryset = InventoryItem.objects.select_related('category', 'default_location', 'created_by')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InventoryItemCreateSerializer
        elif self.action == 'retrieve':
            return InventoryItemDetailSerializer
        elif self.action in ('update', 'partial_update'):
            return InventoryItemUpdateSerializer
        return InventoryItemListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filters
        category = self.request.query_params.get('category')
        item_type = self.request.query_params.get('type')
        low_stock = self.request.query_params.get('low_stock')
        search = self.request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category_id=category)
        if item_type:
            queryset = queryset.filter(item_type=item_type)
        if low_stock == 'true':
            queryset = queryset.filter(current_quantity__lte=F('safety_stock'))
        if search:
            queryset = queryset.filter(
                models.Q(item_code__icontains=search) |
                models.Q(name__icontains=search) |
                models.Q(barcode__icontains=search) |
                models.Q(serial_number__icontains=search) |
                models.Q(manufacturer__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def barcode(self, request, pk=None):
        """품목 바코드/QR 생성"""
        item = self.get_object()
        barcode_service = BarcodeService()
        code_type = request.query_params.get('type', 'barcode')  # barcode or qr
        
        if code_type == 'qr':
            data = barcode_service.generate_qr_code(
                item.barcode,
                additional_info={
                    'name': item.name,
                    'code': item.item_code,
                    'unit': item.unit
                }
            )
        else:
            data = barcode_service.generate_barcode(item.barcode, item.name)
        
        return Response(data)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """품목 거래 이력"""
        item = self.get_object()
        transactions = StockTransaction.objects.filter(item=item).order_by('-created_at')[:50]
        serializer = StockTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """안전재고 미달 품목 목록"""
        items = self.get_queryset().filter(
            current_quantity__lte=F('safety_stock'),
            is_active=True
        )
        serializer = InventoryItemListSerializer(items, many=True)
        return Response(serializer.data)


class StockTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """재고 거래 조회 ViewSet"""
    
    queryset = StockTransaction.objects.select_related(
        'item', 'location', 'performed_by'
    ).order_by('-created_at')
    serializer_class = StockTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filters
        item = self.request.query_params.get('item')
        transaction_type = self.request.query_params.get('type')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if item:
            queryset = queryset.filter(item_id=item)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset


class StockOperationView(generics.GenericAPIView):
    """재고 입출고 처리"""
    
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def _process_transaction(self, item, transaction_type, quantity, user, **kwargs):
        """거래 처리"""
        before_qty = item.current_quantity
        
        if transaction_type == 'in':
            item.current_quantity = F('current_quantity') + quantity
        elif transaction_type == 'out':
            if item.current_quantity < quantity:
                raise ValueError('재고가 부족합니다.')
            item.current_quantity = F('current_quantity') - quantity
        elif transaction_type == 'adjust':
            item.current_quantity = quantity
        
        item.save()
        item.refresh_from_db()
        
        after_qty = item.current_quantity
        
        # 거래 기록 생성
        transaction = StockTransaction.objects.create(
            item=item,
            transaction_type=transaction_type,
            quantity=abs(quantity) if transaction_type != 'adjust' else abs(after_qty - before_qty),
            before_quantity=before_qty,
            after_quantity=after_qty,
            performed_by=user,
            **kwargs
        )
        
        # 안전재고 알림 확인
        self._check_stock_alerts(item)
        
        return transaction
    
    def _check_stock_alerts(self, item):
        """재고 알림 확인 및 생성"""
        if item.current_quantity <= 0:
            StockAlert.objects.get_or_create(
                item=item,
                alert_type='out_of_stock',
                is_resolved=False,
                defaults={
                    'message': f'{item.name}의 재고가 소진되었습니다.',
                    'current_quantity': item.current_quantity,
                    'threshold_quantity': 0,
                }
            )
        elif item.current_quantity <= item.safety_stock:
            StockAlert.objects.get_or_create(
                item=item,
                alert_type='low_stock',
                is_resolved=False,
                defaults={
                    'message': f'{item.name}의 재고가 안전재고({item.safety_stock}) 이하입니다.',
                    'current_quantity': item.current_quantity,
                    'threshold_quantity': item.safety_stock,
                }
            )
        else:
            # 재고가 충분하면 미해결 알림 해결 처리
            StockAlert.objects.filter(
                item=item,
                is_resolved=False
            ).update(is_resolved=True, resolved_at=timezone.now())
    
    def _update_excel_file(self, item, operation_type, quantity, user):
        """엑셀 파일 동기화"""
        try:
            # 바코드로 문서 찾기
            barcode = item.barcode
            if not barcode:
                return  # 바코드 없으면 스킵
            
            # 문서 타입 판별
            document = None
            if barcode.startswith('HP-KSTC-'):
                document = ExcelMasterDocument.objects.filter(doc_type='ks_cert').first()
            elif barcode.startswith('HP-P10-') or barcode.startswith('HP-P20-'):
                document = ExcelMasterDocument.objects.filter(doc_type='measurement').first()
            elif barcode.startswith('HP-PRT-'):
                document = ExcelMasterDocument.objects.filter(doc_type='parts').first()
            elif barcode.startswith('HP-SUP-'):
                document = ExcelMasterDocument.objects.filter(doc_type='supplies').first()
            
            if not document:
                return  # 해당 문서 없으면 스킵
            
            # PRT/SUP만 입고/출고 처리
            if document.doc_type not in ['parts', 'supplies']:
                return
            
            # 현재 엑셀 값 읽기
            items = document.read_all_items()
            existing_item = next((i for i in items if i['barcode'] == barcode), None)
            
            if not existing_item:
                return  # 엑셀에 없으면 스킵
            
            # 현재 값
            current_received = float(existing_item.get('received', 0) or 0)
            current_issued = float(existing_item.get('issued', 0) or 0)
            
            # 새 값 계산
            if operation_type == 'in':
                new_received = current_received + float(quantity)
                new_issued = current_issued
            elif operation_type == 'out':
                new_received = current_received
                new_issued = current_issued + float(quantity)
            else:
                return  # 조정/이동은 스킵
            
            new_current = new_received - new_issued
            
            # 엑셀 파일 업데이트
            updates = {
                'received': new_received,
                'issued': new_issued,
                'current': new_current
            }
            
            success = document.update_item(barcode, updates)
            
            if success:
                # 로그 기록
                ExcelUpdateLog.objects.create(
                    document=document,
                    barcode=barcode,
                    action=f'stock_{operation_type}',
                    updates=updates,
                    previous_values={
                        'received': current_received,
                        'issued': current_issued,
                        'current': current_received - current_issued
                    },
                    created_by=user
                )
                
        except Exception as e:
            # 엑셀 업데이트 실패해도 DB 작업은 성공으로 처리
            import logging
            logger = logging.getLogger('hpe')
            logger.error(f'엑셀 파일 업데이트 실패: {str(e)}')
    
    def post(self, request, operation_type):
        """입출고/조정 처리"""
        if operation_type == 'in':
            serializer = StockInSerializer(data=request.data, context={'request': request})
        elif operation_type == 'out':
            serializer = StockOutSerializer(data=request.data, context={'request': request})
        elif operation_type == 'adjust':
            serializer = StockAdjustSerializer(data=request.data, context={'request': request})
        elif operation_type == 'transfer':
            serializer = StockTransferSerializer(data=request.data, context={'request': request})
        else:
            return Response(
                {'error': '잘못된 작업 유형입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            item = get_object_or_404(InventoryItem, id=data['item_id'])
            
            kwargs = {
                'location_id': data.get('location_id'),
                'reference_number': data.get('reference_number', ''),
                'remarks': data.get('remarks', ''),
                'scanned_barcode': data.get('scanned_barcode', ''),
            }
            
            if operation_type == 'adjust':
                kwargs['remarks'] = data.get('reason', '')
                quantity = data['new_quantity']
            else:
                quantity = data['quantity']
            
            transaction = self._process_transaction(
                item=item,
                transaction_type=operation_type,
                quantity=quantity,
                user=request.user,
                **kwargs
            )
            
            # 엑셀 파일도 업데이트
            self._update_excel_file(item, operation_type, quantity, request.user)
            
            return Response({
                'message': '처리되었습니다.',
                'transaction': StockTransactionSerializer(transaction).data
            })
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BarcodeScanView(generics.GenericAPIView):
    """바코드 스캔 처리"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = BarcodeScanSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        barcode = serializer.validated_data['barcode']
        scan_type = serializer.validated_data.get('scan_type', 'any')
        
        result = {'found': False, 'type': None, 'data': None}
        
        # 품목 바코드 검색
        if scan_type in ['item', 'any']:
            try:
                item = InventoryItem.objects.get(barcode=barcode)
                result = {
                    'found': True,
                    'type': 'item',
                    'data': InventoryItemDetailSerializer(item).data
                }
                return Response(result)
            except InventoryItem.DoesNotExist:
                pass
        
        # 위치 바코드 검색
        if scan_type in ['location', 'any']:
            try:
                location = Location.objects.get(barcode=barcode)
                result = {
                    'found': True,
                    'type': 'location',
                    'data': LocationSerializer(location).data
                }
                return Response(result)
            except Location.DoesNotExist:
                pass
        
        return Response(result)


class StockAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """재고 알림 ViewSet"""
    
    queryset = StockAlert.objects.select_related('item').order_by('-created_at')
    serializer_class = StockAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        unresolved_only = self.request.query_params.get('unresolved')
        if unresolved_only == 'true':
            queryset = queryset.filter(is_resolved=False)
        return queryset
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """알림 해결 처리"""
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.save()
        return Response({'message': '알림이 해결되었습니다.'})


class InventoryCountViewSet(viewsets.ModelViewSet):
    """재고 실사 ViewSet"""
    
    queryset = InventoryCount.objects.select_related('warehouse', 'created_by')
    serializer_class = InventoryCountSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get', 'post'])
    def items(self, request, pk=None):
        """실사 품목 관리"""
        inventory_count = self.get_object()
        
        if request.method == 'GET':
            items = inventory_count.items.select_related('item')
            serializer = InventoryCountItemSerializer(items, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = InventoryCountItemSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(
                inventory_count=inventory_count,
                counted_by=request.user,
                counted_at=timezone.now()
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """실사 완료 및 재고 조정"""
        inventory_count = self.get_object()
        
        if inventory_count.status != 'in_progress':
            return Response(
                {'error': '진행중인 실사만 완료할 수 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # 차이가 있는 품목 조정
            for count_item in inventory_count.items.filter(counted_quantity__isnull=False):
                if count_item.difference and count_item.difference != 0:
                    item = count_item.item
                    StockTransaction.objects.create(
                        item=item,
                        transaction_type='adjust',
                        quantity=abs(count_item.difference),
                        before_quantity=item.current_quantity,
                        after_quantity=count_item.counted_quantity,
                        performed_by=request.user,
                        reference_number=inventory_count.count_number,
                        remarks=f'재고 실사 조정: {count_item.remarks}'
                    )
                    item.current_quantity = count_item.counted_quantity
                    item.save(update_fields=['current_quantity'])
            
            inventory_count.status = 'completed'
            inventory_count.completed_at = timezone.now()
            inventory_count.approved_by = request.user
            inventory_count.save()
        
        return Response({'message': '재고 실사가 완료되었습니다.'})


class InventoryDashboardView(generics.GenericAPIView):
    """재고 대시보드"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        items = InventoryItem.objects.filter(is_active=True)
        
        stats = {
            'total_items': items.count(),
            'low_stock_count': items.filter(
                current_quantity__lte=F('safety_stock'),
                current_quantity__gt=0
            ).count(),
            'out_of_stock_count': items.filter(current_quantity__lte=0).count(),
            'total_value': items.aggregate(
                total=Sum(F('current_quantity') * F('unit_price'))
            )['total'] or 0,
            'transactions_today': StockTransaction.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'pending_alerts': StockAlert.objects.filter(is_resolved=False).count(),
        }
        
        # 최근 거래
        recent_transactions = StockTransaction.objects.select_related(
            'item', 'performed_by'
        ).order_by('-created_at')[:10]
        
        # 안전재고 미달 품목
        low_stock_items = items.filter(
            current_quantity__lte=F('safety_stock')
        ).order_by('current_quantity')[:10]
        
        return Response({
            'stats': stats,
            'recent_transactions': StockTransactionSerializer(recent_transactions, many=True).data,
            'low_stock_items': InventoryItemListSerializer(low_stock_items, many=True).data,
        })
