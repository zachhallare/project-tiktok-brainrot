import math
import random

from config import (
    BASE_KNOCKBACK, HIT_STOP_FRAMES, HAMMER_HIT_STOP_FRAMES, HAMMER_NORMAL_HIT_STOP,
    SCREEN_SHAKE_INTENSITY,
    HIT_SLOWMO_FRAMES, CRIT_CHANCE, CRIT_MULTIPLIER, CRIT_IMPACT_FRAMES,
    MOMENTUM_MAX_STACKS, MOMENTUM_DAMAGE_BONUS
)

class CombatManager:
    """Handles combat interactions, collision detection, and damage calculations."""

    def __init__(self):
        pass

    def _check_sword_hit(self, attacker, defender):
        """
        Profile-based hitbox using per-weapon cross-section data.

        Returns (spawn_pos, damage_t):
          spawn_pos  — world position of the TIP-MOST overlapping profile point,
                       used for particle / damage number placement.
          damage_t   — t of the HANDLE-MOST overlapping profile point,
                       used for sweet-spot / impact-ratio calculations.
        """
        cfg = attacker.weapon_config
        profile      = cfg.get('hitbox_profile', [])
        handle_ratio = cfg.get('handle_ratio', 0.25)

        if not profile:
            return None, 0.0

        max_half_w   = max(hw for _, hw in profile)
        max_reach    = attacker.radius + 3 + attacker.sword_length + defender.radius + max_half_w
        fighter_dist = math.hypot(attacker.x - defender.x, attacker.y - defender.y)
        if fighter_dist > max_reach:
            return None, 0.0

        (base_x, base_y), (tip_x, tip_y) = attacker.get_sword_hitbox()

        best_damage_t  = None
        best_spawn_t   = None
        best_spawn_pos = None

        for (t, half_w) in profile:
            if t < handle_ratio:
                continue

            px = base_x + (tip_x - base_x) * t
            py = base_y + (tip_y - base_y) * t

            dist = math.hypot(px - defender.x, py - defender.y)
            if dist < half_w + defender.radius:
                if best_damage_t is None or t < best_damage_t:
                    best_damage_t = t
                if best_spawn_t is None or t > best_spawn_t:
                    best_spawn_t = t
                    best_spawn_pos = (px, py)

        return (best_spawn_pos, best_damage_t) if best_spawn_pos else (None, 0.0)


    @staticmethod
    def _cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def _segments_intersect(self, p1, p2, p3, p4):
        d1 = self._cross(p3, p4, p1)
        d2 = self._cross(p3, p4, p2)
        d3 = self._cross(p1, p2, p3)
        d4 = self._cross(p1, p2, p4)
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
        return False

    def _get_intersection_point(self, p1, p2, p3, p4):
        x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    def handle_collisions(self, blue, red, game):
        """Detect and resolve combat — parry check then body hit check."""

        # === PARRY CHECK ===
        blue_base, blue_tip = blue.get_sword_hitbox()
        red_base,  red_tip  = red.get_sword_hitbox()

        if self._segments_intersect(blue_base, blue_tip, red_base, red_tip):
            if blue.parry_cooldown <= 0 and red.parry_cooldown <= 0:

                ix_point = self._get_intersection_point(blue_base, blue_tip, red_base, red_tip)
                if not ix_point:
                    ix_point = ((blue_base[0] + red_base[0]) / 2,
                                (blue_base[1] + red_base[1]) / 2)

                both_parried = True
                for fighter in (blue, red):
                    other = red if fighter is blue else blue
                    effective_cost = fighter.parry_cost * other.weapon_config.get("parry_drain_mult", 1.0)

                    if fighter.parry_energy >= effective_cost:
                        fighter.parry_energy -= effective_cost
                        fighter.spin_direction *= -1
                        fighter.parry_cooldown = 15
                    else:
                        both_parried = False
                        game.particles.emit(ix_point[0], ix_point[1], (255, 0, 0),    count=40, size=6)
                        game.particles.emit(ix_point[0], ix_point[1], (255, 255, 255), count=20, size=4)

                        guard_break_dmg = random.randint(15, 25)
                        fighter.health      -= guard_break_dmg
                        fighter.parry_energy = 0
                        fighter.momentum     = 0

                        fighter.vx = -fighter.vx * 1.5
                        fighter.vy = -fighter.vy * 1.5
                        fighter.parry_cooldown = 30

                        if guard_break_dmg > 0:
                            game.damage_numbers.spawn(ix_point[0], ix_point[1] - 30,
                                                      guard_break_dmg, fighter.color, True)

                if both_parried:
                    game.hit_stop     = 8
                    game.screen_shake = 12
                    game.particles.emit(ix_point[0], ix_point[1], (255, 255, 100), count=20, size=4)
                else:
                    game.hit_stop     = 12
                    game.screen_shake = 20

                if hasattr(game, 'sound_manager'):
                    game.sound_manager.play_clash()

        # === BODY HIT CHECK ===
        for attacker, defender in [(blue, red), (red, blue)]:
            hit_pos, impact_ratio = self._check_sword_hit(attacker, defender)
            if hit_pos is None:
                continue

            is_crit   = random.random() < CRIT_CHANCE
            crit_mult = CRIT_MULTIPLIER if is_crit else 1.0

            damage_mult       = attacker.get_attack_damage_multiplier()
            momentum_bonus    = attacker.momentum * MOMENTUM_DAMAGE_BONUS
            total_damage_mult = damage_mult * crit_mult * (1.0 + momentum_bonus)

            angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)

            weapon_kb_mult = attacker.weapon_config.get("knockback_mult", 1.0)
            knockback = BASE_KNOCKBACK * crit_mult * (1.0 + (total_damage_mult - 1.0) * 0.5) * 1.5 * weapon_kb_mult

            if hasattr(game, 'chaos'):
                knockback *= game.chaos.get_knockback_mult()
                if game.chaos.is_ultra_knockback():
                    game.screen_shake = max(game.screen_shake, SCREEN_SHAKE_INTENSITY * 3)

            # Sweet-spot logic
            all_sweet_spot       = attacker.weapon_config.get("all_sweet_spot", False)
            sweet_spot_threshold = attacker.weapon_config.get("sweet_spot_threshold", 0.70)

            if not all_sweet_spot and impact_ratio < sweet_spot_threshold:
                base_damage     = 10
                shake_intensity = 4
                spark_count     = 10
                spark_color     = (255, 255, 0)
                spark_size      = 4
                is_sweet_spot   = False
            else:
                base_damage     = 15
                if is_crit:
                    base_damage = 4
                shake_intensity = 15
                spark_count     = 30
                spark_color     = (255, 100, 0) if random.random() < 0.5 else (255, 0, 0)
                spark_size      = 6
                is_sweet_spot   = True

            damage = base_damage * total_damage_mult

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
                        game.sound_manager.play_crit()
                    else:
                        game.sound_manager.play_hit()

                game.hit_slowmo_frames = HIT_SLOWMO_FRAMES
                game._reset_inactivity()

                gain = attacker.weapon_config.get("momentum_gain", 1)
                attacker.momentum = min(MOMENTUM_MAX_STACKS, attacker.momentum + gain)

                # Weapon special effects
                if attacker.weapon_config.get("reverses_spin", False):
                    defender.spin_direction *= -1

                # Hammer hitstop: normal hits get a moderate freeze (12 frames),
                # only crits get the full dramatic freeze (30 frames).
                # This keeps the chaos identity without exhausting the viewer.
                if attacker.weapon_config.get("max_hitstop", False):
                    if is_crit:
                        game.hit_stop = max(game.hit_stop, HAMMER_HIT_STOP_FRAMES)
                    else:
                        game.hit_stop = max(game.hit_stop, HAMMER_NORMAL_HIT_STOP)

                # Critical hit sequences
                if is_crit and is_sweet_spot:
                    game.decomp_slowmo_frames      = 30
                    game.decomp_slowmo_accumulator = 0.0
                    game.hit_slowmo_frames         = 0
                    game.hit_stop                  = 4
                    game.screen_shake              = max(game.screen_shake, 35)
                    game.particles.emit_explosion(hit_pos[0], hit_pos[1], (0, 255, 255),   count=25)
                    game.particles.emit_explosion(hit_pos[0], hit_pos[1], (255, 0, 255),   count=25)
                    game.particles.emit_explosion(hit_pos[0], hit_pos[1], (255, 255, 255), count=15)
                    # Hammer crit: override the decomp hit_stop=4 with full freeze
                    if attacker.weapon_config.get("max_hitstop", False):
                        game.hit_stop = max(game.hit_stop, HAMMER_HIT_STOP_FRAMES)
                elif is_crit:
                    game.crit_impact_frames      = CRIT_IMPACT_FRAMES
                    game.crit_impact_accumulator = 0.0
                    game.crit_flash_phase        = 1
                    game.screen_shake            = max(game.screen_shake, SCREEN_SHAKE_INTENSITY * 2)


                    