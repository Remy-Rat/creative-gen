#!/usr/bin/env python3
"""TRIAL indexer for Instant Gels — one clip per folder through Gemini.

Lean on purpose: scene-detect hints (ffmpeg) -> Gemini gemini-3.5-flash (Files API) ->
JSON record (prompt-described, not a frozen responseSchema yet) -> per-clip output + cost.
Also runs a compliance check on any segment with claims/safety flags.

Run:  python3 tools/trial_index.py
Outputs JSON + a QA frame per clip into clip-library/_trial/ and prints a cost summary.
"""
import os, sys, re, json, time, pathlib, subprocess

ROOT = pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library')
RAW = ROOT / 'raw'
OUT = ROOT / '_trial'
MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash')
PRICE_IN, PRICE_OUT = 1.50, 9.00  # $ per 1M tokens

CATEGORY = {  # raw folder name -> controlled category
 '01_Hooks & Attention Clips':'hooks','02_Application':'application','03_Removal':'removal',
 '04_Product Shots':'product_shots','05_Durability':'durability',
 '06_Posing & Lifestyle':'posing_lifestyle','07. Fast Motion Edits':'fast_motion'}

def load_key():
    k=os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if k: return k
    env=ROOT/'.env'
    if env.exists():
        for ln in env.read_text().splitlines():
            if ln.strip().startswith('GEMINI_API_KEY') and '=' in ln:
                return ln.split('=',1)[1].strip().strip('"').strip("'")
    sys.exit('No GEMINI_API_KEY (see GEMINI_SETUP.md)')

def ffprobe_dur(p):
    try: return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p],capture_output=True,text=True).stdout.strip())
    except: return 0.0

def scene_cuts(p):
    """ffmpeg scene-change timestamps (boundary hints for Gemini)."""
    try:
        r=subprocess.run(['ffmpeg','-i',p,'-filter:v',"select='gt(scene,0.3)',showinfo",'-f','null','-'],
                         capture_output=True,text=True,timeout=120)
        return sorted({round(float(m),2) for m in re.findall(r'pts_time:([0-9.]+)', r.stderr)})
    except: return []

def qa_frame(p,outp,dur):
    ss=max(0.1,dur*0.45)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',str(ss),'-i',p,'-frames:v','1','-vf','scale=420:-1','-q:v','4',str(outp)],capture_output=True)

def pick_clips():
    chosen={}
    for folder,cat in CATEGORY.items():
        d=RAW/folder
        if not d.exists(): continue
        vids=sorted([f for f in d.rglob('*') if f.suffix.lower() in ('.mov','.mp4','.m4v')])
        if not vids: continue
        # for application, prefer the full-length example (best multi-segment test)
        pref=[f for f in vids if 'full length' in f.name.lower() or 'example' in f.name.lower()]
        chosen[cat]=(pref[0] if (cat=='application' and pref) else vids[0])
    return chosen

SYS = """You are indexing short vertical (9:16) ad b-roll for GLAMRDiP INSTANT GELS — pre-cured soft-gel PRESS-ON nails (NOT dip powder).
Product facts: applied by GLUE or ADHESIVE TABS; no UV/LED; ~2 weeks wear with glue; reusable; 32 shades; APEX/Zero-Edge fit; 6-layer GelStack.
Glue = ethyl-2-cyanoacrylate (safety-sensitive when shown near skin/eyes).
The NAILS ARE THE HERO — note where they sit and where text could safely go without covering them.
Most clips are silent or ASMR (no speech) — focus on visuals + satisfying sounds, don't invent a transcript.
Index editorially meaningful MOMENTS; a short single-shot clip is ONE segment. Use ONLY the controlled vocab given. If unsure, set confidence low and human_review true. Be terse and accurate."""

