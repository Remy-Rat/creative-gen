# GLAMRDiP VO Production (skill)

Turn a finished GLAMRDiP ad script (Notion brief, PDF, screenshot, or pasted text) into production-ready
voice-over audio via ElevenLabs. Formalises pacing, tagging, QA, model-selection, and the mandatory
**confirmation-before-generate** step so credits aren't burned on misread briefs / wrong voice / wrong model.

Triggers: "VO", "voiceover", "voice over", "generate audio", "ElevenLabs", "TTS", "text to speech",
"narrate", "read this script", or any request converting ad copy to spoken audio.

---
## ⚙️ ADAPTED FOR THIS REPO (read first — differs from Daniel's original)
- **Tool:** our connected ElevenLabs MCP `mcp__elevenlabs__text_to_speech` (NOT "ElevenLabs Player MCP / generate_tts").
  Params: `text`, `voice_id`, `model_id`, `output_directory`, `output_format` (default mp3_44100_128),
  `stability`, `similarity_boost`, `style`, `speed`, `use_speaker_boost`, `language`.
- **Models confirmed on our account (2026-06-28):** `eleven_v3` AND `eleven_multilingual_v2` both available.
  Voice IDs in `voice-library.md` resolve on our MCP (same GLAMRDiP account, "[DS]" prefix).
