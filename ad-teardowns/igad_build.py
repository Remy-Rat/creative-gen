#!/usr/bin/env python3
"""Build the Instant Gel test-script ad: beats re-timed to the per-line VO, multi-cut where scripted,
caption styles per the script (magenta hook/CTA, white body, red ✗, ♻ recycle, red end card), clips from
the index (slates where we lack footage), then mux the full VO. Output ad-teardowns/output/igad_v1.mp4."""
import json, subprocess, pathlib, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,'/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/tools')
import retrieve, sqlite3
con=sqlite3.connect(retrieve.DB); con.row_factory=sqlite3.Row
OUT=pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/ad-teardowns/output')
RAW=pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/raw')
VO=pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/vo/output/igad_full_vo.mp3')
TIM={d['seg']:d for d in json.loads((pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/vo/output/igad_vo_timing.json')).read_text())}
WORK=OUT/'igad_work'; WORK.mkdir(parents=True,exist_ok=True)
W,H,FONT="1080","1920","/System/Library/Fonts/Supplemental/Arial Bold.ttf"; Wi,Hi=1080,1920
def F(s): return ImageFont.truetype(FONT,s)
def relax(q,used):
    for drop in ([],['shade'],['keyword'],['category']):
        r=retrieve.retrieve(con,exclude_clips=used,limit=1,**{k:v for k,v in q.items() if k not in drop})
        if r: return r[0][0]
    return None
def wrap(d,t,f,m):
    o,c=[],""
    for w in t.split():
        s=(c+" "+w).strip()
        if d.textlength(s,font=f)<=m: c=s
        else: o.append(c); c=w
    if c:o.append(c)
    return o
def center(d,lines,f,y,fill,outline=None):
    for ln in lines:
        tw=d.textlength(ln,font=f); x=(Wi-tw)/2
        if outline:
            for dx in(-3,0,3):
                for dy in(-3,0,3): d.text((x+dx,y+dy),ln,font=f,fill=outline)
        d.text((x,y),ln,font=f,fill=fill); y+=f.size+12
    return y
def cap_png(style,text,path):
    img=Image.new("RGBA",(Wi,Hi),(0,0,0,0)); d=ImageDraw.Draw(img); f=F(64)
    if style=="magenta":
        lines=wrap(d,text,f,Wi-260); bh=len(lines)*(f.size+12)+60; y0=int(Hi*0.40)
        d.rounded_rectangle([90,y0,Wi-90,y0+bh],40,fill=(214,20,140,235))
        center(d,lines,f,y0+30,(255,255,255,255))
    elif style=="white":
        f=F(60); lines=wrap(d,text,f,Wi-160); center(d,lines,f,int(Hi*0.12),(255,255,255,255),outline=(0,0,0,210))
    elif style=="label":
        f=F(96); center(d,wrap(d,text,f,Wi-160),f,int(Hi*0.44),(255,255,255,255),outline=(0,0,0,220))
    elif style=="redx":
        f=F(72); center(d,wrap(d,text,f,Wi-200),f,int(Hi*0.62),(255,255,255,255),outline=(0,0,0,200))
        cx,cy,s=Wi//2,int(Hi*0.34),150
        for off in(-10,0,10):
            d.line([(cx-s+off,cy-s),(cx+s+off,cy+s)],fill=(229,30,40,255),width=26)
            d.line([(cx-s+off,cy+s),(cx+s+off,cy-s)],fill=(229,30,40,255),width=26)
    elif style=="recycle":
        f=F(58); tw=d.textlength("♻ 100% REUSABLE",font=f) if False else d.textlength("100% REUSABLE",font=f)
        d.rounded_rectangle([(Wi-tw-120)/2,int(Hi*0.12),(Wi+tw+120)/2,int(Hi*0.12)+110],55,fill=(31,122,90,235))
        center(d,["100% REUSABLE"],f,int(Hi*0.12)+28,(255,255,255,255))
    elif style=="endcard":
        f=F(66); center(d,wrap(d,text,f,Wi-180),f,int(Hi*0.34),(255,255,255,255))
    img.save(path)

HERO="Bubbly Babe"
# SUBS: (seg, style, caption, kind) kind=('q',{...}) or ('gap', bg) or ('endcard', None)
S=[
 (1,"magenta","Beautiful nails. Zero stress. Under 10 minutes.",("q",dict(role='demo',category='application',shade=HERO))),
 (2,"redx","Nail polish",("gap","0x1b1020")),(2,"redx","Shellac",("gap","0x1b1020")),(2,"redx","Acrylic",("gap","0x1b1020")),
 (2,"redx","UV light",("gap","0x1b1020")),(2,"redx","Chemicals & filing",("gap","0x1b1020")),
 (3,"white","“I've tried everything... and failed at everything.”",("gap","0x241a2c")),
 (4,"white","The innovation revolutionizing manicures",("q",dict(role='reveal',category='posing_lifestyle',shade=HERO))),
 (4,"white","Instant Gels from GLAMRDiP",("q",dict(role='reveal',category='product_shots'))),
 (5,"label","Blaze Babe",("q",dict(role='lifestyle',category='posing_lifestyle',shade='Blaze Babe'))),
 (5,"label","Forever French",("q",dict(role='lifestyle',category='posing_lifestyle',shade='Forever French'))),
 (5,"label","Chrome Kisses",("q",dict(role='lifestyle',category='posing_lifestyle',shade='Chrome Kisses'))),
 (6,"redx","Cheap plastic",("gap","0x1b1020")),
 (6,"white","Zero damage to your natural nails",("q",dict(category='removal',keyword='healthy'))),
 (6,"recycle","",("q",dict(role='reveal',category='product_shots'))),
 (7,"white","Apply the adhesive sticker",("q",dict(process_step='glue_apply'))),
 (7,"white","Press on",("q",dict(process_step='press_hold'))),
 (7,"white","Done — a perfect manicure that lasts weeks",("q",dict(process_step='final_reveal',category='application',shade=HERO))),
 (8,"white","Removal is super easy",("q",dict(process_step='removal_soak'))),
 (8,"white","Soak & gently lift",("q",dict(process_step='removal_lift'))),
 (8,"white","Reuse them again and again",("q",dict(category='product_shots'))),
 (9,"white","Join the manicure revolution",("q",dict(role='reveal',category='posing_lifestyle',shade=HERO))),
 (9,"endcard","Salon-Perfect Nails in Minutes.  Try GLAMRDiP Today!   +1 FREE DESIGN   ·   -20% OFF",("end","0xc81e3c")),
]
# durations: split each segment's VO dur equally across its subs
from collections import Counter
cnt=Counter(s[0] for s in S)
used=set(); beats=[]
for i,(seg,style,text,(kind,payload)) in enumerate(S):
    dur=round(TIM[seg]['dur']/cnt[seg],2); clip=None
    if kind=="q":
        clip=relax(payload,used)
        if clip: used.add(clip['clip_id'])
    beats.append(dict(i=i,seg=seg,style=style,text=text,kind=kind,payload=payload,dur=max(0.4,dur),clip=clip))

BROLL={"Nail polish":"polish","Shellac":"shellac","Acrylic":"acrylic","UV light":"uvlamp","Chemicals & filing":"filing","Cheap plastic":"cheapplastic"}
BR=pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/generated/broll')
vo_total=round(sum(TIM[s]['dur'] for s in TIM),2)
beats[-1]['dur']=round(beats[-1]['dur']+max(0.0,vo_total-sum(b['dur'] for b in beats)),2)  # pad tail to VO length
def enc(b):
    i=b['i']; seg=WORK/f"s_{i:02d}.mp4"; cp=WORK/f"c_{i:02d}.png"; cap_png(b['style'],b['text'],cp); dur=b['dur']
    bg = b['payload'] if b['kind'] in("gap","end") else None
    brimg = BR/(BROLL[b['text']]+'.png') if (b['kind']=='gap' and b['text'] in BROLL) else None
    if brimg and brimg.exists():
        cmd=["ffmpeg","-y","-loglevel","error","-loop","1","-t",str(dur),"-i",str(brimg),"-i",str(cp),
             "-filter_complex",f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30[v];[v][1:v]overlay=0:0,format=yuv420p[o]",
             "-map","[o]","-an","-c:v","libx264","-r","30",str(seg)]
        for _ in range(2):
            subprocess.run(cmd,capture_output=True)
            if seg.exists() and seg.stat().st_size>0: break
        return i,seg
    if b['clip']:
        cpath=b['clip']['path'] if pathlib.Path(b['clip']['path']).is_absolute() else str(RAW/b['clip']['path'])
        cmd=["ffmpeg","-y","-loglevel","error","-ss",str(b['clip']['t_start']),"-i",cpath,"-i",str(cp),"-t",str(dur),
             "-filter_complex",f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30[v];[v][1:v]overlay=0:0,format=yuv420p[o]",
             "-map","[o]","-an","-c:v","libx264","-r","30",str(seg)]
    else:
        cmd=["ffmpeg","-y","-loglevel","error","-f","lavfi","-i",f"color=c={bg or '0x1b1020'}:s={W}x{H}:d={dur}:r=30","-i",str(cp),
             "-filter_complex","[0:v][1:v]overlay=0:0,format=yuv420p[o]","-map","[o]","-an","-c:v","libx264","-r","30",str(seg)]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if not (seg.exists() and seg.stat().st_size>0):
        (WORK/f"err_{i:02d}.txt").write_text(" ".join(str(x) for x in cmd)+"\n\n"+(r.stderr or "")[-1200:])
    return i,seg
segs={}
with ThreadPoolExecutor(max_workers=4) as ex:
    for i,seg in ex.map(enc,beats): segs[i]=seg
missing=[b['i'] for b in beats if not (WORK/f"s_{b['i']:02d}.mp4").exists()]
assert not missing, f"segments failed to encode: {missing}"
lst=WORK/"c.txt"; lst.write_text("\n".join(f"file '{segs[b['i']]}'" for b in beats))
silent=WORK/"silent.mp4"
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(silent)],check=True)
# --- mix VO + SFX (pop on red-X/text reveals, ding on recycle) ---
sfxf=sorted((OUT/'sfx').glob('sfx_*.mp3')); POP=str(sfxf[0]); DING=str(sfxf[1])
pops=[]; dings=[]; t=0.0
for b in beats:
    if b['style'] in('redx','magenta','endcard'): pops.append(round(t,2))
    elif b['style']=='recycle': dings.append(round(t,2))
    t+=b['dur']
fc=[]; labels=["[1:a]"]
if pops:
    fc.append("[2:a]asplit="+str(len(pops))+''.join(f"[p{i}]" for i in range(len(pops))))
    for i,s in enumerate(pops): ms=int(s*1000); fc.append(f"[p{i}]adelay={ms}|{ms},volume=0.5[pp{i}]"); labels.append(f"[pp{i}]")
if dings:
    fc.append("[3:a]asplit="+str(len(dings))+''.join(f"[g{i}]" for i in range(len(dings))))
    for i,s in enumerate(dings): ms=int(s*1000); fc.append(f"[g{i}]adelay={ms}|{ms},volume=0.5[gg{i}]"); labels.append(f"[gg{i}]")
fc.append(''.join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0[a]")
final=OUT/"igad_v2.mp4"
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(silent),"-i",str(VO),"-i",POP,"-i",DING,
                "-filter_complex",";".join(fc),"-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k",str(final)],check=True)
d=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(final)],capture_output=True,text=True).stdout.strip()
print(f"pops@{pops} dings@{dings}")
gaps=sum(1 for b in beats if not b['clip'] and b['kind']!='end')
print(f"{len(beats)} sub-beats | {gaps} slates | -> {final} ({d}s, with VO)")
for b in beats:
    print(f"  seg{b['seg']} {b['dur']}s [{b['style']}] {(b['clip']['path'].split('/')[-1][:22]+' ['+(b['clip']['process_step'] or b['clip']['category'])+']') if b['clip'] else 'SLATE'} | {b['text'][:30]}")
