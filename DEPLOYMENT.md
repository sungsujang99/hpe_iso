# HPE 시스템 배포 가이드

## 🚀 새로운 리눅스 서버에 배포하기

### 사전 요구사항
- Python 3.10 이상
- PostgreSQL (선택사항, 기본은 SQLite)
- Git

### 1. 코드 가져오기

#### 방법 A: Git 사용 (추천)
```bash
# GitHub에 업로드된 경우
git clone <repository-url>
cd HPE

# 또는 로컬 저장소에서 복사
# Mac에서 tar로 압축 후 전송
```

#### 방법 B: 직접 복사
```bash
# Mac에서 리눅스로 rsync
rsync -avz --exclude='venv' --exclude='*.pyc' --exclude='__pycache__' \
  ~/Documents/coding/HPE/ user@linux-server:/path/to/HPE/
```

### 2. 가상환경 생성 및 의존성 설치

```bash
# 프로젝트 디렉토리로 이동
cd /path/to/HPE

# Python 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 설정

```bash
# .env 파일 생성 (env_example.py 참고)
cp env_example.py .env

# .env 파일 편집
nano .env
```

필요한 환경 변수:
```python
SECRET_KEY='새로운-시크릿-키-생성'
DEBUG=False
ALLOWED_HOSTS='서버IP,도메인'
DATABASE_URL='postgresql://user:password@localhost/hpe_db'  # PostgreSQL 사용 시
```

### 4. 데이터베이스 설정

#### SQLite 사용 (개발/테스트)
```bash
# 마이그레이션 실행
python manage.py migrate

# 초기 데이터 로드
python manage.py shell < scripts/init_data.py
python manage.py shell < scripts/add_iso_procedures.py
python manage.py shell < scripts/add_iso14001_procedures.py

# 관리자 계정 생성
python manage.py createsuperuser
```

#### PostgreSQL 사용 (운영)
```bash
# PostgreSQL 설치
sudo apt update
sudo apt install postgresql postgresql-contrib

# 데이터베이스 생성
sudo -u postgres psql
CREATE DATABASE hpe_db;
CREATE USER hpe_user WITH PASSWORD 'your_password';
ALTER ROLE hpe_user SET client_encoding TO 'utf8';
ALTER ROLE hpe_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE hpe_user SET timezone TO 'Asia/Seoul';
GRANT ALL PRIVILEGES ON DATABASE hpe_db TO hpe_user;
\q

# settings/production.py에서 DATABASE 설정 확인

# 마이그레이션 실행
python manage.py migrate

# 초기 데이터 로드
python manage.py shell < scripts/init_data.py
python manage.py shell < scripts/add_iso_procedures.py
python manage.py shell < scripts/add_iso14001_procedures.py
```

### 5. 정적 파일 수집

```bash
python manage.py collectstatic --noinput
```

### 6. 한글 폰트 설치 (PDF 생성용)

```bash
# Ubuntu/Debian
sudo apt install fonts-nanum fonts-nanum-coding

# CentOS/RHEL
sudo yum install google-noto-sans-cjk-fonts

# 폰트 캐시 업데이트
fc-cache -fv
```

### 7. Celery 설정 (비동기 작업)

```bash
# Redis 설치 (Celery 브로커)
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Celery 워커 실행
celery -A config worker -l info &

# Celery Beat 실행 (스케줄 작업)
celery -A config beat -l info &
```

### 8. 서버 실행

#### 개발 서버 (테스트용)
```bash
python manage.py runserver 0.0.0.0:8000
```

#### 운영 서버 (Gunicorn 사용)
```bash
# Gunicorn 설치 (이미 requirements.txt에 포함)
pip install gunicorn

# Gunicorn 실행
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --daemon

