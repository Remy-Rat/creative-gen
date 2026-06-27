#!/usr/bin/env python3
"""Instant Gels indexer — scene-hint + Gemini gemini-3.5-flash + compliance check -> SQLite + JSON sidecars.

  python3 tools/index.py --sample 24      # diverse validation batch
  python3 tools/index.py --all            # full library (resume-safe; skips already indexed)
  python3 tools/index.py --all --force    # re-index everything
  options: --workers N (default 5)

Writes: index.db (videos+segments tables) and videos/<clip_id>.json sidecars.
"""
import os, sys, re, json, time, sqlite3, pathlib, subprocess, argparse, threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as CFTimeout

ROOT = pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library')
RAW = ROOT/'raw'; SIDE = ROOT/'videos'; DB = ROOT/'index.db'
MODEL = os.environ.get('GEMINI_MODEL','gemini-3.5-flash')
PRICE_IN, PRICE_OUT = 1.50, 9.00
CATEGORY = {'01_Hooks & Attention Clips':'hooks','02_Application':'application','03_Removal':'removal',
 '04_Product Shots':'product_shots','05_Durability':'durability','06_Posing & Lifestyle':'posing_lifestyle','07. Fast Motion Edits':'fast_motion'}
VIDEXT = ('.mov','.mp4','.m4v','.webm')

def load_key():
    k=os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if k: return k
    env=ROOT/'.env'
    if env.exists():
        for ln in env.read_text().splitlines():
            if ln.strip().startswith('GEMINI_API_KEY') and '=' in ln: return ln.split('=',1)[1].strip().strip('"\'')
    sys.exit('No GEMINI_API_KEY')

def dur(p):
    try: return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p],capture_output=True,text=True).stdout.strip())
    except: return 0.0
def cuts(p):
    try:
        r=subprocess.run(['ffmpeg','-i',p,'-filter:v',"select='gt(scene,0.3)',showinfo",'-f','null','-'],capture_output=True,text=True,timeout=150)
        return sorted({round(float(m),2) for m in re.findall(r'pts_time:([0-9.]+)',r.stderr)})
    except: return []

SYS=("You index short 9:16 ad b-roll for GLAMRDiP INSTANT GELS — pre-cured soft-gel PRESS-ON nails (NOT dip). "
 "Applied by GLUE or TABS; no UV/LED; ~2wk wear w/ glue; reusable; 32 shades; APEX/Zero-Edge; 6-layer GelStack. "
 "Glue=cyanoacrylate (safety-sensitive near skin/eyes). THE NAILS ARE THE HERO — record where they sit and where text can go without covering them. "
 "Most clips are silent/ASMR — focus on visuals + sounds, never invent a transcript. Index editorially meaningful MOMENTS; a short single-shot clip is ONE segment. "
 "Use ONLY the controlled vocab. IMPORTANT: only put a value in claims_shown if THIS footage VISUALLY DEMONSTRATES it (e.g. a wear/durability test, glue-and-press for press_on_and_go). Do NOT infer claims from packaging text alone or from the product merely looking nice. "
 "If unsure set confidence low and human_review true. Terse, accurate.")

