#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path
from mutagen.flac import FLAC
from mutagen.mp4 import MP4, MP4Cover
import questionary
from rich.console import Console
from rich.progress import Progress

console = Console()

def convert_flac_to_alac(flac_path: Path, delete_original=False):
    m4a_path = flac_path.with_suffix(".m4a")

    # Extract FLAC metadata
    audio = FLAC(flac_path)
    metadata = {}

    for key in audio.tags.keys():
        val = audio.tags.get(key, [""])[0]
        metadata[key.lower()] = val

    # Extract cover art (if exists)
    cover_data = None
    if audio.pictures:
        pic = audio.pictures[0]
        cover_data = (pic.data, pic.mime)

    # Run FFmpeg conversion
    cmd = [
        "ffmpeg", "-y",
        "-i", str(flac_path),
        "-c:a", "alac",
        str(m4a_path)
    ]

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        console.print(f"[red]FFmpeg failed: {flac_path}[/red]")
        return False

    # Write metadata into new ALAC file
    mp4 = MP4(m4a_path)

    tag_map = {
        "artist": "\xa9ART",
        "album": "\xa9alb",
        "title": "\xa9nam",
        "albumartist": "aART",
        "genre": "\xa9gen",
        "date": "\xa9day",
        "tracknumber": "trkn",
        "discnumber": "disk",
        "composer": "\xa9wrt"
    }

    for key, mp4_tag in tag_map.items():
        if key in metadata:
            if mp4_tag in ("trkn", "disk"):
                try:
                    num = int(metadata[key].split("/")[0])
                    total = int(metadata[key].split("/")[1]) if "/" in metadata[key] else 0
                    mp4[mp4_tag] = [(num, total)]
                except:
                    pass
            else:
                mp4[mp4_tag] = metadata[key]

    # Add cover art
    if cover_data:
        data, mime = cover_data
        if "png" in mime:
            cov = MP4Cover(data, imageformat=MP4Cover.FORMAT_PNG)
        else:
            cov = MP4Cover(data, imageformat=MP4Cover.FORMAT_JPEG)

        mp4["covr"] = [cov]

    mp4.save()

    # Delete FLAC file?
    if delete_original:
        flac_path.unlink()

    return True


def main():
    console.print("[bold cyan]FLAC → ALAC Batch Converter[/bold cyan]\n")

    # Ask user where to scan
    folder = questionary.path(
        "Which directory should be scanned for FLAC files?"
    ).ask()

    folder = Path(folder)
    if not folder.exists():
        console.print("[red]Folder does not exist![/red]")
        return

    delete_original = questionary.confirm(
        "Delete FLAC files after conversion?"
    ).ask()

    flac_files = list(folder.rglob("*.flac"))
    console.print(f"[green]Found {len(flac_files)} FLAC files.[/green]\n")

    with Progress() as progress:
        task = progress.add_task("Converting...", total=len(flac_files))

        for flac_path in flac_files:
            convert_flac_to_alac(flac_path, delete_original)
            progress.advance(task)

    console.print("\n[bold green]Conversion complete![/bold green]")


if __name__ == "__main__":
    main()
