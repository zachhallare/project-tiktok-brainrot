# ⚔️ Red vs Blue Battle

A physics-based sword battle animation optimized for **TikTok** and **YouTube Shorts**.

---

## Combat Philosophy

- **Skill Autotargeting**: Skills always face and launch toward opponent (but can still miss)
- **No Autohit**: Skills can be blocked, parried, or clashed (except Final Flash Draw)
- **Interaction Over Randomness**: Every action creates meaningful combat engagement
- **DVD Movement**: Constant-speed wall-bouncing is NEVER modified by attacks

---

## How to Run

```bash
cd project-tiktok-brainrot
python main.py
```

Press **SPACE** or **CLICK** to start from the title screen.

### Controls
- **SPACE** - Pause/Resume
- **R** - Reset round
- **ESC** - Exit

---

## Combat System

### 3-Hit Combo System

Basic attacks chain into a deterministic combo:

| Hit | Name | Arc | Damage | Recovery |
|-----|------|-----|--------|----------|
| 1 | Left Slash | Wide (120°) | 1.0x | Short |
| 2 | Right Slash | Medium (90°) | 1.2x | Short |
| 3 | Pierce | Narrow (30°) | 1.5x | Long |

**Combo resets on:** miss, taking damage, skill activation, or timeout.

### Defensive Triangle

| Defense | Risk | Effect |
|---------|------|--------|
| **Shield** | Safe | Blocks one hit, resets attacker combo |
| **Spin Parry** | High | Cancels attacks, massive knockback on Pierce |
| **Sword Clash** | Medium | Basic attack deflects/weakens skills |

### Sword Clash Outcomes

Basic attacks can clash with enemy skills during active frames:

| Skill | Clash Result |
|-------|--------------|
| Dash Slash | Deflected off-angle |
| Spin Parry | Dissipates (when active) |
| Ground Slam | Shockwave reduced |
| Phantom Cross | Delayed damage canceled |
| Blade Cyclone | Pushback only |
| Final Flash Draw | ❌ Cannot be clashed |

---

## Arena Escalation

Prevents stalemates without random punishment:

| Timer | Event | Effect |
|-------|-------|--------|
| 5s inactivity | **Arena Pulse** | Visual wave, fighters nudged to center |
| 8s+ inactivity | **Shrinking Walls** | Arena slowly shrinks (pauses on hit) |

---

## Skills (7 Total)

- **Dash Slash** - High-speed burst toward opponent
- **Spin Parry** - Reactive parry with knockback
- **Ground Slam** - Jump + plunge with shockwave
- **Shield** - Instant one-hit block
- **Phantom Cross** - Teleport behind + delayed damage
- **Blade Cyclone** - Spinning multi-hit vortex
- **Final Flash Draw** - Rare autohit iaido (cannot be clashed)

---

## Project Structure

```
project-tiktok-brainrot/
├── main.py           # Game loop, combat, title screen
├── fighter.py        # Fighter class, combo, skills
├── effects.py        # Particles, shockwaves, arena pulse
├── config.py         # Game constants
├── skills.py         # Skill types and orbs
├── sound_manager.py  # Audio system
├── skills/           # Modular skill system
│   ├── base.py       # BaseSkill class
│   ├── registry.py   # Skill registration
│   └── orb.py        # SkillOrb power-up
├── sounds/           # Audio placeholders
└── README.md
```

---

## Victory

Victory is indicated solely by slow-motion death sequence. No text overlay.

---

## License

MIT License
