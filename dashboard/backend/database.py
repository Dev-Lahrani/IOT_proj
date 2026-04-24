import sqlite3
import threading
from datetime import datetime


class Database:
    def __init__(self, db_path="driver_data.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self):
        """Create a new connection with WAL mode enabled."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS driver_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ear REAL,
                    mar REAL,
                    status TEXT,
                    lat REAL,
                    lon REAL,
                    timestamp TEXT
                )
            """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    timestamp TEXT,
                    details TEXT
                )
            """
            )
            c.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON driver_data(timestamp DESC)
            """
            )
            conn.commit()
            conn.close()

    def insert_driver_data(self, data):
        lat = data.get("lat", data.get("latitude"))
        lon = data.get("lon", data.get("longitude"))
        status = data.get("status")
        with self._lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute(
                "INSERT INTO driver_data (ear, mar, status, lat, lon, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    data.get("ear"),
                    data.get("mar"),
                    status,
                    lat,
                    lon,
                    data.get("timestamp"),
                ),
            )
            conn.commit()
            conn.close()

        if status in ("DROWSY", "YAWN", "YAWNING"):
            self.insert_alert(status, data)

    def insert_alert(self, event_type, details=None):
        with self._lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute(
                "INSERT INTO alerts (event_type, timestamp, details) VALUES (?, ?, ?)",
                (
                    event_type,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    str(details) if details else None,
                ),
            )
            conn.commit()
            conn.close()

    def get_latest(self):
        with self._lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM driver_data ORDER BY id DESC LIMIT 1")
            row = c.fetchone()
            conn.close()
            return dict(row) if row else None

    def get_alerts(self, limit=50):
        with self._lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute(
                "SELECT * FROM alerts ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = c.fetchall()
            conn.close()
            return [dict(row) for row in rows]

    def get_stats(self):
        with self._lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM driver_data")
            total_records = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM alerts WHERE event_type = 'DROWSY'")
            drowsy_count = c.fetchone()[0]
            c.execute(
                "SELECT COUNT(*) FROM alerts WHERE event_type IN ('YAWN', 'YAWNING')"
            )
            yawn_count = c.fetchone()[0]
            conn.close()
            return {
                "total_records": total_records,
                "drowsy_alerts": drowsy_count,
                "yawn_alerts": yawn_count,
            }
