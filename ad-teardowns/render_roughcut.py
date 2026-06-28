#!/usr/bin/env python3
"""Render a SILENT rough cut of IG-AD-01 from its manifest: trim each beat's clip to its duration,
scale/crop to 1080x1920, burn the caption (Pillow PNG overlay), lilac slates for b-roll gaps, concat.
v0 = see the visual pacing + clip selection. VO / music / SFX / real b-roll come in the iterate pass."""
import json, subprocess, pathlib, textwrap
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
OUT = HERE / 'output'
RAW = pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/raw')
WORK = OUT / 'roughcut_work'; WORK.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1920
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
LILAC = "0x6B3FA0"
man = json.loads((OUT / 'ig-ad-01.manifest.json').read_text())

def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def caption_png(text, path, gap=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 60)
    lines = wrap(d, text, f, W - 160)
    y = int(H * 0.10)
    for ln in lines:
        tw = d.textlength(ln, font=f); x = (W - tw) / 2
        d.text((x + 3, y + 3), ln, font=f, fill=(0, 0, 0, 160))      # shadow
        d.text((x, y), ln, font=f, fill=(255, 255, 255, 255))         # white
        y += 74
    if gap:
        fb = ImageFont.truetype(FONT, 70); fs = ImageFont.truetype(FONT, 38)
        lab = "[ B-ROLL ]"; tw = d.textlength(lab, font=fb)
        d.text(((W - tw) / 2, H * 0.46), lab, font=fb, fill=(255, 255, 255, 230))
        sub = "to generate (Higgsfield)"; tw = d.textlength(sub, font=fs)
        d.text(((W - tw) / 2, H * 0.46 + 86), sub, font=fs, fill=(255, 255, 255, 180))
    img.save(path)

def parse_dur(t):  # "12.0-14.4s"
    a, b = t.replace('s', '').split('-'); return round(float(b) - float(a), 2)

def encode(beat):
    n = beat['n']; dur = parse_dur(beat['t']); seg = WORK / f"seg_{n:02d}.mp4"
    cap = WORK / f"cap_{n:02d}.png"
    caption_png(beat['caption'], cap, gap=beat['broll_gap'])
    if beat['broll_gap'] or not beat.get('clip'):
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "lavfi", "-i", f"color=c={LILAC}:s={W}x{H}:d={dur}:r=30",
               "-i", str(cap),
               "-filter_complex", "[0:v][1:v]overlay=0:0,format=yuv420p[o]",
               "-map", "[o]", "-an", "-c:v", "libx264", "-r", "30", str(seg)]
    else:
        c = beat['clip']
        cpath = c['path'] if pathlib.Path(c['path']).is_absolute() else str(RAW / c['path'])
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(c['t_in']), "-i", cpath,
               "-i", str(cap), "-t", str(dur),
               "-filter_complex",
               f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30[v];"
               f"[v][1:v]overlay=0:0,format=yuv420p[o]",
               "-map", "[o]", "-an", "-c:v", "libx264", "-r", "30", str(seg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return n, seg, r.returncode, r.stderr[-200:] if r.returncode else ""

beats = man['beats']
print(f"encoding {len(beats)} beats (parallel)...")
results = {}
with ThreadPoolExecutor(max_workers=6) as ex:
    for n, seg, rc, err in ex.map(encode, beats):
        results[n] = (seg, rc)
        if rc: print(f"  beat {n} FAILED: {err}")
        else: print(f"  beat {n} ok", flush=True)

# concat in order
listf = WORK / "concat.txt"
listf.write_text("\n".join(f"file '{results[b['n']][0]}'" for b in beats if results[b['n']][1] == 0))
final = OUT / "ig-ad-01_roughcut.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listf),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", str(final)], check=True)
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(final)],
                     capture_output=True, text=True).stdout.strip()
print(f"\nDONE -> {final}  ({dur}s)")
