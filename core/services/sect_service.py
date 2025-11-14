from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from ..domain.models import User, Sect
from ..repositories.sqlite_sect_repo import SqliteSectRepository
from ..repositories.sqlite_user_repo import SqliteUserRepository
from ..repositories.sqlite_inventory_repo import SqliteInventoryRepository


class SectService:
    def __init__(self, 
                 sect_repo: SqliteSectRepository,
                 user_repo: SqliteUserRepository,
                 inventory_repo: SqliteInventoryRepository,
                 config: dict):
        self.sect_repo = sect_repo
        self.user_repo = user_repo
        self.inventory_repo = inventory_repo
        self.config = config

    def join_sect(self, user: User, sect_name: str) -> Tuple[bool, str]:
        """加入宗门"""
        # 检查是否已经有宗门
        if user.sect_id:
            return False, "你已经有宗门了，无法再加入其他宗门"
            
        # 查找宗门
        sect = self.sect_repo.get_by_name(sect_name)
        if not sect:
            return False, f"未找到宗门: {sect_name}"
            
        # 检查入门条件（简化处理）
        # 可以根据宗门添加不同的入门条件检查
        
        # 加入宗门
        user.sect_id = sect.id
        user.sect_position = "弟子"
        sect.member_count += 1
        
        self.user_repo.update_user(user)
        self.sect_repo.update_sect(sect)
        
        return True, f"成功加入宗门 {sect.name}"

    def betray_sect(self, user: User) -> Tuple[bool, str]:
        """叛出宗门"""
        # 检查是否有宗门
        if not user.sect_id:
            return False, "你没有宗门，无法叛出"
            
        # 查找宗门
        sect = self.sect_repo.get_by_id(user.sect_id)
        if not sect:
            user.sect_id = None
            user.sect_position = None
            self.user_repo.update_user(user)
            return False, "宗门不存在"
            
        # 检查是否在冷却期
        if user.last_sect_roll_call_time:
            cooldown_end = user.last_sect_roll_call_time + timedelta(hours=4)
            if datetime.now() < cooldown_end:
                remaining = (cooldown_end - datetime.now()).seconds
                minutes = remaining // 60
                seconds = remaining % 60
                return False, f"叛门冷却中，还需等待 {minutes} 分 {seconds} 秒"
                
        # 叛出门派
        user.sect_id = None
        user.sect_position = None
        sect.member_count = max(0, sect.member_count - 1)
        
        # 设置叛门冷却时间
        user.last_sect_roll_call_time = datetime.now()
        
        self.user_repo.update_user(user)
        self.sect_repo.update_sect(sect)
        
        return True, f"成功叛出宗门 {sect.name}，进入4小时叛门冷却期"

    def sect_roll_call(self, user: User) -> Tuple[bool, str]:
        """宗门点卯"""
        # 检查是否有宗门
        if not user.sect_id:
            return False, "你没有宗门，无法点卯"
            
        # 查找宗门
        sect = self.sect_repo.get_by_id(user.sect_id)
        if not sect:
            return False, "宗门不存在"
            
        # 检查是否已经点卯（每天一次）
        if user.last_sect_roll_call_time:
            # 检查是否是同一天
            today = datetime.now().date()
            last_call_date = user.last_sect_roll_call_time.date()
            if today == last_call_date:
                return False, "今天已经点卯过了"
                
        # 点卯成功，给予贡献
        contribution = self._calculate_roll_call_contribution(user)
        self.sect_repo.add_user_contribution(user.user_id, sect.id, contribution)
        
        # 更新点卯时间
        user.last_sect_roll_call_time = datetime.now()
        self.user_repo.update_user(user)
        
        return True, f"点卯成功，获得 {contribution} 点宗门贡献"

    def get_user_sect(self, user: User) -> Optional[Sect]:
        """获取用户所在宗门"""
        if not user.sect_id:
            return None
        return self.sect_repo.get_by_id(user.sect_id)

    def get_sect_members(self, sect_id: int) -> List[User]:
        """获取宗门成员"""
        # 这里需要在user_repo中添加根据sect_id查询的方法
        # 简化处理，返回空列表
        return []

    def _calculate_roll_call_contribution(self, user: User) -> float:
        """计算点卯贡献"""
        # 根据境界计算贡献值
        base_contribution = 10.0
        
        if "炼气" in user.realm:
            return base_contribution
        elif "筑基" in user.realm:
            return base_contribution * 2
        elif "结丹" in user.realm:
            return base_contribution * 4
        elif "元婴" in user.realm:
            return base_contribution * 8
        else:
            return base_contribution