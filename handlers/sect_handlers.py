from typing import AsyncGenerator
from astrbot.api.event import AstrMessageEvent, MessageEventResult as EventResult
from astrbot.api import logger


async def join_sect(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """加入宗门"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 解析宗门名称
    message = event.message_str.strip()
    if not message.startswith("拜入宗门"):
        yield event.plain_result("命令格式错误，请使用：拜入宗门 <宗门名>")
        return
        
    sect_name = message[5:].strip()  # 去掉"拜入宗门 "
    if not sect_name:
        yield event.plain_result("请指定要加入的宗门名称")
        return
    
    # 加入宗门
    success, message = plugin.sect_service.join_sect(user, sect_name)
    yield event.plain_result(message)


async def my_sect(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """查看宗门信息"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 检查是否有宗门
    if not user.sect_id:
        yield event.plain_result("你目前没有加入任何宗门")
        return
    
    # 获取宗门信息
    sect = plugin.sect_service.get_user_sect(user)
    if not sect:
        yield event.plain_result("宗门信息异常")
        return
    
    # 获取用户在该宗门的贡献
    contribution = plugin.sect_repo.get_user_contribution(user_id, sect.id)
    contribution_value = contribution.contribution if contribution else 0
    
    # 构造宗门信息
    sect_info = f"=== 宗门信息 ===\n"
    sect_info += f"宗门名称：{sect.name}\n"
    sect_info += f"宗门描述：{sect.description}\n"
    sect_info += f"成员数量：{sect.member_count}\n"
    sect_info += f"宗门贡献：{int(contribution_value)}\n"
    sect_info += f"你的职位：{user.sect_position}\n"
    
    yield event.plain_result(sect_info)


async def betray_sect(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """叛出宗门"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 叛出宗门
    success, message = plugin.sect_service.betray_sect(user)
    yield event.plain_result(message)


async def sect_roll_call(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """宗门点卯"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 检查是否有宗门
    if not user.sect_id:
        yield event.plain_result("你目前没有加入任何宗门")
        return
    
    # 宗门点卯
    success, message = plugin.sect_service.sect_roll_call(user)
    yield event.plain_result(message)