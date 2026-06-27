# Gemini setup — Instant Gels indexer

One-time setup so the indexing pipeline can "watch" clips via Gemini. ~10 minutes. Do this while footage downloads.

## What we're connecting
We call the **Gemini API** directly from Python (the `google-genai` SDK) — not a Claude/MCP connector.
Gemini Flash watches each clip via the **Files API** and returns structured JSON segment records.

---

## Step 1 — Get an API key (recommended path: AI Studio)
1. Go to **https://aistudio.google.com/apikey** (sign in as remy@glamrdip.com).
2. Click **Create API key** → choose the `glamrdip-ops-vault` project (or any project).
3. Copy the key (starts with `AIza…`).

> Alternative (enterprise): use **Vertex AI** on `glamrdip-ops-vault` instead of a key — set
> `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT=glamrdip-ops-vault`, `GOOGLE_CLOUD_LOCATION=us-central1`,
> and authenticate with `gcloud auth application-default login`. Only worth it if you want everything under GCP
> billing/IAM. The API key path above is simpler and is what these scripts assume.

## Step 2 — Store the key (so it persists)
Pick ONE:

**A. Shell profile (persists everywhere):**
```bash
echo 'export GEMINI_API_KEY="AIza-your-key-here"' >> ~/.zshrc
source ~/.zshrc
```
**B. Local .env (kept in this folder, git-ignored):**
```bash
echo 'GEMINI_API_KEY=AIza-your-key-here' > "instant-gels/clip-library/.env"
```
(The test script reads both — env var first, then `.env` in its folder.)

## Step 3 — Install the SDK
System Python here is 3.9, which is fine:
```bash
python3 -m pip install --user --upgrade google-genai
```
(Later, for scene detection + frames we'll also add `scenedetect[opencv]` — not needed yet.)

## Step 4 — Test the connection
```bash
# connectivity + list available Flash models + a text ping
python3 "instant-gels/clip-library/test_gemini.py"

# once you have any clip, also test real video understanding:
python3 "instant-gels/clip-library/test_gemini.py" "/path/to/any/clip.mp4"
```
Success looks like: a list of `…flash…` models, `Text test: GEMINI OK`, and (with a clip) a one-line
description **with an MM:SS timestamp** — that confirms Gemini can watch video and return timestamps.

## Step 5 — Tell me the model id
The test prints the Flash models available to your key (e.g. `gemini-flash-latest`, `gemini-2.5-flash`,
or a 3.x flash). Whichever is the newest non-lite Flash is what the indexer will use — paste me the list.

## Key facts (drive the indexer design)
- Files API: upload once, reuse; videos up to ~1 hr (default res). Use for anything >100 MB / reused.
- Cost ≈ **300 tokens / second** of video at default resolution → indexing the whole library is a few dollars.
- Default sampling **1 FPS** (audio continuous) — we'll add local scene detection for precise fast-cut boundaries.
- Structured output: we pass a JSON `responseSchema` so Gemini returns validated records (no parsing).

## Notes / gotchas
- `ffmpeg` on this machine is currently broken (x265 ABI mismatch) — needed later for cutting/frames/render,
  not for this test. Fix with `brew reinstall ffmpeg` before processing real footage.
- Never commit the API key. A `.gitignore` here already excludes `.env` and keys.
