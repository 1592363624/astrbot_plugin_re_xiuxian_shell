import random
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from ..domain.models import User
from ..repositories.sqlite_user_repo import SqliteUserRepository
from ..repositories.sqlite_inventory_repo import SqliteInventoryRepository
from ..repositories.sqlite_log_repo import SqliteLogRepository


class ArenaService:
    def __init__(self, 
                 user_repo: SqliteUserRepository,
                 inventory_repo: SqliteInventoryRepository,
                 log_repo: SqliteLogRepository,
                 config: dict):
        self.user_repo = user_repo
        self.inventory_repo = inventory_repo
        self.log_repo = log_repo
        self.config = config

    def battle(self, attacker: User, defender_user_id: str) -> Tuple[bool, str]:
        """斗法"""
        # 检查冷却时间
        cooldown_seconds = self.config.get("re_xiuxian", {}).get("battle_cooldown", 300)
        if attacker.last_battle_time:
            if datetime.now() < attacker.last_battle_time + timedelta(seconds=cooldown_seconds):
                remaining = (attacker.last_battle_time + timedelta(seconds=cooldown_seconds) - datetime.now()).seconds
                return False, f"斗法冷却中，还需等待 {remaining} 秒"
        
        # 获取防守方
        defender = self.user_repo.get_by_user_id(defender_user_id)
        if not defender:
            return False, "未找到对手"
            
        # 检查是否可以攻击
        if attacker.is_hermit:
            return False, "你处于避世状态，无法攻击他人"
            
        if defender.is_hermit:
            return False, "对手处于避世状态，无法攻击"
            
        # 简单的胜负判断（基于修为）
        attacker_power = attacker.cultivation
        defender_power = defender.cultivation
        
        # 考虑境界差异
        attacker_power *= self._get_realm_multiplier(attacker.realm)
        defender_power *= self._get_realm_multiplier(defender.realm)
        
        # 添加随机因素
        attacker_power *= random.uniform(0.8, 1.2)
        defender_power *= random.uniform(0.8, 1.2)
        
        # 判断胜负
        if attacker_power > defender_power:
            # 攻击者胜利
            reward = int(defender_power * 0.05)  # 获得对方5%的修为作为奖励
            attacker.cultivation += reward
            attacker.total_battle_win_count += 1
            
            # 记录战斗
            attacker.total_battle_count += 1
            attacker.last_battle_time = datetime.now()
            
            defender.cultivation = max(0, defender.cultivation - reward)
            defender.total_battle_count += 1
            
            self.user_repo.update_user(attacker)
            self.user_repo.update_user(defender)
            
            self.log_repo.add_log(attacker.user_id, "斗法", f"战胜 {defender.nickname or defender.user_id}，获得 {reward} 点修为")
            self.log_repo.add_log(defender.user_id, "斗法", f"败给 {attacker.nickname or attacker.user_id}，损失 {reward} 点修为")
            
            return True, f"斗法胜利！获得 {reward} 点修为"
        else:
            # 防守者胜利
            penalty = int(attacker.cultivation * 0.03)  # 损失3%的修为
            attacker.cultivation = max(0, attacker.cultivation - penalty)
            
            reward = int(penalty * 0.5)  # 防守者获得部分奖励
            defender.cultivation += reward
            
            # 记录战斗
            attacker.total_battle_count += 1
            attacker.last_battle_time = datetime.now()
            
            defender.total_battle_count += 1
            defender.total_battle_win_count += 1
            
            self.user_repo.update_user(attacker)
            self.user_repo.update_user(defender)
            
            self.log_repo.add_log(attacker.user_id, "斗法", f"败给 {defender.nickname or defender.user_id}，损失 {penalty} 点修为")
            self.log_repo.add_log(defender.user_id, "斗法", f"战胜 {attacker.nickname or attacker.user_id}，获得 {reward} 点修为")
            
            return True, f"斗法失败！损失 {penalty} 点修为"

    def get_cultivation_ranking(self, limit: int = 10) -> List[User]:
        """获取修为排行榜"""
        return self.user_repo.get_cultivation_ranking(limit)

    def get_evil_ranking(self, limit: int = 10) -> List[User]:
        """获取恶人排行榜（按胜利次数）"""
        # 这里需要在user_repo中添加按胜利次数排序的方法
        # 简化处理，返回修为排行榜
        return self.user_repo.get_cultivation_ranking(limit)

    def _get_realm_multiplier(self, realm: str) -> float:
        """获取境界倍数"""
        if "炼气" in realm:
            return 1.0
        elif "筑基" in realm:
            return 2.0
        elif "结丹" in realm:
            return 4.0
        elif "元婴" in realm:
            return 8.0
        else:
            return 1.0