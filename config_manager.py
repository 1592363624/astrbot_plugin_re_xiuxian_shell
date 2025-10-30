# config_manager.py

import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

from astrbot.api import logger
from .models import Item


class ConfigManager:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._paths = {
            "level": base_dir / "config" / "level_config.json",
            "item": base_dir / "config" / "items.json",
            "boss": base_dir / "config" / "bosses.json",
            "monster": base_dir / "config" / "monsters.json",
            "realm": base_dir / "config" / "realms.json",
            "tag": base_dir / "config" / "tags.json",
            "world_map": base_dir / "config" / "world_map.json",
            "resources": base_dir / "config" / "resources.json"
        }

        self.level_data: List[dict] = []
        self.item_data: Dict[str, Item] = {}
        self.boss_data: Dict[str, dict] = {}
        self.monster_data: Dict[str, dict] = {}
        self.realm_data: Dict[str, dict] = {}
        self.tag_data: Dict[str, dict] = {}
        self.world_map_data: Dict[str, dict] = {}
        self.resources_data: Dict[str, dict] = {}

        self.level_map: Dict[str, dict] = {}
        self.item_name_to_id: Dict[str, str] = {}
        self.realm_name_to_id: Dict[str, str] = {}
        self.boss_name_to_id: Dict[str, str] = {}
        self.world_map_name_to_id: Dict[str, str] = {}

        self._load_all()

    def _load_json_data(self, file_path: Path) -> Any:
        if not file_path.exists():
            logger.warning(f"数据文件 {file_path} 不存在，将使用空数据。")
            return {} if file_path.suffix == '.json' else []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"成功加载 {file_path.name} (共 {len(data)} 条数据)。")
                return data
        except Exception as e:
            logger.error(f"加载数据文件 {file_path} 失败: {e}")
            return {} if file_path.suffix == '.json' else []

    def _load_all(self):
        """加载所有数据文件并进行后处理"""
        self.level_data = self._load_json_data(self._paths["level"])
        raw_item_data = self._load_json_data(self._paths["item"])
        self.boss_data = self._load_json_data(self._paths["boss"])
        self.monster_data = self._load_json_data(self._paths["monster"])
        self.realm_data = self._load_json_data(self._paths["realm"])
        self.tag_data = self._load_json_data(self._paths["tag"])
        self.world_map_data = self._load_json_data(self._paths["world_map"])
        self.resources_data = self._load_json_data(self._paths["resources"])

        self.level_map = {info["level_name"]: {"index": i, **info}
                          for i, info in enumerate(self.level_data) if "level_name" in info}

        self.item_data = {}
        self.item_name_to_id = {}
        for item_id, info in raw_item_data.items():
            try:
                self.item_data[item_id] = Item(id=item_id, **info)
                if "name" in info:
                    self.item_name_to_id[info["name"]] = item_id
            except TypeError as e:
                logger.error(f"加载物品 {item_id} 失败，配置项不匹配: {e}")

        self.realm_name_to_id = {info["name"]: realm_id
                                 for realm_id, info in self.realm_data.items() if "name" in info}
        self.boss_name_to_id = {info["name"]: boss_id
                                for boss_id, info in self.boss_data.items() if "name" in info}

        # 加载世界地图数据
        if "地图" in self.world_map_data:
            self.world_map_name_to_id = {map_name: map_name
                                         for map_name in self.world_map_data["地图"].keys()}

    def get_item_by_name(self, name: str) -> Optional[Tuple[str, Item]]:
        item_id = self.item_name_to_id.get(name)
        return (item_id, self.item_data[item_id]) if item_id and item_id in self.item_data else None

    def get_realm_by_name(self, name: str) -> Optional[Tuple[str, dict]]:
        realm_id = self.realm_name_to_id.get(name)
        return (realm_id, self.realm_data[realm_id]) if realm_id else None

    def get_boss_by_name(self, name: str) -> Optional[Tuple[str, dict]]:
        boss_id = self.boss_name_to_id.get(name)
        return (boss_id, self.boss_data[boss_id]) if boss_id else None

    def get_map_by_name(self, name: str) -> Optional[Tuple[str, dict]]:
        map_id = self.world_map_name_to_id.get(name)
        if map_id and "地图" in self.world_map_data and map_id in self.world_map_data["地图"]:
            return (map_id, self.world_map_data["地图"][map_id])
        return None

    def get_resources_by_map(self, map_name: str) -> Optional[Dict[str, dict]]:
        """获取指定地图的资源点信息"""
        if "资源点" in self.resources_data and map_name in self.resources_data["资源点"]:
            return self.resources_data["资源点"][map_name]
        return None

    def get_resource_by_name(self, map_name: str, resource_name: str) -> Optional[Dict[str, Any]]:
        """获取指定地图中特定资源点的信息"""
        resources = self.get_resources_by_map(map_name)
        if resources and resource_name in resources:
            return resources[resource_name]
        return None
