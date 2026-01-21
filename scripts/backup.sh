#!/bin/bash
#
# HPE System Daily Backup Script
# Backs up PostgreSQL database and media files to specified location
#
# Usage: ./backup.sh [backup_path]
# Recommended: Run via cron at 2:00 AM daily
#   0 2 * * * /path/to/hpe/scripts/backup.sh /path/to/backup >> /var/log/hpe_backup.log 2>&1
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_BASE="${1:-/backup/hpe}"
RETENTION_DAYS=30

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# Default database settings
DB_NAME="${DATABASE_NAME:-hpe_db}"
DB_USER="${DATABASE_USER:-hpe_user}"
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"

# Create timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE/$TIMESTAMP"

echo "=========================================="
echo "HPE System Backup"
echo "Started: $(date)"
echo "=========================================="

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo "Backup directory: $BACKUP_DIR"

# Database backup
echo ""
echo "Backing up database..."
PGPASSWORD="$DATABASE_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -F c \
    -f "$BACKUP_DIR/database.dump"

if [ $? -eq 0 ]; then
    echo "Database backup completed: $(ls -lh "$BACKUP_DIR/database.dump" | awk '{print $5}')"
else
    echo "ERROR: Database backup failed!"
    exit 1
fi

# Media files backup
echo ""
echo "Backing up media files..."
MEDIA_DIR="$PROJECT_DIR/media"
if [ -d "$MEDIA_DIR" ]; then
    tar -czf "$BACKUP_DIR/media.tar.gz" -C "$PROJECT_DIR" media
    echo "Media backup completed: $(ls -lh "$BACKUP_DIR/media.tar.gz" | awk '{print $5}')"
else
    echo "No media directory found, skipping..."
fi

# Static files backup (optional)
echo ""
echo "Backing up static files..."
STATIC_DIR="$PROJECT_DIR/staticfiles"
if [ -d "$STATIC_DIR" ]; then
    tar -czf "$BACKUP_DIR/static.tar.gz" -C "$PROJECT_DIR" staticfiles
    echo "Static backup completed: $(ls -lh "$BACKUP_DIR/static.tar.gz" | awk '{print $5}')"
else
    echo "No staticfiles directory found, skipping..."
fi

# Create backup info file
echo ""
cat > "$BACKUP_DIR/backup_info.txt" << EOF
HPE System Backup
=================
Timestamp: $TIMESTAMP
Date: $(date)
Database: $DB_NAME
Host: $DB_HOST

Files included:
- database.dump: PostgreSQL database backup
- media.tar.gz: Uploaded files (if exists)
- static.tar.gz: Static files (if exists)

To restore:
1. Database: pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME database.dump
2. Media: tar -xzf media.tar.gz -C /path/to/project/
EOF

# Clean up old backups
echo ""
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_BASE" -maxdepth 1 -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
REMAINING=$(ls -1 "$BACKUP_BASE" | wc -l)
echo "Remaining backups: $REMAINING"

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo ""
echo "=========================================="
echo "Backup completed successfully!"
echo "Location: $BACKUP_DIR"
echo "Total size: $TOTAL_SIZE"
echo "Finished: $(date)"
echo "=========================================="
