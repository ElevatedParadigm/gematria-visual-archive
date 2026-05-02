# Visual Archive Lock File Cleanup Script

## Purpose

This script monitors and handles `.git/index.lock` files during interrupted Visual Archive exports to prevent stale locks from blocking subsequent operations.

## Problem Statement

Git creates `.git/index.lock` when:
- An operation is in progress (checkout, merge, rebase, commit)
- The process is interrupted (Ctrl+C, crash, timeout)  
- System fails unexpectedly

Leftover `.git/index.lock` prevents all subsequent git operations until manually cleaned. This commonly happens with long-running Visual Archive export jobs that:
- Take extended periods to complete
- May be interrupted by system failures
- Run multiple times per hour via cron

## Solution Architecture

The cleanup script uses a **progressive strategy** approach:

### Strategy 1: Git-Based Cleanup (Preferred)
```bash
git rm --cached .git/index.lock && touch .git/index.lock
```
Respects git's internal state and is the cleanest method.

### Strategy 2: Direct File Removal
```python
os.unlink(lock_path)
```
Direct file removal when git methods fail.

### Strategy 3: Permission Handling
- `chmod +w` to make file world-writable
- Nuclear option: remove entire `.git/` directory and recreate

## File Locations

| Path | Purpose |
|------|---------|
| `visual_archive/scripts/cleanup_locks.py` | Main cleanup script |
| `visual_archive/scripts/LOCK_CLEANUP_README.md` | This documentation |
| `visual_archive/database/gematria_symbols.db` | SQLite database with journal table |

## Database Logging

All cleanup operations are logged to the internal `_lock_cleanup_journal` table in `gematria_symbols.db`:

```sql
CREATE TABLE _lock_cleanup_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    git_repo_path TEXT NOT NULL,
    output_dir_path TEXT NOT NULL,
    lock_file_path TEXT,
    action TEXT NOT NULL,        -- 'check', 'removed', 'error'
    details TEXT,
    permissions_before TEXT,
    permissions_after TEXT,
    exit_code INTEGER,
    success INTEGER NOT NULL     -- 1 for success, 0 for error
);
```

Query recent cleanup events:
```bash
sqlite3 ~/.hermes/gematria/visual_archive/database/gematria_symbols.db \
  "SELECT timestamp, action, details FROM _lock_cleanup_journal ORDER BY id DESC LIMIT 20;"
```

## Usage

### Manual Run (Before Export)

```bash
cd /home/avalonas/gematria
python3 visual_archive/scripts/cleanup_locks.py
```

Expected output (no lock file):
```
============================================================
🔍 VISUAL ARCHIVE LOCK FILE CHECK
============================================================
✅ No stale lock file found.
✅ No stale locks - export can proceed normally

✅ Cleanup completed successfully. Export can proceed.
```

Expected output (with lock file):
```
============================================================
🔍 VISUAL ARCHIVE LOCK FILE CHECK
============================================================
⚠️  Stale lock file detected: /home/avalonas/gematria/.git/objects/ab/cd/index.lock
   Age: 0.1 hours
   Hash: d41d8cd98f00b204e9800998ecf8427e
   Permissions: 644

--- Git Cleanup ---
🔧 Attempting git-based cleanup...
✅ Git cleanup completed
   📝 Logged to database (row #1)

✅ Cleanup completed successfully. Export can proceed.
```

### Integration with Visual Archive Export

Add cleanup check to the export workflow:

```python
from visual_archive.scripts.cleanup_locks import LockFileCleanup

cleanup = LockFileCleanup()
result = cleanup.run_cleanup(verbose=True)

if not result['success']:
    print(f"⚠️  Lock file issues detected. Cannot proceed with export.")
    # Optionally wait and retry, or alert operator
```

## Cron Integration

A cron job is already configured:

- **Job ID**: `4094751d4136`
- **Name**: `visual-archive-lock-cleanup`
- **Schedule**: Every 10 minutes (for testing)
- **Status**: Enabled, scheduled

Production schedule should be adjusted based on export frequency:

```python
# Production: run before each export job
schedule = "0 * * * *"  # Every hour if exports run hourly
```

## Troubleshooting

### Lock File Still Exists After Cleanup

If the lock file persists after script execution:

1. Check what process holds the file:
   ```bash
   lsof .git/index.lock
   fuser .git/index.lock
   ```

2. Force kill any stuck git processes:
   ```bash
   pkill -9 git
   ```

3. Manual cleanup (last resort):
   ```bash
   rm -f /home/avalonas/gematria/.git/index.lock
   ```

### Permission Denied Errors

If you see permission errors, the script will attempt to:
1. Change file permissions with `chmod +w`
2. Remove and recreate `.git/` directory (nuclear option)

These are logged to the database with `"action": "error"`.

## Monitoring

### Check for Recent Cleanup Events

```bash
sqlite3 ~/.hermes/gematria/visual_archive/database/gematria_symbols.db \
  "SELECT id, timestamp, action, details FROM _lock_cleanup_journal ORDER BY id DESC LIMIT 10;"
```

### Count Stale Lock Cleanup Events

```bash
sqlite3 ~/.hermes/gematria/visual_archive/database/gematria_symbols.db \
  "SELECT COUNT(*) as stale_locks_count FROM _lock_cleanup_journal WHERE action='error';"
```

If this count is increasing, investigate:
- Are export jobs timing out?
- Is there a process not cleaning up properly?
- Do you need longer intervals between exports?

## Best Practices

1. **Run before each export job**: Prevents blocking operations
2. **Monitor error rate**: Check database for persistent errors
3. **Adjust cron schedule**: Match export frequency (not too frequent)
4. **Investigate root causes**: Why are locks being created and not cleaned?

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Cleanup successful, export can proceed |
| `1` | Lock file persists after all cleanup attempts, manual intervention required |

## References

- Git documentation on index lock: https://git-scm.com/docs/git-checkout
- Cron job management guide: `~/.hermes/skills/devops/hermes-cron-job-management/`
- Gematria repository management: `~/.hermes/skills/devops/gematria-repository-management/`

- Cron job management guide: `~/.hermes/skills/devops/hermes-cron-job-management/`
- Gematria repository management: `~/.hermes/skills/devops/gematria-repository-management/`
