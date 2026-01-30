from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from .models import KSCertificationItem, KSCertificationHistory
from .serializers import (
    KSCertificationItemListSerializer,
    KSCertificationItemDetailSerializer,
    KSCertificationItemCreateSerializer,
    KSCertificationItemUpdateSerializer,
    KSCertificationHistorySerializer,
    KSScanSerializer
)


class KSCertificationItemViewSet(viewsets.ModelViewSet):
    """KS 인증 품목 ViewSet"""
    queryset = KSCertificationItem.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return KSCertificationItemListSerializer
        elif self.action in ['create']:
            return KSCertificationItemCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return KSCertificationItemUpdateSerializer
        return KSCertificationItemDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 검색
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(barcode__icontains=search) |
                Q(name__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(manufacturer__icontains=search) |
                Q(ks_standard_number__icontains=search)
            )
        
        # 상태 필터
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 만료 필터
        is_expired = self.request.query_params.get('is_expired', None)
        if is_expired == 'true':
            queryset = queryset.filter(expiry_date__lt=timezone.now().date())
        elif is_expired == 'false':
            queryset = queryset.filter(
                Q(expiry_date__isnull=True) | Q(expiry_date__gte=timezone.now().date())
            )
        
        # 점검 필터
        inspection_due = self.request.query_params.get('inspection_due', None)
        if inspection_due == 'true':
            queryset = queryset.filter(
                inspection_required=True,
                next_inspection_date__lte=timezone.now().date()
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def scan(self, request, pk=None):
        """바코드 스캔 기록"""
        item = self.get_object()
        serializer = KSScanSerializer(data=request.data)
        
        if serializer.is_valid():
            # 이력 기록
            KSCertificationHistory.objects.create(
                item=item,
                action_type=KSCertificationHistory.ActionType.SCAN,
                action_description=f'바코드 스캔',
                new_value={
                    'quantity': str(serializer.validated_data.get('quantity', 1)),
                    'remarks': serializer.validated_data.get('remarks', '')
                },
                created_by=request.user
            )
            
            return Response({
                'message': '스캔 기록되었습니다.',
                'item': KSCertificationItemDetailSerializer(item).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def inspection(self, request, pk=None):
        """점검 실시"""
        item = self.get_object()
        
        item.last_inspection_date = timezone.now().date()
        
        # 다음 점검일 설정 (요청에서 받거나 기본값)
        next_date = request.data.get('next_inspection_date')
        inspection_result = request.data.get('inspection_result', '')
        
        if next_date:
            item.next_inspection_date = next_date
        
        item.updated_by = request.user
        item.save()
        
        # 이력 기록
        KSCertificationHistory.objects.create(
            item=item,
            action_type=KSCertificationHistory.ActionType.INSPECTION,
            action_description=f'점검 실시: {inspection_result}',
            new_value={
                'last_inspection_date': str(item.last_inspection_date),
                'next_inspection_date': str(item.next_inspection_date) if item.next_inspection_date else None,
                'inspection_result': inspection_result
            },
            created_by=request.user
        )
        
        return Response({
            'message': '점검이 기록되었습니다.',
            'item': KSCertificationItemDetailSerializer(item).data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """통계 정보"""
        total = KSCertificationItem.objects.count()
        active = KSCertificationItem.objects.filter(status=KSCertificationItem.Status.ACTIVE).count()
        expired = KSCertificationItem.objects.filter(
            expiry_date__lt=timezone.now().date()
        ).count()
        inspection_due = KSCertificationItem.objects.filter(
            inspection_required=True,
            next_inspection_date__lte=timezone.now().date()
        ).count()
        
        return Response({
            'total': total,
            'active': active,
            'expired': expired,
            'inspection_due': inspection_due
        })
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """품목 이력 조회"""
        item = self.get_object()
        histories = item.histories.all()[:50]  # 최근 50개
        serializer = KSCertificationHistorySerializer(histories, many=True)
        return Response(serializer.data)


class KSCertificationHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """KS 인증 이력 ViewSet (읽기 전용)"""
    queryset = KSCertificationHistory.objects.all()
    serializer_class = KSCertificationHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 품목별 필터
        item_id = self.request.query_params.get('item_id', None)
        if item_id:
            queryset = queryset.filter(item_id=item_id)
        
        # 작업 유형 필터
        action_type = self.request.query_params.get('action_type', None)
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        return queryset
