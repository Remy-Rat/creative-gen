# Glamrdip Motion Kit — build files

Interactive look-book of vertical-video ad components (subtitles, hooks, product/benefit
cards, social proof, CTA/end cards, transitions, camera moves, annotations, framing, branding).
Each tile is a live looping CSS preview over real footage frames, with a build-spec inspector.

Published artifact: https://claude.ai/code/artifact/329a4259-e24d-494e-9436-d6f47841f793

## Files
- `kit.template.html`  — SOURCE. Edit this. Image slots are tokens like `{{KIT}}`, `{{RESULT}}`.
- `glamrdip-motion-kit.html` — generated final (tokens replaced with base64). Do not hand-edit; regenerate.
- `img/*.jpg` — chosen frames (440px, q55). `img/*.uri` — their base64 data URIs.

## Rebuild after editing kit.template.html
```bash
cd motion-kit-build
python3 - <<'PY'
import re, pathlib
uris={p.stem.upper():p.read_text() for p in pathlib.Path("img").glob("*.uri")}
html=pathlib.Path("kit.template.html").read_text()
out=re.sub(r"\{\{([^}]+)\}\}", lambda m: uris[m.group(1).split()[-1].upper()], html)
pathlib.Path("glamrdip-motion-kit.html").write_text(out)
print("ok", len(out))
PY
```
Then re-publish glamrdip-motion-kit.html via the Artifact tool (pass url= the link above to update in place).

## Image keys → source clip
craft=CLIP-0030 (glitter ombré application) · kit=CLIP-0050 (open kit, BASE/SEAL/GLOW/HEAL)
unbox=CLIP-0247 (golden-hour unbox) · result=CLIP-0188 (milky manicure) · before=CLIP-0250 (bare nails+powder)
table=CLIP-0017 (kit on table) · face=CLIP-0078 (UGC testimonial)
Frames came from clip-library/frames/<CLIP>/interval_00X.png (pre-extracted; 290 clips indexed).
