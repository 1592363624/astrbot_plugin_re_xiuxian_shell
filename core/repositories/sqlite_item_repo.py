import sqlite3
from typing import Optional, List
from datetime import datetime
from ..domain.models import Item


class SqliteItemRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table()

    def _init_table(self):
        """初始化物品表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT,
                    rarity INTEGER DEFAULT 1,
                    effect TEXT,
                    effect_type TEXT,
                    effect_value REAL,
                    requirement TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def create_item(self, item: Item) -> bool:
        """创建物品模板"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO items (
                        name, type, description, rarity, 
                        effect, effect_type, effect_value, requirement
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.name, item.type, item.description, item.rarity,
                    item.effect, item.effect_type, item.effect_value, item.requirement
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_by_id(self, item_id: int) -> Optional[Item]:
        """根据ID获取物品"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return Item(
                id=row[0],
                name=row[1],
                type=row[2],
                description=row[3],
                rarity=row[4] or 1,
                effect=row[5],
                effect_type=row[6],
                effect_value=row[7],
                requirement=row[8],
                created_at=datetime.fromisoformat(row[9]) if row[9] else None
            )

    def get_by_name(self, name: str) -> Optional[Item]:
        """根据名称获取物品"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items WHERE name = ?', (name,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return Item(
                id=row[0],
                name=row[1],
                type=row[2],
                description=row[3],
                rarity=row[4] or 1,
                effect=row[5],
                effect_type=row[6],
                effect_value=row[7],
                requirement=row[8],
                created_at=datetime.fromisoformat(row[9]) if row[9] else None
            )

    def get_items_by_type(self, item_type: str) -> List[Item]:
        """根据类型获取物品列表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items WHERE type = ?', (item_type,))
            
            items = []
            for row in cursor.fetchall():
                items.append(Item(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    description=row[3],
                    rarity=row[4] or 1,
                    effect=row[5],
                    effect_type=row[6],
                    effect_value=row[7],
                    requirement=row[8],
                    created_at=datetime.fromisoformat(row[9]) if row[9] else None
                ))
            
            return items

    def get_all_items(self) -> List[Item]:
        """获取所有物品"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items')
            
            items = []
            for row in cursor.fetchall():
                items.append(Item(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    description=row[3],
                    rarity=row[4] or 1,
                    effect=row[5],
                    effect_type=row[6],
                    effect_value=row[7],
                    requirement=row[8],
                    created_at=datetime.fromisoformat(row[9]) if row[9] else None
                ))
            
            return items