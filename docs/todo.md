todos

Batch 4 — sound_manager.py (1 change)
I need you to implement 1 change to sound_manager.py. Please return the complete file.

Send me sound_manager.py first so you can audit it before making changes.

Change:
WEAPON SOUND PITCH VARIATION: Currently all weapons play sounds at identical pitch. Add a pitch modifier dict keyed by weapon name. Light weapons (dagger) pitch up ~5%, heavy weapons (hammer) pitch down ~8%, mid-weight weapons (sword, axe, spear) stay at baseline. Apply this modifier on playback for parry and hit sounds. Implementation can use pre-pitched sound variants or a runtime pitch modifier depending on what pygame supports cleanly.



Batch 5 — intro_renderer.py + main.py (intro timing fixes)
I need you to implement 2 changes across intro_renderer.py and main.py. Please return both complete files.

Send me both files first so you can audit them before making changes.

Changes:
1. MATCHUP LABELS AT FRAME 0: Currently _draw_countdown_overlay() returns immediately when countdown_active is False, meaning matchup label cards don't appear until ~1 second in. Fix: Move the _draw_matchup_labels() call (or equivalent label card drawing) out of the countdown gate so it renders always when in PLAYING state, not only during countdown. The viewer should see NAME / WEAPON labels for both fighters starting at frame 0, not after the startup timer clears.

2. STARTUP TIMER 60→30 FRAMES: The obs_startup_timer is currently 60 frames (1.0s). Reduce this to 30 frames (0.5s). OBS WebSocket acknowledges StartRecord within 150–200ms so 60 frames was always over-cautious. Update every location this value is set or referenced.




Batch 6 — Bug fixes (record.py + main.py)
I need you to fix 3 bugs across record.py and main.py. Please return both complete files.

Send me both files first so you can audit them before making changes.

Fixes:
1. ??? WINNER BUG (record.py): When both fighters die simultaneously, no [RESULT] line is emitted and the result parser outputs ???-??? with 0% HP. Fix: In record.py's result parser, handle the case where no [RESULT] tag is found. Assign winner as "DRAW", do not count the round toward either fighter's win total in balance stats.

2. DUPLICATE RESET CLEANUP (main.py): In _reset_round(), lead_changes, current_leader, max_blue_lead, and max_red_lead are reset twice in a row. The second reset block (lines 539–542 approximately) is unreachable dead code. Delete the duplicate block. Zero behavior change.

3. MISSING METHOD STUB (intro_renderer.py): draw_title() calls self._draw_old_title_screen() but this method is not defined. Auto-start bypasses it but a manual TITLE state will hard-crash. Add a minimal stub that returns False. Two lines.


=======================================================


what if only:

"blackout" experiment (big what if, dont do it yet):
What actually would work for that "blackout" moment feeling:

Chromatic aberration burst — RGB split on the whole screen for 3-4 frames, then snap back. Screams impact.
Whiteout flash — full white frame for 1-2 frames (the opposite of blackout). This is what fighting games do for ultra hits because it reads as explosive.
Oversaturation spike — everything goes hypersaturated/neon for a beat before returning to normal. Fits your existing aesthetic.
Freeze frame + zoom — 8-12 frame freeze on hit with a slow push-in. This is the most "viral clip" friendly since it gives the viewer a moment to process what happened.


