from typing import Optional, List, Tuple
from ..domain.models import User, Item, UserItem
from ..repositories.sqlite_inventory_repo import SqliteInventoryRepository
from ..repositories.sqlite_user_repo import SqliteUserRepository
from ..repositories.sqlite_item_repo import SqliteItemRepository


class InventoryService:
    def __init__(self, 
                 inventory_repo: SqliteInventoryRepository,
                 user_repo: SqliteUserRepository,
                 item_repo: SqliteItemRepository,
                 config: dict):
        self.inventory_repo = inventory_repo
        self.user_repo = user_repo
        self.item_repo = item_repo
        self.config = config

    def get_user_inventory(self, user_id: str) -> List[Tuple[Item, UserItem]]:
        """获取用户库存"""
        user_items = self.inventory_repo.get_user_items(user_id)
        inventory = []
        
        for user_item in user_items:
            item = self.item_repo.get_by_id(user_item.item_id)
            if item:
                inventory.append((item, user_item))
                
        return inventory

    def use_item(self, user: User, item_name: str, quantity: int = 1) -> Tuple[bool, str]:
        """使用物品"""
        # 查找物品
        item = self.item_repo.get_by_name(item_name)
        if not item:
            return False, f"未找到物品: {item_name}"
            
        # 检查用户是否有足够数量
        if not self.inventory_repo.has_item(user.user_id, item.id, quantity):
            return False, f"你没有足够的 {item_name}"
            
        # 检查使用条件
        if item.requirement and not self._check_requirement(user, item.requirement):
            return False, f"不满足使用条件: {item.requirement}"
            
        # 根据物品类型处理效果
        success, message = self._apply_item_effect(user, item, quantity)
        if success:
            # 消耗物品
            self.inventory_repo.remove_item(user.user_id, item.id, quantity)
            
        return success, message

    def _check_requirement(self, user: User, requirement: str) -> bool:
        """检查使用条件"""
        # 简化实现，实际应根据requirement字符串解析条件
        if requirement == "炼气大圆满" and user.realm != "炼气大圆满":
            return False
        # 可以添加更多条件检查
        return True

    def _apply_item_effect(self, user: User, item: Item, quantity: int) -> Tuple[bool, str]:
        """应用物品效果"""
        if item.type == "丹药":
            if item.effect_type == "突破":
                # 处理突破丹药
                if item.name == "筑基丹":
                    if user.realm == "炼气大圆满":
                        user.realm = "筑基初期"
                        self.user_repo.update_user(user)
                        return True, f"服用筑基丹成功，境界提升至{user.realm}"
                    else:
                        return False, "当前境界无法服用筑基丹"
                        
            elif item.effect_type == "增益":
                # 增加修为
                exp_gain = int(item.effect_value * 100 * quantity)
                user.cultivation += exp_gain
                user.total_exp_gained += exp_gain
                self.user_repo.update_user(user)
                return True, f"服用{item.name}，获得 {exp_gain} 点修为"
                
            elif item.effect_type == "清理":
                # 清理效果，这里简化处理
                return True, f"服用{item.name}，清理了丹毒"
                
        elif item.type == "材料":
            # 材料类物品一般不能直接使用
            return False, f"{item.name}是材料，无法直接使用"
            
        return False, f"未知的物品效果类型: {item.effect_type}"

    def add_item_to_user(self, user_id: str, item_id: int, quantity: int = 1) -> bool:
        """给用户添加物品"""
        return self.inventory_repo.add_item(user_id, item_id, quantity)

    def remove_item_from_user(self, user_id: str, item_id: int, quantity: int = 1) -> bool:
        """从用户移除物品"""
        return self.inventory_repo.remove_item(user_id, item_id, quantity)