# Instant Gels — B-roll Generation Skill (Higgsfield)

The discipline that keeps this from becoming AI slop: **generate rarely, generate sharp, gate with Gemini
before anything enters the library.** This is the prep that happens BEFORE any Higgsfield request.

## 0. Hard rules (non-negotiable — see [[instant-gels-higgsfield-rules]])
- **Faceless** always. Hands/forearms/objects only. Anything needing a face = real footage.
- **No product, no proof.** Generated = problem / abstract-concept / lifestyle-context / transition ONLY.
  (Generic props like a UV lamp or coins are fine; our actual product / a "wear test" is NOT.)
- No other-brand logos, no on-screen text/labels (AI mangles them), no claims implied as proven.
- Every kept clip = `source_type:generated`, AI-disclosure flagged, provenance stored.

## 1. Decision gate — should we generate this at all?
Generate ONLY if all three hold:
1. **Gap:** retrieval / `gap_report.py` finds no real clip that serves the beat. (Current gaps: abstract
   concept [time/"2 weeks", value/$], lifestyle context, a few problem shots. Everything else is covered — don't.)
2. **Reusable:** it's a library asset we'll use across many ads, not a one-off for a single word.
3. **A visual beats a caption:** the idea lands harder shown than said. Not every line needs a clip.
If a real clip exists, or a caption/motion-graphic does the job → DON'T generate.

Prefer a crisp **metaphor** for abstract claims: "no UV lamp" → a bulky UV lamp tossed in a bin; "2 weeks" →
calendar pages flipping; "$ value" → a long salon receipt vs a couple of coins. Tasteful, not cheesy.

## 2. The request (the "sharp brief") — fill this per shot
```
id:            ig-gen-001
fills_gap:     problem | concept-time | concept-value | lifestyle | transition
concept:       the ONE idea it must convey (e.g. "old gel manicure is chipped & worn")
use_roles:     [hook, problem, ...]            # how the assembler will use it
type:          realism | stylised-metaphor
shot:          subject + action + framing + angle
motion:        (for image->video) one subtle move
style:         premium, clean, true-to-life | clean minimal; soft even light; neutral/lilac palette; shallow DoF
constraints:   FACELESS; no product; no text; no other brands
aspect:        9:16   duration: 3-5s
still_model:   text2image_soul_v2 (brand/photoreal) | nano_banana_2 (realism) | flux_2 (stylised)
video_model:   veo3_1 (best) | kling3_0 / kling3_0_turbo (cheaper) | seedance_2_0
```

### Reusable prompt blocks (paste into every prompt)
- **Style (realism):** "photoreal, true-to-life colour, soft even diffused light, shallow depth of field,
  premium and clean, no faces, hand/fingertips only"
- **Negative (bake into prompt — Soul V2 has no negative flag):** "no human face, no text, no logos,
  no extra fingers, no deformed hands, no watermark, no clutter"

## 3. Workflow (still first, then motion)
1. **Still:** `hf generate create <still_model> --prompt "<full prompt>" --aspect_ratio 9:16 --quality 2k --wait`
   (optionally `--image <brand-ref.jpg>` for Soul V2 to hold our look). Generate 2-3 variants, pick best.
2. **Gemini QA the still** (§4). Pass → continue; fail → regenerate (vary prompt/seed) up to 3, else discard.
3. **Image→video:** `hf generate create <video_model> --prompt "<motion line>" --start-image <still> --wait`
4. **Gemini QA the clip** again (motion can add artifacts).
5. **Index** the passed clip via the normal Gemini indexer → it becomes retrievable like any clip.
(`hf` = higgsfield. Media flags auto-upload local paths. Check cost with `hf account status` before/after.)

## 4. Gemini QA rubric (the gate) — run on every still AND clip
Ask Gemini (structured JSON):
- `face_present`  → if true: **FAIL** (auto-reject).
- `artifacts` (extra fingers, warped hand, melted objects, gibberish text, other-brand logo) → any: **FAIL**.
- `shows_product_or_proof` (our nails/kit as if proving a claim) → true: **FAIL** (rule breach).
- `on_concept` 1-10: does it clearly read as the intended `concept`?
- `sharpness` 1-10, `brand_fit` 1-10 (premium, on-palette, not cheesy).
- **PASS** = no FAILs AND avg(on_concept, sharpness, brand_fit) ≥ 7. Else regenerate (≤3) or discard + log.

## 5. Provenance (store with every kept clip)
prompt, still_model, video_model, job/seed ids, fills_gap, concept, date, source_type=generated,
ai_disclosure=true, qa_scores. → reproducible, auditable, disclosure-ready.

## 6. Starter shot list (the current gaps — sharp briefs)
1. **PROBLEM — worn/chipped manicure** (realism). Concept: "old gel chips & lifts." Macro of a single
   chipped, dull, peeling old manicure on a natural nail, edge lifted, neutral soft-lit bg, faceless.
2. **CONCEPT — no UV lamp** (metaphor). A hand dropping/tossing a bulky UV/LED nail lamp into a bin; or lamp
   powering off. Clean minimal bg. Conveys "no lamp needed."
3. **CONCEPT — 2 weeks wear** (metaphor). Calendar pages flipping / "14" highlighted, minimal, lilac accent.
4. **CONCEPT — value** (metaphor). A long salon receipt beside two coins on a clean surface. "$ salon vs cheap."
5. **LIFESTYLE — getting ready** (realism). Faceless over-shoulder/hands at a vanity mirror, nice nails, warm light.
6. **LIFESTYLE — night out** (realism). Hands holding a drink/clutch in a softly-lit bar, nails catching light.

*Trial first (ig-gen-001 = shot #1), judge quality together, then batch the rest.*
