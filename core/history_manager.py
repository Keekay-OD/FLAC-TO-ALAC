import sqlite3
from pathlib import Path
import csv
from datetime import datetime

from utils.paths import HISTORY_DB


class HistoryManager:

    def __init__(self):
        self.db_path = HISTORY_DB
        self._init_db()

    # ------------------------------------------------------------------
    def _init_db(self):
        """Create history database if not exists."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flac_path TEXT,
                alac_path TEXT,
                artist TEXT,
                album TEXT,
                track TEXT,
                size_before INTEGER,
                size_after INTEGER,
                date TEXT,
                status TEXT
            )
        """)

        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    def add_record(self, flac, alac, metadata, size_before, size_after):
        """Insert a conversion record."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO history (
                flac_path, alac_path, artist, album, track,
                size_before, size_after, date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            flac,
            alac,
            metadata.get("artist", "Unknown"),
            metadata.get("album", "Unknown"),
            metadata.get("title", Path(flac).stem),
            size_before,
            size_after,
            datetime.now().isoformat(),
            "success"
        ))

        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    def mark_failed(self, flac):
        """Record failed conversion."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO history (
                flac_path, alac_path, artist, album, track,
                size_before, size_after, date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            flac,
            "",
            "",
            "",
            "",
            0,
            0,
            datetime.now().isoformat(),
            "failed"
        ))

        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    def query(self, search="", artist="", album="", status=""):
        """Return filtered history as list of dicts."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        query = "SELECT * FROM history WHERE 1=1"
        params = []

        if search:
            query += " AND (flac_path LIKE ? OR alac_path LIKE ? OR track LIKE ?)"
            s = f"%{search}%"
            params += [s, s, s]

        if artist:
            query += " AND artist LIKE ?"
            params.append(f"%{artist}%")

        if album:
            query += " AND album LIKE ?"
            params.append(f"%{album}%")

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY date DESC"

        cur.execute(query, params)
        rows = cur.fetchall()

        conn.close()

        # Convert to dicts
        keys = ["id", "flac", "alac", "artist", "album", "track",
                "size_before", "size_after", "date", "status"]

        return [dict(zip(keys, row)) for row in rows]

    # ------------------------------------------------------------------
    def export_csv(self, out_path):
        """Export history to CSV."""
        rows = self.query()

        with open(out_path, "w", newline="", encoding="utf8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "FLAC Path", "ALAC Path", "Artist", "Album", "Track",
                "Size Before", "Size After", "Date", "Status"
            ])

            for r in rows:
                writer.writerow([
                    r["id"], r["flac"], r["alac"], r["artist"], r["album"],
                    r["track"], r["size_before"], r["size_after"],
                    r["date"], r["status"]
                ])

    # ------------------------------------------------------------------
    def clear_history(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM history")
        conn.commit()
        conn.close()
