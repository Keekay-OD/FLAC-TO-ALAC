import sqlite3
from datetime import datetime
from utils.paths import HISTORY_DB


class HistoryManager:
    """SQLite history storage for conversions."""

    def __init__(self):
        self._init_db()

    # ----------------------------------------------------------
    # Initialize DB
    # ----------------------------------------------------------
    def _init_db(self):
        conn = sqlite3.connect(HISTORY_DB)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flac_path TEXT,
                alac_path TEXT,
                artist TEXT,
                album TEXT,
                title TEXT,
                size_before INTEGER,
                size_after INTEGER,
                date TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    # ----------------------------------------------------------
    # Add one conversion record
    # ----------------------------------------------------------
    def add_record(self, flac, alac, metadata, size_before, size_after):
        conn = sqlite3.connect(HISTORY_DB)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO history (
                flac_path, alac_path, artist, album, title,
                size_before, size_after, date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                flac,
                alac,
                metadata.get("ARTIST", "Unknown"),
                metadata.get("ALBUM", "Unknown"),
                metadata.get("TITLE", "Unknown"),
                size_before,
                size_after,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        conn.commit()
        conn.close()

    # ----------------------------------------------------------
    # Load all rows (newest first)
    # ----------------------------------------------------------
    def load_all(self):
        conn = sqlite3.connect(HISTORY_DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM history ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()

        # Convert to dicts so UI is same as before
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "flac": r[1],
                "alac": r[2],
                "artist": r[3],
                "album": r[4],
                "title": r[5],
                "size_before": r[6],
                "size_after": r[7],
                "date": r[8],
            })
        return results

    # ----------------------------------------------------------
    # Delete single entry
    # ----------------------------------------------------------
    def delete(self, row_id):
        conn = sqlite3.connect(HISTORY_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM history WHERE id = ?", (row_id,))
        conn.commit()
        conn.close()

    # ----------------------------------------------------------
    # Clear all
    # ----------------------------------------------------------
    def clear(self):
        conn = sqlite3.connect(HISTORY_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM history")
        conn.commit()
        conn.close()
