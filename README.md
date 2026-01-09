# ⚔️ Red vs Blue Battle

A physics-based sword battle animation optimized for **TikTok** and **YouTube Shorts**.

---

## Overview

Two circular fighters bounce around a square arena, swinging swords and using skill-based power-ups. Features a **Tkinter control panel** for configuration and a **Pygame engine** for real-time combat.

---

## Architecture

This project uses a **two-phase architecture**:

| Phase | Framework | Purpose |
|-------|-----------|---------|
| **1. Control Panel** | Tkinter | Configure game settings before launch |
| **2. Game Engine** | Pygame | Real-time rendering, physics, combat |

This separation avoids event-loop conflicts between frameworks.

---

## How to Run

### Quick Start (Direct Game)
```bash
cd project-tiktok-brainrot
python main.py
```

### Full Launch (Control Panel → Game)
```bash
cd project-tiktok-brainrot
python launcher.py
```

### Controls
- **SPACE** - Pause/Resume
- **R** - Reset round
- **ESC** - Exit

---

## Features

### Combat
- **7 Skill Power-ups**: Dash Slash, Spin Parry, Ground Slam, Shield, Phantom Cross, Blade Cyclone, Final Flash Draw
- **DVD-style bouncing** - fighters constantly move
- **Physics-based knockback** - satisfying hit reactions

### Arena Escalation System
Prevents stalemates without random punishment:

| Timer | Event | Effect |
|-------|-------|--------|
| 5s inactivity | **Arena Pulse** | Visual wave, fighters nudged to center |
| 8s+ inactivity | **Shrinking Walls** | Arena slowly shrinks (pauses on hit) |

### Round Start
- Fighters spawn facing each other
- Locked during countdown: "3" → "2" → "1" → "FIGHT"
- Movement unlocks after "FIGHT"

---

## Project Structure

```
project-tiktok-brainrot/
├── launcher.py       # Entry point (opens control panel)
├── main.py           # Pygame game loop
├── ui.py             # Tkinter control panel
├── fighter.py        # Fighter class with skills
├── effects.py        # Particles, shockwaves, arena pulse
├── config.py         # Game constants & settings
├── utils.py          # Utility functions
├── sound_manager.py  # Audio system
├── skills/           # Modular skill system
│   ├── __init__.py   # Skill exports
│   ├── base.py       # BaseSkill class
│   ├── registry.py   # Skill registration
│   └── orb.py        # SkillOrb power-up
├── sounds/           # Audio files (placeholder .txt)
│   ├── dash_slash.txt
│   ├── spin_parry.txt
│   └── ...
└── README.md
```

---

## Adding New Skills

1. Create a new file in `skills/` (e.g., `skills/my_skill.py`)
2. Inherit from `BaseSkill`:

```python
from skills.base import BaseSkill
from skills.registry import register_skill

@register_skill(skill_id=7)
class MySkill(BaseSkill):
    name = "My Skill"
    duration = 30
    
    def activate(self, fighter, opponent, particles, shockwaves):
        # Setup skill
        pass
    
    def update(self, fighter, opponent, particles, shockwaves):
        # Update each frame
        return self.timer < self.duration
```

3. Import in `skills/__init__.py`

---

## Adding Sounds

1. Place `.wav` or `.ogg` files in `sounds/`
2. Name them to match skill IDs:
   - `dash_slash.wav`
   - `spin_parry.wav`
   - `arena_pulse.wav`
3. The `SoundManager` will auto-load and play them

---

## Performance Notes

- **Target**: 60 FPS on standard hardware
- **Resolution**: 600×600 (1:1 square)
- **Optimized for**: Short-form content (15-60 seconds)

---

## License

MIT License
