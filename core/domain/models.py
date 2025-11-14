from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class User:
    """修仙用户实体"""
    id: int
    user_id: str                           # 平台用户ID
    nickname: Optional[str]                # 昵称
    created_at: datetime
    last_login_at: datetime
    
    # 修仙基本属性
    cultivation: float = 0.0               # 修为点数
    realm: str = "炼气一层"                # 修仙境界
    talent: Optional[str] = None           # 灵根
    dao_name: Optional[str] = None         # 道号
    sect_id: Optional[int] = None          # 宗门ID
    sect_position: Optional[str] = None    # 宗门职位
    avatar: Optional[str] = None           # 头像URL
    
    # 状态
    is_hermit: bool = False                # 是否处于避世状态
    is_in_closing: bool = False            # 是否正在闭关
    closing_start_time: Optional[datetime] = None  # 闭关开始时间
    closing_duration: Optional[int] = None         # 闭关时长(秒)
    deep_closing_end_time: Optional[datetime] = None  # 深度闭关结束时间
    
    # 冷却时间
    last_closing_time: Optional[datetime] = None   # 上次闭关时间
    last_battle_time: Optional[datetime] = None    # 上次斗法时间
    last_sect_roll_call_time: Optional[datetime] = None  # 上次宗门点卯时间
    
    # 统计数据
    total_closing_count: int = 0           # 总闭关次数
    total_battle_count: int = 0            # 总斗法次数
    total_battle_win_count: int = 0        # 总斗法胜利次数
    total_exp_gained: int = 0              # 总获得修为


@dataclass
class Item:
    """物品模板实体"""
    id: int
    name: str                              # 物品名称
    type: str                              # 物品类型 (丹药/法宝/材料等)
    description: Optional[str] = None      # 描述
    rarity: int = 1                        # 稀有度 (1-5)
    effect: Optional[str] = None           # 效果描述
    effect_type: Optional[str] = None      # 效果类型
    effect_value: Optional[float] = None   # 效果数值
    requirement: Optional[str] = None      # 使用要求
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserItem:
    """用户物品实体"""
    id: int
    user_id: str
    item_id: int
    quantity: int = 1
    obtained_at: datetime = field(default_factory=datetime.now)


@dataclass
class Sect:
    """宗门实体"""
    id: int
    name: str                              # 宗门名称
    description: Optional[str] = None      # 宗门描述
    founder_id: Optional[str] = None       # 创始人ID
    created_at: datetime = field(default_factory=datetime.now)
    member_count: int = 1                  # 成员数量
    contribution: float = 0.0              # 宗门贡献
    is_active: bool = True                 # 是否激活


@dataclass
class UserSectContribution:
    """用户宗门贡献实体"""
    id: int
    user_id: str
    sect_id: int
    contribution: float = 0.0              # 对该宗门的贡献
    last_contribution_at: datetime = field(default_factory=datetime.now)


@dataclass
class Log:
    """日志实体"""
    id: int
    user_id: str
    type: str                              # 日志类型 (闭关/斗法/宗门等)
    content: str                           # 日志内容
    created_at: datetime = field(default_factory=datetime.now)