"""
Combat management module for the AlgoRot battle simulation.

This module handles all physical interactions between fighters, including 
high-fidelity hitbox detection, parry/guard-break resolution, and complex 
damage scaling based on weapon momentum and impact quality.
"""

import math
import random

from config import (
    BASE_KNOCKBACK, HIT_STOP_FRAMES, HAMMER_HIT_STOP_FRAMES, HAMMER_NORMAL_HIT_STOP,
    SCREEN_SHAKE_INTENSITY,
    HIT_SLOWMO_FRAMES, CRIT_CHANCE, CRIT_MULTIPLIER, CRIT_IMPACT_FRAMES,
    MOMENTUM_MAX_STACKS, MOMENTUM_DAMAGE_BONUS,
    PARRY_COOLDOWN_FRAMES,
    GUARD_BREAK_STUN_FRAMES, GUARD_BREAK_KNOCKBACK,
    GUARD_BREAK_HIT_STOP, GUARD_BREAK_DAMAGE_MIN, GUARD_BREAK_DAMAGE_MAX,
    GUARD_BREAK_SCREEN_SHAKE
)

class CombatManager:
    """Orchestrates combat logic and physical resolutions.

    The CombatManager is responsible for the 'game feel' of the simulation, 
    calculating when hits occur and applying the appropriate visual and 
    mechanical feedback (hit-stops, screenshake, damage numbers).
    """

    def __init__(self):
        """Initializes the CombatManager."""
        pass

    def _check_sword_hit(self, attacker, defender) -> tuple:
        """Performs profile-based hitbox detection for a weapon.

        Unlike simple line-circle collision, this method checks the weapon's 
        variable-width cross-sections (profile) against the defender's radius. 
        This allows for weapons like axes or spears to have accurately 
        shaped lethal zones.

        Args:
            attacker: The fighter performing the attack.
            defender: The fighter being attacked.

        Returns:
            A tuple of (spawn_pos, damage_t):
                spawn_pos: World coordinates (x, y) of the hit for visual effects.
                damage_t: Normalized position [0.0, 1.0] along the blade length.
        """
        cfg = attacker.weapon_config
        profile      = cfg.get('hitbox_profile', [])
        handle_ratio = cfg.get('handle_ratio', 0.25)

        if not profile:
            return None, 0.0

        # Spatial partitioning: quick distance check before expensive profile sampling
        max_half_w   = max(hw for _, hw in profile)
        max_reach    = attacker.radius + 3 + attacker.sword_length + defender.radius + max_half_w
        fighter_dist = math.hypot(attacker.x - defender.x, attacker.y - defender.y)
        if fighter_dist > max_reach:
            return None, 0.0

        (base_x, base_y), (tip_x, tip_y) = attacker.get_sword_hitbox()

        best_damage_t  = None
        best_spawn_t   = None
        best_spawn_pos = None

        # Sample the weapon profile to find the most favorable hit point
        for (t, half_w) in profile:
            if t < handle_ratio:
                continue

            px = base_x + (tip_x - base_x) * t
            py = base_y + (tip_y - base_y) * t

            dist = math.hypot(px - defender.x, py - defender.y)
            if dist < half_w + defender.radius:
                # damage_t is taken from the handle-most point for consistency
                if best_damage_t is None or t < best_damage_t:
                    best_damage_t = t
                # spawn_pos is taken from the tip-most point for better visual impact
                if best_spawn_t is None or t > best_spawn_t:
                    best_spawn_t = t
                    best_spawn_pos = (px, py)

        return (best_spawn_pos, best_damage_t) if best_spawn_pos else (None, 0.0)


    @staticmethod
    def _cross(o, a, b):
        """Calculates the 2D cross product of vectors (a-o) and (b-o)."""
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def _segments_intersect(self, p1, p2, p3, p4) -> bool:
        """Checks if two line segments (p1-p2) and (p3-p4) intersect.

        Used primarily for weapon-on-weapon parry detection.
        """
        d1 = self._cross(p3, p4, p1)
        d2 = self._cross(p3, p4, p2)
        d3 = self._cross(p1, p2, p3)
        d4 = self._cross(p1, p2, p4)
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
        return False

    def _get_intersection_point(self, p1, p2, p3, p4) -> tuple:
        """Calculates the exact world coordinates of a segment intersection."""
        x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    def _apply_guard_break(self, broken, breaker, ix_point, game):
        """Transitions a fighter into the stunned Guard Break state.

        This occurs when a fighter's energy pool is insufficient to block an incoming 
        weapon clash. The state resets momentum and applies significant knockback.

        Args:
            broken: The fighter who lost their guard.
            breaker: The fighter who caused the break.
            ix_point: The world position of the impact.
            game: Reference to the main game state for particle/UI triggers.
        """
        game.particles.emit(ix_point[0], ix_point[1], (255, 0, 0),    count=50, size=7)
        game.particles.emit(ix_point[0], ix_point[1], (255, 255, 255), count=25, size=5)

        guard_break_dmg = random.randint(GUARD_BREAK_DAMAGE_MIN, GUARD_BREAK_DAMAGE_MAX)
        broken.health       -= guard_break_dmg
        broken.parry_energy  = 0
        broken.momentum      = 0

        kb_angle = math.atan2(broken.y - breaker.y, broken.x - breaker.x)
        broken.vx = math.cos(kb_angle) * GUARD_BREAK_KNOCKBACK
        broken.vy = math.sin(kb_angle) * GUARD_BREAK_KNOCKBACK

        broken.guard_break_stun = GUARD_BREAK_STUN_FRAMES
        broken.invincible       = 0
        broken.parry_cooldown   = GUARD_BREAK_STUN_FRAMES

        if guard_break_dmg > 0:
            game.damage_numbers.spawn(ix_point[0], ix_point[1] - 30,
                                      guard_break_dmg, broken.color, True)

        game.hit_stop     = GUARD_BREAK_HIT_STOP
        game.screen_shake = GUARD_BREAK_SCREEN_SHAKE
        if hasattr(game, 'sound_manager'):
            game.sound_manager.play_guard_break()

    def handle_collisions(self, blue, red, game):
        """Resolves all combat interactions for the current frame.

        Logic flow:
            1. Parry Check: If weapons intersect, check energy for a successful block.
            2. Body Hit Check: If no parry occurred, check if weapons overlap fighter bodies.
        
        Args:
            blue: The blue fighter instance.
            red: The red fighter instance.
            game: Reference to the main simulation state.
        """

        # === PARRY CHECK (Act 1 & 2) ===
        blue_base, blue_tip = blue.get_sword_hitbox()
        red_base,  red_tip  = red.get_sword_hitbox()

        if self._segments_intersect(blue_base, blue_tip, red_base, red_tip):
            if blue.parry_cooldown <= 0 and red.parry_cooldown <= 0:

                ix_point = self._get_intersection_point(blue_base, blue_tip, red_base, red_tip)
                if not ix_point:
                    ix_point = ((blue_base[0] + red_base[0]) / 2,
                                (blue_base[1] + red_base[1]) / 2)

                # Determine if fighters have enough energy to sustain the clash
                blue_cost = blue.parry_cost * red.weapon_config.get("parry_drain_mult", 1.0)
                red_cost  = red.parry_cost  * blue.weapon_config.get("parry_drain_mult", 1.0)
                blue_can  = blue.parry_energy >= blue_cost
                red_can   = red.parry_energy  >= red_cost

                if blue_can and red_can:
                    # Successful Parry: Both fighters pay energy and recoil
                    blue.parry_energy -= blue_cost
                    red.parry_energy  -= red_cost
                    blue.parry_cooldown = PARRY_COOLDOWN_FRAMES
                    red.parry_cooldown  = PARRY_COOLDOWN_FRAMES

                    # Spin reversal logic: the fighter with less remaining energy ratio 
                    # is the one who is 'overpowered' and forced to reverse spin.
                    blue_ratio = blue.parry_energy / blue.max_parry_energy
                    red_ratio  = red.parry_energy  / red.max_parry_energy
                    if blue_ratio < red_ratio:
                        blue.spin_direction *= -1
                    elif red_ratio < blue_ratio:
                        red.spin_direction *= -1
                    else: 
                        if random.random() < 0.5: blue.spin_direction *= -1
                        else:                     red.spin_direction *= -1

                    game.hit_stop     = 8
                    game.screen_shake = 12
                    game.particles.emit_parry(ix_point[0], ix_point[1], (255, 255, 100), count=20)
                    if hasattr(game, 'sound_manager'):
                        # Use the attacker's clash sound — heavier weapons sound heavier
                        game.sound_manager.play_weapon_clash(blue.weapon)

                else:
                    # Guard Break: One or both fighters failed the energy check
                    if blue_can and not red_can:
                        broken, breaker = red, blue
                    elif red_can and not blue_can:
                        broken, breaker = blue, red
                    else:
                        broken, breaker = (blue, red) if blue.parry_energy <= red.parry_energy else (red, blue)

                    self._apply_guard_break(broken, breaker, ix_point, game)

        # === BODY HIT CHECK (Act 3) ===
        pairs = [(blue, red), (red, blue)]
        random.shuffle(pairs)

        for attacker, defender in pairs:
            hit_pos, impact_ratio = self._check_sword_hit(attacker, defender)
            if hit_pos is None:
                continue

            # Damage Calculation Strategy
            is_crit   = random.random() < CRIT_CHANCE
            crit_mult = CRIT_MULTIPLIER if is_crit else 1.0

            damage_mult       = attacker.get_attack_damage_multiplier()
            momentum_bonus    = attacker.momentum * MOMENTUM_DAMAGE_BONUS
            total_damage_mult = damage_mult * crit_mult * (1.0 + momentum_bonus)

            angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)

            # Knockback calculation: scales with damage intensity
            weapon_kb_mult = attacker.weapon_config.get("knockback_mult", 1.0)
            knockback = BASE_KNOCKBACK * crit_mult * (1.0 + (total_damage_mult - 1.0) * 0.5) * 1.5 * weapon_kb_mult

            if hasattr(game, 'chaos'):
                knockback *= game.chaos.get_knockback_mult()
                if game.chaos.is_ultra_knockback():
                    game.screen_shake = max(game.screen_shake, SCREEN_SHAKE_INTENSITY * 3)

            # Rotation-based damage multiplier (prevents damage from accidental grazes)
            rotation_mult = self._get_rotation_mult(attacker.rotation_since_last_hit)

            # Sweet-spot logic: hits near the tip or on specific weapons deal more damage
            all_sweet_spot       = attacker.weapon_config.get("all_sweet_spot", False)
            sweet_spot_threshold = attacker.weapon_config.get("sweet_spot_threshold", 0.70)

            if not all_sweet_spot and impact_ratio < sweet_spot_threshold:
                base_damage     = 13
                shake_intensity = 4
                spark_count     = 10
                spark_color     = (255, 255, 0)
                spark_size      = 4
                is_sweet_spot   = False
            else:
                base_damage     = 18
                shake_intensity = 15
                spark_count     = 30
                spark_color     = (255, 100, 0) if random.random() < 0.5 else (255, 0, 0)
                spark_size      = 6
                is_sweet_spot   = True

            damage = base_damage * total_damage_mult * rotation_mult

            # Reset rotation accumulator on successful hit to prevent back-to-back scaling
            attacker.rotation_since_last_hit = 0.0

            if defender.take_damage(damage, angle, knockback, game.particles):
                game.particles.emit(hit_pos[0], hit_pos[1], spark_color,
                                    count=spark_count, size=spark_size)
                game.hit_stop     = HIT_STOP_FRAMES
                game.screen_shake = shake_intensity

                if damage > 0:
                    game.damage_numbers.spawn(hit_pos[0], hit_pos[1] - 20,
                                              damage, attacker.color, is_crit or is_sweet_spot)

                if hasattr(game, 'sound_manager'):
                    if is_sweet_spot:
                        game.sound_manager.play_weapon_sweet_spot(attacker.weapon)
                    else:
                        game.sound_manager.play_weapon_hit(attacker.weapon)

                game.hit_slowmo_frames = HIT_SLOWMO_FRAMES
                game._reset_inactivity()

                gain = attacker.weapon_config.get("momentum_gain", 1)
                attacker.momentum = min(MOMENTUM_MAX_STACKS, attacker.momentum + gain)

                # Apply weapon-specific effects (e.g., Hammer's spin reversal)
                if attacker.weapon_config.get("reverses_spin", False):
                    defender.spin_direction *= -1

                # Hammer hitstop override for extreme impact feel
                if attacker.weapon_config.get("max_hitstop", False):
                    if is_crit: game.hit_stop = max(game.hit_stop, HAMMER_HIT_STOP_FRAMES)
                    else:       game.hit_stop = max(game.hit_stop, HAMMER_NORMAL_HIT_STOP)

                # High-impact cinematic sequences for critical hits
                if is_crit and is_sweet_spot:
                    game.decomp_slowmo_frames      = 30
                    game.decomp_slowmo_accumulator = 0.0
                    game.hit_slowmo_frames         = 0
                    game.hit_stop                  = 4
                    game.screen_shake              = max(game.screen_shake, 35)
                    game.particles.emit_explosion(hit_pos[0], hit_pos[1], (0, 255, 255),   count=25)
                    game.particles.emit_explosion(hit_pos[0], hit_pos[1], (255, 0, 255),   count=25)
                    game.particles.emit_explosion(hit_pos[0], hit_pos[1], (255, 255, 255), count=15)
                    if attacker.weapon_config.get("max_hitstop", False):
                        game.hit_stop = max(game.hit_stop, HAMMER_HIT_STOP_FRAMES)
                elif is_crit:
                    game.crit_impact_frames      = CRIT_IMPACT_FRAMES
                    game.crit_impact_accumulator = 0.0
                    game.crit_flash_phase        = 1
                    game.screen_shake            = max(game.screen_shake, SCREEN_SHAKE_INTENSITY * 2)


    @staticmethod
    def _get_rotation_mult(rotation: float) -> float:
        """Calculates damage multiplier based on cumulative weapon rotation.

        This ensures that 'grazes' or accidental bumps deal less damage, while 
        full intentional swings are rewarded.

        Pacing:
          - < π (Graze): 0.6x penalty
          - π to 2π (Standard): 1.0x baseline
          - ≥ 2π (Full Swing): 1.3x bonus
        """
        if rotation < math.pi:
            return 0.6
        elif rotation < 2 * math.pi:
            return 1.0
        else:
            return 1.3
