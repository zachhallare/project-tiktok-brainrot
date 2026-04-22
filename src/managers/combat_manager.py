import math
import random

from config import (
    BASE_KNOCKBACK, HIT_STOP_FRAMES, SCREEN_SHAKE_INTENSITY,
    HIT_SLOWMO_FRAMES, CRIT_CHANCE, CRIT_MULTIPLIER, CRIT_IMPACT_FRAMES
)

class CombatManager:
    """Handles combat interactions, collision detection, and damage calculations."""
    
    def __init__(self):
        pass

    def _check_sword_hit(self, attacker, defender):
        """
        Profile-based hitbox using per-weapon cross-section data.

        Each weapon defines a hitbox_profile — a list of (t, half_width_px):
        t=0 is the handle attachment, t=1 is the tip.
        half_width_px is the dangerous radius of the weapon at that point.

        A hit registers when the defender's circle overlaps the weapon's
        cross-section circle at any profile point in the damage zone.
        This correctly ignores empty sprite pixels and handle regions.
        """
        cfg = attacker.weapon_config
        profile      = cfg.get('hitbox_profile', [])
        handle_ratio = cfg.get('handle_ratio', 0.25)

        if not profile:
            return None, 0.0

        # Broad-phase early-out
        max_half_w  = max(hw for _, hw in profile)
        max_reach   = attacker.radius + 3 + attacker.sword_length + defender.radius + max_half_w
        fighter_dist = math.hypot(attacker.x - defender.x, attacker.y - defender.y)
        if fighter_dist > max_reach:
            return None, 0.0

        (base_x, base_y), (tip_x, tip_y) = attacker.get_sword_hitbox()

        best_hit = None
        best_t   = None

        for (t, half_w) in profile:
            if t < handle_ratio:
                continue  # handle — no damage

            # World position of this profile point along the blade centerline
            px = base_x + (tip_x - base_x) * t
            py = base_y + (tip_y - base_y) * t

            # Hit if defender circle overlaps the weapon cross-section circle
            dist = math.hypot(px - defender.x, py - defender.y)
            if dist < half_w + defender.radius:
                # Keep the hit closest to the handle (smallest t) for impact_ratio
                if best_t is None or t < best_t:
                    best_hit = (px, py)
                    best_t   = t

        return (best_hit, best_t) if best_hit else (None, 0.0)


    @staticmethod
    def _cross(o, a, b):
        """2D cross product of vectors OA and OB."""
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    def _segments_intersect(self, p1, p2, p3, p4):
        """Check if line segment p1-p2 intersects p3-p4 using cross products."""
        d1 = self._cross(p3, p4, p1)
        d2 = self._cross(p3, p4, p2)
        d3 = self._cross(p1, p2, p3)
        d4 = self._cross(p1, p2, p4)
        
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
        
        return False
    
    def _get_intersection_point(self, p1, p2, p3, p4):
        """Get the intersection point of segments p1-p2 and p3-p4."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (ix, iy)

    def handle_collisions(self, blue, red, game):
        """Detect and resolve combat interactions with sword-to-sword parry.
        Modifies game state objects directly (particles, screen shake, hit stop, etc).
        """
        
        # === PARRY CHECK: Sword-to-Sword intersection ===
        blue_base, blue_tip = blue.get_sword_hitbox()
        red_base, red_tip = red.get_sword_hitbox()
        
        if self._segments_intersect(blue_base, blue_tip, red_base, red_tip):
            if blue.parry_cooldown <= 0 and red.parry_cooldown <= 0:
                
                ix_point = self._get_intersection_point(blue_base, blue_tip, red_base, red_tip)
                if not ix_point:
                    ix_point = ((blue_base[0] + red_base[0]) / 2, (blue_base[1] + red_base[1]) / 2)
                
                both_parried = True
                for fighter in (blue, red):
                    if fighter.parry_energy >= fighter.parry_cost:
                        # SUCCESSFUL PARRY
                        fighter.parry_energy -= fighter.parry_cost
                        fighter.spin_direction *= -1
                        fighter.parry_cooldown = 15
                    else:
                        both_parried = False
                        # GUARD BREAK! (Energy depleted)
                        # Spawn massive red/white 'Guard Break' sparks
                        game.particles.emit(ix_point[0], ix_point[1], (255, 0, 0), count=40, size=6)
                        game.particles.emit(ix_point[0], ix_point[1], (255, 255, 255), count=20, size=4)

                        # Dynamic Penalty Damage: Softer penalty, between 15 and 25 damage
                        guard_break_dmg = random.randint(15, 25)
                        fighter.health -= guard_break_dmg 
                        fighter.parry_energy = 0 # Reset energy to zero

                        # Apply aggressive hit-stun knockback to the defender
                        fighter.vx = -fighter.vx * 1.5
                        fighter.vy = -fighter.vy * 1.5
                        fighter.parry_cooldown = 30 # Longer penalty

                        if guard_break_dmg > 0:
                            game.damage_numbers.spawn(ix_point[0], ix_point[1] - 30, guard_break_dmg, fighter.color, True)

                if both_parried:
                    # Standard hit-stop and screen shake
                    game.hit_stop = 8
                    game.screen_shake = 12
                    
                    game.particles.emit(ix_point[0], ix_point[1], (255, 255, 100), count=20, size=4)
                else:
                    game.hit_stop = 12
                    game.screen_shake = 20
                
                # Play sword clash sound
                if hasattr(game, 'sound_manager'):
                    game.sound_manager.play_clash()
        
        # === BODY HIT CHECK: Sword vs body (always active - Beyblade mode) ===
        for attacker, defender in [(blue, red), (red, blue)]:
            hit_pos, impact_ratio = self._check_sword_hit(attacker, defender)
            if hit_pos:
                
                # Roll for critical hit (20% chance)
                is_crit = random.random() < CRIT_CHANCE
                crit_mult = CRIT_MULTIPLIER if is_crit else 1.0
                
                # Apply damage multiplier + crit
                damage_mult = attacker.get_attack_damage_multiplier()
                total_damage_mult = damage_mult * crit_mult
                
                angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)
                knockback = BASE_KNOCKBACK * crit_mult * (1.0 + (total_damage_mult - 1.0) * 0.5) * 1.5
                
                if hasattr(game, 'chaos'):
                    knockback *= game.chaos.get_knockback_mult()
                    if game.chaos.is_ultra_knockback():
                        game.screen_shake = max(game.screen_shake, SCREEN_SHAKE_INTENSITY * 3)

                # Dynamic Sweet Spot Damage System
                if impact_ratio < 0.7:
                    # The Grinding Hit
                    base_damage = 10
                    shake_intensity = 4
                    spark_count = 10
                    spark_color = (255, 255, 0) # Yellow
                    spark_size = 4
                    is_sweet_spot = False
                else:
                    # The Sweet Spot / Tip Hit
                    base_damage = 15
                    if is_crit:
                        base_damage = 4 # Keep actual health damage low for decomposition hit
                    shake_intensity = 15
                    spark_count = 30
                    spark_color = (255, 100, 0) if random.random() < 0.5 else (255, 0, 0) # ORANGE or RED
                    spark_size = 6
                    is_sweet_spot = True
                
                damage = base_damage * total_damage_mult
                
                # Fixed hit-stop frames (no combo system)
                hit_stop_frames = HIT_STOP_FRAMES
                
                if defender.take_damage(damage, angle, knockback, game.particles):
                    # Trigger custom hit effects instead of generic _trigger_hit
                    game.particles.emit(hit_pos[0], hit_pos[1], spark_color, count=spark_count, size=spark_size)
                    game.hit_stop = hit_stop_frames if hit_stop_frames else HIT_STOP_FRAMES
                    game.screen_shake = shake_intensity
                    
                    if damage > 0:
                        game.damage_numbers.spawn(hit_pos[0], hit_pos[1] - 20, damage, attacker.color, is_crit or is_sweet_spot)
                    
                    # Play appropriate hit sound based on sweet spot
                    if hasattr(game, 'sound_manager'):
                        if is_sweet_spot:
                            game.sound_manager.play_crit()
                        else:
                            game.sound_manager.play_hit()
                    
                    game.hit_slowmo_frames = HIT_SLOWMO_FRAMES
                    game._reset_inactivity()
                    
                    # Critical Hit: Trigger anime impact sequence (Decomposition for tip hits)
                    if is_crit and is_sweet_spot:
                        game.decomp_slowmo_frames = 30  # Phase 2: 0.5 seconds at 10% timescale
                        game.decomp_slowmo_accumulator = 0.0
                        game.hit_slowmo_frames = 0
                        game.hit_stop = 4  # Phase 1: 4 frames freeze
                        game.screen_shake = max(game.screen_shake, 35)  # Heavy screen shake
                        # Decoupled high-velocity, high-contrast sparks
                        game.particles.emit_explosion(hit_pos[0], hit_pos[1], (0, 255, 255), count=25) # Cyan
                        game.particles.emit_explosion(hit_pos[0], hit_pos[1], (255, 0, 255), count=25) # Magenta
                        game.particles.emit_explosion(hit_pos[0], hit_pos[1], (255, 255, 255), count=15) # White
                    elif is_crit:
                        game.crit_impact_frames = CRIT_IMPACT_FRAMES
                        game.crit_impact_accumulator = 0.0
                        game.crit_flash_phase = 1  # Start flash sequence
                        game.screen_shake = max(game.screen_shake, SCREEN_SHAKE_INTENSITY * 2)
