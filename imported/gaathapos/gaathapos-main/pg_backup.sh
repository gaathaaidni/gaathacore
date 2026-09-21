#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# === Configuration ===
# IMPORTANT: Change this to the absolute path where you want backups saved
BACKUP_DIR="/path/to/your/backups/postgres" 
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/gaatha_db_$TIMESTAMP.sql"

# Docker container details (matching your docker-compose.yml)
DB_CONTAINER="gaatha_db"
DB_USER="gaatha"
DB_NAME="gaathapos"
RETENTION_DAYS=7 # Keep backups for 7 days

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting PostgreSQL backup for $DB_NAME..."

# Execute pg_dump inside the container and output to the host
docker exec -t "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" -c > "$BACKUP_FILE"
echo "✅ Backup saved to $BACKUP_FILE"

# Delete backups older than RETENTION_DAYS
find "$BACKUP_DIR" -name "*.sql" -type f -mtime +$RETENTION_DAYS -delete
echo "🧹 Cleaned up backups older than $RETENTION_DAYS days."