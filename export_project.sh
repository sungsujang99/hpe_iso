#!/bin/bash
# HPE 프로젝트 압축 스크립트

echo "🚀 HPE 프로젝트 압축 시작..."

# 현재 날짜
DATE=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="HPE_${DATE}.tar.gz"

# 프로젝트 루트 디렉토리
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_DIR/.."

# 압축 (venv, __pycache__, .pyc, db.sqlite3, media 제외)
echo "📦 압축 중... (가상환경 및 불필요한 파일 제외)"

tar -czf "$ARCHIVE_NAME" \
    --exclude='HPE/venv' \
    --exclude='HPE/.venv' \
    --exclude='HPE/__pycache__' \
    --exclude='HPE/*/__pycache__' \
    --exclude='HPE/*/*/__pycache__' \
    --exclude='HPE/*/*/*/__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='HPE/db.sqlite3' \
    --exclude='HPE/.git' \
    --exclude='HPE/.DS_Store' \
    --exclude='HPE/logs/*.log' \
    HPE/

echo "✅ 압축 완료: $ARCHIVE_NAME"
echo "📊 파일 크기: $(du -h "$ARCHIVE_NAME" | cut -f1)"
echo ""
echo "📤 리눅스 서버로 전송:"
echo "   scp $ARCHIVE_NAME user@server-ip:/path/to/destination/"
echo ""
echo "🔓 리눅스 서버에서 압축 해제:"
echo "   tar -xzf $ARCHIVE_NAME"
echo "   cd HPE"
echo "   # 이후 DEPLOYMENT.md 가이드를 따라 설치"
