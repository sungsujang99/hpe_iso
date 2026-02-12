"""
Account Serializers
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User, LoginHistory, ActivityLog, Department, Department


def validate_password_min_length(value):
    """비밀번호 최소 길이 검증 (4자리 이상)"""
    if len(value) < 4:
        raise ValidationError('비밀번호는 최소 4자리 이상이어야 합니다.')
    return value


class DepartmentSerializer(serializers.ModelSerializer):
    """부서 시리얼라이저"""
    
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'description', 'is_active', 'member_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """사용자 기본 정보 시리얼라이저"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    display_role = serializers.CharField(read_only=True)
    department_name = serializers.SerializerMethodField()
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else ''
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'employee_id', 'department', 'department_name', 'position', 'phone',
            'is_department_head', 'role', 'display_role', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'role', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """사용자 생성 시리얼라이저"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password_min_length])
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.CharField(read_only=True)  # 역할은 자동 설정됨
    
    class Meta:
        model = User
        fields = [
            'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'employee_id',
            'department', 'position', 'phone', 'is_department_head', 'role', 'email',
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': '비밀번호가 일치하지 않습니다.'})
        
        # 부서가 없으면 부서장 설정 불가
        if attrs.get('is_department_head') and not attrs.get('department'):
            raise serializers.ValidationError({'is_department_head': '부서를 먼저 선택해주세요.'})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # role은 save() 메서드에서 자동 설정됨
        validated_data.pop('role', None)
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """사용자 정보 수정 시리얼라이저"""
    role = serializers.CharField(read_only=True)  # 역할은 자동 설정됨
    username = serializers.CharField(required=False)  # 아이디 수정 가능
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password_min_length])  # 비밀번호 변경 (선택)
    password_confirm = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'department',
            'position', 'phone', 'is_department_head', 'role',
        ]
    
    def validate(self, attrs):
        # 비밀번호 변경 시 확인
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError({'password_confirm': '비밀번호가 일치하지 않습니다.'})
        
        # 부서가 없으면 부서장 설정 불가
        if attrs.get('is_department_head') and not attrs.get('department'):
            raise serializers.ValidationError({'is_department_head': '부서를 먼저 선택해주세요.'})
        
        return attrs
    
    def update(self, instance, validated_data):
        # 비밀번호 변경
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirm', None)
        
        # 아이디 변경
        username = validated_data.pop('username', None)
        if username and username != instance.username:
            # 아이디 중복 체크
            if User.objects.filter(username=username).exclude(id=instance.id).exists():
                raise serializers.ValidationError({'username': '이미 사용 중인 아이디입니다.'})
            instance.username = username
        
        # 나머지 필드 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # 비밀번호 변경
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """비밀번호 변경 시리얼라이저"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password_min_length])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': '새 비밀번호가 일치하지 않습니다.'})
        return attrs


class LoginSerializer(serializers.Serializer):
    """로그인 시리얼라이저"""
    
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            if not user:
                raise serializers.ValidationError('아이디 또는 비밀번호가 올바르지 않습니다.')
            if not user.is_active:
                raise serializers.ValidationError('비활성화된 계정입니다.')
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError('아이디와 비밀번호를 모두 입력해주세요.')
        
        return attrs


class LoginHistorySerializer(serializers.ModelSerializer):
    """로그인 이력 시리얼라이저"""
    
    class Meta:
        model = LoginHistory
        fields = ['id', 'login_at', 'ip_address', 'success', 'failure_reason']


class ActivityLogSerializer(serializers.ModelSerializer):
    """활동 로그 시리얼라이저"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_name', 'action', 'action_display',
            'model_name', 'object_id', 'object_repr', 'changes',
            'ip_address', 'created_at',
        ]


class SignatureUploadSerializer(serializers.Serializer):
    """서명 이미지 업로드 시리얼라이저"""
    
    signature = serializers.ImageField()
    
    def validate_signature(self, value):
        # 파일 크기 제한 (1MB)
        if value.size > 1024 * 1024:
            raise serializers.ValidationError('서명 이미지는 1MB를 초과할 수 없습니다.')
        
        # 이미지 형식 검증
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError('PNG 또는 JPEG 형식만 허용됩니다.')
        
        return value
