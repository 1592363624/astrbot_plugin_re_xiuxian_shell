from typing import AsyncGenerator
from datetime import datetime
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api import logger


async def detect_talent(plugin, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
    """检测灵根"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取或创建用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if user.talent:
        yield event.plain_result(f"你已经是修仙者了，道号：{user.dao_name}，灵根：{user.talent}，境界：{user.realm}")
        return
    
    # 检测灵根
    success = plugin.user_service.detect_talent(user, nickname)
    if success:
        yield event.plain_result(f"恭喜！{nickname}你已成为修仙者！\n道号：{user.dao_name}\n灵根：{user.talent}\n当前境界：{user.realm}\n开始你的修仙之旅吧！")
    else:
        yield event.plain_result("检测失败，请稍后再试")


async def my_talent(plugin, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
    """查看自己的修仙档案"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 检查闭关状态
    if user.is_in_closing:
        success, message = plugin.cultivation_service.check_closing_door_cultivation(user)
        if success and "剩余时间" in message:
            # 仍在闭关中
            pass
        else:
            # 闭关已完成
            yield event.plain_result(message)
    
    # 获取宗门信息
    sect_name = "无"
    if user.sect_id:
        sect = plugin.sect_service.get_user_sect(user)
        if sect:
            sect_name = sect.name
    
    # 构造档案信息
    profile = f"=== 修仙档案 ===\n"
    profile += f"道号：{user.dao_name}\n"
    profile += f"境界：{user.realm}\n"
    profile += f"修为：{int(user.cultivation)}\n"
    profile += f"灵根：{user.talent}\n"
    profile += f"宗门：{sect_name}\n"
    profile += f"总闭关次数：{user.total_closing_count}\n"
    profile += f"总斗法次数：{user.total_battle_count} (胜 {user.total_battle_win_count})\n"
    
    if user.is_hermit:
        profile += "状态：避世中\n"
    
    if user.deep_closing_end_time and user.deep_closing_end_time > datetime.now():
        profile += "状态：深度闭关中\n"
    elif user.is_in_closing:
        profile += "状态：闭关修炼中\n"
    
    yield event.plain_result(profile)


async def closed_door_cultivation(plugin, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
    """闭关修炼"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 如果已经在闭关，检查闭关状态
    if user.is_in_closing:
        success, message = plugin.cultivation_service.check_closing_door_cultivation(user)
        yield event.plain_result(message)
    else:
        # 开始闭关修炼
        success, message = plugin.cultivation_service.start_closing_door_cultivation(user)
        if success:
            # 启动定时任务来自动完成闭关
            import asyncio
            from datetime import timedelta
            
            # 计算剩余时间
            end_time = user.closing_start_time + timedelta(seconds=user.closing_duration)
            delay = (end_time - plugin.cultivation_service._get_current_time()).total_seconds()
            
            # 保存用户的 unified_msg_origin 用于后续发送消息
            user.unified_msg_origin = event.unified_msg_origin
            plugin.user_repo.update_user(user)
            
            # 创建并保存定时任务
            if user_id in plugin.cultivation_tasks:
                plugin.cultivation_tasks[user_id].cancel()
            
            task = asyncio.create_task(plugin._cultivation_timer(user, delay, user_id))
            plugin.cultivation_tasks[user_id] = task
            
        yield event.plain_result(message)


async def deep_closed_door(plugin, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
    """深度闭关"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 开始深度闭关
    success, message = plugin.cultivation_service.start_deep_cultivation(user)
    yield event.plain_result(message)


async def check_deep_cultivation(plugin, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
    """查看深度闭关状态"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 检查深度闭关状态
    success, message = plugin.cultivation_service.check_deep_cultivation(user)
    yield event.plain_result(message)


async def force_exit_cultivation(plugin, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
    """强行出关"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 强行出关
    success, message = plugin.cultivation_service.force_exit_cultivation(user)
    yield event.plain_result(message)


async def hermit_mode(plugin, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
    """开启避世模式"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 开启避世模式
    success, message = plugin.cultivation_service.toggle_hermit_mode(user, True)
    yield event.plain_result(message)


async def return_world(plugin, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
    """关闭避世模式"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 关闭避世模式
    success, message = plugin.cultivation_service.toggle_hermit_mode(user, False)
    yield event.plain_result(message)