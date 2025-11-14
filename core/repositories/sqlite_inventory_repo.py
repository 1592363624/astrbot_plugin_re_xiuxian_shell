import sqlite3
from typing import Optional, List
from datetime import datetime
from ..domain.models import UserItem


class SqliteInventoryRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table()

    def _init_table(self):
        """初始化用户物品表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            ''')
            conn.commit()

    def add_item(self, user_id: str, item_id: int, quantity: int = 1) -> bool:
        """给用户添加物品"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查用户是否已有该物品
            cursor.execute('''
                SELECT id, quantity FROM user_items 
                WHERE user_id = ? AND item_id = ?
            ''', (user_id, item_id))
            
            row = cursor.fetchone()
            if row:
                # 更新数量
                new_quantity = row[1] + quantity
                cursor.execute('''
                    UPDATE user_items 
                    SET quantity = ? 
                    WHERE id = ?
                ''', (new_quantity, row[0]))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO user_items (user_id, item_id, quantity)
                    VALUES (?, ?, ?)
                ''', (user_id, item_id, quantity))
            
            conn.commit()
            return True

    def remove_item(self, user_id: str, item_id: int, quantity: int = 1) -> bool:
        """从用户库存中移除物品"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查用户是否有足够数量的物品
            cursor.execute('''
                SELECT id, quantity FROM user_items 
                WHERE user_id = ? AND item_id = ?
            ''', (user_id, item_id))
            
            row = cursor.fetchone()
            if not row:
                return False
                
            current_quantity = row[1]
            if current_quantity < quantity:
                return False
                
            if current_quantity == quantity:
                # 删除记录
                cursor.execute('''
                    DELETE FROM user_items 
                    WHERE id = ?
                ''', (row[0],))
            else:
                # 更新数量
                new_quantity = current_quantity - quantity
                cursor.execute('''
                    UPDATE user_items 
                    SET quantity = ? 
                    WHERE id = ?
                ''', (new_quantity, row[0]))
            
            conn.commit()
            return True

    def get_user_items(self, user_id: str) -> List[UserItem]:
        """获取用户的所有物品"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, item_id, quantity, obtained_at
                FROM user_items 
                WHERE user_id = ?
            ''', (user_id,))
            
            items = []
            for row in cursor.fetchall():
                items.append(UserItem(
                    id=row[0],
                    user_id=row[1],
                    item_id=row[2],
                    quantity=row[3],
                    obtained_at=datetime.fromisoformat(row[4]) if row[4] else None
                ))
            
            return items

    def get_user_item(self, user_id: str, item_id: int) -> Optional[UserItem]:
        """获取用户特定物品"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, item_id, quantity, obtained_at
                FROM user_items 
                WHERE user_id = ? AND item_id = ?
            ''', (user_id, item_id))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return UserItem(
                id=row[0],
                user_id=row[1],
                item_id=row[2],
                quantity=row[3],
                obtained_at=datetime.fromisoformat(row[4]) if row[4] else None
            )

    def has_item(self, user_id: str, item_id: int, quantity: int = 1) -> bool:
        """检查用户是否有足够数量的物品"""
        user_item = self.get_user_item(user_id, item_id)
        if not user_item:
            return False
        return user_item.quantity >= quantity