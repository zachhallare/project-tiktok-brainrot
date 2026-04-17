# Color Battle by AlgoRot

> A fast-paced, minimalist 2D sword fighting simulation inspired by DVD screensaver physics. Watch as two AI-controlled fighters bounce around an arena, trading blows with swinging swords in epic, bite-sized battles perfect for social media content.

---

## Project Overview

**Color Battle** is an automated AI-vs-AI combat simulation built for endless, satisfying content loops. The game features two circular fighters bouncing around an arena like a DVD screensaver while wielding swords in a continuous "Beyblade-style" spin. Out of the box, it supports a dynamic 6-color Neon Palette selector prior to initialization.

### Core Loop
1. **Countdown** → "3-2-1-FIGHT" initiates each round (accompanied by audio beeps)
2. **Battle Phase** → Fighters autonomously bounce, collide, and attack via a permanent spin
3. **Escalation** → Arena Pulse pushes fighters together after 2 seconds of inactivity
4. **Resolution** → Slow-motion death sequence with particle explosion
5. **Finish** → The game terminates to finalize OBS recording or advance batch

The aesthetic features a sharp **cel-shaded** style—solid neon colors with centralized dark outlines, chunky bordered swords, and elegant fading tip trails. The combat *feels* incredibly punchy thanks to dramatic ricochet physics, hit-stop, screen shake, and slow-motion effects.

---

## Objective & Win/Lose Conditions

### Victory Condition
A fighter wins when their opponent's **health drops to zero** on the Tekken-style top HUD. When this happens:
- Slow-motion kicks in at 20% speed
- The loser explodes in a burst of colored particles
- The winner performs a celebratory bounce animation
- The round resets after a brief delay

### Timeout Condition
If neither fighter is eliminated within **18 seconds** (`ROUND_MAX_TIME`), the fighter **closest to the arena center** wins the round. This prevents stalemates and rewards aggressive, center-controlling play.

### Failure State
There is no player failure state—this is an automated simulation. Both fighters are AI-controlled, so rounds always resolve naturally.

---

## Combat Mechanics

### Weapon System: Beyblade Auto-Battler
The combat is a **"Beyblade" style auto-battler**. There are no directional slash attacks; instead, fighters spin continuously with persistent, always-active sword hitboxes.

- **Constant Rotation:** Fighters maintain a continuous 360-degree spin.
- **Sword Parry System:** Persistent sword-to-sword collision creates a dynamic parry system with high-knockback ricochet physics.
- **Always-Active Damage:** Damage is driven exclusively by physical sword-to-body intersection. 

### Damage & Collision
- **Hit Detection:** If any point along the chunky sword intersects the opponent's body, damage is dealt.
- **Invincibility Frames:** Increased immunity frames after taking damage prevent unintended instant-death multi-hits from the continuous spinning blade.
- **Ricochet Physics:** Extreme, dramatic knockback is applied upon impact, bouncing fighters off each other like spinning tops.

### Hit Feedback
Each successful hit triggers:
- **Hit-Stop:** Momentarily freezes the action to add weight to the impact.
- **Hit Slow-Mo:** 5 frames at 60% speed.
- **Decomposition Effect:** Critical tip-hits trigger a special sequence: a heavy hit-stop freeze (4 frames), followed by a dramatic 0.5s slow-mo phase (10% timescale) with decoupled high-velocity cyan/magenta particle bursts.
- **Screen Shake:** Massive screen shake, decaying at 85% per frame.
- **Particle Burst:** Sparks erupting from the impact point, varying dynamically based on sweet-spot or grinding hits.
- **Sound Effect:** Centralized audio manager playing clash, hit, or critical hit sounds.

---

## Movement & Physics

### DVD Screensaver Physics
Fighters use a unique **constant-velocity bounce** system inspired by DVD screensaver logos:

- **Drag:** `1.0` (no drag—velocity is maintained)
- **Bounce Energy:** `1.0` (perfect elastic bounces)
- **Minimum Velocity:** 6 pixels/frame
- **Maximum Velocity:** 15 pixels/frame
- **Initial Velocity:** Random between -6 and +6 on both axes

If a fighter ever stops moving (velocity = 0), they're given a random directional nudge to keep the action flowing.

### Ninja Wall Boosts
When bouncing off walls, fighters receive a **4 pixel/frame velocity boost toward the arena center**. This prevents corner camping and naturally guides fighters back into combat.

