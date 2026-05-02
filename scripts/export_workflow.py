#!/usr/bin/env python3
"""
Visual Archive Export Workflow
===============================
Core script for exporting symbol states to git commits with wikilinks, ASCII art, and metadata.

Architecture:
  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
  │ Database Query  │───▶ │ Firecrawl API   │───▶ │ Git Commit &    │
  │ (which symbols) │     │ (scrape sources) │     │ Push to remote) │
  └─────────────────┘     └─────────────────┘     └─────────────────┘

This orchestrates the full export pipeline with proper error handling and progress tracking.
"""

import sqlite3
import subprocess
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# Configuration - these values may change based on environment
CONFIG = {
    'output_dir': '/home/avalonas/gematria/visual_archive/output',
    'database_path': '/home/avalonas/gematria/visual_archive/database/gematria_symbols.db',
    'git_repo': '/home/avalonas/gematria',
    'batch_size': 3,  # Process this many symbols per commit
    'enable_firecrawl': True,  # Use Firecrawl for scraping sources
    'firecrawl_api_url': 'http://localhost:3002/api/v1/scrape'  # Local Docker instance


class VisualArchiveExporter:
    """Orchestrates the full export workflow from database to git commits."""

    def __init__(self):
        self.output_dir = Path(CONFIG['output_dir'])
        self.db_path = CONFIG['database_path']
        self.git_repo = Path(CONFIG['git_repo'])
        self.batch_size = CONFIG['batch_size']
        
    def get_pending_symbols(self) -> List[Dict]:
        """
        Get symbols that need exporting (not recently processed).
        Returns: List of symbol data with their current state
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Find symbols not yet exported or last_exported_at is old
            query = """
            SELECT cs.*, ts.export_count, ts.last_exported_at, ts.last_trigger_terms
            FROM core_symbols cs
            LEFT JOIN symbol_state ts ON cs.symbol_value = ts.symbol_value
            WHERE 
                (ts.last_exported_at IS NULL OR date(ts.last_exported_at) < date('now', '-30 days'))
            ORDER BY cs.energy_pattern DESC, cs.symbol_value ASC
            LIMIT %d
            """ % self.batch_size
            
            cursor = conn.execute(query)
            symbols = [dict(row) for row in cursor.fetchall()]
            
            return symbols
        finally:
            conn.close()

    def scrape_source_materials(self, query_context: str) -> Optional[Dict]:
        """
        Scrape relevant source materials using Firecrawl API.
        query_context: Keywords or topics to search for related content
        """
        if not CONFIG['enable_firecrawl']:
            return None
            
        try:
            # Use local Firecrawl API (Docker instance on localhost:3002)
            payload = {
                'query': query_context,
                'max_pages': 5
            }
            
            import urllib.request
            req = urllib.request.Request(
                CONFIG['firecrawl_api_url'],
                data=json.dumps(payload).encode(),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                
            return {
                'success': True,
                'data': result.get('data', []),
                'pages_scraped': len(result.get('data', []))
            }
            
        except Exception as e:
            print(f"Firecrawl scrape failed (optional): {e}")
            return None

    def generate_wikilink(self, symbol_name: str, output_filename: str) -> str:
        """
        Generate a wikilink connecting to Obsidian vault.
        Format: [[symbol-name→related-concept]]
        
        Example: [[124-Bridge→666-Wholeness]]
        """
        # Convert symbol name to clean format
        clean_name = symbol_name.replace('/', '-').replace('\\', '-')
        clean_name = clean_name.strip()
        
        wikilink = f"[[{clean_name}→Output:{output_filename}]]"
        return wikilink

    def create_commit(self, symbols: List[Dict], scrape_result: Optional[Dict] = None) -> Tuple[str, bool]:
        """
        Create a git commit with the batch of symbols.
        Returns: (commit_message, success)
        """
        try:
            # Generate unique commit ID from symbol states
            state_hash = hashlib.md5()
            for sym in symbols:
                state_hash.update(f"{sym['symbol_value']}:{sym['name']}".encode())
            commit_id = f"va-{state_hash.hexdigest()[:8]}"
            
            # Gather all content for this commit
            markdown_content = []
            
            # Symbol header with ASCII art pattern
            header_line = "─" * 60
            markdown_content.append(header_line)
            markdown_content.append(f"# Visual Archive Export: {commit_id}")
            markdown_content.append(f"**Symbols processed**: {[s['symbol_value'] for s in symbols]}")
            markdown_content.append(f"**Exported**: {datetime.now().isoformat()}")
            markdown_content.append("")
            
            # Add scraped content if available
            if scrape_result and scrape_result['success']:
                markdown_content.append("## Source Context")
                for page in scrape_result['data'][:3]:  # First 3 pages
                    md_page = page.get('markdown', '')[:1000]  # Limit length
                    markdown_content.append(f"- `{page.get('url', 'N/A')}`")
                    if md_page:
                        markdown_content.append(md_page)
                markdown_content.append("")
            
            # Add ASCII pattern visualization for each symbol
            for sym in symbols:
                markdown_content.append("─" * 40)
                markdown_content.append(f"**{sym['symbol_value']}: {sym['name']}**")
                
                # Use energy_pattern as ASCII bar graph if available
                if 'energy_pattern' in sym and sym['energy_pattern']:
                    # Clean up pattern and make it more compact
                    clean_pattern = sym['energy_pattern'].replace('\n', ' ').strip()
                    markdown_content.append(f"Pattern: `{clean_pattern}`")
                
                markdown_content.append("")
            
            footer_line = "─" * 60
            wikilink = self.generate_wikilink(symbols[0]['name'], 'export.log') if symbols else ''
            markdown_content.append(footer_line)
            
            return_value = True
            
        except Exception as e:
            print(f"Error creating commit content: {e}")
            return False

    def run_git_commit(self, commit_id: str, content: str) -> bool:
        """
        Stage files and create a git commit.
        """
        try:
            # Create the commit file in output directory
            commit_file = self.output_dir / f"{commit_id}.md"
            
            with open(commit_file, 'w') as f:
                f.write(content)
            
            # Add to staging area
            subprocess.run(
                ['git', '-C', str(self.git_repo), 'add', str(commit_file)],
                check=True,
                capture_output=True
            )
            
            # Create commit
            result = subprocess.run(
                ['git', '-C', str(self.git_repo), 'commit', '--message', f"Visual Archive: {commit_id}"],
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
            
        except subprocess.CalledProcessError as e:
            print(f"Git commit failed: {e.stderr}")
            return False
        except Exception as e:
            print(f"Git error: {e}")
            return False

    def update_database_state(self, symbol_value: int, status: str, output_path: Optional[str] = None):
        """
        Update the symbol's export state in the database.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            query = """
            INSERT OR REPLACE INTO symbol_state (
                symbol_value, export_count, last_exported_at, 
                status, output_path
            ) VALUES (?, ?, ?, ?, ?)
            """
            
            cursor = conn.execute(query, (
                symbol_value,
                1,  # Increment export count (simplified)
                datetime.now(),
                status,
                output_path
            ))
            conn.commit()
        finally:
            conn.close()

    def run_export_job(self) -> Tuple[List[Dict], bool]:
        """
        Main export pipeline for a batch of symbols.
        Returns: (list of completed exports, overall success)
        """
        print(f"\n📦 Starting Visual Archive export...")
        
        # Get pending symbols
        symbols_to_export = self.get_pending_symbols()
        
        if not symbols_to_export:
            print("No pending symbols to export.")
            return [], True
        
        print(f"Found {len(symbols_to_export)} pending symbol(s): {[s['symbol_value'] for s in symbols_to_export]}")
        
        # Create initial commit file
        batch_id = datetime.now().strftime("%Y%m%d%H%M%S")
        initial_commit = self.git_repo / f"visual_archive_{batch_id}.md"
        
        with open(initial_commit, 'w') as f:
            f.write("# Visual Archive - Batch Export\n")
            
            for sym in symbols_to_export:
                # Generate content for this symbol
                markdown_content = [f"**Symbol**: {sym['symbol_value']} ({sym['name']})"]
                
                if 'energy_pattern' in sym:
                    markdown_content.append(f"Energy pattern: `{sym['energy_pattern']}`")
                
                markdown_content.append("")
                
                # Generate wikilink to Obsidian vault
                wikilink = self.generate_wikilink(sym['name'], batch_id)
                markdown_content.append(f"Wikilink: {wikilink}")
            
            f.write('\n'.join(markdown_content))
        
        try:
            # Add initial commit files to git staging area
            subprocess.run(
                ['git', '-C', str(self.git_repo), 'add', str(initial_commit)],
                check=True,
                capture_output=True
            )
            
            # Create initial commit
            result = subprocess.run(
                ['git', '-C', str(self.git_repo), 'commit', '-m', f"Visual Archive: batch {batch_id}"],
                capture_output=True,
                text=True
            )
            
            print(f"✅ Initial commit created: {initial_commit.name}")
            return [dict(sym) for sym in symbols_to_export], True
            
        except subprocess.CalledProcessError as e:
            print(f"Git commit error: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            return [], False


# Main execution point (called by cron job)
if __name__ == '__main__':
    exporter = VisualArchiveExporter()
    
    # Run the export workflow
    exports, success = exporter.run_export_job()
    
    if exports:
        print(f"\n📦 Export complete! Processed {len(exports)} symbols.")
    else:
        print("\n⚠️  No exports completed in this run.")
