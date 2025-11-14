from typing import List
from ..repositories.sqlite_item_repo import SqliteItemRepository
from ..repositories.sqlite_sect_repo import SqliteSectRepository
from ..domain.models import Item, Sect


class DataSetupService:
    def __init__(self, item_repo: SqliteItemRepository, sect_repo: SqliteSectRepository):
        self.item_repo = item_repo
        self.sect_repo = sect_repo

    def setup_initial_data(self):
        """设置初始数据"""
        # 创建初始物品
        self._create_initial_items()
        
        # 创建初始宗门
        self._create_initial_sects()

    def _create_initial_items(self):
        """创建初始物品"""
        initial_items = [
            # 丹药类
            Item(
                id=0,
                name="筑基丹",
                type="丹药",
                description="用于突破炼气期瓶颈的丹药",
                rarity=3,
                effect="突破炼气期瓶颈",
                effect_type="突破",
                effect_value=1.0,
                requirement="炼气大圆满"
            ),
            Item(
                id=0,
                name="清灵丹",
                type="丹药",
                description="清除丹毒的丹药",
                rarity=2,
                effect="清除丹毒",
                effect_type="清理",
                effect_value=1.0,
                requirement=None
            ),
            Item(
                id=0,
                name="聚气丹",
                type="丹药",
                description="增加修为获取的丹药",
                rarity=2,
                effect="增加修为获取",
                effect_type="增益",
                effect_value=0.5,
                requirement=None
            ),
            
            # 材料类
            Item(
                id=0,
                name="灵眼之液",
                type="材料",
                description="蕴含天地造化之力的灵液",
                rarity=5,
                effect="逆天改命或催熟灵物",
                effect_type="特殊",
                effect_value=1.0,
                requirement=None
            ),
            Item(
                id=0,
                name="养魂木",
                type="材料",
                description="用于养魂的珍贵材料",
                rarity=4,
                effect="用于突破或炼制高级丹药",
                effect_type="材料",
                effect_value=1.0,
                requirement=None
            ),
            
            # 法宝类
            Item(
                id=0,
                name="青竹蜂云剑",
                type="法宝",
                description="合欢宗至宝，搭配青元剑诀威力无穷",
                rarity=5,
                effect="大幅提升斗法威力",
                effect_type="战斗",
                effect_value=2.0,
                requirement=None
            )
        ]
        
        for item in initial_items:
            # 检查是否已存在
            existing_item = self.item_repo.get_by_name(item.name)
            if not existing_item:
                self.item_repo.create_item(item)

    def _create_initial_sects(self):
        """创建初始宗门"""
        initial_sects = [
            Sect(
                id=0,
                name="黄枫谷",
                description="炼丹师的摇篮，拥有药园加持和低调修行两大天赋",
                founder_id=None,
                member_count=1,
                contribution=0.0,
                is_active=True
            ),
            Sect(
                id=0,
                name="太一门",
                description="天机推演者，弟子可修炼独有的神识属性",
                founder_id=None,
                member_count=1,
                contribution=0.0,
                is_active=True
            ),
            Sect(
                id=0,
                name="合欢宗",
                description="速成者的捷径，弟子可发起闭关双修",
                founder_id=None,
                member_count=1,
                contribution=0.0,
                is_active=True
            ),
            Sect(
                id=0,
                name="星宫",
                description="统治者的权柄，弟子每日可领灵石俸禄",
                founder_id=None,
                member_count=1,
                contribution=0.0,
                is_active=True
            ),
            Sect(
                id=0,
                name="万灵宗",
                description="御兽者的天堂，弟子入门即送初始灵兽",
                founder_id=None,
                member_count=1,
                contribution=0.0,
                is_active=True
            ),
            Sect(
                id=0,
                name="黑煞教",
                description="魔道枭雄的巢穴，弟子拥有独特的夺舍神通",
                founder_id=None,
                member_count=1,
                contribution=0.0,
                is_active=True
            )
        ]
        
        for sect in initial_sects:
            # 检查是否已存在
            existing_sect = self.sect_repo.get_by_name(sect.name)
            if not existing_sect:
                self.sect_repo.create_sect(sect)