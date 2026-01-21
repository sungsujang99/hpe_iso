"""
Account Views
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone

from .models import User, LoginHistory, ActivityLog, Department
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, LoginSerializer, LoginHistorySerializer,
    ActivityLogSerializer, SignatureUploadSerializer, DepartmentSerializer
)
from .permissions import IsAdminRole, IsManagerOrAdmin


def get_client_ip(request):
    """클라이언트 IP 주소 추출"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT 토큰 발급 (로그인)"""
    
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Update user last login info
            user.last_login = timezone.now()
            user.last_login_ip = ip_address
            user.save(update_fields=['last_login', 'last_login_ip'])
            
            # Record login history
            LoginHistory.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            })
            
        except Exception as e:
            # Record failed login attempt
            username = request.data.get('username', '')
            try:
                user = User.objects.get(username=username)
                LoginHistory.objects.create(
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason=str(e)
                )
            except User.DoesNotExist:
                pass
            
            raise


class UserViewSet(viewsets.ModelViewSet):
    """사용자 관리 ViewSet"""
    
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminRole()]
        elif self.action in ['update', 'partial_update']:
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return User.objects.all()
        elif user.is_manager:
            # 매니저는 같은 부서 사용자만 조회 가능
            return User.objects.filter(department=user.department)
        else:
            # 일반 사용자는 본인만
            return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """현재 로그인한 사용자 정보"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """비밀번호 변경"""
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': '현재 비밀번호가 올바르지 않습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        update_session_auth_hash(request, user)
        
        return Response({'message': '비밀번호가 성공적으로 변경되었습니다.'})
    
    @action(detail=False, methods=['post'])
    def upload_signature(self, request):
        """서명 이미지 업로드"""
        serializer = SignatureUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.signature_image = serializer.validated_data['signature']
        user.save(update_fields=['signature_image'])
        
        return Response({
            'message': '서명이 등록되었습니다.',
            'signature_url': user.signature_image.url if user.signature_image else None
        })
    
    @action(detail=False, methods=['get'])
    def login_history(self, request):
        """로그인 이력 조회"""
        history = LoginHistory.objects.filter(user=request.user)[:50]
        serializer = LoginHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminRole])
    def all_activity_logs(self, request):
        """전체 활동 로그 조회 (관리자 전용)"""
        logs = ActivityLog.objects.select_related('user').all()[:200]
        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data)


class LogoutView(generics.GenericAPIView):
    """로그아웃 (토큰 무효화)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': '로그아웃되었습니다.'})
        except Exception:
            return Response({'message': '로그아웃되었습니다.'})


class ReviewerListView(generics.ListAPIView):
    """검토자 목록 조회 (문서 승인 요청 시 사용)"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(
            role__in=['admin', 'manager'],
            is_active=True
        ).order_by('department', 'last_name')


class ApproverListView(generics.ListAPIView):
    """최종 승인자 목록 조회"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(
            role='admin',
            is_active=True
        ).order_by('last_name')


class DepartmentViewSet(viewsets.ModelViewSet):
    """부서 관리 ViewSet"""
    
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminRole()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 활성화된 부서만 조회 (필터링 옵션)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset.order_by('name')
