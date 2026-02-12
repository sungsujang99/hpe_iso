#!/bin/bash
# 리눅스 서버 배포 스크립트 (HPE 프로젝트)
# 사용법: ./scripts/deploy_server.sh
# 또는: bash scripts/deploy_server.sh

set -e

# 프로젝트 경로 (서버 기준, 필요시 수정)
PROJECT_DIR="${HPE_PROJECT_DIR:-$HOME/hpe_iso}"
cd "$PROJECT_DIR"

echo "=========================================="
echo "HPE 서버 배포 시작: $PROJECT_DIR"
echo "=========================================="

# 1. 최신 코드 가져오기
echo "[1/5] git pull..."
git fetch origin
git pull origin master

# 2. Python 경로 (venv 우선)
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
    echo "[2/5] venv 사용: $PYTHON"
else
    PYTHON="python3"
    echo "[2/5] 시스템 Python 사용"
fi

# logs 디렉토리 생성
mkdir -p logs

# 3. 마이그레이션
echo "[3/5] migrate..."
$PYTHON manage.py migrate --noinput

# 4. 템플릿 동기화 (sync_templates 커맨드 있으면 실행)
if $PYTHON manage.py help 2>/dev/null | grep -q sync_templates; then
    echo "[4/5] sync_templates..."
    $PYTHON manage.py sync_templates
else
    echo "[4/5] sync_templates 없음 (건너뜀)"
fi

# 5. 서버 재시작
echo "[5/5] 서버 재시작..."
pkill -f "manage.py runserver" 2>/dev/null || true
sleep 2
nohup $PYTHON manage.py runserver 0.0.0.0:8000 > logs/server.log 2>&1 &
# 또는 gunicorn 사용 시:
# pkill -f gunicorn 2>/dev/null || true
# sleep 2
# nohup gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 >> logs/server.log 2>&1 &

sleep 2
echo ""
echo "=========================================="
echo "배포 완료!"
echo "서버 로그: tail -f $PROJECT_DIR/logs/server.log"
echo "=========================================="
