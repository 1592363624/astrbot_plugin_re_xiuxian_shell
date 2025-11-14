import sqlite3
from typing import Optional, List
from datetime import datetime
from ..domain.models import Sect, UserSectContribution


class SqliteSectRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table()

    def _init_table(self):
        """初始化宗门相关表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 宗门表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    founder_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    member_count INTEGER DEFAULT 1,
                    contribution REAL DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # 用户宗门贡献表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sect_contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    sect_id INTEGER NOT NULL,
                    contribution REAL DEFAULT 0,
                    last_contribution_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (sect_id) REFERENCES sects(id),
                    UNIQUE(user_id, sect_id)
                )
            ''')
            
            conn.commit()

    def create_sect(self, sect: Sect) -> bool:
        """创建宗门"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO sects (
                        name, description, founder_id, member_count, contribution
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    sect.name, sect.description, sect.founder_id,
                    sect.member_count, sect.contribution
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_by_id(self, sect_id: int) -> Optional[Sect]:
        """根据ID获取宗门"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sects WHERE id = ?', (sect_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return Sect(
                id=row[0],
                name=row[1],
                description=row[2],
                founder_id=row[3],
                created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                member_count=row[5] or 1,
                contribution=row[6] or 0.0,
                is_active=bool(row[7]) if row[7] is not None else True
            )

    def get_by_name(self, name: str) -> Optional[Sect]:
        """根据名称获取宗门"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sects WHERE name = ?', (name,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return Sect(
                id=row[0],
                name=row[1],
                description=row[2],
                founder_id=row[3],
                created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                member_count=row[5] or 1,
                contribution=row[6] or 0.0,
                is_active=bool(row[7]) if row[7] is not None else True
            )

    def get_all_sects(self) -> List[Sect]:
        """获取所有宗门"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sects WHERE is_active = TRUE')
            
            sects = []
            for row in cursor.fetchall():
                sects.append(Sect(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    founder_id=row[3],
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    member_count=row[5] or 1,
                    contribution=row[6] or 0.0,
                    is_active=bool(row[7]) if row[7] is not None else True
                ))
            
            return sects

    def update_sect(self, sect: Sect) -> bool:
        """更新宗门信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sects SET
                    description = ?,
                    founder_id = ?,
                    member_count = ?,
                    contribution = ?,
                    is_active = ?
                WHERE id = ?
            ''', (
                sect.description,
                sect.founder_id,
                sect.member_count,
                sect.contribution,
                sect.is_active,
                sect.id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def add_user_contribution(self, user_id: str, sect_id: int, contribution: float) -> bool:
        """添加用户对宗门的贡献"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查是否已有贡献记录
            cursor.execute('''
                SELECT id, contribution FROM user_sect_contributions 
                WHERE user_id = ? AND sect_id = ?
            ''', (user_id, sect_id))
            
            row = cursor.fetchone()
            if row:
                # 更新贡献值
                new_contribution = (row[1] or 0.0) + contribution
                cursor.execute('''
                    UPDATE user_sect_contributions 
                    SET contribution = ?, last_contribution_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_contribution, row[0]))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO user_sect_contributions (user_id, sect_id, contribution)
                    VALUES (?, ?, ?)
                ''', (user_id, sect_id, contribution))
            
            # 更新宗门总贡献
            cursor.execute('''
                UPDATE sects 
                SET contribution = contribution + ? 
                WHERE id = ?
            ''', (contribution, sect_id))
            
            conn.commit()
            return True

    def get_user_contribution(self, user_id: str, sect_id: int) -> Optional[UserSectContribution]:
        """获取用户对特定宗门的贡献"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_sect_contributions 
                WHERE user_id = ? AND sect_id = ?
            ''', (user_id, sect_id))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return UserSectContribution(
                id=row[0],
                user_id=row[1],
                sect_id=row[2],
                contribution=row[3] or 0.0,
                last_contribution_at=datetime.fromisoformat(row[4]) if row[4] else None
            )