def build_prompt(ctx):
    return f"""CONTEXT (priors from file path — verify visually, flag mismatches):
folder_category: {ctx['category']}
shade_from_folder: {ctx['shade']}
filename: {ctx['filename']}
duration_s: {ctx['dur']}
ffmpeg_scene_cuts_s: {ctx['cuts']}

Return ONLY JSON in exactly this shape:
{{
 "clip_id": "{ctx['clip_id']}",
 "product_line": "instant_gels",
 "category": "{ctx['category']}",
 "shade": "<shade you SEE; should match shade_from_folder or flag>",
 "shade_matches_folder": true/false,
 "colour_finish": "<e.g. ruby red glossy / pearl chrome / nude>",
 "shape": "<almond|round|coffin|squoval|unknown>",
 "method": "<tabs|glue|n/a>",
 "has_speech": true/false,
 "summary": "<=18 words, what happens",
 "asmr": true/false,
 "segments": [
   {{
     "t_start": 0.0, "t_end": 0.0,
     "usable": {{"min":0.0,"max":0.0,"sweet_spot":0.0}},
     "action_climax": {{"t":0.0,"action":"<peak moment e.g. press-on snaps flush / tab peels>"}},
     "creative_role": ["<hook|reveal|demo|proof|payoff|social_proof|transition|cta_support|lifestyle|problem>"],
     "creative_stage": "<Hook|Problem|Reveal|Demo|Benefit|Proof|Transformation|Lifestyle|Offer|CTA|Transition>",
     "process_step": "<prep_shape|prep_pushback|prep_buff|prep_cleanse|size_match|tab_apply|glue_apply|position_at_cuticle|press_hold|final_reveal|removal_soak|removal_lift|removal_cleanup|reuse_clean|n/a>",
     "subject": "<single_nail|single_hand|both_hands|product|hand_and_product>",
     "framing": "<extreme_close_up|close_up|medium|wide>",
     "camera": "<static|pan|zoom_in|zoom_out|tilt|tracking|handheld>",
     "motion_level": "<still|slow|moderate|fast>",
     "setting": "<e.g. white bench|outdoors greenery|flowers|studio>",
     "nail_position": "<top|center|bottom|left|right|top_left|top_right|bottom_left|bottom_right|none>",
     "text_safe_zones": ["<top|bottom|left|right|center>"],
     "products_visible": ["<press_on_set|nailed_it_glue|adhesive_tabs|smooth_moves_file|cuticle_stick|prep_pad|kit_box|sizing_guide|remove_solution|heal_oil|none>"],
     "durability_test": "<typing|handwash|water|hammer|key|drill|screwdriver|other|none>",
     "asmr_moments": [{{"t":0.0,"desc":"<press click|soak|tap>"}}],
     "visual_fingerprint": "<short unique desc for dedup>",
     "claims_shown": ["<2_weeks_wear|chip_resistant|no_uv_no_led|press_on_and_go|reusable|vegan|tpo_free|hema_free|zero_edge|gelstack_6_layer|swap_styles|none>"],
     "safety_sensitive": true/false,
     "scores": {{"visual_quality":0,"product_visibility":0,"hook":0,"proof":0,"standalone":0,"edit_flexibility":0}},
     "search_tags": ["..."],
     "confidence": 0.0,
     "human_review": true/false
   }}
 ]
}}
Scores are 1-10 integers. Timestamps in seconds. JSON only, no prose."""

def cost(u): return (u.prompt_token_count or 0)/1e6*PRICE_IN + (u.candidates_token_count or 0)/1e6*PRICE_OUT

