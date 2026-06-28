# Instant Gel test-script ad - session recap

Last updated: 2026-06-28. Current render: **`ad-teardowns/output/igad_v4.mp4`** (74s, 9:16, no music).

## What this is
A test ad built from `~/Downloads/test-script.md` (9-segment Instant Gels script) to validate the
end-to-end pipeline: VO -> per-line timing -> beats re-timed to VO -> clips from the index + Veo b-roll
+ Pillow caption overlays + soft SFX -> single render. Dip vs Instant Gels stay fully separate.

## Version history
- **v1** - index clips only, slates where footage was missing, full VO muxed.
- **v2** - added still-image b-roll (Soul V2) on the negative beats + pop/ding SFX.
- **v3** - reworked SFX to error(harsh)/ding/swish. User: harsh buzzer too much.
- **v4 (current)** - Veo 3.1 *video* b-roll on pain/reaction beats; agitation montage re-cut to 7 fast
  word-aligned hits (~1.8s ea, was ~2.5s); harsh buzzer -> soft negative blip. ding+swish kept.

## How to rebuild
```bash
cd ~/Desktop/Video-ad-test/ad-teardowns
python3 igad_build.py        # -> output/igad_v4.mp4  (rename the `final=` line to bump version)
```
Inputs it reads:
- VO: `vo/output/igad_full_vo.mp3` + per-line timing `vo/output/igad_vo_timing.json`
- Index: `instant-gels/clip-library/index.db` via `clip-library/tools/retrieve.py`
- Video b-roll: `instant-gels/generated/broll-video/*.mp4` (gitignored - local only)
- SFX: `output/sfx2/` (Light=ding, Quick=swish), `output/sfx3/*2349*` (soft negative)

## Key structures in `igad_build.py`
- `S` = 25 sub-beats: `(seg, style, caption, (kind, payload))`. Styles: magenta/white/label/redx/recycle/endcard.
- Durations: each segment's VO dur split equally across its sub-beats; last beat padded to VO length.
- `VBROLL` dict: caption -> `(video_file, seek_in_seconds)`. **Takes precedence** over still b-roll/slate.
  Reuses smudgedpolish/filing/foilacetone at different in-points for shellac/acrylic/chemicals (no
  dedicated footage for those words).
- SFX mix: soft-negative on every `redx` beat, ding on GOOD set + recycle, swish on transitions/labels.
  Volumes `VOL={'error':0.5,'ding':0.5,'swish':0.4}`.

## B-roll generation (Higgsfield Veo 3.1)
- Model decision: **veo3_1** (22 cr/clip, 8s, 9:16) - best proven realism on hands/nails. Fallbacks:
  Seedance 2.0 (anatomy), Kling 3.0 (cheaper). Account: ~1000 cr left, plan=plus.
- Prompts pack: `~/Downloads/glamrdip-higgsfield-broll-prompts.md` (real footage = proof; AI = pain/lifestyle).
- Scripts: `instant-gels/generated/gen_broll_video.sh` (proof) + `gen_broll_batch.sh` (batch). Set
  `MODEL=seedance_2_0` env to switch. Each `gen` skips if the mp4 already exists.
- Generated so far: smudgedpolish, cheapnailcrack, uvlamp, filing, foilacetone, couchfrustration.

## Open items / next time
- Veo footage is "fine, not great." Regenerate weak clips with tighter prompts or swap to Seedance.
- Optional: distinct clips for shellac / acrylic / chemicals instead of reusing in-points.
- Not yet generated from the pack: salon-waiting, healthy-nail macro, soapy-water, finished-daylight,
  iced-drink (those segments currently use real index footage - only add AI if real is weak).
- Background music intentionally OFF (user choice). Add later if wanted.
- Exact word-level VO sync still needs an ElevenLabs API key in `.env` (MCP STT gives text only).
- The build's end-of-run print labels VBROLL beats "SLATE" - cosmetic only; video b-roll is confirmed
  baked in (frame stddev check). Could make the print VBROLL-aware.

## Backup
Repo: `git@github.com:Remy-Rat/creative-gen.git` (main). v4 commit: `a631dcd`. mp4s + VO gitignored.
