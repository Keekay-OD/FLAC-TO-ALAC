from mutagen.flac import FLAC
from mutagen.mp4 import MP4, MP4Cover
from pathlib import Path


def extract_flac_metadata(flac_path: Path):
    audio = FLAC(flac_path)
    meta = {}

    for key in audio.keys():
        try:
            meta[key.lower()] = audio[key][0]
        except:
            pass

    cover = None
    if audio.pictures:
        pic = audio.pictures[0]
        mime = pic.mime
        cover_format = (MP4Cover.FORMAT_PNG 
                        if "png" in mime 
                        else MP4Cover.FORMAT_JPEG)
        cover = (pic.data, cover_format)

    return meta, cover


def write_alac_metadata(m4a_path: Path, metadata: dict, cover=None):
    mp4 = MP4(m4a_path)

    tag_map = {
        "artist":   "\xa9ART",
        "album":    "\xa9alb",
        "title":    "\xa9nam",
        "albumartist": "aART",
        "composer": "\xa9wrt",
        "genre":    "\xa9gen",
        "date":     "\xa9day",
        "tracknumber": "trkn",
        "discnumber": "disk"
    }

    for key, tag in tag_map.items():
        if key in metadata:
            if tag in ("trkn", "disk"):
                try:
                    num = int(metadata[key].split("/")[0])
                    total = int(metadata[key].split("/")[1]) if "/" in metadata[key] else 0
                    mp4[tag] = [(num, total)]
                except:
                    pass
            else:
                mp4[tag] = metadata[key]

    if cover:
        data, fmt = cover
        mp4["covr"] = [MP4Cover(data, fmt)]

    mp4.save()
