#!/usr/bin/env python3
"""Ad teardown: feed a reference ad to Gemini -> exhaustive timestamped spec for replication.
Captures every shot, caption, animation, SFX, VO line, transition, cut rhythm + a brand-agnostic
structure template we refill with our own footage/copy. `python3 teardown.py <video> [name]`."""
import sys, os, re, json, time, pathlib
KEYENV = pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/.env')
OUT = pathlib.Path(__file__).parent / 'output'
MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash')

def load_key():
    k = os.environ.get('GEMINI_API_KEY')
    if k: return k
    for ln in KEYENV.read_text().splitlines():
        if ln.startswith('GEMINI_API_KEY') and '=' in ln:
            return ln.split('=', 1)[1].strip().strip('"\'')
    sys.exit('no GEMINI_API_KEY')

def retry(fn, n=6):
    for i in range(n):
        try: return fn()
        except Exception as e:
            if i == n-1 or not any(x in str(e) for x in ('503','UNAVAILABLE','429','RESOURCE_EXHAUSTED','500','overloaded','deadline','timeout')): raise
            time.sleep(min(20, 3*2**i))

PROMPT = """You are a senior short-form ad editor reverse-engineering this vertical ad so we can rebuild an ad in the
EXACT same format/technique with our own footage and original copy. Be exhaustive and precise — timestamps to 0.1s.
Watch every frame and listen to all audio. Return ONLY JSON in this shape:
{
 "meta":{"duration_s":0,"aspect":"9:16","total_cuts":0,"avg_shot_len_s":0,"pace":"slow|medium|fast",
   "overall_style":"","color_grade":"","music_style":"","vo_voice_feel":"(gender/accent/age/tone/energy)"},
 "hook":{"first_1_5s":"what literally happens in the first 1.5s","technique":"the hook mechanism","why_it_works":""},
 "persuasion_arc":["ordered creative stages, e.g. Hook -> Problem -> ... -> CTA"],
 "timeline":[{"idx":1,"t_start":0.0,"t_end":0.0,"dur":0.0,
   "shot":"detailed visual of what's on screen","subject":"","framing":"ecu|cu|med|wide","camera":"static|push|pan|handheld|zoom",
   "type":"talking_head|b_roll|product|text_card|ugc",
   "on_screen_text":{"text":"exact words shown","style":"font feel/weight/case","color":"","position":"top|center|lower-third|...","animation_in":"","animation_out":"","sync":"word-by-word|line|static"},
   "vo_line":"exact spoken words this beat","vo_delivery":"tone/pace/emphasis",
   "sfx":[{"t":0.0,"sound":""}],"music_note":"what the music is doing (build/drop/quiet)",
   "transition_to_next":"hard cut|flash|whip|fade|none","cut_length_s":0.0,
   "replication_note":"how to recreate this beat with our footage"}],
 "caption_system":{"font_feel":"","weight":"","case":"","color":"","stroke_shadow":"","position":"","animation_pattern":"","sync_style":""},
 "sound_design":{"music":"","sfx_inventory":["each distinct SFX heard"],"mix_notes":"vo vs music vs sfx balance, ducking"},
 "cta":{"text":"","visual":"","timing_s":0.0},
 "structure_template":[{"beat":"Hook","role":"","approx_dur_s":0,"technique":"","what_to_put_here":"brand-agnostic instruction"}]
}
Transcribe the VO verbatim for analysis. List EVERY cut (the timeline must cover the whole duration with no gaps).
JSON only, no prose."""

def render_md(d, name):
    L=[f"# Ad teardown — {name}\n"]
    m=d.get('meta',{})
    L.append(f"**{m.get('duration_s')}s · {m.get('aspect')} · {m.get('total_cuts')} cuts · avg shot {m.get('avg_shot_len_s')}s · {m.get('pace')} pace**\n")
    L.append(f"- Style: {m.get('overall_style')}\n- Grade: {m.get('color_grade')}\n- Music: {m.get('music_style')}\n- VO: {m.get('vo_voice_feel')}\n")
    h=d.get('hook',{}); L.append(f"\n## Hook\nFirst 1.5s: {h.get('first_1_5s')}\nTechnique: **{h.get('technique')}** — {h.get('why_it_works')}\n")
    L.append("\n## Persuasion arc\n"+" → ".join(d.get('persuasion_arc',[]))+"\n")
    L.append("\n## Timeline\n")
    for b in d.get('timeline',[]):
        ot=b.get('on_screen_text') or {}
        L.append(f"### {b.get('idx')}. {b.get('t_start')}–{b.get('t_end')}s  ({b.get('type')}, {b.get('framing')}, {b.get('camera')}) →{b.get('transition_to_next')}")
        L.append(f"- **Shot:** {b.get('shot')}")
        if b.get('vo_line'): L.append(f"- **VO:** \"{b.get('vo_line')}\"  _({b.get('vo_delivery')})_")
        if ot.get('text'): L.append(f"- **On-screen:** \"{ot.get('text')}\"  [{ot.get('style')}, {ot.get('position')}, in:{ot.get('animation_in')}, {ot.get('sync')}]")
        if b.get('sfx'): L.append(f"- **SFX:** "+", ".join(f"{s.get('t')}s {s.get('sound')}" for s in b.get('sfx',[])))
        if b.get('music_note'): L.append(f"- **Music:** {b.get('music_note')}")
        L.append(f"- **Replicate:** {b.get('replication_note')}\n")
    cs=d.get('caption_system',{}); L.append(f"\n## Caption system\n{json.dumps(cs,indent=2)}\n")
    sd=d.get('sound_design',{}); L.append(f"\n## Sound design\n{json.dumps(sd,indent=2)}\n")
    L.append(f"\n## CTA\n{json.dumps(d.get('cta',{}),indent=2)}\n")
    L.append("\n## Structure template (refill with our content)\n")
    for t in d.get('structure_template',[]):
        L.append(f"- **{t.get('beat')}** (~{t.get('approx_dur_s')}s, {t.get('role')}): {t.get('technique')} → {t.get('what_to_put_here')}")
    return "\n".join(L)

def main():
    if len(sys.argv) < 2: sys.exit("usage: teardown.py <video> [name]")
    path = sys.argv[1]; name = sys.argv[2] if len(sys.argv) > 2 else pathlib.Path(path).stem[:24]
    OUT.mkdir(exist_ok=True)
    from google import genai
    from google.genai import types
    c = genai.Client(api_key=load_key())
    print(f"uploading {pathlib.Path(path).name} ...", flush=True)
    f = retry(lambda: c.files.upload(file=path))
    try:
        w=0
        while f.state.name == 'PROCESSING' and w < 120: time.sleep(3); w+=3; f=c.files.get(name=f.name)
        if f.state.name != 'ACTIVE': sys.exit('upload '+f.state.name)
        print("analysing with Gemini ...", flush=True)
        r = retry(lambda: c.models.generate_content(model=MODEL, contents=[f, PROMPT],
              config=types.GenerateContentConfig(temperature=0.2, response_mime_type='application/json')))
    finally:
        try: c.files.delete(name=f.name)
        except: pass
    data = json.loads(r.text)
    (OUT/f"{name}.json").write_text(json.dumps(data, indent=2))
    (OUT/f"{name}.md").write_text(render_md(data, name))
    u=r.usage_metadata
    print(f"DONE: {len(data.get('timeline',[]))} beats | tokens in {u.prompt_token_count} out {u.candidates_token_count}")
    print(f"  -> {OUT}/{name}.json  and  {name}.md")

if __name__ == '__main__': main()
