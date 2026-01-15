# 🔴 Red vs Blue Battle 🔵

> A fast-paced, minimalist 2D sword fighting simulation inspired by DVD screensaver physics. Watch as two AI-controlled fighters bounce around an arena, trading blows with swinging swords in epic, bite-sized battles perfect for social media content.

---

## 📖 Project Overview

**Red vs Blue Battle** is an automated AI-vs-AI combat simulation built for endless, satisfying content loops. The game features two circular fighters—one Red, one Blue—bouncing around a shrinking arena like a DVD screensaver while wielding swords that swing in fluid combo attacks.

### Core Loop
1. **Countdown** → "3-2-1-FIGHT" initiates each round
2. **Battle Phase** → Fighters autonomously bounce, collide, and attack
3. **Escalation** → The arena shrinks over time, forcing combat
4. **Resolution** → Slow-motion death sequence with particle explosion
5. **Repeat** → Auto-reset for the next round

The aesthetic is intentionally minimalist—solid-colored circles with inner highlights, simple line swords, and health bars—but the combat *feels* punchy thanks to hit-stop, screen shake, and slow-motion effects.

---

## 🏆 Objective & Win/Lose Conditions

### Victory Condition
A fighter wins when their opponent's **health drops to zero**. When this happens:
- Slow-motion kicks in at 20% speed
- The loser explodes in a burst of colored particles
- The winner performs a celebratory bounce animation
- The round resets after a brief delay

### Timeout Condition
If neither fighter is eliminated within **45 seconds** (`ROUND_MAX_TIME`), the fighter **closest to the arena center** wins the round. This prevents stalemates and rewards aggressive, center-controlling play.

### Failure State
There is no player failure state—this is an automated simulation. Both fighters are AI-controlled, so rounds always resolve naturally.

---

## ⚔️ Combat Mechanics

### Attack Triggering
Attacks are triggered **automatically** when fighters are within **120 pixels** of each other (`attack_trigger_range`). There are no player inputs—the AI decides when to swing based on proximity.

### Weapon System: Combo Sword Attacks
The combat uses a **3-hit combo system** with escalating damage:

| Combo Stage | Attack Type | Arc Width | Damage Multiplier |
|-------------|-------------|-----------|-------------------|
| **1st Hit** | Left Slash  | ~120°     | 1.0x (10 damage)  |
| **2nd Hit** | Right Slash | ~90°      | 1.2x (12 damage)  |
| **3rd Hit** | Pierce      | ~30°      | 1.5x (15 damage)  |

#### Attack Mechanics
- **Attack Duration:** 12 frames per swing
- **Attack Cooldown:** 8 frames between attacks
- **Combo Timeout:** 45 frames to land the next hit or the combo resets
- **Pierce Extended Reach:** The 3rd hit extends sword length by 30%

### Damage & Collision
- **Hitbox:** Sword collision is checked at 50%, 75%, and 100% of sword length
- **Hit Detection:** If any hitbox point is within the defender's body radius + 8 pixels, damage is dealt
- **Invincibility Frames:** 10 frames of immunity after taking damage
- **Knockback:** Varies slightly based on combo stage (1.0x to 1.25x)

### Hit Feedback
Each successful hit triggers:
- **Hit-Stop:** 3 frames (5 frames for pierce attacks)
- **Hit Slow-Mo:** 5 frames at 60% speed
- **Screen Shake:** Intensity 8, decaying at 85% per frame
- **Particle Burst:** 10 white particles
- **Sound Effect:** Procedurally generated hit sound

---

## 🎮 Movement & Physics

### DVD Screensaver Physics
Fighters use a unique **constant-velocity bounce** system inspired by DVD screensaver logos:

- **Drag:** `1.0` (no drag—velocity is maintained)
- **Bounce Energy:** `1.0` (perfect elastic bounces)
- **Minimum Velocity:** 10 pixels/frame
- **Maximum Velocity:** 20 pixels/frame
- **Initial Velocity:** Random between -8 and +8 on both axes

If a fighter ever stops moving (velocity = 0), they're given a random directional nudge to keep the action flowing.

### Ninja Wall Boosts
When bouncing off walls, fighters receive a **4 pixel/frame velocity boost toward the arena center**. This prevents corner camping and naturally guides fighters back into combat.

### Sword Orientation
The sword **always points toward the opponent**, with an angular offset based on the current combo stage:
- **Left Slash Ready:** Sword angled 0.6 radians to the left
- **Right Slash Ready:** Sword angled 0.6 radians to the right  
- **Pierce Ready:** Sword straight ahead

---

## 🎯 Arena Escalation System

To prevent stalemates and keep battles short, the arena features multiple escalation mechanics:

### Time-Based Shrinking
- Every **10 seconds**, the arena shrinks by 12 pixels per side
- Minimum arena size: 300x300 pixels

### Inactivity Pressure
If no combat occurs for **5 seconds**:
1. **Arena Pulse** — Purple shockwave pushes fighters toward center (4 velocity boost)
2. **Warning Phase** — Arena border turns yellow (3 additional seconds)
3. **Rapid Shrink** — Arena border turns orange and shrinks at 0.3 px/frame continuously

Any successful hit pauses the shrink for 2 seconds, rewarding aggression.

---

## 🕹️ Controls

| Key          | Action                           |
|--------------|----------------------------------|
| **SPACE**    | Start game / Pause               |
| **R**        | Reset current round              |
| **ESC**      | Exit game                        |
| **Mouse Click** | Start game (title screen only) |

---

## 🛠️ Technical Stack

| Component    | Technology                        |
|--------------|-----------------------------------|
| **Language** | Python 3.x                        |
| **Framework**| Pygame (game loop, rendering, audio) |
| **Audio**    | Procedurally generated at runtime |
| **Physics**  | Custom bounce-based movement      |

### Project Structure
```
project-tiktok-brainrot/
├── main.py           # Game loop, combat handling, rendering
├── fighter.py        # Fighter class with movement and attacks
├── config.py         # All tuning constants and physics values
├── effects.py        # Particle, shockwave, and slash effects
├── sound_manager.py  # Sound generation utilities
├── utils.py          # Helper functions
└── sounds/           # Audio assets directory
```

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install pygame

# Run the game
python project-tiktok-brainrot/main.py
```

---

## 📊 Key Constants Reference

| Constant              | Value | Description                          |
|-----------------------|-------|--------------------------------------|
| `SCREEN_WIDTH`        | 600   | Window width in pixels               |
| `SCREEN_HEIGHT`       | 600   | Window height in pixels              |
| `FPS`                 | 60    | Target frames per second             |
| `BASE_HEALTH`         | 240   | Hit points per fighter               |
| `DAMAGE_PER_HIT`      | 10    | Base damage (before multipliers)     |
| `FIGHTER_RADIUS`      | 30    | Fighter body size                    |
| `SWORD_LENGTH`        | 55    | Sword reach in pixels                |
| `ROUND_MAX_TIME`      | 45    | Force resolution after 45 seconds    |

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