def prompt(c):
    return (f"CONTEXT (path priors — verify visually): category={c['category']} | shade_from_folder={c['shade']} | filename={c['filename']} | duration_s={c['dur']} | scene_cuts_s={c['cuts']}\n"
 "Return ONLY JSON: {\n"
 f' "clip_id":"{c["clip_id"]}","product_line":"instant_gels","category":"{c["category"]}",\n'
 ' "shade":"<shade NAME you see>","shade_matches_folder":<does the shade NAME match shade_from_folder? true/false>,\n'
 ' "colour_finish":"<visual desc e.g. ruby red glossy / pearl chrome / nude>","shape":"<almond|round|coffin|squoval|unknown>",\n'
 ' "method":"<tabs|glue|n/a>","has_speech":<bool>,"summary":"<=18 words","asmr":<bool>,\n'
 ' "segments":[{\n'
 '  "t_start":0.0,"t_end":0.0,"usable":{"min":0.0,"max":0.0,"sweet_spot":0.0},\n'
 '  "action_climax":{"t":0.0,"action":"<peak moment>"},\n'
 '  "creative_role":["<hook|reveal|demo|proof|payoff|social_proof|transition|cta_support|lifestyle|problem>"],\n'
 '  "creative_stage":"<Hook|Problem|Reveal|Demo|Benefit|Proof|Transformation|Lifestyle|Offer|CTA|Transition>",\n'
 '  "process_step":"<prep_shape|prep_pushback|prep_buff|prep_cleanse|size_match|tab_apply|glue_apply|position_at_cuticle|press_hold|final_reveal|removal_soak|removal_lift|removal_cleanup|reuse_clean|n/a>",\n'
 '  "subject":"<single_nail|single_hand|both_hands|product|hand_and_product>","framing":"<extreme_close_up|close_up|medium|wide>",\n'
 '  "camera":"<static|pan|zoom_in|zoom_out|tilt|tracking|handheld>","motion_level":"<still|slow|moderate|fast>","setting":"<short>",\n'
 '  "nail_position":"<top|center|bottom|left|right|top_left|top_right|bottom_left|bottom_right|none>","text_safe_zones":["<top|bottom|left|right|center>"],\n'
 '  "products_visible":["<press_on_set|nailed_it_glue|adhesive_tabs|smooth_moves_file|cuticle_stick|prep_pad|kit_box|sizing_guide|remove_solution|heal_oil|none>"],\n'
 '  "durability_test":"<typing|handwash|water|hammer|key|drill|screwdriver|other|none>","asmr_moments":[{"t":0.0,"desc":"<short>"}],\n'
 '  "visual_fingerprint":"<short unique desc>","claims_shown":["<only if VISUALLY DEMONSTRATED: 2_weeks_wear|chip_resistant|no_uv_no_led|press_on_and_go|reusable|zero_edge|swap_styles|none>"],\n'
 '  "safety_sensitive":<bool>,"scores":{"visual_quality":0,"product_visibility":0,"hook":0,"proof":0,"standalone":0,"edit_flexibility":0},\n'
 '  "search_tags":["..."],"confidence":0.0,"human_review":<bool>\n'
 ' }]\n}\nScores 1-10 ints. Seconds. JSON only.')

def cost(u): return (u.prompt_token_count or 0)/1e6*PRICE_IN+(u.candidates_token_count or 0)/1e6*PRICE_OUT

def retry(fn,n=6):
    for i in range(n):
        try: return fn()
        except Exception as e:
            msg=str(e)
            if i==n-1 or not any(x in msg for x in('503','UNAVAILABLE','429','RESOURCE_EXHAUSTED','500','deadline','timeout','overloaded')): raise
            time.sleep(min(20,3*2**i))

def all_videos():
    v=[]
    for folder,cat in CATEGORY.items():
        d=RAW/folder
        if d.exists(): v+=[(cat,f) for f in sorted(d.rglob('*')) if f.suffix.lower() in VIDEXT]
    return v
def sample(n):
    by={}
    for cat,f in all_videos(): by.setdefault((cat,f.parent.name),[]).append(f)
    keys=sorted(by); out=[]; i=0
    while len(out)<n and any(by.values()):
        k=keys[i%len(keys)]
        if by[k]: out.append((k[0],by[k].pop(0)))
        i+=1
        if i>len(keys)*40: break
    return out[:n]