### Sword Orientation & Rotation
The sword rotates 360 degrees constantly. The weapon leaves a smooth, fading, semi-transparent light trail at the tip to emphasize the speed and direction of the spin, with a thick cel-shaded black outline.

---

## Arena Escalation System

To prevent stalemates and keep the action flowing, the arena features an inactivity pressure mechanic:

### Arena Pulse
If no combat occurs for **2 seconds**, an **Arena Pulse** triggers.
- A radial shockwave fires, abruptly pushing both fighters toward the center of the arena to force combat.
- This pulse repeats every 2 seconds of inactivity, ensuring the action is constant.

---

## Controls

| Key          | Action                           |
|--------------|----------------------------------|
| **SPACE**    | Start game / Pause               |
| **R**        | Reset current round              |
| **ESC**      | Exit game                        |
| **Mouse Click** | Start game (title screen only) |

---

## Technical Stack

| Component    | Technology                        |
|--------------|-----------------------------------|
| **Language** | Python 3.x                        |
| **Framework**| Pygame (game loop, rendering, audio) |
| **Audio**    | Procedurally generated at runtime |
| **Physics**  | Custom bounce-based movement      |

### Project Structure
```text
project_root/
├── assets/           # Media assets (audio, images) extracted to root
├── src/
│   ├── config.py           # Constants, physics values, and configuration
│   ├── effects.py          # Particle, shockwave, and slash effects
│   ├── main.py             # Main game loop and window management
│   ├── utils.py            # Helpful utilities
│   ├── entities/
│   │   └── fighter.py      # Core fighter logical state and movement
│   ├── managers/
│   │   ├── combat_manager.py # Handles collision, hitting, and parry logic
│   │   ├── obs_manager.py    # OBS WebSocket integration for automated recording
│   │   └── sound_manager.py  # Centralized sound generation and effect playback
│   └── renderers/
│       ├── fighter_renderer.py # Draws the fighter visuals
│       └── ui_renderer.py      # HUD and UI element drawing
└── record.py         # Consolidated batch recording script
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

# CLI Bypass: Pass colors directly (1=Red, 2=Orange, 3=Yellow, 4=Green, 5=Blue, 6=Violet)
python src/main.py --auto-start --f1 5 --f2 1

# OR: Run the batch recorder for multiple automated rounds or test loops
# Fighter colors are fully randomized for each video before launching OBS sequences!
# You will be prompted to run in "Test Mode" (no OBS) or "Batch Recording" (OBS)
python record.py
```

---

## Dynamic Color Casting

Fighter colors are strictly limited to a customized 8-color high-contrast `NEON_PALETTE` for aesthetics. When you run `main.py` or the batch recorder, colors are dynamically injected. The batch recorder fully randomizes these colors automatically. The chosen colors don't just change the fighters—they globally cascade and replace visual variables across the simulation:
- The game's standard arena borders dynamically swap between Fighter 1 and Fighter 2 colors every 3 seconds.
- The UI features a persistent, flush, **Tekken-style HUD** displaying robust health bars dynamically themed to the chosen fighters' colors, bordered with a dark cel-shaded outline.
- The **Winner Announcer** dynamically renders a sleek, color-coded dot corresponding to the winning fighter followed by "WINS" to keep text sizing absolutely uniform across all outcomes.

---

## OBS Auto-Recording Integration (TikTok Automation)

This project is built to automate the creation of YouTube shorts content. It includes a built-in integration with **OBS Studio** via WebSockets perfectly configured to capture clips without manual editing.

### How it works:
1. The game sends a command directly to OBS in the background to **Start Recording**.
2. Two seconds after the Winner text appears, the application will automatically close, and command OBS to **Stop Recording** and save your clip. 

### OBS Setup Instructions:
1. Add a **Window Capture** source and select the Python game window (`Color Battle`).
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

| Constant              | Value | Description                          |
|-----------------------|-------|--------------------------------------|
| `SCREEN_WIDTH`        | 600   | Window width in pixels               |
| `SCREEN_HEIGHT`       | 600   | Window height in pixels              |
| `FPS`                 | 60    | Target frames per second             |
| `BASE_HEALTH`         | 250   | Hit points per fighter               |
| `DAMAGE_PER_HIT`      | 15    | Base damage (before multipliers)     |
| `FIGHTER_RADIUS`      | 30    | Fighter body size                    |
| `SWORD_LENGTH`        | 55    | Sword reach in pixels                |
| `ROUND_MAX_TIME`      | 18    | Force resolution after 18 seconds    |

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
