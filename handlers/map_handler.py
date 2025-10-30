# handlers/map_handler.py
from astrbot.api.event import AstrMessageEvent
from .utils import player_required
from ..config_manager import ConfigManager
from ..data import DataBase
from ..models import Player
import time
import random
import astrbot.api.message_components as Comp

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

        # 显示资源点
        resources = self.config_manager.get_resources_by_map(current_map_name)
        if resources:
            reply_lines.append("🪨资源点：")
            for resource_name, resource_info in resources.items():
                # 获取资源当前状态
                resource_status = await self.db.get_map_resource(current_map_name, resource_name)
                if resource_status:
                    current_quantity = resource_status['current_quantity']
                    max_quantity = resource_info['最大数量']
                    reply_lines.append(f"  {resource_name}：{resource_info['描述']} ({current_quantity}/{max_quantity})")
                else:
                    # 初始化资源点
                    max_quantity = resource_info['最大数量']
                    await self.db.update_map_resource(current_map_name, resource_name, max_quantity, time.time())
                    reply_lines.append(f"  {resource_name}：{resource_info['描述']} ({max_quantity}/{max_quantity})")

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

    @player_required
    async def handle_collect_resource(self, player: Player, event: AstrMessageEvent, resource_name: str = ""):
        """采集资源"""
        if not resource_name:
            yield event.plain_result("指令格式错误！请使用「采集 <资源名>」。")
            return

        current_map_name = player.current_map
        resource_config = self.config_manager.get_resource_by_name(current_map_name, resource_name)

        if not resource_config:
            yield event.plain_result(f"在「{current_map_name}」找不到名为「{resource_name}」的资源点。")
            return

        # 检查是否已经有正在进行的采集任务
        existing_task = await self.db.get_resource_collection_task(player.user_id, current_map_name, resource_name)
        if existing_task:
            remaining_time = existing_task['completion_time'] - time.time()
            if remaining_time > 0:
                yield event.plain_result(f"你已经在采集{resource_name}了，还需要{int(remaining_time)}秒完成。")
                return
            else:
                # 任务已完成，自动领取资源
                resource_config = self.config_manager.get_resource_by_name(current_map_name, resource_name)
                if resource_config:
                    resource_type = resource_config['资源类型']

                    # 查找对应的物品ID
                    resource_item_id = None
                    for item_id, item_info in self.config_manager.item_data.items():
                        if item_info.type == "资源" and item_info.name == resource_type:
                            resource_item_id = item_id
                            break

                    # 如果没有找到对应的物品，创建一个虚拟ID
                    if not resource_item_id:
                        resource_item_id = f"resource_{resource_type}"

                    # 添加资源到背包
                    await self.db.add_items_to_inventory_in_transaction(
                        player.user_id, {resource_item_id: existing_task['quantity']})

                    # 标记任务为已完成
                    await self.db.complete_resource_collection_task(existing_task['id'])

                    # 移除任务
                    await self.db.remove_completed_resource_collection_task(existing_task['id'])

                    yield event.plain_result(
                        f"采集完成！获得了 {existing_task['quantity']} 个{resource_type}，已自动存入背包。")

        # 检查资源点是否有足够资源
        resource_status = await self.db.get_map_resource(current_map_name, resource_name)
        current_time = time.time()

        # 如果资源点不存在，初始化它
        if not resource_status:
            await self.db.update_map_resource(current_map_name, resource_name,
                                              resource_config['最大数量'], current_time)
            resource_status = {
                'current_quantity': resource_config['最大数量'],
                'last_refresh_time': current_time
            }

        # 检查是否需要刷新资源
        time_since_refresh = current_time - resource_status['last_refresh_time']
        if time_since_refresh >= resource_config['刷新时间']:
            # 刷新资源
            await self.db.update_map_resource(current_map_name, resource_name,
                                              resource_config['最大数量'], current_time)
            resource_status['current_quantity'] = resource_config['最大数量']

        # 检查资源是否足够
        if resource_status['current_quantity'] <= 0:
            yield event.plain_result(f"{resource_name}已经枯竭，请等待刷新。")
            return

        # 创建采集任务
        collection_time = resource_config['每次采集时间']
        start_time = current_time
        completion_time = start_time + collection_time

        # 计算采集数量
        quantity_range = resource_config['每次采集数量范围']
        collected_quantity = random.randint(quantity_range[0], quantity_range[1])

        # 限制采集数量不超过当前资源量
        collected_quantity = min(collected_quantity, resource_status['current_quantity'])

        # 添加采集任务
        await self.db.add_resource_collection_task(
            player.user_id, current_map_name, resource_name,
            start_time, completion_time, collected_quantity
        )

        # 减少资源点的资源量
        new_quantity = resource_status['current_quantity'] - collected_quantity
        await self.db.update_map_resource(current_map_name, resource_name,
                                          new_quantity, resource_status['last_refresh_time'])
        
        yield event.plain_result(f"开始采集{resource_name}，需要{collection_time}秒，预计获得{collected_quantity}个。")

    async def check_and_complete_resource_collections(self):
        """检查并完成所有已完成的资源采集任务"""
        pending_tasks = await self.db.get_all_pending_resource_tasks()
        completed_notifications = []

        for task in pending_tasks:
            # 自动将资源添加到玩家背包
            resource_config = self.config_manager.get_resource_by_name(task['map_name'], task['resource_name'])
            if resource_config:
                resource_type = resource_config['资源类型']

                # 查找对应的物品ID
                resource_item_id = None
                for item_id, item_info in self.config_manager.item_data.items():
                    if item_info.type == "资源" and item_info.name == resource_type:
                        resource_item_id = item_id
                        break

                # 如果没有找到对应的物品，创建一个虚拟ID
                if not resource_item_id:
                    resource_item_id = f"resource_{resource_type}"

                # 添加资源到背包
                await self.db.add_items_to_inventory_in_transaction(
                    task['user_id'], {resource_item_id: task['quantity']})

                # 标记任务为已完成
                await self.db.complete_resource_collection_task(task['id'])

                # 添加通知消息
                completed_notifications.append({
                    "user_id": task['user_id'],
                    "message": f"你在{task['map_name']}采集的{task['resource_name']}已完成，获得了{task['quantity']}个{resource_type}。"
                })

        return completed_notifications

    @player_required
    async def handle_check_collection(self, player: Player, event: AstrMessageEvent):
        """检查采集进度"""
        tasks = await self.db.get_user_active_collection_tasks(player.user_id)

        if not tasks:
            yield event.plain_result("你当前没有进行任何采集任务。")
            return

        reply_lines = ["🔄 你的采集任务："]
        current_time = time.time()

        for task in tasks:
            remaining_time = task['completion_time'] - current_time
            if remaining_time <= 0:
                reply_lines.append(f"✅ {task['resource_name']}：已完成")
            else:
                reply_lines.append(f"⏳ {task['resource_name']}：剩余 {int(remaining_time)} 秒")

        yield event.plain_result("\n".join(reply_lines))

    @player_required
    async def handle_claim_resource(self, player: Player, event: AstrMessageEvent):
        """领取已完成的采集资源"""
        completed_tasks = await self.db.get_completed_resource_collection_tasks(player.user_id)

        if not completed_tasks:
            yield event.plain_result("你没有已完成的采集任务可以领取。")
            return

        total_collected = {}
        claimed_task_ids = []

        for task in completed_tasks:
            resource_config = self.config_manager.get_resource_by_name(
                task['map_name'], task['resource_name'])

            if resource_config:
                resource_type = resource_config['资源类型']

                # 累计资源
                if resource_type not in total_collected:
                    total_collected[resource_type] = 0
                total_collected[resource_type] += task['quantity']

                # 标记任务为已领取
                if 'id' in task:
                    success = await self.db.complete_resource_collection_task(task['id'])
                    if success:
                        claimed_task_ids.append(task['id'])

        # 给玩家添加资源（这里简化处理，实际应该添加到玩家的资源背包中）
        reply_lines = ["🎉 采集完成，获得资源："]
        for resource_type, quantity in total_collected.items():
            reply_lines.append(f"  {resource_type}: {quantity}个")

            # 如果是灵石，直接加到玩家的金币中
            if resource_type == "灵石":
                p_clone = player.clone()
                p_clone.gold += quantity
                await self.db.update_player(p_clone)

        # 移除已领取的任务
        for task_id in claimed_task_ids:
            await self.db.remove_completed_resource_collection_task(task_id)

        yield event.plain_result("\n".join(reply_lines))