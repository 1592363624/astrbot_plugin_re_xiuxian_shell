import random
from datetime import datetime, timedelta
from typing import Optional, Tuple
from ..domain.models import User
from ..repositories.sqlite_user_repo import SqliteUserRepository
from ..repositories.sqlite_inventory_repo import SqliteInventoryRepository
from ..repositories.sqlite_log_repo import SqliteLogRepository


class CultivationService:
    def __init__(self, 
                 user_repo: SqliteUserRepository,
                 inventory_repo: SqliteInventoryRepository,
                 log_repo: SqliteLogRepository,
                 config: dict):
        self.user_repo = user_repo
        self.inventory_repo = inventory_repo
        self.log_repo = log_repo
        self.config = config

    def start_closing_door_cultivation(self, user: User) -> Tuple[bool, str]:
        """开始闭关修炼"""
        # 检查是否正在闭关
        if user.is_in_closing:
            return False, "你正在闭关中，无法再次闭关"
            
        # 检查冷却时间
        if user.last_closing_time:
            cooldown_seconds = self.config.get("re_xiuxian", {}).get("closed_door_cooldown", 60)
            if self._get_current_time() < user.last_closing_time + timedelta(seconds=cooldown_seconds):
                remaining = (user.last_closing_time + timedelta(seconds=cooldown_seconds) - self._get_current_time()).seconds
                return False, f"闭关冷却中，还需等待 {remaining} 秒"
        
        # 检查是否处于避世状态
        if user.is_hermit and not user.realm.startswith("炼气"):
            return False, "避世状态下无法闭关修炼"
            
        # 开始闭关（设置闭关状态和时间）
        closing_duration = self.config.get("re_xiuxian", {}).get("closed_door_duration", 60)
        user.is_in_closing = True
        user.closing_start_time = self._get_current_time()
        user.closing_duration = closing_duration
        
        self.user_repo.update_user(user)
        return True, f"开始闭关修炼，需要 {closing_duration} 秒完成"

    def check_closing_door_cultivation(self, user: User) -> Tuple[bool, str]:
        """检查闭关状态"""
        # 检查是否正在闭关
        if not user.is_in_closing:
            return False, "你没有在闭关修炼"
        
        # 检查闭关是否完成
        if user.closing_start_time and user.closing_duration:
            closing_end_time = user.closing_start_time + timedelta(seconds=user.closing_duration)
            if self._get_current_time() >= closing_end_time:
                # 闭关完成，计算结果
                return self._complete_closing_door_cultivation(user)
            else:
                # 还在闭关中
                remaining = closing_end_time - self._get_current_time()
                return True, f"闭关修炼中，剩余时间: {remaining.seconds} 秒"
        else:
            # 数据异常，重置状态
            user.is_in_closing = False
            user.closing_start_time = None
            user.closing_duration = None
            self.user_repo.update_user(user)
            return False, "闭关数据异常，已重置状态"

    def _complete_closing_door_cultivation(self, user: User) -> Tuple[bool, str]:
        """完成闭关修炼"""
        # 重置闭关状态
        user.is_in_closing = False
        user.closing_start_time = None
        user.closing_duration = None
        
        # 随机闭关结果
        rand = random.random()
        if rand < 0.7:  # 70% 成功
            # 成功闭关，获得修为
            exp_gain = self._calculate_exp_gain(user)
            user.cultivation += exp_gain
            user.total_exp_gained += exp_gain
            user.last_closing_time = self._get_current_time()
            user.total_closing_count += 1
            
            self.user_repo.update_user(user)
            self.log_repo.add_log(user.user_id, "闭关", f"闭关成功，获得 {exp_gain} 点修为")
            return True, f"闭关成功，获得 {exp_gain} 点修为"
            
        elif rand < 0.9:  # 20% 失败
            user.last_closing_time = self._get_current_time()
            user.total_closing_count += 1
            
            self.user_repo.update_user(user)
            self.log_repo.add_log(user.user_id, "闭关", "闭关失败，未获得修为")
            return True, "闭关失败，未获得修为"
            
        else:  # 10% 走火入魔
            # 损失部分修为
            loss = int(user.cultivation * 0.1) if user.cultivation > 0 else 0
            user.cultivation = max(0, user.cultivation - loss)
            user.last_closing_time = self._get_current_time()
            user.total_closing_count += 1
            
            self.user_repo.update_user(user)
            self.log_repo.add_log(user.user_id, "闭关", f"走火入魔，损失 {loss} 点修为")
            return True, f"走火入魔，损失 {loss} 点修为"

    def start_deep_cultivation(self, user: User) -> Tuple[bool, str]:
        """开始深度闭关"""
        # 检查是否已经在深度闭关
        if user.deep_closing_end_time and user.deep_closing_end_time > self._get_current_time():
            return False, "你已经在深度闭关中"
            
        # 检查冷却时间
        if user.last_closing_time:
            cooldown_seconds = self.config.get("re_xiuxian", {}).get("deep_closed_door_cooldown", 79200)
            if self._get_current_time() < user.last_closing_time + timedelta(seconds=cooldown_seconds):
                remaining = (user.last_closing_time + timedelta(seconds=cooldown_seconds) - self._get_current_time()).seconds
                return False, f"深度闭关冷却中，还需等待 {remaining} 秒"
        
        # 开始深度闭关
        duration = self.config.get("re_xiuxian", {}).get("deep_closed_door_duration", 28800)
        user.deep_closing_end_time = self._get_current_time() + timedelta(seconds=duration)
        user.last_closing_time = self._get_current_time()
        
        self.user_repo.update_user(user)
        self.log_repo.add_log(user.user_id, "闭关", f"开始深度闭关，将持续 {duration//3600} 小时")
        return True, f"开始深度闭关，将持续 {duration//3600} 小时"

    def check_deep_cultivation(self, user: User) -> Tuple[bool, str]:
        """检查深度闭关状态"""
        if not user.deep_closing_end_time:
            return False, "你没有在进行深度闭关"
            
        if user.deep_closing_end_time <= self._get_current_time():
            # 深度闭关结束，计算收益
            exp_gain = self._calculate_deep_exp_gain(user)
            user.cultivation += exp_gain
            user.total_exp_gained += exp_gain
            user.deep_closing_end_time = None
            user.total_closing_count += 1
            
            self.user_repo.update_user(user)
            self.log_repo.add_log(user.user_id, "闭关", f"深度闭关结束，获得 {exp_gain} 点修为")
            return True, f"深度闭关结束，获得 {exp_gain} 点修为"
        else:
            # 还在闭关中
            remaining = user.deep_closing_end_time - self._get_current_time()
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            return True, f"深度闭关中，剩余时间: {hours} 小时 {minutes} 分钟"

    def force_exit_cultivation(self, user: User) -> Tuple[bool, str]:
        """强行出关"""
        if not user.deep_closing_end_time:
            return False, "你没有在进行深度闭关"
            
        # 强行出关，只获得部分收益
        remaining_time = user.deep_closing_end_time - self._get_current_time()
        completed_ratio = 1 - (remaining_time.total_seconds() / 
                              self.config.get("re_xiuxian", {}).get("deep_closed_door_duration", 28800))
        
        # 按完成比例计算收益，但有折扣
        exp_gain = int(self._calculate_deep_exp_gain(user) * completed_ratio * 0.7)
        user.cultivation += exp_gain
        user.total_exp_gained += exp_gain
        user.deep_closing_end_time = None
        user.total_closing_count += 1
        
        self.user_repo.update_user(user)
        self.log_repo.add_log(user.user_id, "闭关", f"强行出关，获得 {exp_gain} 点修为")
        return True, f"强行出关，获得 {exp_gain} 点修为"

    def toggle_hermit_mode(self, user: User, enable: bool) -> Tuple[bool, str]:
        """切换避世模式"""
        # 检查是否为炼气期
        if not user.realm.startswith("炼气") and enable:
            return False, "只有炼气期修士才能开启避世模式"
            
        user.is_hermit = enable
        self.user_repo.update_user(user)
        
        if enable:
            self.log_repo.add_log(user.user_id, "状态", "开启避世模式")
            return True, "已开启避世模式，你将无法被攻击，也无法攻击他人"
        else:
            self.log_repo.add_log(user.user_id, "状态", "关闭避世模式")
            return True, "已关闭避世模式，重新入世"

    def _get_current_time(self):
        """获取当前时间"""
        return datetime.now()

    def _calculate_exp_gain(self, user: User) -> int:
        """计算普通闭关获得的修为"""
        base_gain = self.config.get("re_xiuxian", {}).get("base_exp_gain", 10)
        
        # 根据境界调整
        realm_multiplier = 1.0
        if "炼气" in user.realm:
            realm_multiplier = 1.0
        elif "筑基" in user.realm:
            realm_multiplier = 2.0
        elif "结丹" in user.realm:
            realm_multiplier = 4.0
        elif "元婴" in user.realm:
            realm_multiplier = 8.0
            
        # 根据灵根调整
        talent_multiplier = 1.0
        if user.talent:
            talent_count = len(user.talent)
            if talent_count == 1:  # 单灵根
                talent_multiplier = 1.5
            elif talent_count == 2:  # 双灵根
                talent_multiplier = 1.2
            elif talent_count >= 4:  # 四灵根及以上
                talent_multiplier = 0.8
                
        return int(base_gain * realm_multiplier * talent_multiplier)

    def _calculate_deep_exp_gain(self, user: User) -> int:
        """计算深度闭关获得的修为"""
        # 深度闭关相当于多次普通闭关
        duration = self.config.get("re_xiuxian", {}).get("deep_closed_door_duration", 28800)
        base_cooldown = self.config.get("re_xiuxian", {}).get("closed_door_cooldown", 60)
        
        # 计算相当于多少次普通闭关
        times = duration // base_cooldown
        
        # 每次普通闭关的收益累加，但有递减效应
        total_exp = 0
        for i in range(times):
            # 每次递减5%
            exp = int(self._calculate_exp_gain(user) * (0.95 ** i))
            total_exp += exp
            
        return total_exp