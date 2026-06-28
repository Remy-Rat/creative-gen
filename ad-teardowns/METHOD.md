# Ad Teardown — Method

How we reverse-engineer a reference ad into a buildable spec. Tool: `teardown.py`.

## Purpose
Turn a reference ad (any short-form video) into an exhaustive, timestamped spec — every shot, caption,
animation, SFX, VO line, transition, cut rhythm — plus a brand-agnostic structure template we refill with
our own footage + original copy (see `build_ad_0N.py`).

## Current pipeline (v1 — what runs today)
1. **Probe** the source with `ffprobe` (duration, aspect, fps, audio).
2. **Upload** the full video to **Gemini (`gemini-3.5-flash`)** via the Files API (patient retry on 503/429;
   file deleted after).
3. **One structured-JSON pass.** Gemini "watches" the video and returns a single JSON object:
   - `meta` (duration, aspect, total_cuts, avg_shot_len, pace, style, grade, music_style, vo_voice_feel)
   - `hook` (first 1.5s, technique, why it works)
   - `persuasion_arc` (ordered stages)
   - `timeline[]` — per beat: t_start/t_end, shot, subject, framing, camera, type, on_screen_text
     {text, style, position, animation_in/out, sync}, vo_line, vo_delivery, sfx[], music_note,
     transition, cut_length, replication_note
   - `caption_system`, `sound_design`, `cta`, `structure_template` (brand-agnostic skeleton)
4. **Render outputs:** `output/<name>.json` (machine) + `<name>.md` (readable report).
5. **Build step (separate):** `build_ad_0N.py` reads the teardown, we author original copy per beat, and
   `retrieve.py` maps each beat to a real indexed clip (or a b-roll-gap slate).

Cost: one Gemini call (~6k in / ~13k out tokens for a 60s ad) ≈ a few cents.

## ⚠️ What's missing / weak (the gap you're sensing)
The whole teardown rests on **one Gemini pass that samples the video at ~1 frame/second.** That's the core
limitation, and it cascades:

1. **Timings are estimated, not ground-truth.** At 1 FPS, a 0.8s cut can be missed or mis-placed. We trust
   Gemini's eyeballed t_start/t_end and cut count rather than detecting the *actual* cut frames. For a
   "match-the-creative" twin, the timing is only as good as that estimate.
2. **No reference frames extracted.** We never pull a frame per shot, so (a) we can't visually verify Gemini's
   descriptions, and (b) we have no visual *target* to match our retrieval/generation against.
3. **No real audio transcript / alignment.** VO lines + their timing are Gemini's read, not a forced
   alignment of the actual audio. Word/line boundaries (which should drive beat cuts) aren't exact.
4. **Single pass, no verification.** Nothing checks that the timeline covers the full duration with no gaps,
   that cut_lengths sum correctly, or that beats weren't merged/missed.
5. **Music/SFX is coarse.** "upbeat electronic" / "buzzer, ding" — no BPM, no beat-drop timestamps, so we
   can't sync our cuts to the track's rhythm the way the original does.
6. **Manual teardown→build bridge.** The teardown doesn't emit a suggested retrieval query per beat; we
   hand-author the mapping in `build_ad_0N.py`.

## Planned v2 method (fixes the above)
1. **Ground-truth cuts:** run **PySceneDetect/ffmpeg scene detection** on the reference → exact cut
   timestamps. Feed those to Gemini as the beat boundaries (describe *these* shots) instead of letting it
   guess. → real timings, real cut count.
2. **Frame extraction:** pull one frame per detected shot → a contact sheet saved with the teardown, for
   visual verification + as retrieval/generation targets.
3. **Audio layer:** transcribe the reference VO with word timestamps (ElevenLabs STT / forced alignment /
   whisper) → exact line boundaries; reconcile with the visual cuts.
4. **Verification pass:** a second Gemini (or local) check — full-duration coverage, monotonic timings,
   cut_length vs (t_end−t_start) consistency; flag anomalies.
5. **Music analysis:** detect BPM + beat grid (librosa/aubio) so we can place cuts on the beat.
6. **Auto-bridge:** have the teardown emit a suggested `retrieve.py` query per beat (role/category/shade)
   so `build_ad` is closer to one-click.

## Bottom line
v1 gives a *very good descriptive* teardown fast and cheap — great for understanding structure/technique.
For a *frame-accurate twin* (your side-by-side QA), the missing pieces are **scene-detection-driven exact
cuts + extracted frames + real audio alignment**. That's the v2 upgrade.
