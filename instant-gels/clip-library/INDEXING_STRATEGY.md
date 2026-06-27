# Instant Gels — Indexing & Assembly Strategy (DRAFT v0.1)

> Light working draft to react to — not the final spec. Builds on the locked decisions:
> **fully separate library · SQLite + JSON sidecars · two-pass Gemini + compliance check**.
> Merges the "Creative Library Indexing Theory" doc with the proven dip `schema_v2.json`.

---

## 0. Objective
Turn Instant Gels footage into a retrievable creative library so that, given a script (or a creative
recipe), the system pulls the exact *moments*, sequences them, adds captions/transitions, calls AI voice,
(later) generates Higgsfield b-roll for gaps, renders a 9:16 ad, and writes a `build_manifest.json`
describing exactly how it was made. **Index the moment, not the file.**

## 1. Principles
1. The unit of value is the **segment** (a usable moment), not the source clip.
2. Tag both **what is shown** and **what job it can do** in an ad (role + stage).
3. **Controlled vocab first, free-text second** — controlled fields drive reliable retrieval.
4. **Compliance is structural** — claims come from an approved list; safety-sensitive clips force a disclaimer.
5. **Crossover firewall** — this library physically cannot mix with the dip library (see §8).
6. Source files are never modified; everything generated is a derivative.

## 2. Architecture
```
instant-gels/clip-library/
  raw/                     # original downloads, untouched (mirror the 7 ingest folders)
  index.db                 # SQLite — the query layer (segments, videos, claims, performance)
  videos/<video_id>.json   # per-video sidecar (human-readable, git-friendly)
  segments/<segment_id>.json
  frames/<video_id>/...    # contact-sheet frames for QA + look-book
  schema/                  # JSON Schemas + controlled-vocab files
  tools/                   # indexer, retrieval, assembler (shared code, gel-scoped config)
```
SQLite is the retrieval/reporting brain (role/score/colour/compat queries + the future performance join);
JSON sidecars stay readable and diffable.

## 3. Two record levels (field sketch, not final schema)

**VIDEO-level** (one per source file): `video_id`, `product_line:"instant_gels"`, `content_hash`,
`file{path,duration,fps,resolution,orientation,has_audio}`, `source_type{studio|ugc|generated}`,
`creator`, `primary_folder` (one of the 7), `transcript[{t_start,t_end,text}]`, `overall_summary`,
`quality`, `ingested_at`.

**SEGMENT-level** (the unit; many per video):
- *Identity/timing*: `segment_id` (`IG-0007-s03`), `video_id`, `t_start/t_end`, `usable_range{min,max,sweet_spot}`,
  `action_climax{t,action}` ← exact peak frame for VO/cut sync (from dip schema).
- *Classification*: `primary_category`, `secondary_categories[]`, `creative_role[]`, `creative_stage`,
  `method{tabs|glue|n/a}`, `process_step`.
- *Product/style*: `sku` (e.g. "Chrome Kisses"), `colour_finish`, `shape`, `length`, `products_visible[]`.
- *Visual/audio*: `subject`, `framing`, `camera`, `motion_level`, `visual_fingerprint` (dedup),
  `audio{has_voice,has_asmr,asmr_moments[],assembly_recommendation}`.
- *Platform*: `crop{9_16,4_5,1_1}`, `safe_zone_clear`, `text_overlay_space`.
- *Compliance*: `claims_shown[]` (from approved list), `claim_evidence`, `safety_sensitive`,
  `requires_disclaimer`, `claim_risk`.
- *Scores (drive ranking)*: `visual_quality`, `product_visibility`, `hook`, `proof`, `standalone`,
  `edit_flexibility`, `brand_fit`.
- *Compatibility*: `compat{follows[],precedes[]}`.
- *Meta*: `search_tags[]`, `confidence`, `human_review_status`.

## 4. Controlled vocabularies (gel-specific — no dip terms)
- **primary_category** (= the 7 folders, but assigned by content, not just folder):
  `01_hooks`, `02_application`, `03_removal`, `04_product_shots`, `05_durability`, `06_posing_lifestyle`,
  `07_fast_motion` (style layer, not a true category).