# 또는 systemd 서비스로 등록
sudo nano /etc/systemd/system/hpe.service
```

**systemd 서비스 파일 예시:**
```ini
[Unit]
Description=HPE Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/HPE
Environment="PATH=/path/to/HPE/venv/bin"
ExecStart=/path/to/HPE/venv/bin/gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl start hpe
sudo systemctl enable hpe
sudo systemctl status hpe
```

### 9. Nginx 설정 (리버스 프록시)

```bash
# Nginx 설치
sudo apt install nginx

# Nginx 설정 파일 생성
sudo nano /etc/nginx/sites-available/hpe
```

**Nginx 설정 예시:**
```nginx
server {
    listen 80;
    server_name your-domain.com 192.168.1.100;

    client_max_body_size 100M;

    location /static/ {
        alias /path/to/HPE/static/;
    }

    location /media/ {
        alias /path/to/HPE/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 120;
        proxy_send_timeout 120;
        proxy_read_timeout 120;
    }
}
```

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/hpe /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. 방화벽 설정

```bash
# UFW 사용 시
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp  # 개발 서버 직접 접근 시
sudo ufw enable

# firewalld 사용 시
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### 11. 자동 백업 설정

```bash
# 백업 스크립트 실행 권한 부여
chmod +x scripts/backup.sh

# Cron 작업 등록 (매일 새벽 2시)
crontab -e

# 다음 라인 추가
0 2 * * * /path/to/HPE/scripts/backup.sh
```

## 🔧 트러블슈팅

### 문제 1: 한글이 깨져서 나옴
```bash
# 한글 로케일 설치
sudo apt install language-pack-ko
sudo locale-gen ko_KR.UTF-8
sudo update-locale LANG=ko_KR.UTF-8

# 한글 폰트 재설치
sudo apt install --reinstall fonts-nanum
```

### 문제 2: PDF 생성 실패
```bash
# WeasyPrint 의존성 설치
sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

### 문제 3: Permission Denied
```bash
# 디렉토리 권한 설정
sudo chown -R www-data:www-data /path/to/HPE
sudo chmod -R 755 /path/to/HPE
sudo chmod -R 775 /path/to/HPE/media
sudo chmod -R 775 /path/to/HPE/logs
```

### 문제 4: 정적 파일이 로드되지 않음
```bash
# collectstatic 재실행
python manage.py collectstatic --clear --noinput

# Nginx 설정 확인
sudo nginx -t
sudo systemctl restart nginx
```

## 📊 서버 모니터링

### 로그 확인
```bash
# Django 로그
tail -f logs/hpe.log

# Nginx 로그
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Gunicorn 로그
journalctl -u hpe -f

# Celery 로그
tail -f celery_worker.log
```

### 서버 상태 확인
```bash
# HPE 서비스 상태
sudo systemctl status hpe

# Nginx 상태
sudo systemctl status nginx

# Redis 상태
sudo systemctl status redis

# 프로세스 확인
ps aux | grep gunicorn
ps aux | grep celery
```

## 🔄 업데이트 프로세스

```bash
# 코드 업데이트
cd /path/to/HPE
git pull origin master

# 가상환경 활성화
source venv/bin/activate

# 의존성 업데이트
pip install -r requirements.txt --upgrade

# 데이터베이스 마이그레이션
python manage.py migrate

# 정적 파일 재수집
python manage.py collectstatic --noinput

# 서비스 재시작
sudo systemctl restart hpe
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

## 🔐 보안 권장사항

1. **DEBUG=False** 설정
2. **SECRET_KEY** 변경
3. **ALLOWED_HOSTS** 설정
4. **HTTPS** 사용 (Let's Encrypt)
5. **데이터베이스 백업** 자동화
6. **방화벽** 설정
7. **정기적인 보안 업데이트**

## 📞 지원

문제가 발생하면 다음을 확인하세요:
- 로그 파일: `logs/hpe.log`, `logs/audit.log`
- Django 설정: `config/settings/production.py`
- 서버 상태: `sudo systemctl status hpe`
