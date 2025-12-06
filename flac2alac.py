#!/usr/bin/env python3
"""
FLAC to ALAC Batch Converter with Database Tracking
Scans artist folders and converts FLAC files to ALAC (.m4a)
"""

import os
import sys
import subprocess
import hashlib
import sqlite3
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from getpass import getpass
from tqdm import tqdm
import questionary
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
import signal

# Configure rich console
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flac2alac.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ConversionRecord:
    """Record of a completed conversion."""
    flac_path: str
    alac_path: str
    flac_hash: str
    alac_hash: str
    flac_size: int
    alac_size: int
    artist: str
    album: str
    track: str
    conversion_date: str
    verified: bool = True

class ConversionTracker:
    """SQLite database to track conversion progress."""
    
    def __init__(self, db_path: str = "flac2alac.db"):
        self.db_path = Path(db_path)
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create conversions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flac_path TEXT UNIQUE NOT NULL,
                    alac_path TEXT NOT NULL,
                    flac_hash TEXT NOT NULL,
                    alac_hash TEXT NOT NULL,
                    flac_size INTEGER NOT NULL,
                    alac_size INTEGER NOT NULL,
                    artist TEXT,
                    album TEXT,
                    track TEXT,
                    conversion_date TEXT NOT NULL,
                    verified BOOLEAN DEFAULT 1,
                    skip_count INTEGER DEFAULT 0,
                    last_checked TEXT
                )
            ''')
            
            # Create settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Create statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    date TEXT PRIMARY KEY,
                    files_converted INTEGER DEFAULT 0,
                    bytes_saved INTEGER DEFAULT 0,
                    total_time INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
    
    def is_converted(self, flac_path: str) -> bool:
        """Check if a FLAC file has already been converted."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM conversions WHERE flac_path = ? AND verified = 1",
                (str(flac_path),)
            )
            return cursor.fetchone()[0] > 0
    
    def record_conversion(self, record: ConversionRecord):
        """Record a successful conversion."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if this file was previously marked to skip
            cursor.execute(
                "SELECT skip_count FROM conversions WHERE flac_path = ?",
                (record.flac_path,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute('''
                    UPDATE conversions SET
                        alac_path = ?,
                        flac_hash = ?,
                        alac_hash = ?,
                        flac_size = ?,
                        alac_size = ?,
                        artist = ?,
                        album = ?,
                        track = ?,
                        conversion_date = ?,
                        verified = ?,
                        last_checked = ?
                    WHERE flac_path = ?
                ''', (
                    record.alac_path,
                    record.flac_hash,
                    record.alac_hash,
                    record.flac_size,
                    record.alac_size,
                    record.artist,
                    record.album,
                    record.track,
                    record.conversion_date,
                    1 if record.verified else 0,
                    datetime.now().isoformat(),
                    record.flac_path
                ))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO conversions (
                        flac_path, alac_path, flac_hash, alac_hash,
                        flac_size, alac_size, artist, album, track,
                        conversion_date, verified, last_checked
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.flac_path,
                    record.alac_path,
                    record.flac_hash,
                    record.alac_hash,
                    record.flac_size,
                    record.alac_size,
                    record.artist,
                    record.album,
                    record.track,
                    record.conversion_date,
                    1 if record.verified else 0,
                    datetime.now().isoformat()
                ))
            
            conn.commit()
    
    def mark_skipped(self, flac_path: str, reason: str = "user_skip"):
        """Mark a file to be skipped in future scans."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO conversions (
                    flac_path, alac_path, flac_hash, alac_hash,
                    flac_size, alac_size, artist, album, track,
                    conversion_date, verified, skip_count, last_checked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(flac_path),
                "",
                "",
                "",
                0,
                0,
                "",
                "",
                "",
                datetime.now().isoformat(),
                0,
                1,
                datetime.now().isoformat()
            ))
            
            # Also record skip reason in settings
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (f"skip_reason:{flac_path}", reason)
            )
            
            conn.commit()
    
    def get_conversion_stats(self) -> Dict:
        """Get statistics about conversions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM conversions WHERE verified = 1")
            total_converted = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(flac_size) FROM conversions WHERE verified = 1")
            total_flac_size = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(alac_size) FROM conversions WHERE verified = 1")
            total_alac_size = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM conversions WHERE verified = 0 AND skip_count > 0")
            total_skipped = cursor.fetchone()[0]
            
            return {
                'total_converted': total_converted,
                'total_flac_size': total_flac_size,
                'total_alac_size': total_alac_size,
                'total_skipped': total_skipped,
                'space_saved': total_flac_size - total_alac_size,
                'compression_ratio': (total_alac_size / total_flac_size * 100) if total_flac_size > 0 else 0
            }
    
    def get_artist_stats(self) -> List[Tuple[str, int]]:
        """Get conversion statistics by artist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT artist, COUNT(*) as count 
                FROM conversions 
                WHERE verified = 1 AND artist IS NOT NULL 
                GROUP BY artist 
                ORDER BY count DESC
            ''')
            return cursor.fetchall()

