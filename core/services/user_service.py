import random
from typing import Optional
from ..domain.models import User
from ..repositories.sqlite_user_repo import SqliteUserRepository


class UserService:
    def __init__(self, user_repo: SqliteUserRepository):
        self.user_repo = user_repo
        
        # 灵根类型
        self.talent_types = [
            "金", "木", "水", "火", "土",
            "金火", "木火", "水火", "土火", "金水",
            "木水", "土水", "金木", "火木", "土木",
            "金土", "火土", "水土",
            "金火水", "金火土", "金水土", "火水土",
            "金木火", "金木水", "金木土", "木火土", "木水土",
            "金木水火", "金木水土", "金木火土", "金水火土", "木水火土",
            "五行齐全"
        ]
        
        # 道号前缀
        self.dao_name_prefixes = [
            "无尘", "青云", "玄真", "清虚", "明心",
            "静虚", "天行", "浩然", "凌霄", "紫阳",
            "太初", "混元", "纯阳", "太阴", "九霄",
            "碧落", "苍穹", "逍遥", "无极", "太虚"
        ]
        
        # 道号后缀
        self.dao_name_suffixes = [
            "真人", "散人", "居士", "道人", "上人",
            "仙子", "圣女", "天师", "上仙", "真君",
            "帝君", "天尊", "圣人", "大帝", "至尊"
        ]

    def get_or_create_user(self, user_id: str, nickname: Optional[str] = None) -> User:
        """获取或创建用户"""
        user = self.user_repo.get_by_user_id(user_id)
        if not user:
            user = self.user_repo.create_user(user_id, nickname)
        return user

    def detect_talent(self, user: User, platform_nickname: Optional[str] = None) -> bool:
        """检测灵根，初始化修仙者"""
        if user.talent:
            return False  # 已有灵根，不能再检测
            
        # 更新用户昵称（使用平台昵称）
        if platform_nickname and not user.nickname:
            user.nickname = platform_nickname
            
        # 随机生成灵根（权重分配）
        talent_weights = [
            (10, 30),   # 单灵根
            (31, 60),   # 双灵根
            (61, 80),   # 三灵根
            (81, 95),   # 四灵根
            (96, 100)   # 五行齐全
        ]
        
        rand = random.randint(1, 100)
        talent_type = ""
        for start, end in talent_weights:
            if start <= rand <= end:
                if end == 30:
                    # 单灵根
                    talent_type = random.choice(self.talent_types[:5])
                elif end == 60:
                    # 双灵根
                    talent_type = random.choice(self.talent_types[5:14])
                elif end == 80:
                    # 三灵根
                    talent_type = random.choice(self.talent_types[14:19])
                elif end == 95:
                    # 四灵根
                    talent_type = random.choice(self.talent_types[19:24])
                else:
                    # 五行齐全
                    talent_type = self.talent_types[-1]
                break
        
        # 生成道号
        prefix = random.choice(self.dao_name_prefixes)
        suffix = random.choice(self.dao_name_suffixes)
        dao_name = f"{prefix}{suffix}"
        
        # 更新用户信息
        user.talent = talent_type
        user.dao_name = dao_name
        user.realm = "炼气一层"
        user.cultivation = 0.0
        
        return self.user_repo.update_user(user)

    def update_user_nickname(self, user: User, nickname: str) -> bool:
        """更新用户昵称"""
        user.nickname = nickname
        return self.user_repo.update_user(user)