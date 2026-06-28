#!/usr/bin/env python3
"""IG-AD-01 v1: beats re-timed to the VO (proportional to each line's length until we have word-level
timestamps), clips/captions burned, VO muxed. Gap beats remain lilac slates. `python3 render_v1.py`"""
import json, subprocess, pathlib
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent; OUT = HERE / 'output'
RAW = pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/raw')
WORK = OUT / 'v1_work'; WORK.mkdir(parents=True, exist_ok=True)
VO = pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/vo/output/tts_I_gav_20260628_133410.mp3')
W, H = 1080, 1920; FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"; LILAC = "0x6B3FA0"
man = json.loads((OUT / 'ig-ad-01.manifest.json').read_text())

def ffdur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],
                                capture_output=True,text=True).stdout.strip() or 0)

def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t=(cur+" "+w).strip()
        if d.textlength(t,font=font)<=maxw: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines

def caption_png(text, path, gap=False):
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img); f=ImageFont.truetype(FONT,60)
    y=int(H*0.10)
    for ln in wrap(d,text,f,W-160):
        tw=d.textlength(ln,font=f); x=(W-tw)/2
        d.text((x+3,y+3),ln,font=f,fill=(0,0,0,160)); d.text((x,y),ln,font=f,fill=(255,255,255,255)); y+=74
    if gap:
        fb=ImageFont.truetype(FONT,70); fs=ImageFont.truetype(FONT,38)
        for t,fo,yy,al in [("[ B-ROLL ]",fb,0.46,230),("to generate (Higgsfield)",fs,0.46,180)]:
            tw=d.textlength(t,font=fo); d.text(((W-tw)/2,H*yy+(0 if fo is fb else 86)),t,font=fo,fill=(255,255,255,al))
    img.save(path)

# re-time beats to VO (proportional to line length); end-card (no VO) fixed 3.0s
vo_dur = ffdur(VO)
spoken = [b for b in man['beats'] if b['vo'].strip()]
tot = sum(len(b['vo']) for b in spoken)
for b in man['beats']:
    b['_dur'] = round(vo_dur*len(b['vo'])/tot, 2) if b['vo'].strip() else 3.0

def encode(beat):
    n=beat['n']; dur=beat['_dur']; seg=WORK/f"seg_{n:02d}.mp4"; cap=WORK/f"cap_{n:02d}.png"
    caption_png(beat['caption'], cap, gap=beat['broll_gap'])
    if beat['broll_gap'] or not beat.get('clip'):
        cmd=["ffmpeg","-y","-loglevel","error","-f","lavfi","-i",f"color=c={LILAC}:s={W}x{H}:d={dur}:r=30",
             "-i",str(cap),"-filter_complex","[0:v][1:v]overlay=0:0,format=yuv420p[o]","-map","[o]","-an",
             "-c:v","libx264","-r","30",str(seg)]
    else:
        c=beat['clip']; cp=c['path'] if pathlib.Path(c['path']).is_absolute() else str(RAW/c['path'])
        cmd=["ffmpeg","-y","-loglevel","error","-ss",str(c['t_in']),"-i",cp,"-i",str(cap),"-t",str(dur),
             "-filter_complex",f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30[v];[v][1:v]overlay=0:0,format=yuv420p[o]",
             "-map","[o]","-an","-c:v","libx264","-r","30",str(seg)]
    rc=subprocess.run(cmd,capture_output=True,text=True).returncode
    return n,seg,rc

print(f"VO {vo_dur}s -> re-timing {len(spoken)} spoken beats; encoding (parallel)...")
res={}
with ThreadPoolExecutor(max_workers=6) as ex:
    for n,seg,rc in ex.map(encode, man['beats']):
        res[n]=(seg,rc); print(f"  beat {n} {'ok' if rc==0 else 'FAIL'}",flush=True)
listf=WORK/"concat.txt"; listf.write_text("\n".join(f"file '{res[b['n']][0]}'" for b in man['beats'] if res[b['n']][1]==0))
silent=WORK/"silent.mp4"
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(listf),"-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(silent)],check=True)
final=OUT/"ig-ad-01_v1.mp4"
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(silent),"-i",str(VO),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k",str(final)],check=True)
print(f"DONE -> {final}  ({ffdur(final)}s, with VO)")
