import sqlite3
from typing import Optional, List
from datetime import datetime
from ..domain.models import Log


class SqliteLogRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table()

    def _init_table(self):
        """初始化日志表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            conn.commit()

    def add_log(self, user_id: str, log_type: str, content: str) -> bool:
        """添加日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs (user_id, type, content)
                VALUES (?, ?, ?)
            ''', (user_id, log_type, content))
            conn.commit()
            return True

    def get_user_logs(self, user_id: str, log_type: Optional[str] = None, limit: int = 50) -> List[Log]:
        """获取用户日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if log_type:
                cursor.execute('''
                    SELECT * FROM logs 
                    WHERE user_id = ? AND type = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (user_id, log_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM logs 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (user_id, limit))
            
            logs = []
            for row in cursor.fetchall():
                logs.append(Log(
                    id=row[0],
                    user_id=row[1],
                    type=row[2],
                    content=row[3],
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None
                ))
            
            return logs

    def get_recent_logs(self, limit: int = 10) -> List[Log]:
        """获取最近的日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            logs = []
            for row in cursor.fetchall():
                logs.append(Log(
                    id=row[0],
                    user_id=row[1],
                    type=row[2],
                    content=row[3],
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None
                ))
            
            return logs