def init_db():
    SIDE.mkdir(exist_ok=True)
    cx=sqlite3.connect(DB)
    cx.executescript("""
    CREATE TABLE IF NOT EXISTS videos(clip_id TEXT PRIMARY KEY,path TEXT,category TEXT,shade TEXT,shade_match INT,
      colour_finish TEXT,shape TEXT,method TEXT,asmr INT,summary TEXT,duration REAL,n_segments INT,
      tokens_in INT,tokens_out INT,cost REAL,compliance TEXT,indexed_at TEXT,json TEXT);
    CREATE TABLE IF NOT EXISTS segments(seg_id TEXT PRIMARY KEY,clip_id TEXT,t_start REAL,t_end REAL,
      role TEXT,stage TEXT,process_step TEXT,framing TEXT,camera TEXT,motion TEXT,nail_position TEXT,
      text_safe TEXT,colour_finish TEXT,products TEXT,claims TEXT,safety INT,durability_test TEXT,
      climax_t REAL,climax TEXT,fingerprint TEXT,vis_quality INT,hook INT,proof INT,confidence REAL,human_review INT);
    """)
    cx.commit(); return cx

def index_one(client,types,cat,path):
    rel=path.relative_to(RAW); shade=path.parent.name if path.parent.name not in CATEGORY else '-'
    cid='IG-'+re.sub(r'[^A-Za-z0-9]+','-',str(rel.with_suffix(''))).strip('-').lower()
    d=dur(str(path)); c=dict(category=cat,shade=shade,filename=path.name,dur=round(d,1),cuts=cuts(str(path)),clip_id=cid)
    f=retry(lambda:client.files.upload(file=str(path)))
    try:
        waited=0
        while f.state.name=='PROCESSING' and waited<90: time.sleep(2); waited+=2; f=client.files.get(name=f.name)
        if f.state.name!='ACTIVE': raise RuntimeError('upload '+f.state.name)
        r=retry(lambda:client.models.generate_content(model=MODEL,contents=[f,prompt(c)],
           config=types.GenerateContentConfig(system_instruction=SYS,temperature=0.1,response_mime_type='application/json')))
        tin=r.usage_metadata.prompt_token_count or 0; tout=r.usage_metadata.candidates_token_count or 0; cst=cost(r.usage_metadata)
        try: data=json.loads(r.text)
        except Exception as e: data={'_parse_error':str(e),'raw':r.text}
        segs=[s for s in (data.get('segments',[]) if isinstance(data,dict) else []) if isinstance(s,dict)]
        comp=None
        if any(s.get('safety_sensitive') or [x for x in s.get('claims_shown',[]) if x!='none'] for s in segs):
            cp=("Approved IG claims ONLY: 2_weeks_wear,chip_resistant,no_uv_no_led,press_on_and_go,reusable,zero_edge,swap_styles. "
                "Glue=cyanoacrylate. Mark verdict 'revise' ONLY if a tagged claim is NOT visually demonstrated by THIS video or a safety flag is wrong; else 'ok'. "
                f"Tags: {json.dumps([{'claims':s.get('claims_shown'),'safety':s.get('safety_sensitive')} for s in segs])}. "
                'Return JSON {"verdict":"ok|revise","issues":[]}.')
            cr=retry(lambda:client.models.generate_content(model=MODEL,contents=[f,cp],config=types.GenerateContentConfig(temperature=0.0,response_mime_type='application/json')))
            tin+=cr.usage_metadata.prompt_token_count or 0; tout+=cr.usage_metadata.candidates_token_count or 0; cst+=cost(cr.usage_metadata)
            try: comp=json.loads(cr.text)
            except: comp={'raw':cr.text}
        return dict(cid=cid,rel=str(rel),cat=cat,shade=shade,dur=round(d,1),data=data,comp=comp,tin=tin,tout=tout,cost=cst)
    finally:
        try: client.files.delete(name=f.name)   # always free storage, even on error
        except: pass

