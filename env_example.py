"""
Environment Variables Example
Copy this file to .env and modify the values

Usage in shell:
  export $(cat .env | xargs)

Or create a .env file with:
  DEBUG=True
  SECRET_KEY=your-secret-key
  ...
"""

# Example environment variables
ENV_VARIABLES = """
# Django Settings
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production-with-secure-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL)
DATABASE_NAME=hpe_db
DATABASE_USER=hpe_user
DATABASE_PASSWORD=your-secure-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=HPE System <noreply@hpengineering.com>

# Backup Configuration
BACKUP_ENABLED=True
BACKUP_PATH=/path/to/backup/nas
BACKUP_RETENTION_DAYS=30

# Company Information
COMPANY_NAME=에이치피엔지니어링
COMPANY_LOGO=images/logo.png
"""

if __name__ == '__main__':
    print("Environment Variables for HPE System")
    print("=" * 50)
    print(ENV_VARIABLES)
    print("=" * 50)
    print("\nTo create .env file, run:")
    print("  python env_example.py > .env")
    print("\nThen edit .env with your actual values.")
