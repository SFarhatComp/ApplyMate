#!/usr/bin/env python3
import os
import sys
import shutil
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def cleanup_cover_letters(days_old=7, dry_run=True):
    """
    Clean up cover letter files older than the specified number of days.
    
    Args:
        days_old (int): Remove files older than this many days
        dry_run (bool): If True, only print what would be deleted without actually deleting
    """
    cover_letter_dir = "data/cover_letters"
    
    if not os.path.exists(cover_letter_dir):
        print(f"Cover letter directory not found: {cover_letter_dir}")
        return
    
    # Calculate the cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    # Count files
    total_files = 0
    deleted_files = 0
    
    print(f"{'[DRY RUN] ' if dry_run else ''}Cleaning up cover letters older than {days_old} days ({cutoff_date.strftime('%Y-%m-%d')})")
    
    for filename in os.listdir(cover_letter_dir):
        file_path = os.path.join(cover_letter_dir, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        total_files += 1
        
        # Get file modification time
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # Check if file is older than cutoff date
        if file_time < cutoff_date:
            if dry_run:
                print(f"Would delete: {filename} (modified: {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                try:
                    os.remove(file_path)
                    print(f"Deleted: {filename} (modified: {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
                except Exception as e:
                    print(f"Error deleting {filename}: {str(e)}")
                    continue
            
            deleted_files += 1
    
    print(f"\nSummary:")
    print(f"Total files: {total_files}")
    print(f"{'Would delete' if dry_run else 'Deleted'}: {deleted_files} files")
    
    if dry_run and deleted_files > 0:
        print("\nThis was a dry run. To actually delete files, run with --force")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up old cover letter files")
    parser.add_argument("--days", type=int, default=7, help="Delete files older than this many days")
    parser.add_argument("--force", action="store_true", help="Actually delete files (without this flag, it's a dry run)")
    
    args = parser.parse_args()
    
    cleanup_cover_letters(days_old=args.days, dry_run=not args.force) 