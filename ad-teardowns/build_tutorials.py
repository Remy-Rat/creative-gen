#!/usr/bin/env python3
"""Index test: build Instant Gels APPLICATION + REMOVAL tutorials by retrieving the best clip per
process_step (in the approved order) and stitching with step captions. Tests process_step/method tagging."""
import json, subprocess, pathlib, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/tools')
import retrieve, sqlite3
con = sqlite3.connect(retrieve.DB); con.row_factory = sqlite3.Row
OUTDIR = pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/_tutorials'); OUTDIR.mkdir(exist_ok=True)
RAW = pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/raw')
W, H, FONT = 1080, 1920, "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
STEP_DUR = 2.8

# (caption, query). Approved process order. Pure process_step retrieval = index test.
APPLY = [
 ("Shape & file your natural nails", dict(process_step='prep_shape')),
 ("Gently push back your cuticles", dict(process_step='prep_pushback')),
 ("Lightly buff to remove shine", dict(process_step='prep_buff')),
 ("Cleanse with the prep pad", dict(process_step='prep_cleanse')),
 ("Match your size — 16 sizes included", dict(process_step='size_match')),
 ("Apply a thin, even layer of glue", dict(process_step='glue_apply')),
 ("Place at the cuticle, press centre-out", dict(process_step='position_at_cuticle')),
 ("Hold firmly for 20–30 seconds", dict(process_step='press_hold')),
 ("Done — salon-gel nails. No UV, no lamp.", dict(process_step='final_reveal', category='application')),
]
REMOVAL = [
 ("Soak in warm water + a drop of oil", dict(process_step='removal_soak')),
 ("Gently lift from the sides — never force", dict(process_step='removal_lift')),
 ("Wipe away residue, nourish with oil", dict(process_step='removal_cleanup')),
 ("Healthy natural nails — ready to reuse", dict(category='removal', keyword='healthy')),
]

def relax(q, used):
    for drop in ([], ['category'], ['keyword'], ['shade']):
        qq = {k: v for k, v in q.items() if k not in drop}
        r = retrieve.retrieve(con, exclude_clips=used, limit=1, **qq)
        if r: return r[0][0]   # (row, score) -> row
    return None

def wrap(d, t, f, m):
    out, cur = [], ""
    for w in t.split():
        s = (cur+" "+w).strip()
        if d.textlength(s, font=f) <= m: cur = s
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

def cap_png(num, total, text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    # lower-third translucent bar
    d.rectangle([0, int(H*0.74), W, int(H*0.90)], fill=(20, 12, 26, 150))
    fb = ImageFont.truetype(FONT, 34); f = ImageFont.truetype(FONT, 50)
    badge = f"STEP {num}/{total}" if num else "FINISH"
    d.text((60, int(H*0.70)), badge, font=fb, fill=(218, 186, 243, 255))
    y = int(H*0.755)
    for ln in wrap(d, text, f, W-120):
        d.text((60+2, y+2), ln, font=f, fill=(0,0,0,160)); d.text((60, y), ln, font=f, fill=(255,255,255,255)); y += 62
    img.save(path)

def render(name, steps):
    work = OUTDIR / f"{name}_work"; work.mkdir(exist_ok=True)
    used, beats = set(), []
    for i, (cap, q) in enumerate(steps, 1):
        r = relax(q, used)
        if r: used.add(r['clip_id'])
        beats.append((i, cap, r))
    def enc(args):
        i, cap, r = args; seg = work/f"seg_{i:02d}.mp4"; cp = work/f"cap_{i:02d}.png"
        num = i if i < len(steps) else 0
        cap_png(num, len(steps)-1, cap, cp)
        if not r:
            cmd = ["ffmpeg","-y","-loglevel","error","-f","lavfi","-i",f"color=c=0x6B3FA0:s={W}x{H}:d={STEP_DUR}:r=30","-i",str(cp),
                   "-filter_complex","[0:v][1:v]overlay=0:0,format=yuv420p[o]","-map","[o]","-an","-c:v","libx264","-r","30",str(seg)]
        else:
            cpath = r['path'] if pathlib.Path(r['path']).is_absolute() else str(RAW/r['path'])
            cmd = ["ffmpeg","-y","-loglevel","error","-ss",str(r['t_start']),"-i",cpath,"-i",str(cp),"-t",str(STEP_DUR),
                   "-filter_complex",f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30[v];[v][1:v]overlay=0:0,format=yuv420p[o]",
                   "-map","[o]","-an","-c:v","libx264","-r","30",str(seg)]
        subprocess.run(cmd, capture_output=True); return i, seg
    segs = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        for i, seg in ex.map(enc, beats): segs[i] = seg
    lst = work/"c.txt"; lst.write_text("\n".join(f"file '{segs[i]}'" for i,_,_ in beats))
    final = OUTDIR/f"ig-{name}.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(final)], check=True)
    print(f"{name}: " + " | ".join(f"{i}.{(pathlib.Path(r['path']).name[:18]+' ['+r['process_step']+']') if r else 'GAP'}" for i,_,r in beats))
    print(f"  -> {final}")
    return final

print("=== APPLICATION ==="); render("apply", APPLY)
print("=== REMOVAL ==="); render("removal", REMOVAL)
