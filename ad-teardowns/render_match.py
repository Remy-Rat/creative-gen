#!/usr/bin/env python3
"""Render IG-AD-02 at the teardown's EXACT beat durations (silent) for side-by-side QA."""
import json, subprocess, pathlib
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
OUT = pathlib.Path(__file__).parent / 'output'
RAW = pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/raw')
WORK = OUT / 'v2_work'; WORK.mkdir(parents=True, exist_ok=True)
W,H=1080,1920; FONT="/System/Library/Fonts/Supplemental/Arial Bold.ttf"; LILAC="0x6B3FA0"
man=json.loads((OUT/'ig-ad-02.manifest.json').read_text())
def wrap(d,t,f,m):
    out,cur=[],""
    for w in t.split():
        s=(cur+" "+w).strip()
        if d.textlength(s,font=f)<=m: cur=s
        else: out.append(cur); cur=w
    if cur: out.append(cur)
    return out
def cap_png(text,path,gap=False):
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img); f=ImageFont.truetype(FONT,58); y=int(H*0.10)
    for ln in wrap(d,text,f,W-160):
        tw=d.textlength(ln,font=f); x=(W-tw)/2
        d.text((x+3,y+3),ln,font=f,fill=(0,0,0,160)); d.text((x,y),ln,font=f,fill=(255,255,255,255)); y+=72
    if gap:
        fb=ImageFont.truetype(FONT,68); fs=ImageFont.truetype(FONT,36)
        for t,fo,off,al in [("[ B-ROLL ]",fb,0,230),("to generate",fs,86,180)]:
            tw=d.textlength(t,font=fo); d.text(((W-tw)/2,H*0.46+off),t,font=fo,fill=(255,255,255,al))
    img.save(path)
def enc(b):
    n=b['n']; dur=max(0.3,b['dur']); seg=WORK/f"seg_{n:02d}.mp4"; cap=WORK/f"cap_{n:02d}.png"
    cap_png(b['caption'],cap,gap=b['broll_gap'])
    if b['broll_gap'] or not b.get('clip'):
        cmd=["ffmpeg","-y","-loglevel","error","-f","lavfi","-i",f"color=c={LILAC}:s={W}x{H}:d={dur}:r=30","-i",str(cap),
             "-filter_complex","[0:v][1:v]overlay=0:0,format=yuv420p[o]","-map","[o]","-an","-c:v","libx264","-r","30",str(seg)]
    else:
        c=b['clip']; cp=c['path'] if pathlib.Path(c['path']).is_absolute() else str(RAW/c['path'])
        cmd=["ffmpeg","-y","-loglevel","error","-ss",str(c['t_in']),"-i",cp,"-i",str(cap),"-t",str(dur),
             "-filter_complex",f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30[v];[v][1:v]overlay=0:0,format=yuv420p[o]",
             "-map","[o]","-an","-c:v","libx264","-r","30",str(seg)]
    return n,seg,subprocess.run(cmd,capture_output=True,text=True).returncode
res={}
with ThreadPoolExecutor(max_workers=6) as ex:
    for n,seg,rc in ex.map(enc,man['beats']):
        res[n]=(seg,rc)
        if rc: print(f"beat {n} FAIL")
lst=WORK/"c.txt"; lst.write_text("\n".join(f"file '{res[b['n']][0]}'" for b in man['beats'] if res[b['n']][1]==0))
final=OUT/"ig-ad-02_match.mp4"
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(final)],check=True)
dur=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(final)],capture_output=True,text=True).stdout.strip()
print(f"DONE -> {final} ({dur}s)")