class FLACtoALACConverter:
    """Main converter class with database integration."""
    
    def __init__(self, music_root: Path, delete_original: bool = False):
        self.music_root = music_root
        self.delete_original = delete_original
        self.tracker = ConversionTracker()
        self.interrupted = False
        
        # Setup signal handler for graceful interruption
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Check for required tools
        self._check_required_tools()
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully."""
        self.interrupted = True
        console.print("\n[yellow]Interrupt received. Finishing current conversions...[/yellow]")
    
    def _check_required_tools(self):
        """Check if required command-line tools are available."""
        required = ['ffmpeg', 'metaflac']
        missing = []
        
        for tool in required:
            try:
                subprocess.run([tool, '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(tool)
        
        if missing:
            console.print(f"[red]Missing required tools: {', '.join(missing)}[/red]")
            console.print("Please install them:")
            console.print("  Ubuntu/Debian: sudo apt-get install ffmpeg flac")
            console.print("  macOS: brew install ffmpeg flac")
            console.print("  Windows: Download from official websites")
            sys.exit(1)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extract_metadata(self, flac_file: Path) -> Dict[str, str]:
        """Extract metadata from FLAC file."""
        metadata = {}
        
        tags = [
            'ARTIST', 'ALBUMARTIST', 'TITLE', 'ALBUM', 'DATE',
            'GENRE', 'TRACKNUMBER', 'TRACKTOTAL', 'DISCNUMBER',
            'DISCTOTAL', 'COMPOSER', 'COMMENT'
        ]
        
        for tag in tags:
            try:
                result = subprocess.run(
                    ['metaflac', '--show-tag', tag, str(flac_file)],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.stdout.strip():
                    metadata[tag] = result.stdout.strip().split('=', 1)[1]
            except Exception:
                pass
        
        # Fallback: use directory structure for artist/album
        if 'ARTIST' not in metadata:
            # Try to get artist from directory structure
            rel_path = flac_file.relative_to(self.music_root)
            parts = rel_path.parts
            if len(parts) >= 1:
                metadata['ARTIST'] = parts[0]
        
        return metadata
    
    def convert_single_file(self, flac_file: Path, progress_callback=None) -> Optional[ConversionRecord]:
        """Convert a single FLAC file to ALAC."""
        if self.interrupted:
            return None
        
        # Check if already converted
        if self.tracker.is_converted(str(flac_file)):
            if progress_callback:
                progress_callback(f"Skipped (already converted): {flac_file.name}")
            return None
        
        try:
            # Extract metadata
            metadata = self.extract_metadata(flac_file)
            
            # Create output path
            alac_file = flac_file.with_suffix('.m4a')
            
            # Build ffmpeg command
            cmd = [
                'ffmpeg', '-i', str(flac_file),
                '-c:a', 'alac',
                '-map_metadata', '0',
                '-id3v2_version', '3',
                '-write_id3v1', '1'
            ]
            
            # Add metadata
            metadata_map = {
                'ARTIST': '-metadata', 'artist',
                'ALBUMARTIST': '-metadata', 'album_artist',
                'TITLE': '-metadata', 'title',
                'ALBUM': '-metadata', 'album',
                'DATE': '-metadata', 'date',
                'GENRE': '-metadata', 'genre',
                'TRACKNUMBER': '-metadata', 'track',
                'COMPOSER': '-metadata', 'composer'
            }
            
            for flac_tag, ffmpeg_flag in metadata_map.items():
                if flac_tag in metadata and metadata[flac_tag]:
                    cmd.extend([ffmpeg_flag, metadata[flac_tag]])
            
            cmd.append(str(alac_file))
            
            # Run conversion
            if progress_callback:
                progress_callback(f"Converting: {flac_file.name}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Calculate hashes for verification
            flac_hash = self.calculate_file_hash(flac_file)
            alac_hash = self.calculate_file_hash(alac_file)
            
            # Create record
            record = ConversionRecord(
                flac_path=str(flac_file),
                alac_path=str(alac_file),
                flac_hash=flac_hash,
                alac_hash=alac_hash,
                flac_size=flac_file.stat().st_size,
                alac_size=alac_file.stat().st_size,
                artist=metadata.get('ARTIST', 'Unknown'),
                album=metadata.get('ALBUM', 'Unknown'),
                track=metadata.get('TITLE', flac_file.stem),
                conversion_date=datetime.now().isoformat(),
                verified=True
            )
            
            # Record in database
            self.tracker.record_conversion(record)
            
            # Delete original if requested
            if self.delete_original:
                flac_file.unlink()
                if progress_callback:
                    progress_callback(f"Deleted original: {flac_file.name}")
            
            if progress_callback:
                progress_callback(f"Completed: {flac_file.name}")
            
            return record
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error for {flac_file}: {e.stderr}")
            if progress_callback:
                progress_callback(f"Failed: {flac_file.name}")
            return None
        except Exception as e:
            logger.error(f"Error converting {flac_file}: {e}")
            if progress_callback:
                progress_callback(f"Failed: {flac_file.name}")
            return None
    
    def scan_for_flac_files(self) -> List[Path]:
        """Scan music directory for FLAC files."""
        flac_files = []
        
        console.print(f"[cyan]Scanning {self.music_root} for FLAC files...[/cyan]")
        
        # Walk through all artist directories
        for artist_dir in self.music_root.iterdir():
            if not artist_dir.is_dir():
                continue
            
            # Look for FLAC files in this artist directory
            for flac_file in artist_dir.rglob('*.flac'):
                flac_files.append(flac_file)
        
        return flac_files
    
    def convert_batch(self, flac_files: List[Path], max_workers: int = 4) -> Dict:
        """Convert a batch of FLAC files."""
        total_files = len(flac_files)
        completed = 0
        failed = 0
        skipped = 0
        
        console.print(f"[green]Found {total_files} FLAC files to process[/green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            main_task = progress.add_task("[cyan]Converting files...", total=total_files)
            
            def update_progress(msg: str):
                nonlocal completed, failed, skipped
                if "Completed" in msg or "Skipped" in msg:
                    completed += 1
                    progress.update(main_task, advance=1)
                elif "Failed" in msg:
                    failed += 1
                    progress.update(main_task, advance=1)
            
            # Convert files in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(self.convert_single_file, flac_file, update_progress): flac_file
                    for flac_file in flac_files
                }
                
                for future in as_completed(future_to_file):
                    if self.interrupted:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
        
        return {
            'total': total_files,
            'completed': completed,
            'failed': failed,
            'skipped': skipped
        }

def display_menu():
    """Display the main menu."""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]FLAC to ALAC Batch Converter[/bold cyan]\n"
        "Converts FLAC files to Apple Lossless Audio Codec (.m4a)",
        border_style="cyan"
    ))
    
    menu_options = [
        {"name": "1. Scan and convert all FLAC files", "value": "scan_all"},
        {"name": "2. Convert specific number of files", "value": "convert_n"},
        {"name": "3. View conversion statistics", "value": "stats"},
        {"name": "4. View artist statistics", "value": "artist_stats"},
        {"name": "5. Clear database and start fresh", "value": "clear_db"},
        {"name": "6. Exit", "value": "exit"}
    ]
    
    for option in menu_options:
        console.print(option["name"])
    
    return questionary.select(
        "Select an option:",
        choices=[option["value"] for option in menu_options],
        default="scan_all"
    ).ask()

def get_music_directory() -> Path:
    """Get or verify the music directory."""
    default_path = Path.home() / "Music"
    
    if questionary.confirm(f"Use default music directory ({default_path})?").ask():
        music_dir = default_path
    else:
        music_dir = questionary.text(
            "Enter music directory path:",
            default=str(default_path)
        ).ask()
    
    music_path = Path(music_dir)
    
    if not music_path.exists():
        console.print(f"[red]Directory does not exist: {music_path}[/red]")
        if questionary.confirm("Create it?").ask():
            music_path.mkdir(parents=True)
        else:
            sys.exit(1)
    
    return music_path

def display_statistics(tracker: ConversionTracker):
    """Display conversion statistics."""
    stats = tracker.get_conversion_stats()
    
    table = Table(title="Conversion Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total files converted", str(stats['total_converted']))
    table.add_row("Files skipped", str(stats['total_skipped']))
    table.add_row("Total FLAC size", f"{stats['total_flac_size'] / (1024**3):.2f} GB")
    table.add_row("Total ALAC size", f"{stats['total_alac_size'] / (1024**3):.2f} GB")
    table.add_row("Space saved", f"{stats['space_saved'] / (1024**3):.2f} GB")
    table.add_row("Compression ratio", f"{stats['compression_ratio']:.1f}%")
    
    console.print(table)

def display_artist_stats(tracker: ConversionTracker):
    """Display statistics by artist."""
    artist_stats = tracker.get_artist_stats()
    
    if not artist_stats:
        console.print("[yellow]No artist statistics available yet.[/yellow]")
        return
    
    table = Table(title="Artist Conversion Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Artist", style="cyan", no_wrap=True)
    table.add_column("Files Converted", style="green", justify="right")
    
    for artist, count in artist_stats[:20]:  # Show top 20
        table.add_row(artist if artist else "Unknown", str(count))
    
    console.print(table)
    
    if len(artist_stats) > 20:
        console.print(f"[dim]... and {len(artist_stats) - 20} more artists[/dim]")

def main():
    """Main function with interactive menu."""
    parser = argparse.ArgumentParser(description='FLAC to ALAC Batch Converter')
    parser.add_argument('--music-dir', type=str, help='Music directory path')
    parser.add_argument('--delete', action='store_true', help='Delete FLAC after conversion')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--batch-size', type=int, help='Number of files to convert at once')
    parser.add_argument('--non-interactive', action='store_true', help='Run without menu')
    
    args = parser.parse_args()
    
    # Get music directory
    if args.music_dir:
        music_root = Path(args.music_dir)
    else:
        music_root = get_music_directory()
    
    # Create converter
    converter = FLACtoALACConverter(music_root, delete_original=args.delete)
    
    if args.non_interactive:
        # Non-interactive mode
        flac_files = converter.scan_for_flac_files()
        if args.batch_size:
            flac_files = flac_files[:args.batch_size]
        
        results = converter.convert_batch(flac_files, max_workers=args.workers)
        
        console.print(f"\n[green]Conversion Complete![/green]")
        console.print(f"Total: {results['total']}")
        console.print(f"Completed: {results['completed']}")
        console.print(f"Failed: {results['failed']}")
        console.print(f"Skipped: {results['skipped']}")
        
        # Show statistics
        display_statistics(converter.tracker)
        
        return
    
    # Interactive mode with menu
    while True:
        choice = display_menu()
        
        if choice == "exit":
            console.print("[yellow]Goodbye![/yellow]")
            break
        
        elif choice == "scan_all":
            flac_files = converter.scan_for_flac_files()
            if not flac_files:
                console.print("[yellow]No FLAC files found.[/yellow]")
                continue
            
            # Ask for confirmation
            if questionary.confirm(
                f"Found {len(flac_files)} FLAC files. Start conversion?"
            ).ask():
                # Ask about deletion
                if not args.delete:
                    converter.delete_original = questionary.confirm(
                        "Delete original FLAC files after conversion?"
                    ).ask()
                
                # Ask about parallel workers
                workers = questionary.text(
                    "Number of parallel conversions (recommended: 4):",
                    default="4"
                ).ask()
                
                try:
                    workers = int(workers)
                except ValueError:
                    workers = 4
                
                results = converter.convert_batch(flac_files, max_workers=workers)
                
                console.print(f"\n[green]Conversion Complete![/green]")
                console.print(f"Total: {results['total']}")
                console.print(f"Completed: {results['completed']}")
                console.print(f"Failed: {results['failed']}")
                console.print(f"Skipped: {results['skipped']}")
                
                input("\nPress Enter to continue...")
        
        elif choice == "convert_n":
            flac_files = converter.scan_for_flac_files()
            if not flac_files:
                console.print("[yellow]No FLAC files found.[/yellow]")
                continue
            
            total_count = len(flac_files)
            console.print(f"[cyan]Found {total_count} FLAC files.[/cyan]")
            
            # Ask how many to convert
            try:
                n_files = questionary.text(
                    f"How many files to convert (1-{total_count})?",
                    validate=lambda x: x.isdigit() and 1 <= int(x) <= total_count
                ).ask()
                n_files = int(n_files)
            except (ValueError, TypeError):
                console.print("[red]Invalid number.[/red]")
                continue
            
            # Select files to convert (skip already converted)
            files_to_convert = []
            for flac_file in flac_files[:n_files]:
                if not converter.tracker.is_converted(str(flac_file)):
                    files_to_convert.append(flac_file)
            
            if not files_to_convert:
                console.print("[yellow]All selected files are already converted.[/yellow]")
                continue
            
            console.print(f"[cyan]Converting {len(files_to_convert)} files...[/cyan]")
            
            results = converter.convert_batch(files_to_convert, max_workers=args.workers)
            
            console.print(f"\n[green]Batch Complete![/green]")
            console.print(f"Converted: {results['completed']}")
            console.print(f"Failed: {results['failed']}")
            
            input("\nPress Enter to continue...")
        
        elif choice == "stats":
            display_statistics(converter.tracker)
            input("\nPress Enter to continue...")
        
        elif choice == "artist_stats":
            display_artist_stats(converter.tracker)
            input("\nPress Enter to continue...")
        
        elif choice == "clear_db":
            if questionary.confirm(
                "[red]Are you sure you want to clear the database?[/red]",
                default=False
            ).ask():
                converter.tracker.db_path.unlink(missing_ok=True)
                converter.tracker = ConversionTracker()
                console.print("[green]Database cleared.[/green]")
                time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Program interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Unhandled exception")