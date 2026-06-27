#!/usr/bin/env python3
"""Delete files parked in the Gemini Files API (frees the 20GB storage quota).
Parallel deletes. Safe between indexing passes (no uploads in flight at a boundary)."""
import sys, time, pathlib
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from index import load_key
from google import genai

c = genai.Client(api_key=load_key())
t = time.time()
names = []
try:
    for f in c.files.list():
        names.append(f.name)
except Exception as e:
    print("list error:", e)
print(f"{len(names)} files stored; deleting...", flush=True)
def d(n):
    try: c.files.delete(name=n); return 1
    except Exception: return 0
done = 0
with ThreadPoolExecutor(max_workers=12) as ex:
    for r in ex.map(d, names): done += r
print(f"purged {done}/{len(names)} files in {time.time()-t:.0f}s", flush=True)
