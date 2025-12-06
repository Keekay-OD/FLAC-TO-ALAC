#!/usr/bin/env python3
"""
Convert FLAC files to ALAC (Apple Lossless Audio Codec) format (.m4a)
with metadata preservation and optional FLAC deletion.
"""

import os
import sys
import subprocess
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Dict, Tuple
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FLACtoALACConverter:
    def __init__(self, delete_original: bool = False, verify_conversion: bool = True):
        self.delete_original = delete_original
        self.verify_conversion = verify_conversion
        self.required_tools = ['ffmpeg', 'ffprobe', 'metaflac']
        self._check_required_tools()
        
    def _check_required_tools(self):
        """Check if required command-line tools are available."""
        missing_tools = []
        for tool in self.required_tools:
            if shutil.which(tool) is None:
                missing_tools.append(tool)
        
        if missing_tools:
            logger.error(f"Missing required tools: {', '.join(missing_tools)}")
            logger.error("Please install them before running this script:")
            logger.error("  - ffmpeg: for audio conversion")
            logger.error("  - ffprobe: for metadata extraction (usually comes with ffmpeg)")
            logger.error("  - metaflac: for FLAC metadata extraction")
            sys.exit(1)
    
    def extract_flac_metadata(self, flac_file: Path) -> Dict[str, str]:
        """Extract metadata from FLAC file using metaflac."""
        metadata = {}
        
        # Common metadata tags to extract
        tags = [
            'ARTIST', 'ALBUMARTIST', 'TITLE', 'ALBUM', 'DATE',
            'GENRE', 'TRACKNUMBER', 'TRACKTOTAL', 'DISCNUMBER',
            'DISCTOTAL', 'DESCRIPTION', 'COMPOSER', 'COMMENT'
        ]
        
        for tag in tags:
            try:
                result = subprocess.run(
                    ['metaflac', '--show-tag', tag, str(flac_file)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if result.stdout.strip():
                    # Remove the tag= prefix
                    metadata[tag] = result.stdout.strip().split('=', 1)[1]
            except subprocess.CalledProcessError:
                # Tag might not exist, continue
                pass
        
        # Try to extract cover art
        cover_path = self._extract_cover_art(flac_file)
        if cover_path:
            metadata['COVER_ART'] = str(cover_path)
        
        return metadata
    
    def _extract_cover_art(self, flac_file: Path) -> Optional[Path]:
        """Extract embedded cover art from FLAC file."""
        cover_dir = flac_file.parent
        cover_name = f".arttmp_{flac_file.stem}"
        
        try:
            # Try to export picture
            result = subprocess.run(
                ['metaflac', '--export-picture-to', str(cover_dir / cover_name), str(flac_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and (cover_dir / cover_name).exists():
                # Determine file extension
                file_type_result = subprocess.run(
                    ['file', '-b', '--mime-type', str(cover_dir / cover_name)],
                    capture_output=True,
                    text=True
                )
                
                mime_type = file_type_result.stdout.strip()
                if 'image/png' in mime_type:
                    new_path = cover_dir / f"{cover_name}.png"
                elif 'image/jpeg' in mime_type:
                    new_path = cover_dir / f"{cover_name}.jpg"
                else:
                    # Unknown format, clean up and skip
                    (cover_dir / cover_name).unlink(missing_ok=True)
                    return None
                
                (cover_dir / cover_name).rename(new_path)
                return new_path
        except Exception as e:
            logger.debug(f"Failed to extract cover art: {e}")
        
        return None
    
    def convert_to_alac(self, flac_file: Path, metadata: Dict[str, str]) -> Tuple[bool, Optional[Path]]:
        """Convert FLAC file to ALAC format."""
        output_file = flac_file.with_suffix('.m4a')
        
        # Build ffmpeg command with metadata
        cmd = [
            'ffmpeg', '-i', str(flac_file),
            '-c:a', 'alac',
            '-map_metadata', '0',
            '-id3v2_version', '3',
            '-write_id3v1', '1'
        ]
        
        # Add metadata from FLAC file
        metadata_map = {
            'ARTIST': '-metadata', 'artist',
            'ALBUMARTIST': '-metadata', 'album_artist',
            'TITLE': '-metadata', 'title',
            'ALBUM': '-metadata', 'album',
            'DATE': '-metadata', 'date',
            'GENRE': '-metadata', 'genre',
            'TRACKNUMBER': '-metadata', 'track',
            'TRACKTOTAL': '-metadata', 'totaltracks',
            'DISCNUMBER': '-metadata', 'disc',
            'DISCTOTAL': '-metadata', 'totaldiscs',
            'DESCRIPTION': '-metadata', 'description',
            'COMPOSER': '-metadata', 'composer',
            'COMMENT': '-metadata', 'comment'
        }
        
        for flac_tag, ffmpeg_flag in metadata_map.items():
            if flac_tag in metadata and metadata[flac_tag]:
                cmd.extend([ffmpeg_flag, metadata[flac_tag]])
        
        # Add cover art if available
        if 'COVER_ART' in metadata:
            cover_path = Path(metadata['COVER_ART'])
            if cover_path.exists():
                cmd.extend(['-i', str(cover_path), '-map', '0', '-map', '1', '-c:v', 'copy'])
        
        cmd.append(str(output_file))
        
        try:
            # Run conversion
            logger.info(f"Converting {flac_file.name} to ALAC...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Clean up temporary cover art
            if 'COVER_ART' in metadata:
                cover_path = Path(metadata['COVER_ART'])
                if cover_path.exists():
                    cover_path.unlink()
            
            return True, output_file
        except subprocess.CalledProcessError as e:
            logger.error(f"Conversion failed for {flac_file.name}: {e.stderr}")
            return False, None
    
    def verify_audio_equality(self, flac_file: Path, alac_file: Path) -> bool:
        """Verify that the ALAC file contains the same audio data as the FLAC file."""
        try:
            # Decode both files to raw audio and compare
            flac_wav = flac_file.parent / f".verify_{flac_file.stem}_flac.wav"
            alac_wav = flac_file.parent / f".verify_{flac_file.stem}_alac.wav"
            
            # Decode FLAC to WAV
            subprocess.run(
                ['ffmpeg', '-i', str(flac_file), '-f', 'wav', str(flac_wav)],
                capture_output=True,
                check=True
            )
            
            # Decode ALAC to WAV
            subprocess.run(
                ['ffmpeg', '-i', str(alac_file), '-f', 'wav', str(alac_wav)],
                capture_output=True,
                check=True
            )
            
            # Calculate MD5 checksums
            def calculate_md5(file_path: Path) -> str:
                hash_md5 = hashlib.md5()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
                return hash_md5.hexdigest()
            
            flac_md5 = calculate_md5(flac_wav)
            alac_md5 = calculate_md5(alac_wav)
            
            # Clean up temporary files
            flac_wav.unlink(missing_ok=True)
            alac_wav.unlink(missing_ok=True)
            
            if flac_md5 == alac_md5:
                logger.debug(f"Verification passed for {flac_file.name}")
                return True
            else:
                logger.error(f"Verification failed for {flac_file.name}: checksums differ")
                return False
                
        except Exception as e:
            logger.error(f"Verification error for {flac_file.name}: {e}")
            return False
    
    def convert_file(self, flac_file: Path) -> bool:
        """Convert a single FLAC file to ALAC."""
        try:
            # Extract metadata
            metadata = self.extract_flac_metadata(flac_file)
            
            # Convert to ALAC
            success, alac_file = self.convert_to_alac(flac_file, metadata)
            
            if not success or not alac_file:
                return False
            
            # Verify conversion if requested
            if self.verify_conversion:
                if not self.verify_audio_equality(flac_file, alac_file):
                    logger.error(f"Verification failed for {flac_file.name}, deleting output file")
                    alac_file.unlink(missing_ok=True)
                    return False
            
            # Calculate file sizes
            flac_size = flac_file.stat().st_size
            alac_size = alac_file.stat().st_size
            
            if flac_size > 0:
                size_ratio = (alac_size / flac_size) * 100
                logger.info(f"Converted: {flac_file.name} -> {alac_file.name}")
                logger.info(f"Size ratio: ALAC is {size_ratio:.1f}% of FLAC size")
            
            # Delete original FLAC if requested
            if self.delete_original:
                flac_file.unlink()
                logger.info(f"Deleted original: {flac_file.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error converting {flac_file.name}: {e}")
            return False
    
    def scan_and_convert_directory(self, directory: Path, recursive: bool = True):
        """Scan directory for FLAC files and convert them."""
        if recursive:
            flac_files = list(directory.rglob('*.flac'))
        else:
            flac_files = list(directory.glob('*.flac'))
        
        if not flac_files:
            logger.warning(f"No FLAC files found in {directory}")
            return
        
        logger.info(f"Found {len(flac_files)} FLAC file(s) to convert")
        
        # Convert files with progress tracking
        successful = 0
        failed = 0
        
        # Use ThreadPoolExecutor for parallel conversion
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_file = {
                executor.submit(self.convert_file, flac_file): flac_file 
                for flac_file in flac_files
            }
            
            for future in as_completed(future_to_file):
                flac_file = future_to_file[future]
                try:
                    if future.result():
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Exception processing {flac_file.name}: {e}")
                    failed += 1
        
        logger.info(f"Conversion complete: {successful} successful, {failed} failed")

def main():
    parser = argparse.ArgumentParser(
        description='Convert FLAC files to ALAC format (.m4a)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/music.flac
  %(prog)s /path/to/music_directory -d
  %(prog)s /path/to/music_directory -r -d
  %(prog)s *.flac -d
        
Note: Requires ffmpeg, ffprobe, and metaflac to be installed.
        """
    )
    
    parser.add_argument(
        'path',
        nargs='+',
        help='FLAC file(s) or directory(ies) to convert'
    )
    
    parser.add_argument(
        '-d', '--delete',
        action='store_true',
        help='Delete original FLAC files after successful conversion'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Scan directories recursively for FLAC files'
    )
    
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip audio verification after conversion (faster but less safe)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))
    
    # Create converter
    converter = FLACtoALACConverter(
        delete_original=args.delete,
        verify_conversion=not args.no_verify
    )
    
    # Process each path
    for path_str in args.path:
        path = Path(path_str)
        
        if not path.exists():
            logger.error(f"Path does not exist: {path}")
            continue
        
        if path.is_file() and path.suffix.lower() == '.flac':
            # Convert single file
            success = converter.convert_file(path)
            if success:
                logger.info(f"Successfully converted {path.name}")
            else:
                logger.error(f"Failed to convert {path.name}")
        elif path.is_dir():
            # Convert directory
            converter.scan_and_convert_directory(path, args.recursive)
        else:
            logger.warning(f"Skipping {path}: not a FLAC file or directory")

if __name__ == '__main__':
    main()