def main():
    from google import genai
    from google.genai import types
    client=genai.Client(api_key=load_key())
    OUT.mkdir(exist_ok=True)
    clips=pick_clips()
    print(f"Trial: {len(clips)} clips, model {MODEL}\n")
    tot_in=tot_out=0.0; tot_cost=0.0; rows=[]
    for cat,path in clips.items():
        rel=path.relative_to(RAW)
        shade=path.parent.name if path.parent.name not in CATEGORY else '-'
        clip_id='IG-'+re.sub(r'[^A-Za-z0-9]+','-',str(rel.with_suffix(''))).strip('-').lower()
        dur=ffprobe_dur(str(path))
        print(f"• {cat:16} {rel}  ({dur:.1f}s)")
        cuts=scene_cuts(str(path))
        qa_frame(str(path), OUT/(clip_id+'.jpg'), dur)
        ctx=dict(category=cat,shade=shade,filename=path.name,dur=round(dur,1),cuts=cuts,clip_id=clip_id)
        try:
            f=client.files.upload(file=str(path))
            t0=time.time()
            while f.state.name=='PROCESSING': time.sleep(2); f=client.files.get(name=f.name)
            if f.state.name!='ACTIVE':
                print(f"    upload state {f.state.name} — skipping"); continue
            resp=client.models.generate_content(model=MODEL,contents=[f,build_prompt(ctx)],
                 config=types.GenerateContentConfig(system_instruction=SYS,temperature=0.1,response_mime_type='application/json'))
            u=resp.usage_metadata; c=cost(u); tot_cost+=c
            tot_in+=u.prompt_token_count or 0; tot_out+=u.candidates_token_count or 0
            try: data=json.loads(resp.text)
            except Exception as e: data={"_parse_error":str(e),"raw":resp.text}
            # compliance pass if any claim/safety flag
            comp=None
            segs=data.get('segments',[]) if isinstance(data,dict) else []
            flagged=any(s.get('safety_sensitive') or [x for x in s.get('claims_shown',[]) if x not in('none',)] for s in segs)
            if flagged:
                cprompt=("Approved Instant Gels claims ONLY: 2_weeks_wear, chip_resistant, no_uv_no_led, press_on_and_go, "
                 "reusable, vegan, tpo_free, hema_free, zero_edge, gelstack_6_layer, swap_styles. Glue is cyanoacrylate (safety). "
                 f"For this clip's tags {json.dumps([{'claims':s.get('claims_shown'),'safety':s.get('safety_sensitive')} for s in segs])}: "
                 "is each claim visually substantiated by THIS video, and are safety flags correct? "
                 'Return JSON {"verdict":"ok|revise","issues":["..."]}.')
                cr=client.models.generate_content(model=MODEL,contents=[f,cprompt],
                   config=types.GenerateContentConfig(temperature=0.0,response_mime_type='application/json'))
                tot_cost+=cost(cr.usage_metadata); tot_in+=cr.usage_metadata.prompt_token_count or 0; tot_out+=cr.usage_metadata.candidates_token_count or 0
                try: comp=json.loads(cr.text)
                except: comp={"raw":cr.text}
            rec=dict(meta=dict(path=str(rel),category=cat,shade=shade,duration=round(dur,1),scene_cuts=cuts,
                     tokens_in=u.prompt_token_count,tokens_out=u.candidates_token_count,cost_usd=round(c,4),
                     secs=round(time.time()-t0,1)),record=data,compliance=comp)
            (OUT/(clip_id+'.json')).write_text(json.dumps(rec,indent=2))
            nseg=len(segs)
            rows.append((cat,nseg,u.prompt_token_count,u.candidates_token_count,round(c,4)))
            print(f"    -> {nseg} segment(s) | in {u.prompt_token_count} out {u.candidates_token_count} | ${c:.4f}{'  [compliance:'+str(comp.get('verdict'))+']' if comp else ''}")
        except Exception as e:
            print(f"    ERROR: {e}")
    print("\n=== TRIAL COST ===")
    print(f"clips ok: {len(rows)} | input {int(tot_in)} tok | output {int(tot_out)} tok | TOTAL ${tot_cost:.4f}")
    if rows:
        per=tot_cost/len(rows)
        print(f"avg ${per:.4f}/clip  ->  extrapolated 825 clips ≈ ${per*825:.2f}")
    print(f"outputs in {OUT}")

if __name__=='__main__':
    main()
