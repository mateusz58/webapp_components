#!/usr/bin/env python3
"""
Database Backup Tool
Creates backups of the Component Management System database
"""
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path
import argparse

def create_backup(host, port, database, username, password, backup_dir, schema="component_app"):
    """Create a database backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"component_db_backup_{timestamp}.sql"
    backup_path = Path(backup_dir) / backup_filename
    
    # Ensure backup directory exists
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🗄️  Creating database backup...")
    print(f"📁 Backup file: {backup_path}")
    print(f"🏠 Host: {host}:{port}")
    print(f"🗃️  Database: {database}")
    print(f"📊 Schema: {schema}")
    
    # pg_dump command
    cmd = [
        "pg_dump",
        f"--host={host}",
        f"--port={port}",
        f"--username={username}",
        f"--dbname={database}",
        f"--schema={schema}",
        "--verbose",
        "--clean",
        "--no-owner",
        "--no-privileges",
        "--format=plain",
        f"--file={backup_path}"
    ]
    
    # Set password via environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    
    try:
        print("⏳ Running pg_dump...")
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if backup file was created and has content
        if backup_path.exists() and backup_path.stat().st_size > 0:
            file_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ Backup created successfully!")
            print(f"📏 File size: {file_size:.2f} MB")
            print(f"📍 Location: {backup_path}")
            
            # Create a symlink to latest backup
            latest_path = backup_path.parent / "latest_backup.sql"
            if latest_path.exists():
                latest_path.unlink()
            latest_path.symlink_to(backup_filename)
            
            return str(backup_path)
        else:
            print("❌ Backup file not created or is empty")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ pg_dump failed with exit code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return None
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        return None

def restore_backup(backup_file, host, port, database, username, password):
    """Restore from a backup file"""
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    print(f"🔄 Restoring database from backup...")
    print(f"📁 Backup file: {backup_path}")
    print(f"🏠 Target: {host}:{port}/{database}")
    
    # Confirm restoration
    response = input("⚠️  This will overwrite existing data. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("🛑 Restoration cancelled")
        return False
    
    # psql command for restoration
    cmd = [
        "psql",
        f"--host={host}",
        f"--port={port}",
        f"--username={username}",
        f"--dbname={database}",
        f"--file={backup_path}"
    ]
    
    # Set password via environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    
    try:
        print("⏳ Running psql...")
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✅ Database restored successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Restoration failed with exit code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Restoration failed: {str(e)}")
        return False

def list_backups(backup_dir):
    """List available backups"""
    backup_path = Path(backup_dir)
    
    if not backup_path.exists():
        print(f"📁 Backup directory not found: {backup_dir}")
        return
    
    backup_files = list(backup_path.glob("component_db_backup_*.sql"))
    
    if not backup_files:
        print("📁 No backup files found")
        return
    
    print(f"📁 Available backups in {backup_dir}:")
    print("-" * 60)
    
    # Sort by modification time (newest first)
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for backup_file in backup_files:
        stat = backup_file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        
        print(f"📄 {backup_file.name}")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   Created: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

def main():
    """Main backup function"""
    parser = argparse.ArgumentParser(description="Database Backup Tool")
    parser.add_argument('action', choices=['backup', 'restore', 'list'], help='Action to perform')
    parser.add_argument('--host', default='192.168.100.35', help='Database host')
    parser.add_argument('--port', default='5432', help='Database port')
    parser.add_argument('--database', default='promo_database', help='Database name')
    parser.add_argument('--username', default='component_user', help='Database username')
    parser.add_argument('--password', default='component_app_123', help='Database password')
    parser.add_argument('--schema', default='component_app', help='Database schema')
    parser.add_argument('--backup-dir', default='backups', help='Backup directory')
    parser.add_argument('--file', help='Backup file (for restore action)')
    
    args = parser.parse_args()
    
    print("💾 Component Management System - Database Backup Tool")
    print("=" * 60)
    
    if args.action == 'backup':
        backup_file = create_backup(
            args.host, args.port, args.database, 
            args.username, args.password, args.backup_dir, args.schema
        )
        return 0 if backup_file else 1
        
    elif args.action == 'restore':
        if not args.file:
            print("❌ --file argument required for restore action")
            return 1
        
        success = restore_backup(
            args.file, args.host, args.port, args.database,
            args.username, args.password
        )
        return 0 if success else 1
        
    elif args.action == 'list':
        list_backups(args.backup_dir)
        return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main())