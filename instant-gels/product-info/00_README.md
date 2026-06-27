# Instant Gels™ — Product Info (index)

Clean, marketing-focused product context for the Instant Gels press-on line. These files are the source of
truth the AI clip-indexer and ad-assembler read from. **Separate from the dip-powder system.**

| File | What's in it |
|---|---|
| `01_PRODUCT.md` | What Instant Gels are, GelStack™ 6-layer system, kit contents, features, innovations, packaging |
| `02_CLAIMS_AND_COMPLIANCE.md` | **Approved claims (controlled vocab)** + verbatim safety cautions. Source of truth for what ads may say |
| `03_APPLICATION_AND_REMOVAL.md` | Approved application (tabs + glue) & removal steps; the **process-step vocabulary** |
| `04_SKU_CATALOG.md` | The **32 styles/colours** (names, codes, shapes) — the colour taxonomy for retrieval |
| `05_CREATIVE_BRIEF.md` | Content pillars (ASMR, durability, before/after, UGC…), competitors, styling notes |
| `06_CLINICAL_TRIAL_CAPTURE.md` | Clinical-trial capture brief (claim-backing footage, face-free) |
| `07_HIGGSFIELD_BROLL_PROMPTS.md` | AI b-roll generation prompts (for the clinical reference shots / future b-roll) |
| `assets/packaging-front.webp` | Final retail packaging render |
| `_source_originals/` | Untouched original files (raw briefs, .docx, supplier invoice PDF, landing-page prompts) |

## Notes
- **Marketing focus only** — no COGs/pricing captured. The supplier invoice (in `_source_originals/`)
  contains pricing + banking; treat as sensitive.
- Anything outside approved copy (`02`) must go to **Regulatory** before use in an ad.
- Related: the indexing/assembly plan lives in the assistant's project memory (`instant-gels-indexing-plan`).
