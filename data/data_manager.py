# data/data_manager.py

import time
from dataclasses import fields
from typing import Optional, List, Dict, Any, Tuple

import aiosqlite

from astrbot.api import logger
from astrbot.api.star import StarTools
from ..config_manager import ConfigManager
from ..models import Player, PlayerEffect, ActiveWorldBoss


class DataBase:
    """数据库管理器，封装所有数据库操作"""

    def __init__(self, db_file_name: str):
        data_dir = StarTools.get_data_dir("re_xiuxian")
        data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = data_dir / db_file_name
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        if self.conn is None:
            self.conn = await aiosqlite.connect(self.db_path)
            self.conn.row_factory = aiosqlite.Row
            logger.info(f"数据库连接已创建: {self.db_path}")

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None
            logger.info("数据库连接已关闭。")

    async def get_all_players(self) -> List[Player]:
        """获取所有玩家"""
        try:
            async with self.conn.execute("SELECT * FROM players") as cursor:
                rows = await cursor.fetchall()
                return [Player(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"获取所有玩家数据时出错: {e}")
            return []

    async def get_active_bosses(self) -> List[ActiveWorldBoss]:
        async with self.conn.execute("SELECT * FROM active_world_bosses") as cursor:
            rows = await cursor.fetchall()
            return [ActiveWorldBoss(**dict(row)) for row in rows]

    async def create_active_boss(self, boss: ActiveWorldBoss):
        await self.conn.execute(
            "INSERT INTO active_world_bosses (boss_id, current_hp, max_hp, spawned_at, level_index) VALUES (?, ?, ?, ?, ?)",
            (boss.boss_id, boss.current_hp, boss.max_hp, boss.spawned_at, boss.level_index)
        )
        await self.conn.commit()

    async def update_active_boss_hp(self, boss_id: str, new_hp: int):
        await self.conn.execute(
            "UPDATE active_world_bosses SET current_hp = ? WHERE boss_id = ?",
            (new_hp, boss_id)
        )
        await self.conn.commit()

    async def delete_active_boss(self, boss_id: str):
        await self.conn.execute("DELETE FROM active_world_bosses WHERE boss_id = ?", (boss_id,))
        await self.conn.commit()

    async def record_boss_damage(self, boss_id: str, user_id: str, user_name: str, damage: int):
        await self.conn.execute("""
                                INSERT INTO world_boss_participants (boss_id, user_id, user_name, total_damage)
                                VALUES (?, ?, ?, ?) ON CONFLICT(boss_id, user_id) DO
                                UPDATE SET total_damage = total_damage + excluded.total_damage;
                                """, (boss_id, user_id, user_name, damage))
        await self.conn.commit()

    async def get_boss_participants(self, boss_id: str) -> List[Dict[str, Any]]:
        sql = "SELECT user_id, user_name, total_damage FROM world_boss_participants WHERE boss_id = ? ORDER BY total_damage DESC"
        async with self.conn.execute(sql, (boss_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def clear_boss_data(self, boss_id: str):
        try:
            await self.conn.execute("BEGIN")
            await self.conn.execute("DELETE FROM active_world_bosses WHERE boss_id = ?", (boss_id,))
            await self.conn.execute("DELETE FROM world_boss_participants WHERE boss_id = ?", (boss_id,))
            await self.conn.commit()
            logger.info(f"Boss {boss_id} 的数据已清理。")
        except aiosqlite.Error as e:
            await self.conn.rollback()
            logger.error(f"清理Boss {boss_id} 数据失败: {e}")

    async def get_top_players(self, limit: int) -> List[Player]:
        async with self.conn.execute(
                "SELECT * FROM players ORDER BY level_index DESC, experience DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [Player(**dict(row)) for row in rows]

    async def get_player_by_id(self, user_id: str) -> Optional[Player]:
        async with self.conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return Player(**dict(row)) if row else None

    async def create_player(self, player: Player):
        player_fields = [f.name for f in fields(Player)]
        columns = ", ".join(player_fields)
        placeholders = ", ".join([f":{f}" for f in player_fields])
        sql = f"INSERT INTO players ({columns}) VALUES ({placeholders})"
        await self.conn.execute(sql, player.__dict__)
        await self.conn.commit()

    async def update_player(self, player: Player):
        player_fields = [f.name for f in fields(Player) if f.name != 'user_id']
        set_clause = ", ".join([f"{f} = :{f}" for f in player_fields])
        sql = f"UPDATE players SET {set_clause} WHERE user_id = :user_id"
        await self.conn.execute(sql, player.__dict__)
        await self.conn.commit()

    async def update_players_in_transaction(self, players: List[Player]):
        if not players:
            return
        player_fields = [f.name for f in fields(Player) if f.name != 'user_id']
        set_clause = ", ".join([f"{f} = :{f}" for f in player_fields])
        sql = f"UPDATE players SET {set_clause} WHERE user_id = :user_id"
        try:
            await self.conn.execute("BEGIN")
            for player in players:
                await self.conn.execute(sql, player.__dict__)
            await self.conn.commit()
        except aiosqlite.Error as e:
            await self.conn.rollback()
            logger.error(f"批量更新玩家事务失败: {e}")
            raise

    async def create_sect(self, sect_name: str, leader_id: str) -> int:
        async with self.conn.execute("INSERT INTO sects (name, leader_id) VALUES (?, ?)",
                                     (sect_name, leader_id)) as cursor:
            await self.conn.commit()
            return cursor.lastrowid

    async def delete_sect(self, sect_id: int):
        await self.conn.execute("DELETE FROM sects WHERE id = ?", (sect_id,))
        await self.conn.commit()

    async def get_sect_by_name(self, sect_name: str) -> Optional[Dict[str, Any]]:
        async with self.conn.execute("SELECT * FROM sects WHERE name = ?", (sect_name,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_sect_by_id(self, sect_id: int) -> Optional[Dict[str, Any]]:
        async with self.conn.execute("SELECT * FROM sects WHERE id = ?", (sect_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_sect_members(self, sect_id: int) -> List[Player]:
        async with self.conn.execute("SELECT * FROM players WHERE sect_id = ?", (sect_id,)) as cursor:
            rows = await cursor.fetchall()
            return [Player(**dict(row)) for row in rows]

    async def update_player_sect(self, user_id: str, sect_id: Optional[int], sect_name: Optional[str]):
        await self.conn.execute("UPDATE players SET sect_id = ?, sect_name = ? WHERE user_id = ?",
                                (sect_id, sect_name, user_id))
        await self.conn.commit()

    async def get_inventory_by_user_id(self, user_id: str, config_manager: ConfigManager) -> List[Dict[str, Any]]:
        async with self.conn.execute("SELECT item_id, quantity FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            inventory_list = []
            for row in rows:
                item_id, quantity = row['item_id'], row['quantity']
                item_info = config_manager.item_data.get(str(item_id))
                if item_info:
                    inventory_list.append({
                        "item_id": item_id, "name": item_info.name,
                        "quantity": quantity, "description": item_info.description,
                        "rank": item_info.rank, "type": item_info.type
                    })
                else:
                    inventory_list.append({
                        "item_id": item_id, "name": f"未知物品(ID:{item_id})",
                        "quantity": quantity, "description": "此物品信息已丢失",
                        "rank": "未知", "type": "未知"
                    })
            return inventory_list

    async def get_item_from_inventory(self, user_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        async with self.conn.execute("SELECT item_id, quantity FROM inventory WHERE user_id = ? AND item_id = ?",
                                     (user_id, item_id)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def set_player_creation_state(self, user_id: str, state: str):
        """设置玩家创建状态"""
        await self.conn.execute("""
            INSERT OR REPLACE INTO player_creation_states (user_id, state)
            VALUES (?, ?)
        """, (user_id, state))
        await self.conn.commit()

    async def get_player_creation_state(self, user_id: str) -> Optional[str]:
        """获取玩家创建状态"""
        async with self.conn.execute("""
                                     SELECT state
                                     FROM player_creation_states
                                     WHERE user_id = ?
                                     """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row['state'] if row else None

    async def set_player_creation_data(self, user_id: str, key: str, value: str):
        """设置玩家创建数据"""
        await self.conn.execute("""
            INSERT OR REPLACE INTO player_creation_data (user_id, data_key, data_value)
            VALUES (?, ?, ?)
        """, (user_id, key, value))
        await self.conn.commit()

    async def clear_player_creation_state(self, user_id: str):
        """清除玩家创建状态"""
        await self.conn.execute("DELETE FROM player_creation_states WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def add_items_to_inventory_in_transaction(self, user_id: str, items: Dict[str, int]):
        try:
            await self.conn.execute("BEGIN")
            for item_id, quantity in items.items():
                await self.conn.execute("""
                                        INSERT INTO inventory (user_id, item_id, quantity)
                                        VALUES (?, ?, ?) ON CONFLICT(user_id, item_id) DO
                                        UPDATE SET quantity = quantity + excluded.quantity;
                                        """, (user_id, item_id, quantity))
            await self.conn.commit()
        except aiosqlite.Error as e:
            await self.conn.rollback()
            logger.error(f"批量添加物品事务失败: {e}")
            raise

    async def remove_item_from_inventory(self, user_id: str, item_id: str, quantity: int = 1) -> bool:
        try:
            await self.conn.execute("BEGIN")
            cursor = await self.conn.execute("""
                                             UPDATE inventory
                                             SET quantity = quantity - ?
                                             WHERE user_id = ?
                                               AND item_id = ?
                                               AND quantity >= ?
                                             """, (quantity, user_id, item_id, quantity))

            if cursor.rowcount == 0:
                await self.conn.rollback()
                return False

            await self.conn.execute("DELETE FROM inventory WHERE user_id = ? AND item_id = ? AND quantity <= 0",
                                    (user_id, item_id))
            await self.conn.commit()
            return True
        except aiosqlite.Error as e:
            await self.conn.rollback()
            logger.error(f"移除物品事务失败: {e}")
            return False

    async def transactional_buy_item(self, user_id: str, item_id: str, quantity: int, total_cost: int) -> Tuple[
        bool, str]:
        try:
            await self.conn.execute("BEGIN")
            cursor = await self.conn.execute(
                "UPDATE players SET gold = gold - ? WHERE user_id = ? AND gold >= ?",
                (total_cost, user_id, total_cost)
            )
            if cursor.rowcount == 0:
                await self.conn.rollback()
                return False, "ERROR_INSUFFICIENT_FUNDS"

            await self.conn.execute("""
                                    INSERT INTO inventory (user_id, item_id, quantity)
                                    VALUES (?, ?, ?) ON CONFLICT(user_id, item_id) DO
                                    UPDATE SET quantity = quantity + excluded.quantity;
                                    """, (user_id, item_id, quantity))

            await self.conn.commit()
            return True, "SUCCESS"
        except aiosqlite.Error as e:
            await self.conn.rollback()
            logger.error(f"购买物品事务失败: {e}")
            return False, "ERROR_DATABASE"

    async def transactional_apply_item_effect(self, user_id: str, item_id: str, quantity: int,
                                              effect: PlayerEffect) -> bool:
        try:
            await self.conn.execute("BEGIN")
            cursor = await self.conn.execute(
                "UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND item_id = ? AND quantity >= ?",
                (quantity, user_id, item_id, quantity)
            )
            if cursor.rowcount == 0:
                await self.conn.rollback()
                return False

            await self.conn.execute("DELETE FROM inventory WHERE user_id = ? AND item_id = ? AND quantity <= 0",
                                    (user_id, item_id))

            await self.conn.execute(
                """
                UPDATE players
                SET experience = experience + ?,
                    gold       = gold + ?,
                    hp         = MIN(max_hp, hp + ?)
                WHERE user_id = ?
                """,
                (effect.experience, effect.gold, effect.hp, user_id)
            )
            await self.conn.commit()
            return True
        except aiosqlite.Error as e:
            await self.conn.rollback()
            logger.error(f"使用物品事务失败: {e}")
            return False

    async def get_players_in_map(self, map_name: str) -> List[Player]:
        """获取指定地图中的所有玩家"""
        async with self.conn.execute("SELECT * FROM players WHERE current_map = ?", (map_name,)) as cursor:
            rows = await cursor.fetchall()
            return [Player(**dict(row)) for row in rows]

    async def get_player_avatar(self, user_id: str) -> str:
        """获取玩家形象数据"""
        async with self.conn.execute(
                "SELECT data_value FROM player_creation_data WHERE user_id = ? AND data_key = ?",
                (user_id, "avatar")
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "default_avatar"

    async def get_player_avatar_data(self, user_id: str) -> str:
        """获取玩家完整形象数据（可能是base64或文件路径）"""
        # 首先尝试从players表获取（这是主要的存储位置）
        async with self.conn.execute(
                "SELECT avatar FROM players WHERE user_id = ?",
                (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return row[0]

        # 如果players表中没有，则尝试从player_creation_data获取（向后兼容）
        async with self.conn.execute(
                "SELECT data_value FROM player_creation_data WHERE user_id = ? AND data_key = ?",
                (user_id, "avatar")
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]

        return "default_avatar"

    async def get_map_resources(self, map_name: str) -> Dict[str, Dict[str, Any]]:
        """获取指定地图的所有资源点当前状态"""
        async with self.conn.execute(
                "SELECT resource_name, current_quantity, last_refresh_time FROM map_resources WHERE map_name = ?",
                (map_name,)) as cursor:
            rows = await cursor.fetchall()
            return {row['resource_name']: {
                'current_quantity': row['current_quantity'],
                'last_refresh_time': row['last_refresh_time']
            } for row in rows}

    async def get_map_resource(self, map_name: str, resource_name: str) -> Optional[Dict[str, Any]]:
        """获取指定地图中特定资源点的当前状态"""
        async with self.conn.execute(
                "SELECT current_quantity, last_refresh_time FROM map_resources WHERE map_name = ? AND resource_name = ?",
                (map_name, resource_name)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_map_resource(self, map_name: str, resource_name: str, current_quantity: int,
                                  last_refresh_time: float):
        """更新地图资源点状态"""
        await self.conn.execute("""
            INSERT OR REPLACE INTO map_resources 
            (map_name, resource_name, current_quantity, last_refresh_time)
            VALUES (?, ?, ?, ?)
        """, (map_name, resource_name, current_quantity, last_refresh_time))
        await self.conn.commit()

    async def add_resource_collection_task(self, user_id: str, map_name: str, resource_name: str,
                                           start_time: float, completion_time: float, quantity: int,
                                           session_id: str = None):
        """添加资源采集任务"""
        await self.conn.execute("""
                                INSERT INTO resource_collection_queue
                                (user_id, map_name, resource_name, start_time, completion_time, quantity, session_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (user_id, map_name, resource_name, start_time, completion_time, quantity, session_id))
        await self.conn.commit()

    async def get_user_active_collection_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户正在进行的采集任务"""
        async with self.conn.execute(
                "SELECT * FROM resource_collection_queue WHERE user_id = ? AND collected = FALSE",
                (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_resource_collection_task(self, user_id: str, map_name: str, resource_name: str) -> Optional[
        Dict[str, Any]]:
        """获取用户对特定资源的采集任务"""
        async with self.conn.execute(
                """SELECT *
                   FROM resource_collection_queue
                   WHERE user_id = ?
                     AND map_name = ?
                     AND resource_name = ?
                     AND collected = FALSE""",
                (user_id, map_name, resource_name)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_completed_resource_collection_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户已完成的采集任务"""
        async with self.conn.execute(
                "SELECT * FROM resource_collection_queue WHERE user_id = ? AND completion_time <= ? AND collected = FALSE",
                (user_id, time.time())) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_all_pending_resource_tasks(self) -> List[Dict[str, Any]]:
        """获取所有待完成的资源采集任务"""
        current_time = time.time()
        async with self.conn.execute(
                "SELECT * FROM resource_collection_queue WHERE completion_time <= ? AND collected = FALSE",
                (current_time,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def complete_resource_collection_task(self, task_id: int) -> bool:
        """完成资源采集任务"""
        try:
            await self.conn.execute("BEGIN")
            # 更新任务状态为已完成
            await self.conn.execute(
                "UPDATE resource_collection_queue SET collected = TRUE WHERE id = ?",
                (task_id,)
            )

            # 检查是否更新成功
            async with self.conn.execute(
                    "SELECT collected FROM resource_collection_queue WHERE id = ?",
                    (task_id,)) as cursor:
                row = await cursor.fetchone()
                if not row or not row['collected']:
                    await self.conn.rollback()
                    return False

            await self.conn.commit()
            return True
        except aiosqlite.Error as e:
            await self.conn.rollback()
            logger.error(f"完成资源采集任务失败: {e}")
            return False

    async def remove_completed_resource_collection_task(self, task_id: int):
        """移除已完成的采集任务"""
        await self.conn.execute("DELETE FROM resource_collection_queue WHERE id = ?", (task_id,))
        await self.conn.commit()
