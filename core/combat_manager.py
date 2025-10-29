# core/combat_manager.py

import random
import time
from typing import Dict, List, Optional, Tuple

from astrbot.api import logger, AstrBotConfig
from ..config_manager import ConfigManager
from ..data import DataBase
from ..models import Player, Boss, ActiveWorldBoss, Monster


class MonsterGenerator:
    """基于标签系统的怪物和Boss生成器"""

    @staticmethod
    def _generate_rewards(base_loot: List) -> Dict[str, int]:
        gained_items = {}
        for entry in base_loot:
            if random.random() < entry.get("chance", 0):
                quantity_range = entry.get("quantity", [1, 1])
                min_qty = quantity_range[0]
                max_qty = quantity_range[1] if len(quantity_range) > 1 else min_qty

                item_id = str(entry["item_id"])
                amount = random.randint(min_qty, max_qty)
                gained_items[item_id] = gained_items.get(item_id, 0) + amount
        return gained_items

    @classmethod
    def create_monster(cls, template_id: str, player_level_index: int, config_manager: ConfigManager) -> Optional[
        Monster]:
        template = config_manager.monster_data.get(template_id)
        if not template:
            logger.warning(f"尝试创建怪物失败：找不到模板ID {template_id}")
            return None

        base_hp = 15 * player_level_index + 60
        base_attack = 2 * player_level_index + 8
        base_defense = 1 * player_level_index + 4
        base_gold = 3 * player_level_index + 10
        base_exp = 5 * player_level_index + 20

        final_name = template["name"]
        final_hp = base_hp
        final_attack = base_attack
        final_defense = base_defense
        final_gold = base_gold
        final_exp = base_exp
        combined_loot_table = []

        for tag_name in template.get("tags", []):
            tag_effect = config_manager.tag_data.get(tag_name)
            if not tag_effect:
                continue

            if "name_prefix" in tag_effect:
                final_name = f"【{tag_effect['name_prefix']}】{final_name}"

            final_hp *= tag_effect.get("hp_multiplier", 1.0)
            final_attack *= tag_effect.get("attack_multiplier", 1.0)
            final_defense *= tag_effect.get("defense_multiplier", 1.0)
            final_gold *= tag_effect.get("gold_multiplier", 1.0)
            final_exp *= tag_effect.get("exp_multiplier", 1.0)

            if "add_to_loot" in tag_effect:
                combined_loot_table.extend(tag_effect["add_to_loot"])

        final_hp = int(final_hp)
        instance = Monster(
            id=template_id,
            name=final_name,
            hp=final_hp,
            max_hp=final_hp,
            attack=int(final_attack),
            defense=int(final_defense),
            rewards={
                "gold": int(final_gold),
                "experience": int(final_exp),
                "items": cls._generate_rewards(combined_loot_table)
            }
        )
        return instance

    @classmethod
    def create_boss(cls, template_id: str, player_level_index: int, config_manager: ConfigManager,
                    scaling_factor: float = 1.0) -> Optional[Boss]:
        template = config_manager.boss_data.get(template_id)
        if not template:
            logger.warning(f"尝试创建Boss失败：找不到模板ID {template_id}")
            return None

        base_hp = 100 * player_level_index + 500
        base_attack = 10 * player_level_index + 40
        base_defense = 5 * player_level_index + 20
        base_gold = 50 * player_level_index + 1000
        base_exp = 100 * player_level_index + 2000

        final_name = template["name"]
        final_hp = base_hp
        final_attack = base_attack
        final_defense = base_defense
        final_gold = base_gold
        final_exp = base_exp
        combined_loot_table = []

        for tag_name in template.get("tags", []):
            tag_effect = config_manager.tag_data.get(tag_name, {})
            if "name_prefix" in tag_effect:
                final_name = f"【{tag_effect['name_prefix']}】{final_name}"
            final_hp *= tag_effect.get("hp_multiplier", 1.0)
            final_attack *= tag_effect.get("attack_multiplier", 1.0)
            final_defense *= tag_effect.get("defense_multiplier", 1.0)
            final_gold *= tag_effect.get("gold_multiplier", 1.0)
            final_exp *= tag_effect.get("exp_multiplier", 1.0)
            if "add_to_loot" in tag_effect:
                combined_loot_table.extend(tag_effect["add_to_loot"])

        # 应用强度系数
        final_hp *= scaling_factor
        final_attack *= scaling_factor
        final_defense *= scaling_factor

        final_hp = int(final_hp)
        instance = Boss(
            id=template_id,
            name=final_name,
            hp=final_hp,
            max_hp=final_hp,
            attack=int(final_attack),
            defense=int(final_defense),
            cooldown_minutes=template["cooldown_minutes"],
            rewards={
                "gold": int(final_gold),
                "experience": int(final_exp),
                "items": cls._generate_rewards(combined_loot_table)
            }
        )
        return instance


