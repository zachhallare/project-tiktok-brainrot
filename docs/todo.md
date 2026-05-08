
0.  "blackout" experiment (big what if, dont do it yet):
What actually would work for that "blackout" moment feeling:

Chromatic aberration burst — RGB split on the whole screen for 3-4 frames, then snap back. Screams impact.
Whiteout flash — full white frame for 1-2 frames (the opposite of blackout). This is what fighting games do for ultra hits because it reads as explosive.
Oversaturation spike — everything goes hypersaturated/neon for a beat before returning to normal. Fits your existing aesthetic.
Freeze frame + zoom — 8-12 frame freeze on hit with a slow push-in. This is the most "viral clip" friendly since it gives the viewer a moment to process what happened.

=======================================================

1. sound effects

# Honest Audit of Your Sound Design

## What you have right now (11 sound files):

| Category | File | Used for |
| :--- | :--- | :--- |
| combat | `hit_1.mp3`, `hit_2.mp3` | Generic body hit (alternating) |
| combat | `critical_hit.mp3` | Sweet spot / crit hit |
| combat | `sword_clash.mp3` | Parry clash + guard break |
| combat | `death_final_hit.mp3` | Death moment |
| combat | `sword_to_the_ground.mp3` | Post-death weapon drop |
| combat | `knockback_whoosh.mp3` | EXISTS but UNUSED in code |
| countdown | `countdown_beep.mp3` | 3, 2, 1 beeps |
| countdown | `sword-fight.mp3` | "FIGHT" reveal |
| feedback | `arena_pulse.mp3` | Inactivity pulse |
| ending | `victory_fireworks.mp3` | Winner fireworks |

---

## The Problems

1. **`knockback_whoosh.mp3` is orphaned.** It's sitting in your combat folder doing nothing. You paid for that sound (or spent time finding it). Wire it up.
2. **Every weapon sounds identical.** This is the big one. You have a sword, dagger, spear, axe, and hammer — five mechanically distinct weapons with unique personalities (the hammer reverses spin and has max hitstop, the dagger is a rapid glass cannon, the spear is a sniper). But right now a dagger hit sounds the same as a hammer hit. That's a MASSIVE missed opportunity for Shorts. Sound is 50% of the dopamine hit on these platforms. When a hammer crits, the audience should *feel* that different from a dagger flurry. Right now they can't.
3. **Your parry/clash sound is doing double duty.** `sword_clash.mp3` plays for both a clean sword parry AND a guard break. Those are mechanically and emotionally opposite events — a parry is "nice block!", a guard break is "you're DONE." They need different sounds.
4. **Missing ambient/juice sounds.** No wall bounce sound, no guard break shatter, no momentum stack feedback. These are the micro-sounds that make viewers feel the physics.

---

## What You Need Per Weapon

Each weapon needs **3 sounds minimum** to have its own identity:

| Sound | Purpose | Why it matters |
| :--- | :--- | :--- |
| `hit.mp3` (or 2 variants) | Normal body hit | The bread-and-butter. Viewers hear this most. |
| `sweet_spot.mp3` | Sweet spot / powerful hit | The "money" sound. This is the clip moment. |
| `clash.mp3` | Weapon-on-weapon parry | Defines the weapon's weight when it clashes. |

### Sound character per weapon:

* **Sword** — Clean metallic slashes, sharp ring on clash. Classic anime.
* **Dagger** — Quick, light, "shink" sounds. Fast staccato. Thin but snappy.
* **Spear** — Piercing/thrusting "thwack". Pointed impact, not broad. Staff-like thud on clash.
* **Axe** — Chunky, meaty chops. Heavy wood + metal. Satisfying crunch.
* **Hammer** — Deep, bassy THUD. Earthquake bass. The heaviest, most dramatic impact of all five. This weapon's whole identity is "I hit like a truck" — the sound must deliver that.

---

## Proposed Folder Structure

```text
assets/
├── audios/
│   ├── combat/
│   │   ├── death_final_hit.mp3        # Kill blow (shared)
│   │   ├── guard_break.mp3            # NEW — guard break shatter
│   │   ├── knockback_whoosh.mp3       # Wire this up! Big knockback events
│   │   └── wall_bounce.mp3            # NEW — wall impact thud
│   │
│   ├── weapons/                       # NEW — per-weapon sound folder
│   │   ├── sword/
│   │   │   ├── hit_1.mp3              # Normal hit variant 1
│   │   │   ├── hit_2.mp3              # Normal hit variant 2
│   │   │   ├── sweet_spot.mp3         # Sweet spot hit
│   │   │   └── clash.mp3              # Parry/sword-on-sword
│   │   ├── dagger/
│   │   │   ├── hit_1.mp3
│   │   │   ├── hit_2.mp3
│   │   │   ├── sweet_spot.mp3
│   │   │   └── clash.mp3
│   │   ├── spear/
│   │   │   ├── hit_1.mp3
│   │   │   ├── hit_2.mp3
│   │   │   ├── sweet_spot.mp3
│   │   │   └── clash.mp3
│   │   ├── axe/
│   │   │   ├── hit_1.mp3
│   │   │   ├── hit_2.mp3
│   │   │   ├── sweet_spot.mp3
│   │   │   └── clash.mp3
│   │   └── hammer/
│   │       ├── hit_1.mp3
│   │       ├── hit_2.mp3
│   │       ├── sweet_spot.mp3
│   │       └── clash.mp3
│   │
│   ├── countdown/
│   │   ├── countdown_beep.mp3         # 3, 2, 1
│   │   └── sword-fight.mp3            # "FIGHT" reveal
│   │
│   ├── ending/
│   │   ├── victory_fireworks.mp3
│   │   └── sword_to_the_ground.mp3    # MOVE here from combat/ — it's a death sequence sound
│   │
│   └── feedback/
│       └── arena_pulse.mp3



Priority Ranking (What to find first)
🔴 Hammer sounds — The hammer is your most visually dramatic weapon (max hitstop, spin reverse, all sweet spot). It NEEDS a unique bassy impact sound or it completely undermines the visual identity. This is your biggest audio gap right now.

🔴 Guard break shatter — This is a major combat event with huge particles and screen shake but plays the same generic clash sound. Needs its own "crack/shatter" SFX.

🟡 Dagger hit sounds — Fast, light, snappy. Without these, dagger vs hammer matchups (your most asymmetric fight) sound boring.

🟡 Axe chop sounds — Meaty, chunky. Distinct from sword.

🟡 Spear thrust sounds — Piercing, pointed.

🟢 Sword sounds — You already have these (current hit_1, hit_2, sword_clash). Just rename/move them into the weapons/sword/ folder.

🟢 wall_bounce.mp3 — Nice to have for juice. Low priority.

🟢 Wire up knockback_whoosh.mp3 — It's already there, just needs code.