def save(cx,res):
    raw=res['data']; cid=res['cid']; d=raw if isinstance(raw,dict) else {}
    segs=[s for s in d.get('segments',[]) if isinstance(s,dict)]
    sidecar=dict(meta=dict(path=res['rel'],category=res['cat'],shade=res['shade'],duration=res['dur'],
        tokens_in=res['tin'],tokens_out=res['tout'],cost=round(res['cost'],4)),record=raw,compliance=res['comp'])
    (SIDE/(cid+'.json')).write_text(json.dumps(sidecar,indent=2))
    cx.execute("INSERT OR REPLACE INTO videos VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(cid,res['rel'],res['cat'],
        d.get('shade'),1 if d.get('shade_matches_folder') else 0,d.get('colour_finish'),d.get('shape'),d.get('method'),
        1 if d.get('asmr') else 0,d.get('summary'),res['dur'],len(segs),res['tin'],res['tout'],round(res['cost'],4),
        json.dumps(res['comp']) if res['comp'] else None,time.strftime('%Y-%m-%dT%H:%M:%S'),json.dumps(raw)))
    cx.execute("DELETE FROM segments WHERE clip_id=?",(cid,))
    for i,s in enumerate(segs):
        try:
            sc=s.get('scores') if isinstance(s.get('scores'),dict) else {}
            cl=s.get('action_climax') if isinstance(s.get('action_climax'),dict) else {}
            cx.execute("INSERT OR REPLACE INTO segments VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
             (f"{cid}-s{i+1:02d}",cid,s.get('t_start'),s.get('t_end'),json.dumps(s.get('creative_role')),s.get('creative_stage'),
              s.get('process_step'),s.get('framing'),s.get('camera'),s.get('motion_level'),s.get('nail_position'),
              json.dumps(s.get('text_safe_zones')),s.get('colour_finish') or d.get('colour_finish'),json.dumps(s.get('products_visible')),
              json.dumps(s.get('claims_shown')),1 if s.get('safety_sensitive') else 0,s.get('durability_test'),
              cl.get('t'),cl.get('action'),s.get('visual_fingerprint'),sc.get('visual_quality'),sc.get('hook'),sc.get('proof'),
              s.get('confidence'),1 if s.get('human_review') else 0))
        except Exception:
            continue
    cx.commit()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--sample',type=int); ap.add_argument('--all',action='store_true')
    ap.add_argument('--workers',type=int,default=6); ap.add_argument('--force',action='store_true')
    ap.add_argument('--limit',type=int); ap.add_argument('--budget',type=int,default=240)
    a=ap.parse_args()
    from google import genai; from google.genai import types
    client=genai.Client(api_key=load_key()); cx=init_db()
    done=set(r[0] for r in cx.execute("SELECT clip_id FROM videos")) if not a.force else set()
    items=all_videos() if a.all else sample(a.sample or 12)
    def cid_of(p): return 'IG-'+re.sub(r'[^A-Za-z0-9]+','-',str(p.relative_to(RAW).with_suffix(''))).strip('-').lower()
    items=[(c,p) for c,p in items if cid_of(p) not in done]
    if a.limit: items=items[:a.limit]
    print(f"model {MODEL} | {len(items)} clips this pass | {a.workers} workers | resume-skip {len(done)} | budget {a.budget}s")
    tin=tout=tc=0.0; ok=err=0; lock=threading.Lock()
    ex=ThreadPoolExecutor(max_workers=a.workers)
    futs={ex.submit(index_one,client,types,c,p):(c,p) for c,p in items}
    try:
        for fut in as_completed(futs, timeout=a.budget):
            c,p=futs[fut]
            try:
                res=fut.result()
                with lock:
                    save(cx,res); ok+=1; tin+=res['tin']; tout+=res['tout']; tc+=res['cost']
                    v=res['comp'].get('verdict') if res['comp'] else ''
                    print(f"  [{ok}] {res['cat']:15} {pathlib.Path(res['rel']).name[:34]:34} {len(res['data'].get('segments',[]))}seg ${res['cost']:.4f} {v}",flush=True)
            except Exception as e:
                with lock: err+=1; print(f"  ERR {p.name[:40]}: {e}",flush=True)
    except CFTimeout:
        print(f"  [budget {a.budget}s hit — {ok} saved this pass; rest resumes next pass]",flush=True)
    print(f"PASS ok={ok} err={err} | ${tc:.4f}",flush=True)
    sys.stdout.flush()
    os._exit(0)   # hard exit so hung upload threads can't block shutdown

if __name__=='__main__': main()