- **Output:** set `output_directory` to `vo/output/` (or a per-ad subfolder) — our MCP RESPECTS output_directory
  (unlike Daniel's Player MCP). Verify the exact filename it writes on the first call (it may name by voice/time);
  if it doesn't honour a logical name, do the post-gen bash rename (see File Naming).
- **Extra levers our tool has** (use to shape delivery, esp. for v2 voices with no tags): `stability` (lower =
  more emotional range/variance, higher = flatter/stable), `style` (0 default; small values add expressiveness),
  `speed` (1.0 default). Treat these as fine-tuning AFTER pacing/punctuation.
- **"Daniel" → the requester (Remy) / the assembler's VO step.** In automated assembly, the build pipeline calls
  this per script section; the GO/confirmation step still applies for human-driven runs.
- **Headless renderer (later):** drop an ElevenLabs API key into `.env` for the standalone assembler; the MCP
  covers interactive/now.

---
## Stack
- **Tool:** `mcp__elevenlabs__text_to_speech`
- **Model:** read per-voice **Default Model** from `voice-library.md`. Do NOT assume a default.
  - `eleven_v3` — supports audio tags ([concerned], [excited]…). For v3-safe voices only.
  - `eleven_multilingual_v2` — NO tags; preserves training accent. For v2-default voices + all PVCs.
- **Voice menu:** `voice-library.md`

## Known limitations
- **Audio tags only work on `eleven_v3`.** On v2 they're read aloud or stripped — both fail the brief. For
  v2-default voices, remove tags and convey emotion via pacing (below).
- **v3 accent drift:** 11/16 voices drifted UK, 1/16 US on v3 (audition 17 Apr 2026). Only the 3 v3-safe voices
  are accent-verified on v3; everything else MUST use v2.
- **Filename:** confirm how our MCP names files on first run; if not logical, provide a post-gen bash rename.

## Workflow (mandatory steps)
1. **Parse the script** — Notion concept (Master Creative DB → concept → Editing Brief → Shot List), PDF,
   screenshot, or pasted text. Extract spoken copy by section (Hook / Body 1..N / CTA). Ignore visual/shot/B-roll/
   music columns. If "Hook Variations" change visuals but keep the same hook script, don't duplicate VO.
2. **Select voice AND model** (never skip):
   - Voice named/ID'd → use it. "Aussie female voice" with no name → default **AUS GM** and flag it.
     No voice at all → **STOP, ask** (present the library with v3/v2 classification).
   - Model = the voice's Default Model from `voice-library.md` (v3-safe→v3; v2-default→v2; PVC→v2). Never infer.
     If Daniel overrides ("use v3 on Dawn"), apply + flag accent-drift risk.
   - Tag/model conflict: if brief implies emotion tags AND voice is v2-default → flag: translate to pacing, or
     swap to a v3-safe voice (AUS GM / Aurora / Christina).
3. **Confirmation table** (output BEFORE generating):
   ```
   Concept: [name] · [batch] · [due]
   Voice: [name] ([id])   Model: [eleven_v3|eleven_multilingual_v2]   Audio tags: [Yes|No]
   | # | Module | Copy (final TTS) | Tag | Pacing formula | Chars | Flag |
   ```
   Tag column must be empty/n-a for every row if model is v2. Copy = final TTS-ready (em-dash conversions,
   phonetic spellings, tag removal for v2 already applied).
4. **Pre-gen QA checklist** — surface, don't silently fix:
   - Numbers that misread ("18-Free" → "eighteen-free" for TTS only, NOT in Notion).
   - Brand names ("GLAMRDiP" usually reads "glamour dip"; if it's misread before, use "glamour dip"/"GLAM-R-DIP").
   - Genuine copy bugs (e.g. "$35 dollars off" = redundant) → flag + ask before editing Notion.
   - Hyphen → em-dash for pacing (keep hyphens inside compound adjectives like "paper-thin").
   - Chemical/scientific names (Toluene, HEMA, TPO, keratin…) → QA-listen after.
   - Currency: $2→"two dollars" fine; "$35 dollars" redundant.
   - Sections <250 chars → flag variance (plan 1–2 regens).
   - Brand-term rule: written (brand standard) ≠ spoken (phonetic TTS workaround). Never pollute Notion with phonetics.
   - v2 voice → confirm NO tags in any row. Accent-critical brief + unverified voice → flag/audition first.
5. **Wait for GO** — "GO" / "GO, fix [X]" / "GO, [copy edit]" (regen table first) / section overrides.
6. **Generate** — one `text_to_speech` call per section. `model_id` = per-voice Default Model. `voice_id` from step 2.
   `text` = final TTS copy (no tags if v2). `output_directory` = `vo/output/` (or per-ad subfolder). Logical name:
   `GLAMRDiP_[ScriptName]_[Section]_v[N]`.
7. **Output summary** — table of section → status → actual filename → target filename; + a bash rename/mkdir+mv
   chain. QA priorities to listen for. Feedback format: "regen [section]" / "regen [section] with [tag]" / "all good".

## Pacing rules (work on BOTH v2 and v3) — punctuation = rhythm, tags = emotion (v3 only)
Pause hierarchy: comma `,` ~150ms < em-dash `—` ~300ms < period `.` ~500ms < ellipsis `...` ~800ms+ <
`[pause]` ~1s+ (v3 only). Defaults: commas/em-dashes/periods for 95% of copy; reserve `...`/`[pause]` for
deliberate drama; CAPS for single-word emphasis. Convert source hyphens → em-dashes (except compound adjectives).

**Winning formulas (production-tested):**
- **A — Problem-reveal hook (fear):** `[concerned (v3)] [setup]? [clinical statement]—[punch], [punch].`
  v2 = same, tag dropped (punctuation carries).
- **B — Enumeration + qualifier:** `[item], [item], [item], [item]—[resolving clause].`
  (Periods between items = ~500ms each = heavy/slow; use only for deliberate drama.)
- **C — Clean confident statement (claims/CTA/offer):** `[Statement]. [Statement]. [Statement].` No tag.
- **D — Personal pivot / story:** natural punctuation, no tag.

Pacing troubleshooting: "pauses too long at periods" → em-dashes; "too long generally" → drop `...`/`[pause]`;
"flat/monotone" → upgrade commas to em-dashes/periods (or lower `stability`); "too slow" (v3) → drop the tag;
"too fast on list" → upgrade commas to em-dashes/periods.

## Tagging rules (v3 ONLY)
On v2: never pass tags — translate intent to pacing ([concerned]→measured commas/em-dashes; [excited]→shorter
sentences/tighter commas; [serious]→more periods), or escalate to swap to a v3-safe voice.
Tag-by-section (v3): Hook fear→[concerned]/[whispers], Hook discovery→[excited]/[curious], Body clinical→[serious],
Body testimonial→no tag/[sighs], Body reveal→[curious], Claims/feature list→no tag, CTA urgency→[excited]
(often too hyped — check), confident close→no tag, offer→no tag preferred.
Interaction: [serious]/[concerned] slow delivery; if content already has gravitas the tag over-delivers — drop
first, add only if flat; never stack >2 tags. Syntax: lowercase `[concerned]`, place at start of the fragment it
affects, persists until next tag; audio-event tags ([sighs],[laughs]) render the actual sound.

## File naming
`GLAMRDiP_[ScriptName]_[Section]_v[N]` (ScriptName PascalCase from concept title; Section = Hook/Body1../CTA;
increment v on regens). If our MCP doesn't honour the name, provide post-gen bash rename (+ `mkdir -p` for subfolders).

## Model selection quick reference
v3-safe voice → `eleven_v3` · v2-default voice → `eleven_multilingual_v2` · PVC → `eleven_multilingual_v2` ·
long-form → v2 · real-time → flash_v2_5 · (tags needed + v2 voice → ESCALATE) · (strict accent + unverified voice → audition first).

## Overrides Daniel might give
"Use voice [name/ID]" (update model per library) · "Use V2/multilingual_v2" · "Use v3 on [v2 voice]" (flag drift) ·
"Section N should be [tag]" (v3 only) · "Regen section N" (new take) · "Regen N with [tag]" / "as '[copy]'" ·
"All sections no tag" · "Tighter/faster" (periods→em-dashes→commas) · "Heavier/more drama" (reverse) ·
"Too excited/flat" (adjust tag v3 / pacing v2) · "Audition all voices on [copy]" (per-voice model; name `[Voice] - [Label].mp3`).

## Do NOT
Default to v3 · pass tags to v2 voices · promise MCP filename/subfolders without verifying · rewrite Daniel's copy
(only: hyphen→em-dash except compound adjectives, phonetic spellings for numbers/brand TTS-only, tag removal for v2) ·
narrate the process (execute silently, summarise at end) · skip the confirmation table · skip voice/model selection ·
add `[pause]`/`...` by default · pollute Notion with phonetic spellings · generate without GO.

## Notion attachment constraint
Notion API can't upload binaries to Files & Media (URL-link only). Paths: (1) upload to Drive, link URLs;
(2) Daniel drags MP3s into Notion UI manually; (3) build Drive-auto-upload automation. Default: (2) one-off, (3) scalable.

---
*Source: Daniel's GLAMRDiP VO skill v1.1 (17 Apr 2026), adapted to this repo's ElevenLabs MCP + paths. Voice menu: `voice-library.md`.*
