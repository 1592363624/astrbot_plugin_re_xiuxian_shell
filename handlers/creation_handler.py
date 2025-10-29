# handlers/creation_handler.py
from astrbot.api import AstrBotConfig
from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import Image
from ..config_manager import ConfigManager
from ..core import CultivationManager
from ..data import DataBase

__all__ = ["CreationHandler"]


class CreationHandler:
    # 玩家创建相关处理器

    def __init__(self, db: DataBase, config: AstrBotConfig, config_manager: ConfigManager):
        self.db = db
        self.config = config
        self.config_manager = config_manager
        self.cultivation_manager = CultivationManager(config, config_manager)

    async def handle_new_player_story(self, event: AstrMessageEvent):
        """处理新玩家的开场白剧情"""
        user_id = event.get_sender_id()
        if await self.db.get_player_by_id(user_id):
            yield event.plain_result("道友，你已踏入仙途，无需重复此举。")
            return

        # 开场白剧情
        story_lines = [
            "混沌初开，天地始分。",
            "在这浩瀚的修仙世界中，你从沉睡中苏醒。",
            "你发现自己身处一片荒芜之地，四周空无一人。",
            "一个苍老的声音在你耳边响起：",
            "「孩子，你终于醒了。这个世界需要新的修仙者来维护它的平衡。」",
            "「不过，修仙之路漫长而艰辛，你需要先在这个世界立足。」",
            "「告诉我，你的名字是什么？（请回复你的角色名）」"
        ]

        yield event.plain_result("\n".join(story_lines))
        # 设置玩家状态为等待输入名字
        await self.db.set_player_creation_state(user_id, "awaiting_name")

    async def handle_player_name_input(self, event: AstrMessageEvent, player_name: str):
        """处理玩家输入名字"""
        user_id = event.get_sender_id()
        creation_state = await self.db.get_player_creation_state(user_id)

        if creation_state != "awaiting_name":
            return

        if not player_name or len(player_name) < 1 or len(player_name) > 10:
            yield event.plain_result("名字长度需在1-10个字符之间，请重新输入你的角色名：")
            return

        # 保存玩家名字
        await self.db.set_player_creation_data(user_id, "name", player_name)

        story_lines = [
            f"「{player_name}，好名字！」老者满意地点头。",
            "「接下来，你需要选择一个形象来代表你在这个世界的模样。」",
            "「请发送一张图片作为你的形象。」"
        ]

        yield event.plain_result("\n".join(story_lines))
        # 设置玩家状态为等待输入形象
        await self.db.set_player_creation_state(user_id, "awaiting_avatar")

    async def handle_player_avatar_input(self, event: AstrMessageEvent):
        """处理玩家输入形象"""
        user_id = event.get_sender_id()
        creation_state = await self.db.get_player_creation_state(user_id)

        if creation_state != "awaiting_avatar":
            return

        # 检查是否有图片
        messages = event.get_messages()
        image_components = [msg for msg in messages if isinstance(msg, Image)]

        if not image_components:
            yield event.plain_result("请发送一张图片作为你的形象。")
            return

        # 保存玩家形象
        # 获取第一张图片
        image_component = image_components[0]

        # 尝试获取图片的URL或Base64数据
        avatar_data = "custom_avatar"  # 默认值

        try:
            # 尝试获取图片的base64数据
            image_base64 = await image_component.convert_to_base64()
            if image_base64:
                avatar_data = f"base64://{image_base64}"
        except Exception as e:
            # logger.error(f"获取图片base64数据失败: {e}")
            try:
                # 如果base64获取失败，尝试获取文件路径
                image_path = await image_component.convert_to_file_path()
                if image_path:
                    avatar_data = f"file://{image_path}"
            except Exception as e:
                # logger.error(f"获取图片文件路径失败: {e}")
                # 如果都失败了，就使用默认值
                pass

        # 保存玩家形象数据
        await self.db.set_player_creation_data(user_id, "avatar", avatar_data)

        # 创建玩家角色
        new_player = self.cultivation_manager.generate_new_player_stats(user_id)
        # 设置玩家初始位置为青云镇
        new_player.current_map = "青云镇"
        # 设置玩家头像
        new_player.avatar = avatar_data

        await self.db.create_player(new_player)
        # 清除创建状态，但保留avatar数据
        await self.db.conn.execute("DELETE FROM player_creation_states WHERE user_id = ?", (user_id,))
        await self.db.conn.commit()

        story_lines = [
            "「很好，现在你有了在这个世界立足的形象。」",
            "「接下来，你需要通过自己的努力在这个世界生存下去。」",
            "「你可以通过挖矿、砍伐、采集等方式获取资源，然后建造属于你的家园。」",
            "「当你积累足够的资源后，就可以踏上真正的修仙之路了。」",
            "「发送「我的信息」查看状态，「查看地图」了解周围环境！」",
            "「祝你好运，未来的修仙者！」"
        ]

        yield event.plain_result("\n".join(story_lines))
