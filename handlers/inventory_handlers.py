from typing import AsyncGenerator
from astrbot.api.event import AstrMessageEvent, MessageEventResult as EventResult
from astrbot.api import logger


async def inventory(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """查看储物袋"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 获取用户库存
    inventory_items = plugin.inventory_service.get_user_inventory(user_id)
    
    if not inventory_items:
        yield event.plain_result("你的储物袋空空如也")
        return
    
    # 构造物品列表
    inventory_info = "=== 储物袋 ===\n"
    for item, user_item in inventory_items:
        inventory_info += f"{item.name} x{user_item.quantity}\n"
        if item.description:
            inventory_info += f"  {item.description}\n"
        inventory_info += "\n"
    
    yield event.plain_result(inventory_info)


async def take_pill(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """服用丹药"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 解析命令
    message = event.message_str.strip()
    if not message.startswith("服用"):
        yield event.plain_result("命令格式错误，请使用：服用 <丹药名>[*数量]")
        return
    
    pill_info = message[3:].strip()  # 去掉"服用 "
    if not pill_info:
        yield event.plain_result("请指定要服用的丹药")
        return
    
    # 解析物品名和数量
    if "*" in pill_info:
        pill_name, quantity_str = pill_info.split("*", 1)
        try:
            quantity = int(quantity_str)
        except ValueError:
            yield event.plain_result("数量必须是数字")
            return
    else:
        pill_name = pill_info
        quantity = 1
    
    # 使用物品
    success, message = plugin.inventory_service.use_item(user, pill_name, quantity)
    yield event.plain_result(message)


async def alchemy(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """炼制物品"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 这里应该实现炼制逻辑，暂时简化处理
    yield event.plain_result("炼制功能正在开发中...")


async def learn(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """学习配方"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 这里应该实现学习配方逻辑，暂时简化处理
    yield event.plain_result("学习功能正在开发中...")


async def give_item(plugin, event: AstrMessageEvent) -> AsyncGenerator[EventResult, None]:
    """赠送物品"""
    user_id = event.get_sender_id()
    nickname = event.get_sender_name()
    
    # 获取用户
    user = plugin.user_service.get_or_create_user(user_id, nickname)
    
    # 检查是否已检测过灵根
    if not user.talent:
        yield event.plain_result("你尚未踏入修仙之路，请先使用「检测灵根」命令")
        return
    
    # 这里应该实现赠送物品逻辑，暂时简化处理
    yield event.plain_result("赠送功能正在开发中...")