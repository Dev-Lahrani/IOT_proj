import sqlite3
import threading
import time
from datetime import datetime


class Database:
    def __init__(self, db_path="driver_data.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
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
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "INSERT INTO driver_data (ear, mar, status, lat, lon, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    data.get("ear"),
                    data.get("mar"),
                    data.get("status"),
                    data.get("lat"),
                    data.get("lon"),
                    data.get("timestamp"),
                ),
            )
            conn.commit()
            conn.close()

        if data.get("status") in ["DROWSY", "YAWNING"]:
            self.insert_alert(data["status"], data)

    def insert_alert(self, event_type, details=None):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
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
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM driver_data ORDER BY id DESC LIMIT 1")
            row = c.fetchone()
            conn.close()
            return dict(row) if row else None

    def get_alerts(self, limit=50):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
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
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM driver_data")
            total_records = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM alerts WHERE event_type = 'DROWSY'")
            drowsy_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM alerts WHERE event_type = 'YAWNING'")
            yawn_count = c.fetchone()[0]
            conn.close()
            return {
                "total_records": total_records,
                "drowsy_alerts": drowsy_count,
                "yawn_alerts": yawn_count,
            }
