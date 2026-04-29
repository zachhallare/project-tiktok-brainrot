# Color Battle by AlgoRot

> A fast-paced, minimalist 2D fighting simulation inspired by DVD screensaver physics. Watch as two AI-controlled fighters bounce around an arena, trading blows with various spinning weapons in epic, bite-sized battles perfect for social media content.

---

## Project Overview

**Color Battle** is an automated AI-vs-AI combat simulation built for endless, satisfying content loops. The game features two circular fighters bouncing around an arena like a DVD screensaver while wielding one of five unique weapons in a continuous "Beyblade-style" spin. Out of the box, it supports a dynamic 12-color Neon Palette selector prior to initialization.

### Core Loop
1. **Countdown** → "3-2-1-FIGHT" initiates each round (accompanied by audio beeps)
2. **Battle Phase** → Fighters autonomously bounce, collide, and attack via a permanent spin
3. **Escalation** → Arena Pulse pushes fighters together after 2.5 seconds of inactivity
4. **Resolution** → Slow-motion death sequence with particle explosion
5. **Finish** → The game terminates to finalize OBS recording or advance batch

The aesthetic features a sharp **cel-shaded** style—solid neon colors with high-fidelity weapon sprites for each weapon type. The arena uses a textured **Dark Grey background** (#1a1a1a) with a faint cyberpunk grid overlay to maximize the visual pop of neon effects, body trails, and particle explosions. Combat *feels* incredibly punchy thanks to dramatic ricochet physics, hit-stop, screen shake, and slow-motion effects.

---

## Objective & Win/Lose Conditions

### Victory Condition
A fighter wins when their opponent's **health drops to zero** on the Tekken-style top HUD. When this happens:
- Slow-motion kicks in at 20% speed
- The loser explodes in a burst of colored particles
- The winner performs a celebratory bounce animation
- A death sound sequence plays (final hit → sword-to-ground)
- The round ends after a brief delay

### Timeout Condition
If neither fighter is eliminated within **18 seconds** (`ROUND_MAX_TIME`), the round resolves based on proximity to the arena center. This prevents stalemates and rewards aggressive, center-controlling play.

### Failure State
There is no player failure state—this is an automated simulation. Both fighters are AI-controlled, so rounds always resolve naturally.

---

## Weapons

The game features **5 distinct weapon types**, each with unique sprites, hitbox profiles, stat distributions, and special mechanics:

| Weapon   | Reach | Damage | Spin Speed | Knockback | HP  | Move Speed | Special |
|----------|-------|--------|------------|-----------|-----|------------|---------|
| **Sword**   | 40px  | 1.05×  | 0.75×      | 1.0×      | 250 | 1.0×       | Balanced all-rounder |
| **Dagger**  | 20px  | 1.45×  | 0.95×      | 0.5×      | 260 | 1.25×      | 2.5× parry drain, +2 momentum per hit, longer trail |
| **Spear**   | 148px | 1.20×  | 0.58×      | 0.8×      | 215 | 1.0×       | Massive reach, high handle ratio (0.78) with tip sweet-spot |
| **Hammer**  | 29px  | 0.72×  | 0.53×      | 0.9×      | 275 | 0.88×      | Reverses defender spin, all hits are sweet-spot, max hitstop on crits |
| **Axe**     | 33px  | 1.10×  | 0.41×      | 1.5×      | 245 | 0.85×      | Wide hitbox profile, highest knockback |

Each weapon has a unique **hitbox profile** — a series of `(t, half_width)` sampling points along the blade that define the cross-sectional collision shape. This means the Spear's narrow tip behaves differently from the Axe's wide head.

---

## Combat Mechanics

### Weapon System: Beyblade Auto-Battler
The combat is a **"Beyblade" style auto-battler**. There are no directional slash attacks; instead, fighters spin continuously with persistent, always-active weapon hitboxes.

- **Constant Rotation:** Fighters maintain a continuous 360-degree spin at weapon-specific speeds.
- **Energy-Based Parry System:** Persistent weapon-to-weapon collision triggers a parry. Each parry consumes **Parry Energy** (scaled by the attacker's `parry_drain_mult`).
- **Guard Break Mechanic:** If a fighter runs out of energy, they suffer a **Guard Break**—taking 15–25 penalty damage, receiving massive knockback, and facing a temporary stun.
- **Always-Active Damage:** Damage is driven exclusively by physical weapon-to-body intersection. 
- **Momentum System:** Landing consecutive hits builds up momentum stacks (up to 3), increasing the damage multiplier by +6% per stack. Taking damage resets a fighter's momentum back to zero.

### Rotation-Based Damage Scaling
Damage scales based on how much the weapon has rotated since the last hit:
- **< π (accidental/graze):** 0.6× damage penalty
- **π–2π (standard hit):** 1.0× normal damage
- **≥ 2π (full rotation):** 1.3× damage bonus

### Damage & Collision
- **Profile-Based Hit Detection:** Each weapon has a unique hitbox profile with multiple sampling points along the blade. Hit detection checks if any profile point intersects the opponent's body, using the **handle-most** hit for damage calculations and the **tip-most** hit for particle placement.
- **Sweet-Spot System:** Hits beyond the `sweet_spot_threshold` deal 18 base damage with heavy feedback; handle/shaft hits deal 13 base damage with lighter effects. The Hammer treats every hit as a sweet-spot.
- **Invincibility Frames:** 20 frames of immunity after taking damage prevent unintended instant-death multi-hits.
- **Ricochet Physics:** Extreme, dramatic knockback is applied upon impact, bouncing fighters off each other like spinning tops.

### Hit Feedback
Each successful hit triggers:
- **Hit-Stop:** Momentarily freezes the action to add weight to the impact (8 frames standard, 12/30 for Hammer normal/crit).
- **Hit Slow-Mo:** 5 frames at 60% speed.
- **Decomposition Effect:** Critical sweet-spot hits trigger a special sequence: a 4-frame hit-stop freeze, followed by a dramatic 30-frame slow-mo phase (10% timescale) with decoupled high-velocity cyan/magenta particle bursts.
- **Critical Impact Flash:** Non-sweet-spot crits trigger a black → white → normal screen flash sequence during an anime-style impact freeze (12 frames at ~2% timescale).
- **Screen Shake:** Massive screen shake, decaying at 85% per frame.
- **Particle Burst:** Sparks erupting from the impact point, varying dynamically based on sweet-spot or grinding hits.
- **Floating Damage Numbers:** Gold, larger numbers for crits; color-coded for standard hits.
- **Sound Effect:** Centralized audio manager playing clash, hit, or critical hit sounds.

### Weapon Special Effects
- **Hammer — Spin Reversal:** Every body hit reverses the defender's spin direction, disorienting them.
- **Dagger — Parry Shredder:** 2.5× parry energy drain on parries makes Guard Breaks far more likely against a Dagger user.
- **Dagger — Momentum Stacker:** Gains 2 momentum stacks per hit instead of the default 1.

---

## Movement & Physics

### DVD Screensaver Physics
Fighters use a unique **constant-velocity bounce** system inspired by DVD screensaver logos:

- **Drag:** `1.0` (no drag—velocity is maintained)
- **Bounce Energy:** `1.0` (perfect elastic bounces)
- **Minimum Velocity:** 6 pixels/frame (scaled by weapon `move_speed_mult`)
- **Maximum Velocity:** 15 pixels/frame (scaled by weapon `move_speed_mult`)
- **Initial Velocity:** Random between -8 and +8 on both axes

If a fighter ever stops moving (velocity = 0), they're given a random directional nudge to keep the action flowing.

### Ninja Wall Boosts
When bouncing off walls, fighters receive a **4 pixel/frame velocity boost toward the arena center**. This prevents corner camping and naturally guides fighters back into combat.

### Body-to-Body Collision
If two fighters physically overlap, they are separated by pushing each body outward by half the overlap distance. This prevents phantom sword hits caused by body intersection.

### Weapon Orientation & Rotation
Weapons are rendered as high-quality sprite images, scaled for optimal visual clarity. They rotate 360 degrees constantly, with the sprite rigidly attached at the body edge. Each weapon's rotation center is dynamically aligned to the physics hitbox.

---

## Arena Escalation System

To prevent stalemates and keep the action flowing, the arena features an inactivity pressure mechanic:

### Arena Pulse
If no combat occurs for **2.5 seconds**, an **Arena Pulse** triggers.
- A radial shockwave fires, abruptly pushing both fighters toward the center of the arena to force combat.
- This pulse repeats every 2.5 seconds of inactivity, ensuring the action is constant.
- Accompanied by a dedicated audio cue.

---

## Visual Systems

### Dynamic Color Casting
Fighter colors are selected from a 12-color high-contrast `NEON_PALETTE`. Colors cascade across all visual elements:
- **Arena Borders** swap between Fighter 1 and Fighter 2 colors every 3 seconds.
- **Tekken-Style HUD** displays health bars dynamically themed to each fighter's color.
    - **Minimum Width:** Health bars maintain a visible fill as long as the fighter is alive.
    - **Danger Zone:** Health bars shake at ≤10% HP.
    - **Low HP Blink:** Health bars blink rapidly when below 15% HP (alternating between normal and 40% darker shade).
- **Winner Announcer** renders a color-coded circle indicator with "WINS" text in a pulsing box.
- **Arena Watermark:** A semi-transparent AlgoRot logo is centered in the arena as a background watermark.

### Trail System
Each fighter leaves a fading motion trail. Trail length and fade behavior are per-weapon:
- Default weapons: 8-position trail with standard size/alpha
- Dagger: 12-position trail with more aggressive fade for a motion-blur effect

### Particle & Effect Systems
- **ParticleSystem:** Sparks, explosions, and impact bursts
- **ShockwaveSystem:** Radial shockwaves on death
- **ArenaPulseSystem:** Visualizes the inactivity pulse
- **DamageNumberSystem:** Floating damage numbers with crit-scaling

---

## Audio System

All sound effects are managed through a centralized `SoundManager` that preloads audio files at initialization to prevent in-game stutter.

### Sound Categories
| Category      | Sounds                                     |
|---------------|---------------------------------------------|
| **Combat**    | `hit_1.mp3`, `hit_2.mp3` (alternating), `critical_hit.mp3`, `sword_clash.mp3` |
| **Death**     | `death_final_hit.mp3`, `sword_to_the_ground.mp3` |
| **Countdown** | `countdown_beep.mp3`, `sword-fight.mp3` |
| **Feedback**  | `arena_pulse.mp3` |

### Audio Controls
- **Mute flag:** Pass `--mute-sounds` on the command line to silence all effects
- **Headless mode** automatically mutes sounds
- **Toggle mute** programmatically via `SoundManager.toggle_mute()`
- **Master volume** control via `SoundManager.set_master_volume(level)`

---

## Controls

| Key          | Action                           |
|--------------|----------------------------------|
| **SPACE**    | Start game / Pause               |
| **R**        | Reset current round              |
| **M**        | Manual OBS delay (60 frames)     |
| **ESC**      | Exit game                        |
| **Mouse Click** | Start game (title screen only) |

---

## Technical Stack

| Component    | Technology                        |
|--------------|-----------------------------------|
| **Language** | Python 3.x                        |
| **Framework**| Pygame (game loop, rendering, audio) |
| **Audio**    | Preloaded MP3 assets via Pygame mixer |
| **Physics**  | Custom bounce-based movement      |
| **Recording**| OBS Studio via WebSockets (`obsws-python`) |
| **Config**   | `.env` file via `python-dotenv`   |

### Project Structure
```text
project_root/
├── assets/
│   ├── audios/
│   │   ├── combat/          # Hit, clash, death sounds
│   │   ├── countdown/       # Beep and fight sounds
│   │   └── feedback/        # Arena pulse sounds
│   └── images/
│       ├── logos/            # Arena watermark
│       └── weapons/         # Weapon sprite PNGs (sword, dagger, spear, axe, hammer)
├── docs/
│   └── todo.md              # Development notes and future plans
├── src/
│   ├── config.py            # Constants, physics values, weapon configs, and color palette
│   ├── effects.py           # Particle, shockwave, arena pulse, and damage number systems
│   ├── main.py              # Main game loop, window management, and CLI entry point
│   ├── titles.py            # Dynamic title pool generation for viral video naming
│   ├── utils.py             # Helpful utilities
│   ├── entities/
│   │   └── fighter.py       # Core fighter state, movement, and weapon integration
│   ├── managers/
│   │   ├── combat_manager.py # Profile-based hit detection, parry, guard break, damage calc
│   │   ├── obs_manager.py    # OBS WebSocket integration for automated recording
│   │   └── sound_manager.py  # Centralized sound preloading and playback
│   └── renderers/
│       ├── fighter_renderer.py # Sprite-based weapon rendering and body/trail drawing
│       └── ui_renderer.py      # Tekken-style HUD with health bars and danger effects
├── record.py                # Batch recording + manual/auto test runner
├── used_titles.json         # Persistent title tracker (prevents repeated video titles)
├── requirements.txt         # Python dependencies
└── .env                     # OBS WebSocket credentials (OBS_PORT, OBS_PASSWORD)
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup your .env file in the root directory (for Auto-Recording)
# OBS_PASSWORD=your_websocket_password
# OBS_PORT=4455

# 3. Run the game for a single round (Interactive Color Selection)
python src/main.py

# CLI Bypass: Pass colors and weapons directly
python src/main.py --auto-start --f1-weapon sword --f2-weapon axe

# Specify weapons for a test round (no OBS)
python src/main.py --test-mode --f1-weapon dagger --f2-weapon hammer

# Run headless (no window, no rendering, no FPS cap — for fast automated testing)
python src/main.py --test-mode --headless --f1-weapon spear --f2-weapon sword

# Run the batch recorder / test suite
python record.py
```

### CLI Flags

| Flag              | Description                                        |
|-------------------|----------------------------------------------------|
| `--auto-start`    | Skip title screen, start recording immediately     |
| `--test-mode`     | Skip title screen, no OBS recording                |
| `--headless`      | No window, no rendering, no FPS cap (fastest)      |
| `--f1-weapon X`   | Set Fighter 1 weapon (`sword`, `dagger`, `spear`, `axe`, `hammer`) |
| `--f2-weapon X`   | Set Fighter 2 weapon                               |
| `--mute-sounds`   | Mute all sound effects                             |

---

## Record.py — Batch Recorder & Test Suite

`record.py` provides a menu-driven interface for two modes:

### 1. Batch Recording (OBS)
Automated batch recording for content creation:
- Verifies OBS WebSocket connection before proceeding
- Choose weapon pool: **Sword-only** or **12 specific combos**
- Combo tracker (`used_combos_*.json`) ensures all matchups are cycled before repeating
- Fighter colors randomized per match
- 3-second delay between rounds for OBS to save

### 2. Test Mode
Two sub-modes for debugging and balance testing:

**Manual Test:** Pick weapons for each fighter, specify round count, watch the battles.

**Auto Test:** Runs all 10 cross-weapon matchups headless with configurable rounds per matchup. Outputs structured results including winner, remaining HP%, and elapsed time per round. Final summary shows win/loss tallies for each matchup.

### Auto Test Matchups
```
dagger vs hammer    |  dagger vs axe    |  dagger vs sword
dagger vs spear     |  hammer vs axe    |  hammer vs sword
hammer vs spear     |  sword vs spear   |  sword vs axe
spear vs axe
```

---

## OBS Auto-Recording Integration (YT Shorts Automation)

This project is built to automate the creation of YouTube Shorts content. It includes a built-in integration with **OBS Studio** via WebSockets perfectly configured to capture clips without manual editing.

### How it works:
1. The game sends a command directly to OBS in the background to **Start Recording**.
2. After the winner is announced, the application automatically closes and commands OBS to **Stop Recording** and save your clip.
3. The saved clip is automatically renamed using a dynamically generated viral title from the `titles.py` pool system.

### OBS Setup Instructions:
1. Add a **Window Capture** source and select the Python game window.
2. Setup the OBS WebSocket for automated recording:
   - Click on **Tools** in the very top menu bar.
   - Select **WebSocket Server Settings** from the dropdown menu.
   - In the window that pops up, make sure **Enable WebSocket server** is checked. You will find your details right there:
     - **OBS_PORT**: Look for the Server Port field (it almost always defaults to `4455`).
     - **OBS_PASSWORD**: Make sure Enable authentication is checked. You can either type a new password directly into the Server Password box, or click the Show Connect Info button to reveal and copy the currently active password.
3. Add your `OBS_PASSWORD` and `OBS_PORT` to your `.env` file in the root directory.
4. Simply leave OBS open in the background! Run `python src/main.py` and hit space for a single round, or run `python record.py` for fully automated batch recording.

---

## Key Constants Reference

| Constant                  | Value   | Description                              |
|---------------------------|---------|------------------------------------------|
| `SCREEN_WIDTH`            | 600     | Game surface width in pixels             |
| `SCREEN_HEIGHT`           | 600     | Game surface height in pixels            |
| `CANVAS_WIDTH`            | 600     | High-res canvas width (for OBS capture)  |
| `CANVAS_HEIGHT`           | 1067    | High-res canvas height (9:16 aspect)     |
| `DISPLAY_WIDTH`           | 540     | Window display width                     |
| `DISPLAY_HEIGHT`          | 960     | Window display height                    |
| `FPS`                     | 60      | Target frames per second                 |
| `FIGHTER_RADIUS`          | 30      | Fighter body size                        |
| `BASE_HEALTH`             | 250     | Default hit points (overridden per weapon)|
| `DAMAGE_PER_HIT`          | 15      | Base damage constant                     |
| `ROUND_MAX_TIME`          | 18      | Force resolution after 18 seconds        |
| `BASE_KNOCKBACK`          | 10      | Base knockback force                     |
| `INACTIVITY_PULSE_TIME`   | 2.5     | Seconds before arena pulse triggers      |
| `MOMENTUM_MAX_STACKS`     | 3       | Maximum momentum stacks                  |
| `MOMENTUM_DAMAGE_BONUS`   | 0.06    | +6% damage per momentum stack            |
| `CRIT_CHANCE`             | 0.20    | 20% chance of critical hit               |
| `CRIT_MULTIPLIER`         | 1.6     | Critical hit damage multiplier           |

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