- **method**: `tabs` | `glue` | `n/a`.
- **process_step**: prep_shape · prep_pushback · prep_buff · prep_cleanse · size_match · tab_apply ·
  glue_apply · position_at_cuticle · press_hold · final_reveal · removal_soak · removal_lift ·
  removal_cleanup · reuse_clean. *(see `product-info/03`)*
- **products_visible**: press_on_set · nailed_it_glue · adhesive_tabs · smooth_moves_file · cuticle_stick ·
  prep_pad · kit_box · sizing_guide · remove_solution · heal_oil.
- **durability_test**: typing · handwash · water · hair_run · hammer · key · drill · screwdriver · other.
- **creative_role**: hook · reveal · demo · proof · payoff · social_proof · transition · cta_support.
- **creative_stage**: Hook · Problem · Agitation · Reveal · Demo · Benefit · Proof · Comparison ·
  Transformation/Payoff · Lifestyle · Offer · CTA · Outro · Transition.
- **sku / colour_finish / shape**: from `product-info/04_SKU_CATALOG.md` (32 styles; shape codes TBC).
- **claims_shown**: from `product-info/02_CLAIMS_AND_COMPLIANCE.md` (approved only).

## 5. Indexing pipeline (per clip)
1. **Ingest** — copy to `raw/`, compute `content_hash` (skip if already indexed).
2. **Scene detection** (local, cheap) — PySceneDetect/ffmpeg proposes hard-cut boundaries → candidate
   segment bounds. Enforces "split where purpose changes" deterministically; mitigates Gemini's 1-FPS
   blind spots on fast cuts.
3. **Pass A — Gemini (Files API)**: transcript w/ timestamps + video summary + confirm/adjust segment
   boundaries.
4. **Pass B — Gemini (structured `responseSchema`)**: per-segment enrichment → the full segment record.
   System prompt carries the controlled vocab + approved-claims list so it can only tag approved values;
   temperature ~0.1; force `human_review_status="pending"` when confidence < 0.8.
5. **Compliance check** — for any segment with `claims_shown` or `safety_sensitive`, a focused second call:
   "is this claim approved and visually substantiated?" Disagreement → flag for human review.
6. **Frames** — extract a contact sheet per clip for QA + look-book.
7. **Write** — JSON sidecars + upsert into `index.db`.

Cost is trivial (~300 tok/s of video) so we spend on the verify pass, not on skipping it. Apply the theory
doc's segment-length guides (fast insert 0.25–1s, hook 0.8–3s, application 2–8s, etc.).

## 6. Retrieval contract
A script is split into **beats**; each beat becomes an **asset-request**:
```
{ role, stage, method?, sku/colour?, duration{min,max}, must_show[], audio_need,
  crop:"9:16", needs_text_space?, compliance_ok:true }
```
Ranking: hard-filter `product_line` + hard constraints → score
`= w·quality_scores + compat_bonus(prev/next) − fingerprint_similarity_penalty(recent picks)`.
Returns a ranked shortlist; the assembler picks, never just "first match".

## 7. Assembly + provenance
Output of an ad = render **+** `build_manifest.json`: every `segment_id` with in/out, transitions, caption/
CTA component IDs (reused from the dip motion-kit vocab), VO voice + script + word timings (ElevenLabs),
music, **claims shown + which disclaimer was auto-inserted**, and any Higgsfield generation prompts.
→ reproducible *and* compliance-auditable, and the join target for the future performance layer
(spend, thumb-stop, watch-rate, CTR, ROAS).

## 8. Crossover firewall (the "don't cross over" rule)
- `product_line` is required + the **first** retrieval filter; only `instant_gels` exists in this DB.
- Separate folder, `index.db`, frames — no shared data with `clip-library/` (dip).
- Gel vocab contains no dip steps/powders, so a clip *can't* be mis-tagged into the other line.

## 9. Open / to confirm
- Map the 4 shape codes (US001A/UT002A/UX002A/UY002A) → shape names.
- Lock the Gemini Flash model id (from `test_gemini.py` output).
- Confirm hybrid scene-detect + Gemini boundaries.
- Later: gel-specific motion kit (premium/fashion/ASMR), branched from the dip kit.
- Prereq: fix ffmpeg (`brew reinstall ffmpeg`) before processing footage.

*Next, when greenlit: turn §3 into a strict JSON Schema, build the indexer in `tools/`, and draft the
retrieval + manifest formats.*
