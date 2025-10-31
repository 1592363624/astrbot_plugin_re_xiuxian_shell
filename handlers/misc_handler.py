# handlers/misc_handler.py
from astrbot.api.event import AstrMessageEvent
# 从专门的指令配置文件导入
from ..data import DataBase

__all__ = ["MiscHandler"]


class MiscHandler:
    # 杂项指令处理器

    def __init__(self, db: DataBase):
        self.db = db

    async def handle_help(self, event: AstrMessageEvent):
        help_text = (
            "这是皇帝的新帮助\n"
            "----------\n"
            "📖 基础指令:\n"
            "  我要修仙 - 创建角色\n"
            "  我的信息 - 查看个人信息\n"
            "  签到 - 每日签到领取灵石\n"
            "  闭关/出关 - 修炼获取修为\n"
            "  突破 - 突破境界\n"
            "  我的背包 - 查看背包物品\n"
            "  坊市 - 查看商店\n"
            "  购买 <物品名> [数量] - 购买物品\n"
            "  使用 <物品名> [数量] - 使用物品\n"
            "  重入仙途 - 重新随机灵根\n"
            "----------\n"
            "🗺️ 地图指令:\n"
            "  地图 - 查看当前地图\n"
            "  世界地图 - 查看所有地图\n"
            "  移动 <地图名> - 移动到指定地图\n"
            "  采集 <资源名> - 采集资源(消耗灵力)\n"
            "  我的采集 - 查看采集进度\n"
            "----------\n"
            "⚔️ 战斗指令:\n"
            "  秘境 - 进入秘境探险\n"
            "  前进 - 在秘境中前进\n"
            "  离开秘境 - 离开秘境\n"
            "----------\n"
            "👥 社交指令:\n"
            "  创建宗门 <宗门名> - 创建宗门\n"
            "  解散宗门 - 解散自己的宗门\n"
            "  宗门列表 - 查看所有宗门\n"
            "  加入宗门 <宗门名> - 加入宗门\n"
            "  退出宗门 - 退出当前宗门\n"
            "  我的宗门 - 查看宗门信息\n"
            "----------\n"
            "✨ 新增灵力系统:\n"
            "  灵力会在你进行采集等操作时消耗\n"
            "  每分钟自动回复1点灵力\n"
        )
        yield event.plain_result(help_text)