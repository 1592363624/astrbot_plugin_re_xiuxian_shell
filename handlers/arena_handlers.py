from typing import AsyncGenerator
from astrbot.api.event import AstrMessageEvent, MessageEventResult as EventResult
from astrbot.api import logger


async def battle(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """斗法"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取攻击者
    attacker = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not attacker.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 解析命令，获取被挑战者
    message = event.message_str.strip()
    if not message.startswith("斗法"):
        yield event.plain_result("命令格式错误，请使用：斗法 @对手")
        return
    
    # 获取被挑战者ID（简化处理，实际应该从消息中解析@的用户）
    # 这里需要根据平台具体实现解析被挑战者ID的逻辑
    # 暂时返回提示信息
    yield event.plain_result("斗法功能正在开发中...")


async def cultivation_ranking(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """修为排行榜"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 获取修为排行榜
    ranking = plugin.arena_service.get_cultivation_ranking(10)
    
    if not ranking:
        yield event.plain_result("暂无排行数据")
        return
    
    # 构造排行榜信息
    ranking_info = "=== 修为排行榜 ===\n"
    for i, rank_user in enumerate(ranking, 1):
        name = rank_user.dao_name or rank_user.nickname or f"修士{i}"
        ranking_info += f"第{i}名：{name} ({rank_user.realm}) - {int(rank_user.cultivation)} 修为\n"
    
    yield event.plain_result(ranking_info)


async def evil_ranking(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """恶人排行榜"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 获取恶人排行榜
    ranking = plugin.arena_service.get_evil_ranking(10)
    
    if not ranking:
        yield event.plain_result("暂无排行数据")
        return
    
    # 构造排行榜信息
    ranking_info = "=== 恶人排行榜 ===\n"
    for i, rank_user in enumerate(ranking, 1):
        name = rank_user.dao_name or rank_user.nickname or f"修士{i}"
        ranking_info += f"第{i}名：{name} - {rank_user.total_battle_win_count} 胜\n"
    
    yield event.plain_result(ranking_info)