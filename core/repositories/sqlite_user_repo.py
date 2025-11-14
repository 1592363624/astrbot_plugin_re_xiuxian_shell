import sqlite3
from typing import Optional, List
from datetime import datetime
from ..domain.models import User


class SqliteUserRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table()

    def _init_table(self):
        """初始化用户表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    nickname TEXT,
                    avatar TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    cultivation REAL DEFAULT 0,
                    realm TEXT DEFAULT '炼气一层',
                    talent TEXT,
                    dao_name TEXT,
                    sect_id INTEGER,
                    sect_position TEXT,
                    
                    is_hermit BOOLEAN DEFAULT FALSE,
                    is_in_closing BOOLEAN DEFAULT FALSE,
                    closing_start_time TIMESTAMP,
                    closing_duration INTEGER,
                    deep_closing_end_time TIMESTAMP,
                    
                    last_closing_time TIMESTAMP,
                    last_battle_time TIMESTAMP,
                    last_sect_roll_call_time TIMESTAMP,
                    
                    total_closing_count INTEGER DEFAULT 0,
                    total_battle_count INTEGER DEFAULT 0,
                    total_battle_win_count INTEGER DEFAULT 0,
                    total_exp_gained INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def create_user(self, user_id: str, nickname: Optional[str] = None) -> User:
        """创建新用户"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, nickname)
                VALUES (?, ?)
            ''', (user_id, nickname))
            conn.commit()
            
            return self.get_by_user_id(user_id)

    def get_by_user_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return User(
                id=row[0],
                user_id=row[1],
                nickname=row[2],
                avatar=row[3],
                created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                last_login_at=datetime.fromisoformat(row[5]) if row[5] else None,
                cultivation=row[6] or 0.0,
                realm=row[7] or "炼气一层",
                talent=row[8],
                dao_name=row[9],
                sect_id=row[10],
                sect_position=row[11],
                is_hermit=bool(row[12]),
                is_in_closing=bool(row[13]),
                closing_start_time=datetime.fromisoformat(row[14]) if row[14] else None,
                closing_duration=row[15],
                deep_closing_end_time=datetime.fromisoformat(row[16]) if row[16] else None,
                last_closing_time=datetime.fromisoformat(row[17]) if row[17] else None,
                last_battle_time=datetime.fromisoformat(row[18]) if row[18] else None,
                last_sect_roll_call_time=datetime.fromisoformat(row[19]) if row[19] else None,
                total_closing_count=row[20] or 0,
                total_battle_count=row[21] or 0,
                total_battle_win_count=row[22] or 0,
                total_exp_gained=row[23] or 0
            )

    def update_user(self, user: User) -> bool:
        """更新用户信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET
                    nickname = ?,
                    avatar = ?,
                    last_login_at = ?,
                    cultivation = ?,
                    realm = ?,
                    talent = ?,
                    dao_name = ?,
                    sect_id = ?,
                    sect_position = ?,
                    is_hermit = ?,
                    is_in_closing = ?,
                    closing_start_time = ?,
                    closing_duration = ?,
                    deep_closing_end_time = ?,
                    last_closing_time = ?,
                    last_battle_time = ?,
                    last_sect_roll_call_time = ?,
                    total_closing_count = ?,
                    total_battle_count = ?,
                    total_battle_win_count = ?,
                    total_exp_gained = ?
                WHERE user_id = ?
            ''', (
                user.nickname,
                user.avatar,
                user.last_login_at.isoformat() if user.last_login_at else None,
                user.cultivation,
                user.realm,
                user.talent,
                user.dao_name,
                user.sect_id,
                user.sect_position,
                user.is_hermit,
                user.is_in_closing,
                user.closing_start_time.isoformat() if user.closing_start_time else None,
                user.closing_duration,
                user.deep_closing_end_time.isoformat() if user.deep_closing_end_time else None,
                user.last_closing_time.isoformat() if user.last_closing_time else None,
                user.last_battle_time.isoformat() if user.last_battle_time else None,
                user.last_sect_roll_call_time.isoformat() if user.last_sect_roll_call_time else None,
                user.total_closing_count,
                user.total_battle_count,
                user.total_battle_win_count,
                user.total_exp_gained,
                user.user_id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def get_cultivation_ranking(self, limit: int = 10) -> List[User]:
        """获取修为排行榜"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                WHERE cultivation > 0 
                ORDER BY cultivation DESC 
                LIMIT ?
            ''', (limit,))
            
            users = []
            for row in cursor.fetchall():
                users.append(User(
                    id=row[0],
                    user_id=row[1],
                    nickname=row[2],
                    avatar=row[3],
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    last_login_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    cultivation=row[6] or 0.0,
                    realm=row[7] or "炼气一层",
                    talent=row[8],
                    dao_name=row[9],
                    sect_id=row[10],
                    sect_position=row[11],
                    is_hermit=bool(row[12]),
                    is_in_closing=bool(row[13]),
                    closing_start_time=datetime.fromisoformat(row[14]) if row[14] else None,
                    closing_duration=row[15],
                    deep_closing_end_time=datetime.fromisoformat(row[16]) if row[16] else None,
                    last_closing_time=datetime.fromisoformat(row[17]) if row[17] else None,
                    last_battle_time=datetime.fromisoformat(row[18]) if row[18] else None,
                    last_sect_roll_call_time=datetime.fromisoformat(row[19]) if row[19] else None,
                    total_closing_count=row[20] or 0,
                    total_battle_count=row[21] or 0,
                    total_battle_win_count=row[22] or 0,
                    total_exp_gained=row[23] or 0
                ))
            
            return users