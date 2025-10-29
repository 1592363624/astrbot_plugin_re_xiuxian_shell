# handlers/map_handler.py
from astrbot.api.event import AstrMessageEvent
from .utils import player_required
from ..config_manager import ConfigManager
from ..data import DataBase
from ..models import Player

__all__ = ["MapHandler"]


class MapHandler:
    # 地图相关指令处理器

    def __init__(self, db: DataBase, config_manager: ConfigManager):
        self.db = db
        self.config_manager = config_manager

    @player_required
    async def handle_map_view(self, player: Player, event: AstrMessageEvent):
        """查看当前地图信息"""
        current_map_name = player.current_map
        map_data = self.config_manager.get_map_by_name(current_map_name)

        if not map_data:
            yield event.plain_result("地图数据异常，请联系管理员。")
            return

        map_id, map_info = map_data

        # 获取当前地图的玩家列表
        players_in_map = await self.db.get_players_in_map(current_map_name)
        player_names = [p.get_level(self.config_manager) + "-" + p.user_id[-4:] for p in players_in_map if
                        p.user_id != player.user_id]

        reply_lines = [
            f"📍当前位置：{current_map_name}",
            f"📝地图描述：{map_info['描述']}",
            f"🛡️安全区域：{'是' if map_info.get('安全区域', False) else '否'}"
        ]

        # 显示相邻区域
        if "相邻区域" in map_info and map_info["相邻区域"]:
            reply_lines.append("🚪相邻区域：" + "、".join(map_info["相邻区域"]))

        # 显示NPC
        if "NPC" in map_info and map_info["NPC"]:
            npc_names = [npc["名称"] for npc in map_info["NPC"]]
            reply_lines.append("🧙地图NPC：" + "、".join(npc_names))

        # 显示其他玩家
        if player_names:
            reply_lines.append("👥其他修士：" + "、".join(player_names) if player_names else "👥其他修士：无")
        else:
            reply_lines.append("👥其他修士：无")

        reply_lines.append("--------------------------")
        yield event.plain_result("\n".join(reply_lines))

    @player_required
    async def handle_move(self, player: Player, event: AstrMessageEvent, target_map: str):
        """移动到指定地图"""
        if not target_map:
            yield event.plain_result("指令格式错误！请使用「移动 <地图名>」。")
            return

        current_map_name = player.current_map
        current_map_data = self.config_manager.get_map_by_name(current_map_name)

        if not current_map_data:
            yield event.plain_result("当前地图数据异常，请联系管理员。")
            return

        current_map_id, current_map_info = current_map_data

        # 检查目标地图是否存在
        target_map_data = self.config_manager.get_map_by_name(target_map)
        if not target_map_data:
            yield event.plain_result(f"不存在名为「{target_map}」的地图。")
            return

        target_map_id, target_map_info = target_map_data

        # 检查目标地图是否与当前位置相邻
        if "相邻区域" not in current_map_info or target_map not in current_map_info["相邻区域"]:
            yield event.plain_result(f"无法直接前往「{target_map}」，该地图与当前位置不相邻。")
            return

        # 更新玩家位置
        p_clone = player.clone()
        p_clone.current_map = target_map
        await self.db.update_player(p_clone)

        yield event.plain_result(f"你已从「{current_map_name}」移动到「{target_map}」。")

    @player_required
    async def handle_world_map(self, player: Player, event: AstrMessageEvent):
        """查看世界地图"""
        if "地图" not in self.config_manager.world_map_data:
            yield event.plain_result("世界地图数据异常，请联系管理员。")
            return

        world_maps = self.config_manager.world_map_data["地图"]
        current_map_name = player.current_map

        reply_lines = ["🗺️世界地图："]
        for map_name, map_info in world_maps.items():
            prefix = "📍" if map_name == current_map_name else "  "
            safe_marker = "🛡️" if map_info.get("安全区域", False) else "⚔️"
            reply_lines.append(f"{prefix}{safe_marker} {map_name} - {map_info['描述']}")

        reply_lines.append("--------------------------")
        yield event.plain_result("\n".join(reply_lines))
