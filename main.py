import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from astrbot.api import logger, AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter, MessageChain
from astrbot.api.star import Context, Star
from astrbot.core.star.filter.permission import PermissionType

# ==========================================================
# 导入仓储层 & 服务层
# ==========================================================
from .core.repositories.sqlite_user_repo import SqliteUserRepository
from .core.repositories.sqlite_item_repo import SqliteItemRepository
from .core.repositories.sqlite_inventory_repo import SqliteInventoryRepository
from .core.repositories.sqlite_sect_repo import SqliteSectRepository
from .core.repositories.sqlite_log_repo import SqliteLogRepository

from .core.services.data_setup_service import DataSetupService
from .core.services.user_service import UserService
from .core.services.cultivation_service import CultivationService
from .core.services.inventory_service import InventoryService
from .core.services.sect_service import SectService
from .core.services.arena_service import ArenaService # noqa: F401

from .core.database.migration import run_migrations

# ==========================================================
# 导入指令函数
# ==========================================================
from .handlers import cultivation_handlers, sect_handlers, inventory_handlers, arena_handlers  # noqa: F401


class XiuxianPlugin(Star):
    
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        
        # 插件ID
        self.plugin_id = "astrbot_plugin_re_xiuxian"
        
        # --- 数据与临时文件路径管理 ---
        try:
            # 使用框架提供的 get_data_dir 方法
            from astrbot.api.star import StarTools
            self.data_dir = StarTools.get_data_dir(self.plugin_id)
        except (AttributeError, TypeError):
            # 如果方法不存在或调用失败，则回退到旧的硬编码路径
            logger.warning(f"无法使用 StarTools.get_data_dir('{self.plugin_id}'), 将回退到旧的 'data/' 目录。")
            self.data_dir = "data"
        
        self.tmp_dir = os.path.join(self.data_dir, "tmp")
        os.makedirs(self.tmp_dir, exist_ok=True)
        
        db_path = os.path.join(self.data_dir, "re_xiuxian.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # --- 配置 ---
        xiuxian_config = config.get("re_xiuxian", {})
        self.game_config = {
            "cultivation": {
                "base_exp_gain": xiuxian_config.get("base_exp_gain", 10),
                "closed_door_cooldown": xiuxian_config.get("closed_door_cooldown", 600),  # 10分钟
                "deep_closed_door_duration": xiuxian_config.get("deep_closed_door_duration", 28800),  # 8小时
                "deep_closed_door_cooldown": xiuxian_config.get("deep_closed_door_cooldown", 79200),  # 22小时
            },
            "sect": {
                "default_sects": xiuxian_config.get("default_sects", [
                    "黄枫谷", "太一门", "合欢宗", "星宫", "万灵宗", "黑煞教"
                ])
            },
            "arena": {
                "battle_cooldown": xiuxian_config.get("battle_cooldown", 300)  # 5分钟
            }
        }
        
        # 初始化数据库模式
        plugin_root_dir = os.path.dirname(__file__)
        migrations_path = os.path.join(plugin_root_dir, "core", "database", "migrations")
        run_migrations(db_path, migrations_path)
        
        # --- 实例化仓储层 ---
        self.user_repo = SqliteUserRepository(db_path)
        self.item_repo = SqliteItemRepository(db_path)
        self.inventory_repo = SqliteInventoryRepository(db_path)
        self.sect_repo = SqliteSectRepository(db_path)
        self.log_repo = SqliteLogRepository(db_path)
        
        # --- 实例化服务层 ---
        self.user_service = UserService(self.user_repo)
        self.cultivation_service = CultivationService(
            self.user_repo, 
            self.inventory_repo, 
            self.log_repo, 
            self.game_config
        )
        self.inventory_service = InventoryService(
            self.inventory_repo,
            self.user_repo,
            self.item_repo,
            self.game_config
        )
        self.sect_service = SectService(
            self.sect_repo,
            self.user_repo,
            self.inventory_repo,
            self.game_config
        )
        self.arena_service = ArenaService(
            self.user_repo,
            self.inventory_repo,
            self.log_repo,
            self.game_config
        )
        
        # --- 初始化核心游戏数据 ---
        data_setup_service = DataSetupService(
            self.item_repo, self.sect_repo
        )
        data_setup_service.setup_initial_data()
        
        logger.info("修仙插件初始化完成")

    async def initialize(self):
        """插件初始化"""
        logger.info("""
        __  __        _ _           
        \ \/ /       (_) |          
         \  /   _ _ __ _| | _____  __
         /  \  | | '__| | |/ / \ \/ /
        /_/\_\ |_|_|  | |   <   >  < 
                      |_|\_\  /_/\_\\
        
        修仙插件加载成功！
        """)
    
    # =========== 修仙基础命令 ==========

    @filter.command("检测灵根")
    async def detect_talent(self, event: AstrMessageEvent):
        """开启修仙之路的唯一方式"""
        async for r in cultivation_handlers.detect_talent(self, event):
            yield r

    @filter.command("我的灵根")
    async def my_talent(self, event: AstrMessageEvent):
        """查看自己的修仙档案"""
        async for r in cultivation_handlers.my_talent(self, event):
            yield r

    @filter.command("闭关修炼")
    async def closed_door_cultivation(self, event: AstrMessageEvent):
        """主动进行修炼，获取修为"""
        async for r in cultivation_handlers.closed_door_cultivation(self, event):
            yield r

    @filter.command("深度闭关")
    async def deep_closed_door(self, event: AstrMessageEvent):
        """开启自动挂机修炼"""
        async for r in cultivation_handlers.deep_closed_door(self, event):
            yield r

    @filter.command("查看闭关")
    async def check_deep_cultivation(self, event: AstrMessageEvent):
        """查看深度闭关剩余时间"""
        async for r in cultivation_handlers.check_deep_cultivation(self, event):
            yield r

    @filter.command("强行出关")
    async def force_exit_cultivation(self, event: AstrMessageEvent):
        """提前结束深度闭关"""
        async for r in cultivation_handlers.force_exit_cultivation(self, event):
            yield r

    @filter.command("避世")
    async def hermit_mode(self, event: AstrMessageEvent):
        """开启和平模式"""
        async for r in cultivation_handlers.hermit_mode(self, event):
            yield r

    @filter.command("入世")
    async def return_world(self, event: AstrMessageEvent):
        """关闭和平模式"""
        async for r in cultivation_handlers.return_world(self, event):
            yield r

    # =========== 宗门命令 ==========

    @filter.command("拜入宗门")
    async def join_sect(self, event: AstrMessageEvent):
        """尝试加入一个宗门"""
        async for r in sect_handlers.join_sect(self, event):
            yield r

    @filter.command("我的宗门")
    async def my_sect(self, event: AstrMessageEvent):
        """查看当前所属宗门信息"""
        async for r in sect_handlers.my_sect(self, event):
            yield r

    @filter.command("叛出宗门")
    async def betray_sect(self, event: AstrMessageEvent):
        """脱离当前宗门"""
        async for r in sect_handlers.betray_sect(self, event):
            yield r

    @filter.command("宗门点卯")
    async def sect_roll_call(self, event: AstrMessageEvent):
        """每日点卯领取贡献"""
        async for r in sect_handlers.sect_roll_call(self, event):
            yield r

    # =========== 背包与物品命令 ==========

    @filter.command("储物袋")
    async def inventory(self, event: AstrMessageEvent):
        """查看拥有的所有物品"""
        async for r in inventory_handlers.inventory(self, event):
            yield r

    @filter.command("服用")
    async def take_pill(self, event: AstrMessageEvent):
        """使用储物袋中的丹药"""
        async for r in inventory_handlers.take_pill(self, event):
            yield r

    @filter.command("炼制")
    async def alchemy(self, event: AstrMessageEvent):
        """炼制已学会的丹药或法宝"""
        async for r in inventory_handlers.alchemy(self, event):
            yield r

    @filter.command("学习")
    async def learn(self, event: AstrMessageEvent):
        """学习配方"""
        async for r in inventory_handlers.learn(self, event):
            yield r

    @filter.command("赠送")
    async def give_item(self, event: AstrMessageEvent):
        """将物品赠送给其他道友"""
        async for r in inventory_handlers.give_item(self, event):
            yield r

    # =========== 斗法命令 ==========

    @filter.command("斗法")
    async def battle(self, event: AstrMessageEvent):
        """与其他修士斗法"""
        async for r in arena_handlers.battle(self, event):
            yield r

    @filter.command("修为榜")
    async def cultivation_ranking(self, event: AstrMessageEvent):
        """查看修为排行榜"""
        async for r in arena_handlers.cultivation_ranking(self, event):
            yield r

    @filter.command("恶人榜")
    async def evil_ranking(self, event: AstrMessageEvent):
        """查看恶人排行榜"""
        async for r in arena_handlers.evil_ranking(self, event):
            yield r