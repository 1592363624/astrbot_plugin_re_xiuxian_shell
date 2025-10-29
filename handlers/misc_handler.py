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
            "这是皇帝的新帮助"
        )
        yield event.plain_result(help_text)
