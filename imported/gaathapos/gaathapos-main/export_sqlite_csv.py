import sqlite3
import csv
import os
from datetime import datetime

DB_PATH = 'instance/app.db'

def export_to_csv():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}")
        print("Please ensure you are running this script from the project root.")
        return

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"backups/sqlite_csv_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all table names in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    for table_name in tables:
        # Skip internal SQLite tables and Alembic migration tracking tables
        if table_name.startswith('sqlite_') or table_name == 'alembic_version':
            continue
            
        print(f"Exporting table: {table_name}...")
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Get column headers
        column_names = [description[0] for description in cursor.description]
        
        csv_file_path = os.path.join(backup_dir, f"{table_name}.csv")
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(column_names)  # Write headers
            csv_writer.writerows(rows)         # Write data
            
    conn.close()
    print(f"\n✅ Backup completed successfully! Files saved in: {backup_dir}")

if __name__ == '__main__':
    export_to_csv()