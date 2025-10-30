from pathlib import Path

from astrbot.api import logger, AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image
import astrbot.api.message_components as Comp
from astrbot.api.star import Context, Star, register
# 从专门的指令配置文件导入
from data.plugins.astrbot_plugin_re_xiuxian_shell.commands import *
from .config_manager import ConfigManager
from .data import DataBase, MigrationManager
from .handlers import (
    MiscHandler, PlayerHandler, ShopHandler, SectHandler, CombatHandler, RealmHandler,
    EquipmentHandler, MapHandler, CreationHandler
)


@register(
    "astrbot_plugin_re_xiuxian_shell",
    "Shell",
    "重生之凡人修仙",
    "v0.0.1",
    "https://github.com/1592363624/astrbot_plugin_re_xiuxian_shell"
)
class XiuXianPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        _current_dir = Path(__file__).parent
        self.config_manager = ConfigManager(_current_dir)

        files_config = self.config.get("FILES", {})
        db_file = files_config.get("DATABASE_FILE", "re_xiuxian_data.db")
        self.db = DataBase(db_file)

        self.misc_handler = MiscHandler(self.db)
        self.player_handler = PlayerHandler(self.db, self.config, self.config_manager)
        self.shop_handler = ShopHandler(self.db, self.config_manager, self.config)  # 传入config
        self.sect_handler = SectHandler(self.db, self.config, self.config_manager)
        self.combat_handler = CombatHandler(self.db, self.config, self.config_manager)
        self.realm_handler = RealmHandler(self.db, self.config, self.config_manager)
        self.equipment_handler = EquipmentHandler(self.db, self.config_manager)
        self.map_handler = MapHandler(self.db, self.config_manager)
        self.creation_handler = CreationHandler(self.db, self.config, self.config_manager)

        access_control_config = self.config.get("ACCESS_CONTROL", {})
        self.whitelist_groups = [str(g) for g in access_control_config.get("WHITELIST_GROUPS", [])]

        logger.info("【重生之凡人修仙】 __init__ 方法成功执行完毕。")

    def _check_access(self, event: AstrMessageEvent) -> bool:
        """检查访问权限，支持群聊白名单控制
        
        返回值:
        - True: 允许访问
        - False: 拒绝访问
        """
        # 如果没有配置白名单，允许所有访问
        if not self.whitelist_groups:
            return True

        # 获取群组ID，私聊时为None
        group_id = event.get_group_id()

        # 如果是私聊，允许访问（私聊通常应该被允许）
        if not group_id:
            return True

        # 检查群组是否在白名单中
        if str(group_id) in self.whitelist_groups:
            return True

        return False

    async def _send_access_denied_message(self, event: AstrMessageEvent):
        """发送访问被拒绝的提示消息"""
        try:
            # message_chain = MessageChain().message("此群聊未在修仙插件的白名单中，无法使用相关功能。")
            # await event.send(message_chain)
            pass
        except:
            # 如果发送失败，静默处理
            pass

    async def initialize(self):
        await self.db.connect()
        migration_manager = MigrationManager(self.db.conn, self.config_manager)
        await migration_manager.migrate()
        logger.info("重生之凡人修仙插件已加载。")

    async def terminate(self):
        await self.db.close()
        logger.info("重生之凡人修仙插件已卸载。")

    # @filter.command(修仙帮助, "显示帮助信息")
    # async def handle_help(self, event: AstrMessageEvent):
    #     if not self._check_access(event):
    #         await self._send_access_denied_message(event)
    #         return
    #     async for r in self.misc_handler.handle_help(event): yield r

    @filter.command(我要修仙, "开始你的修仙之路")
    async def handle_start_xiuxian(self, event: AstrMessageEvent):
        """开始你的修仙之路"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.creation_handler.handle_new_player_story(event): yield r

    @filter.command(我的信息, "查看你的角色信息")
    async def handle_player_info(self, event: AstrMessageEvent):
        """查看你的角色信息"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.player_handler.handle_player_info(event): yield r

    @filter.command(签到, "每日签到领取奖励")
    async def handle_check_in(self, event: AstrMessageEvent):
        """每日签到领取奖励"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.player_handler.handle_check_in(event): yield r

    @filter.command(闭关, "开始闭关修炼")
    async def handle_start_cultivation(self, event: AstrMessageEvent):
        """开始闭关修炼"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.player_handler.handle_start_cultivation(event): yield r

    @filter.command(出关, "结束闭关修炼")
    async def handle_end_cultivation(self, event: AstrMessageEvent):
        """结束闭关修炼"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.player_handler.handle_end_cultivation(event): yield r

    @filter.command(突破, "尝试突破当前境界")
    async def handle_breakthrough(self, event: AstrMessageEvent):
        """尝试突破当前境界"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.player_handler.handle_breakthrough(event): yield r

    @filter.command(重入仙途, "花费灵石，重置灵根")
    async def handle_reroll_spirit_root(self, event: AstrMessageEvent):
        """花费灵石，重置灵根"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.player_handler.handle_reroll_spirit_root(event): yield r

    @filter.command(商店, "查看坊市商品")
    async def handle_shop(self, event: AstrMessageEvent):
        """查看坊市商品"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.shop_handler.handle_shop(event): yield r

    @filter.command(我的背包, "查看你的背包")
    async def handle_backpack(self, event: AstrMessageEvent):
        """查看你的背包"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.shop_handler.handle_backpack(event): yield r

    @filter.command(购买, "购买物品")
    async def handle_buy(self, event: AstrMessageEvent, item_name: str, quantity: int = 1):
        """购买+物品+数量（默认为1）:购买灵石2"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.shop_handler.handle_buy(event, item_name, quantity): yield r

    @filter.command(使用, "使用背包中的物品")
    async def handle_use(self, event: AstrMessageEvent, item_name: str, quantity: int = 1):
        """使用+物品+数量（默认为1）:使用灵液瓶2"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.shop_handler.handle_use(event, item_name, quantity): yield r

    @filter.command(创建宗门, "创建你的宗门")
    async def handle_create_sect(self, event: AstrMessageEvent, sect_name: str):
        """创建你的宗门"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.sect_handler.handle_create_sect(event, sect_name): yield r

    @filter.command(加入宗门, "加入一个宗门")
    async def handle_join_sect(self, event: AstrMessageEvent, sect_name: str):
        """加入宗门+宗门名字：加入宗门巅峰阁"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.sect_handler.handle_join_sect(event, sect_name): yield r

    @filter.command(退出宗门, "退出当前宗门")
    async def handle_leave_sect(self, event: AstrMessageEvent):
        """退出当前宗门"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.sect_handler.handle_leave_sect(event): yield r

    @filter.command(我的宗门, "查看我的宗门信息")
    async def handle_my_sect(self, event: AstrMessageEvent):
        """查看我的宗门信息"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.sect_handler.handle_my_sect(event): yield r

    @filter.command(切磋, "与其他玩家切磋")
    async def handle_spar(self, event: AstrMessageEvent):
        """与其他玩家切磋"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.combat_handler.handle_spar(event): yield r

    @filter.command(查看世界boss, "查看当前所有世界Boss")
    async def handle_boss_list(self, event: AstrMessageEvent):
        """查看当前所有世界Boss"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.combat_handler.handle_boss_list(event): yield r

    @filter.command(讨伐boss, "讨伐指定ID的世界Boss")
    async def handle_fight_boss(self, event: AstrMessageEvent, boss_id: str):
        """讨伐boss+bossID:讨伐boss1"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.combat_handler.handle_fight_boss(event, boss_id): yield r

    @filter.command(探索秘境, "根据当前境界，探索一个随机秘境")
    async def handle_enter_realm(self, event: AstrMessageEvent):
        """根据当前境界，探索一个随机秘境"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.realm_handler.handle_enter_realm(event): yield r

    @filter.command(前进, "在秘境中前进")
    async def handle_realm_advance(self, event: AstrMessageEvent):
        """在秘境中前进"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.realm_handler.handle_realm_advance(event): yield r

    @filter.command(离开秘境, "离开当前秘境")
    async def handle_leave_realm(self, event: AstrMessageEvent):
        """离开当前秘境"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.realm_handler.handle_leave_realm(event): yield r

    # --- 装备指令 ---
    @filter.command(卸下, "卸下一件装备")
    async def handle_unequip(self, event: AstrMessageEvent, subtype_name: str):
        """卸下+装备名:卸下尚方宝剑"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.equipment_handler.handle_unequip(event, subtype_name): yield r

    @filter.command(我的装备, "查看当前装备")
    async def handle_my_equipment(self, event: AstrMessageEvent):
        """查看当前装备"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.equipment_handler.handle_my_equipment(event): yield r

    # --- 地图指令 ---
    @filter.command(查看地图, "查看当前地图信息")
    async def handle_map_view(self, event: AstrMessageEvent):
        """查看当前地图信息"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.map_handler.handle_map_view(event): yield r

    @filter.command(移动, "移动到指定地图")
    async def handle_move(self, event: AstrMessageEvent, target_map: str):
        """移动+地图名:移动青云山脉"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.map_handler.handle_move(event, target_map): yield r

    @filter.command(世界地图, "查看世界地图")
    async def handle_world_map(self, event: AstrMessageEvent):
        """查看世界地图"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.map_handler.handle_world_map(event): yield r

    @filter.command(采集, "采集地图上的资源")
    async def handle_collect_resource(self, event: AstrMessageEvent, resource_name: str = ""):
        """采集+资源名:采集灵石矿脉"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.map_handler.handle_collect_resource(event, resource_name): yield r

    @filter.command(查看采集, "查看采集进度")
    async def handle_check_collection(self, event: AstrMessageEvent):
        """查看当前采集任务进度"""
        if not self._check_access(event):
            await self._send_access_denied_message(event)
            return
        async for r in self.map_handler.handle_check_collection(event): yield r


    # --- 角色创建指令 ---
    async def on_message(self, event: AstrMessageEvent):
        """消息处理入口"""
        # 处理玩家创建流程
        user_id = event.get_sender_id()
        creation_state = await self.db.get_player_creation_state(user_id)

        if creation_state == "awaiting_name":
            async for r in self.creation_handler.handle_player_name_input(event): yield r
            return

        if creation_state == "awaiting_avatar":
            async for r in self.creation_handler.handle_player_avatar_input(event): yield r
            return

        # 检查是否有已完成的资源采集任务
        completed_notifications = await self.map_handler.check_and_complete_resource_collections()
        for notification in completed_notifications:
            if notification["user_id"] == user_id:
                # 使用CQ码格式发送@消息
                message_chain = [
                    Comp.At(qq=user_id),
                    Comp.Plain(text=" " + notification['message'])
                ]
                yield event.chain_result(message_chain)

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_message(self, event: AstrMessageEvent):
        """处理普通消息，用于角色创建过程中的姓名输入等"""
        if not self._check_access(event):
            return

        user_id = event.get_sender_id()
        creation_state = await self.db.get_player_creation_state(user_id)

        # 如果用户处于角色创建状态，处理相应输入
        if creation_state == "awaiting_name":
            player_name = event.get_message_str().strip()
            # 排除命令消息
            if not player_name.startswith("/") and player_name != "我要修仙":
                async for r in self.creation_handler.handle_player_name_input(event, player_name):
                    yield r
                return

        elif creation_state == "awaiting_avatar":
            # 检查消息中是否包含图片
            messages = event.get_messages()
            has_image = any(isinstance(msg, Image) for msg in messages)

            if has_image:
                async for r in self.creation_handler.handle_player_avatar_input(event):
                    yield r
                return

        # 可以在这里添加更多基于状态的消息处理
