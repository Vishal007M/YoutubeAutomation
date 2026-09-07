"""
history_manager.py - Tracks all used topics in SQLite so topics NEVER repeat.
Even if you delete everything else, keep history.db to avoid repeating topics.
"""
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HistoryManager:
    def __init__(self, db_path="history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                topic          TEXT    NOT NULL,
                category       TEXT    DEFAULT '',
                created_at     TEXT    NOT NULL,
                video_id_part1 TEXT    DEFAULT '',
                video_id_part2 TEXT    DEFAULT ''
            )
        """)
        conn.commit()
        conn.close()
        logger.debug(f"History DB ready: {self.db_path}")

    def add_topic(self, topic, category="", video_id_part1="", video_id_part2=""):
        """Record a used topic after successful upload."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO topics
               (topic, category, created_at, video_id_part1, video_id_part2)
               VALUES (?, ?, ?, ?, ?)""",
            (topic, category, datetime.now().isoformat(), video_id_part1, video_id_part2),
        )
        conn.commit()
        conn.close()
        logger.info(f"History saved: {topic}")

    def get_used_topics(self, limit=150):
        """Return list of previously used topic strings."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT topic FROM topics ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        topics = [row[0] for row in cursor.fetchall()]
        conn.close()
        return topics

    def get_total_count(self):
        """Return total number of topics/video-sets created."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM topics")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def is_topic_used(self, topic):
        """Check if a topic (case-insensitive) has already been used."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM topics WHERE LOWER(topic) = LOWER(?)", (topic,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