class BattleManager:
    """战斗管理器"""

    def __init__(self, db: DataBase, config: AstrBotConfig, config_manager: ConfigManager):
        self.db = db
        self.config = config
        self.config_manager = config_manager

    async def ensure_bosses_are_spawned(self) -> List[Tuple[ActiveWorldBoss, Boss]]:
        active_boss_instances = await self.db.get_active_bosses()
        active_boss_map = {b.boss_id: b for b in active_boss_instances}
        all_boss_templates = self.config_manager.boss_data

        top_players = await self.db.get_top_players(self.config["VALUES"]["WORLD_BOSS_TOP_PLAYERS_AVG"])

        for boss_id, template in all_boss_templates.items():
            if boss_id not in active_boss_map:
                logger.info(f"世界Boss {template['name']} (ID: {boss_id}) 当前未激活，开始生成...")

                avg_level_index = int(sum(p.level_index for p in top_players) / len(top_players)) if top_players else 1

                boss_with_stats = MonsterGenerator.create_boss(boss_id, avg_level_index, self.config_manager)
                if not boss_with_stats:
                    logger.error(f"无法为Boss ID {boss_id} 生成属性，请检查配置。")
                    continue

                new_boss_instance = ActiveWorldBoss(
                    boss_id=boss_id,
                    current_hp=boss_with_stats.max_hp,
                    max_hp=boss_with_stats.max_hp,
                    spawned_at=time.time(),
                    level_index=avg_level_index
                )
                await self.db.create_active_boss(new_boss_instance)
                active_boss_map[boss_id] = new_boss_instance

        result = []
        for boss_id, active_instance in active_boss_map.items():
            boss_template = MonsterGenerator.create_boss(boss_id, active_instance.level_index, self.config_manager)
            if boss_template:
                result.append((active_instance, boss_template))
        return result

    async def player_fight_boss(self, player: Player, boss_id: str, player_name: str) -> str:
        active_boss_instance = next((b for b in await self.db.get_active_bosses() if b.boss_id == boss_id), None)
        if not active_boss_instance or active_boss_instance.current_hp <= 0:
            return f"来晚了一步，ID为【{boss_id}】的Boss已被击败或已消失！"

        boss = MonsterGenerator.create_boss(boss_id, active_boss_instance.level_index, self.config_manager)
        if not boss:
            return "错误：无法加载Boss战斗数据！"

        p_clone = player.clone()
        p_stats = p_clone.get_combat_stats(self.config_manager)  # 获取最终战斗属性
        boss_hp = active_boss_instance.current_hp

        total_damage_dealt = 0
        total_damage_taken = 0
        turn = 0
        max_turns = 50

        while p_clone.hp > 1 and boss_hp > 0 and turn < max_turns:
            turn += 1
            damage_to_boss = max(1, p_stats['attack'] - boss.defense)
            damage_to_boss = min(damage_to_boss, boss_hp)
            boss_hp -= damage_to_boss
            total_damage_dealt += damage_to_boss

            if boss_hp <= 0:
                break

            damage_to_player = max(1, boss.attack - p_stats['defense'])
            p_clone.hp -= damage_to_player
            total_damage_taken += damage_to_player

        if p_clone.hp < 1:
            p_clone.hp = 1

        combat_summary = [f"你向【{boss.name}】发起了挑战！", "……激战过后……"]
        if p_clone.hp <= 1 and boss_hp > 0:
            combat_summary.append("✗ 你不敌妖兽，力竭倒下！")
        else:
            combat_summary.append("✓ 你坚持到了最后！")

        combat_summary.append(f"- 战斗历时: {turn}回合")
        combat_summary.append(f"- 总计伤害: {total_damage_dealt}点")
        combat_summary.append(f"- 承受伤害: {total_damage_taken}点")

        final_report = ["\n".join(combat_summary)]
        player.hp = p_clone.hp
        await self.db.update_player(player)
        await self.db.update_active_boss_hp(boss_id, boss_hp)
        if total_damage_dealt > 0:
            await self.db.record_boss_damage(boss_id, player.user_id, player_name, total_damage_dealt)
            final_report.append(f"\n你本次共对Boss贡献了 {total_damage_dealt} 点伤害！")

        if boss_hp <= 0:
            final_report.append(f"\n**惊天动地！【{boss.name}】在众位道友的合力之下倒下了！**")
            final_report.append(await self._end_battle(boss, active_boss_instance))

        return "\n".join(final_report)

    async def _end_battle(self, boss_template: Boss, boss_instance: ActiveWorldBoss) -> str:
        participants = await self.db.get_boss_participants(boss_instance.boss_id)
        if not participants:
            await self.db.clear_boss_data(boss_instance.boss_id)
            return "但似乎无人对此Boss造成伤害，奖励无人获得。"
        total_damage_dealt = sum(p['total_damage'] for p in participants) or 1
        reward_report = ["\n--- 战利品结算 ---"]
        updated_players = []
        for p_data in participants:
            player_obj = await self.db.get_player_by_id(p_data['user_id'])
            if player_obj:
                damage_contribution = p_data['total_damage'] / total_damage_dealt
                gold_reward = int(boss_template.rewards['gold'] * damage_contribution)
                exp_reward = int(boss_template.rewards['experience'] * damage_contribution)
                player_obj.gold += gold_reward
                player_obj.experience += exp_reward
                updated_players.append(player_obj)
                reward_report.append(f"道友 {p_data['user_name']} 获得灵石 {gold_reward}，修为 {exp_reward}！")
        if updated_players:
            await self.db.update_players_in_transaction(updated_players)
        await self.db.clear_boss_data(boss_instance.boss_id)
        return "\n".join(reward_report)

    def player_vs_monster(self, player: Player, monster) -> Tuple[bool, List[str], Player]:
        p_clone = player.clone()
        p_stats = p_clone.get_combat_stats(self.config_manager)  # 获取最终战斗属性
        monster_hp = monster.hp

        total_damage_dealt = 0
        total_damage_taken = 0
        turn = 0

        while p_clone.hp > 1 and monster_hp > 0:
            turn += 1
            damage_to_monster = max(1, p_stats['attack'] - monster.defense)
            monster_hp -= damage_to_monster
            total_damage_dealt += damage_to_monster

            if monster_hp <= 0:
                break

            damage_to_player = max(1, monster.attack - p_stats['defense'])
            p_clone.hp -= damage_to_player
            total_damage_taken += damage_to_player

        if p_clone.hp < 1:
            p_clone.hp = 1

        victory = monster_hp <= 0

        combat_summary = [f"你遭遇了【{monster.name}】！", "……激战过后……"]
        if victory:
            combat_summary.append("✓ 你获得了胜利！")
        else:
            combat_summary.append("✗ 你不敌对手，力竭倒下！")

        combat_summary.append(f"- 战斗历时: {turn}回合")
        combat_summary.append(f"- 总计伤害: {total_damage_dealt}点")
        combat_summary.append(f"- 承受伤害: {total_damage_taken}点")

        return victory, combat_summary, p_clone

    def player_vs_player(self, attacker: Player, defender: Player, attacker_name: Optional[str],
                         defender_name: Optional[str]) -> Tuple[Optional[Player], Optional[Player], List[str]]:
        p1 = attacker.clone()
        p2 = defender.clone()

        p1_stats = p1.get_combat_stats(self.config_manager)
        p2_stats = p2.get_combat_stats(self.config_manager)

        p1_display = attacker_name or attacker.user_id[-4:]
        p2_display = defender_name or defender.user_id[-4:]

        p1_damage_dealt = 0
        p2_damage_dealt = 0
        turn = 0
        max_turns = 30

        while p1.hp > 1 and p2.hp > 1 and turn < max_turns:
            turn += 1
            damage_to_p2 = max(1, p1_stats['attack'] - p2_stats['defense'])
            p2.hp -= damage_to_p2
            p1_damage_dealt += damage_to_p2
            if p2.hp <= 1:
                p2.hp = 1
                break

            damage_to_p1 = max(1, p2_stats['attack'] - p1_stats['defense'])
            p1.hp -= damage_to_p1
            p2_damage_dealt += damage_to_p1
            if p1.hp <= 1:
                p1.hp = 1
                break

        combat_summary = [f"⚔️【切磋】{p1_display} vs {p2_display}", "……一番激斗……"]

        winner = None
        winner_display = ""
        if p1.hp <= 1:
            winner = defender
            winner_display = p2_display
            combat_summary.append(f"🏆 {winner_display} 技高一筹，获得了胜利！")
        elif p2.hp <= 1:
            winner = attacker
            winner_display = p1_display
            combat_summary.append(f"🏆 {winner_display} 技高一筹，获得了胜利！")
        else:
            combat_summary.append("平【平局】双方大战三十回合，未分胜负！")

        combat_summary.append(f"\n--- {p1_display} 战报 ---")
        combat_summary.append(f"- 总计伤害: {p1_damage_dealt}点")
        combat_summary.append(f"- 承受伤害: {p2_damage_dealt}点")
        combat_summary.append(f"- 剩余生命: {p1.hp}/{p1.max_hp}")

        combat_summary.append(f"\n--- {p2_display} 战报 ---")
        combat_summary.append(f"- 总计伤害: {p2_damage_dealt}点")
        combat_summary.append(f"- 承受伤害: {p1_damage_dealt}点")
        combat_summary.append(f"- 剩余生命: {p2.hp}/{p2.max_hp}")

        if winner == attacker:
            return attacker, defender, combat_summary
        elif winner == defender:
            return defender, attacker, combat_summary
        else:
            return None, None, combat_summary
