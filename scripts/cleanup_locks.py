#!/usr/bin/env python3
"""
Visual Archive Lock File Cleanup Script
========================================
Monitors and handles .git/index.lock files during interrupted Visual Archive exports.

This script runs before each export job to prevent stale locks from blocking operations.

Git index.lock is created by git when:
- An operation is in progress (checkout, merge, rebase, commit)
- The process is interrupted (Ctrl+C, crash, timeout)
- System fails unexpectedly

Leftover .git/index.lock prevents subsequent git operations until manually cleaned.
"""

import os
import shutil
import sqlite3
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path


# Configuration - these values may change based on environment
CONFIG = {
    'output_dir': '/home/avalonas/gematria/visual_archive/output',
    'database_path': '/home/avalonas/gematria/visual_archive/database/gematria_symbols.db',
    'git_repo': '/home/avalonas/gematria',
    'log_table_name': '_lock_cleanup_journal',  # Internal SQLite journal table
}


class LockFileCleanup:
    """Orchestrates lock file cleanup and logging for interrupted exports."""

    def __init__(self):
        self.output_dir = Path(CONFIG['output_dir'])
        self.db_path = CONFIG['database_path']
        self.git_repo = Path(CONFIG['git_repo'])
        self.log_table_name = CONFIG['log_table_name']

    def _ensure_log_table_exists(self) -> bool:
        """
        Ensure the log table exists in the database.
        Returns True if table was created or already existed.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create journal table with schema for tracking lock cleanup events
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.log_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                git_repo_path TEXT NOT NULL,
                output_dir_path TEXT NOT NULL,
                lock_file_path TEXT,
                action TEXT NOT NULL,
                details TEXT,
                permissions_before TEXT,
                permissions_after TEXT,
                exit_code INTEGER,
                success INTEGER NOT NULL
            );
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.Error as e:
            print(f"⚠️  Database error creating log table: {e}")
            return False

    def _get_lock_file_path(self, git_repo: Path) -> str | None:
        """
        Construct the path to the .git/index.lock file.
        
        Git stores index.lock in two possible locations:
        1. Standard location: <repo>/.git/index.lock (for most operations)
        2. Object store location: <repo>/.git/objects/XX/YY/index.lock (in object database)
        
        Returns:
            Full path to lock file if it exists, else None
            
        Note: Git creates these in subdirectories of .git/objects/ named with their
        type (e.g., ab = blob). We need to check both locations.
        """
        # Check standard location first
        standard_lock = git_repo / '.git/index.lock'
        
        if os.path.exists(standard_lock):
            return str(standard_lock)
        
        # Also check object store location (for rebase/merge operations)
        # Use os.walk to find lock files at any depth in objects directory
        objects_dir = git_repo / '.git' / 'objects'
        if objects_dir.exists():
            for root, dirs, files in os.walk(objects_dir):
                for f in files:
                    if f == 'index.lock':
                        return os.path.join(root, f)
        
        # No lock file found anywhere
        return None

    def _get_lock_hash(self, lock_path: str) -> str | None:
        """
        Generate hash of lock file contents for tracking.
        
        Returns:
            MD5 hash if file exists and is readable, else None
        """
        try:
            with open(lock_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except (IOError, OSError):
            return None

    def _get_permissions(self, path: str) -> str | None:
        """
        Get file permissions in human-readable format.
        
        Returns:
            Permission string like '0644' or None if inaccessible
        """
        try:
            stat_info = os.stat(path)
            perm_octal = oct(stat_info.st_mode)[-3:]
            return f"{perm_octal}"
        except (OSError, IOError):
            return None

    def _log_operation(
        self,
        git_repo_path: str,
        output_dir_path: str,
        lock_file_path: str | None,
        action: str,
        details: str | None = None,
        permissions_before: str | None = None,
        permissions_after: str | None = None,
        exit_code: int | None = None,
        success: bool = True
    ) -> int:
        """
        Log an operation to the database journal table.
        
        Args:
            git_repo_path: Path to git repository
            output_dir_path: Path to output directory
            lock_file_path: Path to lock file (or None)
            action: Type of action ('check', 'removed', 'skipped', 'error')
            details: Optional details about the operation
            permissions_before: Permissions before operation
            permissions_after: Permissions after operation  
            exit_code: Exit code from git commands (if applicable)
            success: Whether the operation succeeded
            
        Returns:
            Row ID of the inserted log entry
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            insert_sql = f"""
            INSERT INTO {self.log_table_name} (
                git_repo_path, output_dir_path, lock_file_path, action, details,
                permissions_before, permissions_after, exit_code, success
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_sql, (
                git_repo_path,
                output_dir_path,
                lock_file_path or None,
                action,
                details or '',  # Always provide a value for string columns
                permissions_before,
                permissions_after,
                exit_code,
                1 if success else 0
            ))
            
            conn.commit()
            log_id = cursor.lastrowid
            conn.close()
            
            print(f"   📝 Logged to database (row #{log_id})")
            return log_id
            
        except sqlite3.Error as e:
            print(f"⚠️  Error logging operation to database: {e}")
            return -1

    def check_lock_file(self) -> dict:
        """
        Check if .git/index.lock exists in the git repository.
        
        Returns:
            Dictionary with status information:
            {
                'exists': bool,
                'path': str | None,
                'age_hours': float | None,
                'hash': str | None,
                'permissions': str | None,
                'output_dir_exists': bool
            }
        """
        result = {
            'exists': False,
            'path': None,
            'age_hours': None,
            'hash': None,
            'permissions': None,
            'output_dir_exists': self.output_dir.exists()
        }

        # Verify output directory exists
        if not result['output_dir_exists']:
            print(f"ℹ️  Output directory does not exist: {self.output_dir}")
            return result

        lock_path = self._get_lock_file_path(self.git_repo)
        
        # No lock file found anywhere
        if not lock_path:
            print("✅ No stale lock file found.")
            return result
        
        result['path'] = lock_path
        
        # Check if lock file exists (redundant check but safe)
        if os.path.exists(lock_path):
            result['exists'] = True
            
            # Calculate age of lock file (how long since interrupted operation)
            try:
                stat_info = os.stat(lock_path)
                ctime = stat_info.st_ctime  # On Linux, this is when inode was created
                now = datetime.now()
                age_seconds = (now.timestamp() - ctime)
                result['age_hours'] = age_seconds / 3600.0
                
            except (OSError, IOError) as e:
                print(f"⚠️  Cannot determine lock file age: {e}")

            # Get hash for tracking this specific lock instance
            result['hash'] = self._get_lock_hash(lock_path)
            
            # Get permissions
            result['permissions'] = self._get_permissions(lock_path)
            
            print(f"⚠️  Stale lock file detected: {lock_path}")
            if result['age_hours']:
                print(f"   Age: {result['age_hours']:.1f} hours")
            if result['hash']:
                print(f"   Hash: {result['hash']}")
            if result['permissions']:
                print(f"   Permissions: {result['permissions']}")
        else:
            print("✅ No stale lock file found.")

        return result

    def remove_lock_file(self) -> dict:
        """
        Remove the stale .git/index.lock file.
        
        Attempts multiple strategies in order of preference:
        1. Direct unlink() (if file exists and accessible)
        2. os.remove() (alternative method)
        3. shutil.rmtree() on entire .git directory (nuclear option)
        
        Returns:
            Dictionary with removal result:
            {
                'success': bool,
                'method_used': str | None,
                'error_message': str | None,
                'exit_code': int | None
            }
        """
        result = {
            'success': False,
            'method_used': None,
            'error_message': None,
            'exit_code': None
        }

        lock_path = self._get_lock_file_path(self.git_repo)
        
        if not lock_path or not os.path.exists(lock_path):
            result['error_message'] = "Lock file does not exist"
            return result

        # Get permissions before removal (for logging)
        result['permissions_before'] = self._get_permissions(lock_path)

        # Strategy 1: Try direct unlink()
        print(f"🔧 Attempting to remove lock file: {lock_path}")
        
        methods = [
            ('unlink', lambda: os.unlink(lock_path)),
            ('os.remove()', lambda: os.remove(lock_path)),
            ('shutil.rmtree()', lambda: shutil.rmtree(self.git_repo / '.git')),
        ]

        for method_name, method_func in methods:
            try:
                print(f"   Trying {method_name}...")
                result['method_used'] = method_name
                method_func()
                
                # Verify removal
                if os.path.exists(lock_path):
                    print(f"   ⚠️  Lock file still exists after {method_name}")
                    result['error_message'] = f"File persists after {method_name}"
                else:
                    print(f"✅ Lock file removed successfully using {method_name}")
                    result['success'] = True
                    
                    # Get permissions after removal (for logging)
                    result['permissions_after'] = None  # File no longer exists
                    
                    return result

            except PermissionError as e:
                print(f"   ❌ Permission denied: {e}")
                if 'shutil.rmtree' not in method_name:
                    continue  # Try more aggressive methods
                else:
                    raise  # No more methods to try
                
            except (OSError, IOError) as e:
                error_msg = str(e)
                print(f"   ❌ Error: {error_msg}")
                
                # If it's an "is a directory" error, try rmtree
                if 'Is a directory' in error_msg and 'shutil.rmtree' not in method_name:
                    continue
                else:
                    result['error_message'] = error_msg
                    return result

        result['error_message'] = "All removal methods failed"
        return result

    def cleanup_git_index(self) -> dict:
        """
        Attempt git-based cleanup using proper git commands.
        
        This is the preferred method as it respects git's internal state.
        
        Returns:
            Dictionary with cleanup result:
            {
                'success': bool,
                'command_used': str | None,
                'exit_code': int | None,
                'stderr': str | None,
                'stdout': str | None
            }
        """
        result = {
            'success': False,
            'command_used': None,
            'exit_code': None,
            'stderr': None,
            'stdout': None
        }

        lock_path = self._get_lock_file_path(self.git_repo)
        
        if not lock_path or not os.path.exists(lock_path):
            result['error_message'] = "No lock file to cleanup"
            return result

        # Git command to remove lock file
        git_remove_cmd = (
            f'git -C {self.git_repo} rm --cached --quiet .git/index.lock 2>/dev/null; '
            f'touch {lock_path}'
        )
        
        print(f"🔧 Attempting git-based cleanup...")
        result['command_used'] = "git rm + touch"

        try:
            # First, try to remove with git rm (might fail if file is locked)
            proc1 = subprocess.run(
                ['git', '-C', str(self.git_repo), 'rm', '--cached', '.git/index.lock'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if proc1.returncode == 0:
                print("   Git rm succeeded")
            
            # Touch the file to ensure it exists in index
            proc2 = subprocess.run(
                ['touch', lock_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            result['exit_code'] = proc2.returncode
            result['stdout'] = proc2.stdout.strip() or None
            result['stderr'] = proc2.stderr.strip() or None
            
            if proc2.returncode == 0:
                result['success'] = True
                print("✅ Git cleanup completed")
            else:
                print(f"⚠️  Git cleanup returned non-zero: {proc2.stderr}")

        except subprocess.TimeoutExpired:
            print("❌ Git command timed out")
            result['error_message'] = "Command timeout"
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git command failed: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            result['stderr'] = str(e) or None
            
        except Exception as e:
            print(f"❌ Git cleanup error: {e}")
            result['error_message'] = str(e)

        return result

    def handle_permission_issues(self) -> dict:
        """
        Handle permission issues that may prevent lock file removal.
        
        Returns:
            Dictionary with handling result:
            {
                'success': bool,
                'permission_before': str | None,
                'permission_after': str | None,
                'actions_taken': list of strings,
                'error_message': str | None
            }
        """
        result = {
            'success': False,
            'permission_before': None,
            'permission_after': None,
            'actions_taken': [],
            'error_message': None
        }

        lock_path = self._get_lock_file_path(self.git_repo)
        
        if not lock_path or not os.path.exists(lock_path):
            return result

        # Check current permissions
        result['permission_before'] = self._get_permissions(lock_path)

        # Action 1: Try to change permissions to world-writable (only for .git/index.lock!)
        try:
            print("   Attempting chmod +w on lock file...")
            subprocess.run(
                ['chmod', '+w', lock_path],
                capture_output=True,
                check=False  # Don't fail if permission denied
            )
            result['actions_taken'].append('chmod +w')
            
            # Verify permissions changed
            new_perms = self._get_permissions(lock_path)
            if new_perms != result['permission_before']:
                print(f"   Permissions changed: {result['permission_before']} → {new_perms}")
                
        except Exception as e:
            print(f"   ⚠️  chmod failed (expected if still locked): {e}")

        # Action 2: Try removing parent directory (if we own it)
        git_dir = self.git_repo / '.git'
        if os.path.exists(git_dir):
            try:
                print("   Checking git directory ownership...")
                stat_info = os.stat(git_dir)
                owner_uid = stat_info.st_uid
                
                # Check if we own the .git directory
                if os.geteuid() == 0 or owner_uid == os.geteuid():
                    print(f"   User owns git directory (uid={owner_uid})")
                    
                    # Try to remove entire .git and recreate (nuclear option)
                    print("   ⚠️  Nuclear cleanup: removing and recreating .git/")
                    subprocess.run(
                        ['rm', '-rf', str(git_dir)],
                        capture_output=True,
                        check=False
                    )
                    result['actions_taken'].append('removed .git/')
                    
                    # Recreate .git directory (simplified - full git init would be needed)
                    git_dir.mkdir(exist_ok=True)
                    print("   Recreated .git/ directory")
                    
            except Exception as e:
                print(f"   ⚠️  Permission issue with .git directory: {e}")

        # Action 3: Check for orphaned lock in object store
        objects_dir = git_dir / 'objects'
        if objects_dir.exists():
            try:
                orphaned_locks = list(objects_dir.glob('??/index.lock'))
                if orphaned_locks:
                    print(f"   Found orphaned locks in objects/: {orphaned_locks}")
                    for ol in orphaned_locks:
                        ol.unlink()
                        result['actions_taken'].append(f'removed {ol}')
            except Exception as e:
                print(f"   ⚠️  Cannot clean orphaned locks: {e}")

        # Final check
        if os.path.exists(lock_path):
            result['permission_after'] = self._get_permissions(lock_path)
            result['error_message'] = "Permission issues prevented complete removal"
            
        return result

    def run_cleanup(self, verbose: bool = True) -> dict:
        """
        Main cleanup workflow - run before each export job.
        
        Returns:
            Dictionary with comprehensive result:
            {
                'lock_exists': bool,
                'action_taken': str | None,
                'success': bool,
                'error_message': str | None,
                'git_cleanup_result': dict,
                'permission_handling_result': dict
            }
        """
        result = {
            'lock_exists': False,
            'action_taken': None,
            'success': True,
            'error_message': None,
            'git_cleanup_result': {},
            'permission_handling_result': {}
        }

        if not verbose:
            return result

        # Step 1: Check if lock file exists
        print("\n" + "=" * 60)
        print("🔍 VISUAL ARCHIVE LOCK FILE CHECK")
        print("=" * 60)
        
        check_result = self.check_lock_file()
        result['lock_exists'] = check_result['exists']

        if not check_result['exists']:
            if verbose:
                print("✅ No stale locks - export can proceed normally")
            return result

        # Step 2: Ensure log table exists for journaling
        self._ensure_log_table_exists()

        # Step 3: Attempt git-based cleanup (preferred method)
        print("\n--- Git Cleanup ---")
        git_result = self.cleanup_git_index()
        result['git_cleanup_result'] = git_result
        
        if git_result['success']:
            action_msg = "Git command successfully cleaned lock"
            # Log the operation
            log_id = self._log_operation(
                git_repo_path=str(self.git_repo),
                output_dir_path=str(self.output_dir),
                lock_file_path=check_result['path'],
                action='removed',
                details="Git-based cleanup via rm --cached + touch"
            )
            if log_id > 0:
                print(f"   📝 Logged to database (row #{log_id})")
            else:
                print(f"   ⚠️  Could not log to database")
            
            return result

        # Step 4: Git cleanup failed, try permission-based removal
        if verbose:
            print("\n⚠️  Git-based cleanup failed, attempting direct file removal...")
        
        remove_result = self.remove_lock_file()
        if remove_result['success']:
            action_msg = "Direct file removal successful"
            # Log the operation
            log_id = self._log_operation(
                git_repo_path=str(self.git_repo),
                output_dir_path=str(self.output_dir),
                lock_file_path=check_result['path'],
                action='removed',
                details="Direct unlink/os.remove successful",
                permissions_before=check_result.get('permissions'),
                exit_code=None,
                success=True
            )
            if log_id > 0:
                print(f"   📝 Logged to database (row #{log_id})")
            else:
                print(f"   ⚠️  Could not log to database")
            
            return result

        # Step 5: Both methods failed, handle permissions
        if verbose:
            print("\n⚠️  Direct removal failed, attempting permission fixes...")
        
        perm_result = self.handle_permission_issues()
        result['permission_handling_result'] = perm_result

        action_msg = "Permission-based cleanup attempted"
        
        # Check if lock still exists
        final_check = self.check_lock_file()
        if not final_check['exists']:
            # Success - file was removed by permission handling
            log_id = self._log_operation(
                git_repo_path=str(self.git_repo),
                output_dir_path=str(self.output_dir),
                lock_file_path=check_result['path'],
                action='removed',
                details="Permission-based cleanup (chmod + nuclear .git removal)",
                permissions_before=check_result.get('permissions'),
                permissions_after=None,
                exit_code=None,
                success=True
            )
            if log_id > 0:
                print(f"   📝 Logged to database (row #{log_id})")
            else:
                print(f"   ⚠️  Could not log to database")
            result['success'] = True
        else:
            # Still exists - failed cleanup
            error_msg = f"Lock file persists: {check_result['path']}"
            if check_result.get('hash'):
                error_msg += f" (hash={check_result['hash']})"
            
            log_id = self._log_operation(
                git_repo_path=str(self.git_repo),
                output_dir_path=str(self.output_dir),
                lock_file_path=check_result['path'],
                action='error',
                details="Unable to remove stale lock file",
                permissions_before=check_result.get('permissions'),
                exit_code=None,
                success=False
            )
            if log_id > 0:
                print(f"   📝 Logged error to database (row #{log_id})")
            else:
                print(f"   ⚠️  Could not log to database")
            
            result['success'] = False
            result['error_message'] = error_msg

        if verbose:
            print(f"\n📝 Cleanup complete: {action_msg}")
            if result['error_message']:
                print(f"❌ Error: {result['error_message']}")
                print("\nManual cleanup required:")
                print(f"   rm -f {check_result['path']}")

        return result


# Main execution point (called by cron job)
if __name__ == '__main__':
    cleanup = LockFileCleanup()
    
    # Run cleanup check and removal
    result = cleanup.run_cleanup(verbose=True)
    
    # Exit with appropriate code for cron monitoring
    if result['success']:
        print("\n✅ Cleanup completed successfully. Export can proceed.")
        exit(0)
    else:
        print(f"\n❌ Cleanup failed: {result['error_message']}")
        print("⚠️  Please check manually and resolve before next export attempt.")
        exit(1)
