# ⚔️ Red vs Blue Battle

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

**A physics-based sword battle animation optimized for TikTok and YouTube Shorts.**

Red vs Blue Battle is a DVD-style bouncing combat game featuring rotating swords, skill-based power-ups, and stunning visual effects. Two AI-controlled fighters bounce around a square arena, continuously spinning their swords while collecting power-ups to unleash devastating skill moves. Perfect for creating engaging short-form video content.

---

## ✨ Key Features

- **DVD Logo Physics** — Fighters bounce around the arena at constant velocity with satisfying wall bounces
- **Continuous Sword Rotation** — Swords always spin, creating dynamic sword-on-sword parries and body hits
- **5 Unique Skills** — Collectible power-ups grant special abilities (Dash Slash, Spin Parry, Ground Slam, Shield, Blade Cyclone)
- **Juicy Combat Feel** — Hit-stop, slow-motion effects, screen shake, and particle explosions
- **Arena Escalation** — Prevents stalemates with arena pulses and shrinking boundaries
- **Optimized for Short-Form** — Rounds designed for 30-second TikTok-friendly loops
- **Modular Skill System** — Easy to add new skills via the registry pattern

---

## 🎮 Combat Philosophy

| Principle | Description |
|-----------|-------------|
| **Skill Autotargeting** | Skills always face and launch toward opponent (but can still miss) |
| **No Auto-hit** | Skills can be blocked, parried, or clashed |
| **Interaction Over Randomness** | Every action creates meaningful combat engagement |
| **DVD Movement** | Constant-speed wall-bouncing is never modified by attacks |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.8+** | Core programming language |
| **Pygame 2.0+** | Game engine, rendering, and audio |

---

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

---

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/zachhallare/project-tiktok-brainrot.git
   cd project-tiktok-brainrot
   ```

2. **Install dependencies**
   ```bash
   pip install pygame
   ```

3. **(Optional) Add sound files**
   
   Replace `.txt` placeholder files in `project-tiktok-brainrot/sounds/` with actual `.wav` or `.ogg` audio files:
   - `dash_slash.wav`
   - `spin_parry.wav`
   - `ground_slam.wav`
   - `shield.wav`
   - `blade_cyclone.wav`
   - `hit_impact.wav`
   - `explosion.wav`
   - `arena_pulse.wav`
   - `arena_shrink.wav`

---

## ▶️ Usage

**Run the game:**
```bash
cd project-tiktok-brainrot
python main.py
```

**Controls:**
| Key | Action |
|-----|--------|
| `SPACE` / `CLICK` | Start game from title screen |
| `SPACE` | Pause / Resume |
| `R` | Reset round |
| `ESC` | Exit game |

---

## ⚔️ Combat System

### Continuous Rotation Combat

Swords constantly rotate around each fighter. When the sword tip connects with an opponent's body, it deals damage. Two rotating swords meeting causes a **parry** — a satisfying clash with slow-motion and knockback.

### Defensive Triangle

| Defense | Risk | Effect |
|---------|------|--------|
| **Shield** | Safe | Blocks one hit, resets attacker momentum |
| **Spin Parry** | High | Cancels attacks, massive knockback on success |
| **Sword Clash** | Medium | Basic rotation deflects/weakens incoming skills |

### Sword Clash Outcomes

| Skill | Clash Result |
|-------|--------------|
| Dash Slash | Deflected off-angle |
| Spin Parry | Dissipates (when active) |
| Ground Slam | Shockwave reduced |
| Blade Cyclone | Pushback only |

---

## 🌟 Skills (5 Total)

| Skill | Color | Description |
|-------|-------|-------------|
| **Dash Slash** | Cyan | High-speed burst toward opponent with trailing particles |
| **Spin Parry** | Orange | Reactive parry stance with knockback on successful counter |
| **Ground Slam** | Purple | Jump into the air and plunge with a shockwave impact |
| **Shield** | Green | Instant one-hit block barrier |
| **Blade Cyclone** | Yellow | Spinning vortex multi-hit attack |

---

## ⏱️ Arena Escalation

Prevents stalemates without random punishment:

| Timer | Event | Effect |
|-------|-------|--------|
| 5s inactivity | **Arena Pulse** | Visual wave, fighters nudged to center |
| 8s+ inactivity | **Shrinking Walls** | Arena slowly shrinks (pauses on hit) |

---

## 📁 Project Structure

```
project-tiktok-brainrot/
├── project-tiktok-brainrot/
│   ├── main.py            # Game loop, combat logic, title screen
│   ├── fighter.py         # Fighter class, movement, skills, drawing
│   ├── effects.py         # Particles, shockwaves, slash effects
│   ├── config.py          # Game constants and settings
│   ├── skills.py          # Skill types and SkillOrb (legacy)
│   ├── sound_manager.py   # Audio system with fallback support
│   ├── utils.py           # Utility functions (lerp, clamp, etc.)
│   ├── skills/            # Modular skill system
│   │   ├── __init__.py    # Skill exports and SkillType enum
│   │   ├── base.py        # BaseSkill abstract class
│   │   ├── registry.py    # Skill registration system
│   │   └── orb.py         # SkillOrb power-up collectible
│   └── sounds/            # Audio placeholders (.txt → replace with .wav/.ogg)
├── LICENSE                # MIT License
└── README.md              # Documentation
```

---

## ⚙️ Configuration

Key settings in `config.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `SCREEN_WIDTH` | 600 | Window width (1:1 aspect ratio) |
| `SCREEN_HEIGHT` | 600 | Window height |
| `FPS` | 60 | Target frame rate |
| `BASE_HEALTH` | 240 | Fighter health points |
| `MAX_VELOCITY` | 20 | Maximum movement speed |
| `WEAPON_ROTATION_SPEED` | 0.18 | Radians per frame (~10.3°/frame) |
| `SLOW_MOTION_SPEED` | 0.20 | Death sequence slow-mo (20% speed) |
| `PARRY_SLOWMO_TIMESCALE` | 0.30 | Parry slow-mo (30% speed) |

---

## 🏆 Victory

Victory is indicated by a slow-motion death sequence. The winning fighter continues bouncing as the loser fades out. No text overlay — pure visual storytelling.

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by classic DVD screensaver physics
- Built with [Pygame](https://www.pygame.org/)
- Designed for TikTok content creation
