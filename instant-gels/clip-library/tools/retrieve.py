#!/usr/bin/env python3
"""Retrieval over the Instant Gels index: asset-request -> ranked candidate clips.

A 'beat' is a request: role + optional category/method/shade/stage/durability/duration/text-zone.
Ranking blends visual-quality + the role-relevant score, filters hard constraints, and avoids
picking the same clip or near-duplicate shots twice. `python3 retrieve.py` runs a demo script.
"""
import sqlite3, json, pathlib, sys
DB = pathlib.Path(__file__).parent.parent / 'index.db'

# role -> scoring weight (v=visual_quality, h=hook, p=proof)
ROLE_W = {
 'hook':       lambda v,h,p: h*2 + v,
 'problem':    lambda v,h,p: h*1.5 + v,
 'reveal':     lambda v,h,p: v + p,
 'demo':       lambda v,h,p: v + p*0.5,
 'proof':      lambda v,h,p: p*2 + v,
 'payoff':     lambda v,h,p: v*1.5,
 'lifestyle':  lambda v,h,p: v*1.5,
 'cta_support':lambda v,h,p: v + p,
 'transition': lambda v,h,p: v,
}

def retrieve(con, role=None, category=None, method=None, shade=None, stage=None,
             durability=None, keyword=None, process_step=None, min_dur=0.0, max_dur=999.0, need_text=None,
             exclude_clips=(), limit=5):
    con.row_factory = sqlite3.Row
    where, args = ["1=1"], []
    if category:   where.append("v.category=?"); args.append(category)
    if method:     where.append("v.method=?"); args.append(method)
    if process_step: where.append("s.process_step=?"); args.append(process_step)
    if shade:      where.append("v.shade LIKE ?"); args.append(f"%{shade}%")
    if stage:      where.append("s.stage=?"); args.append(stage)
    if durability: where.append("s.durability_test=?"); args.append(durability)
    if role:       where.append("s.role LIKE ?"); args.append(f'%"{role}"%')
    if keyword:    where.append("(s.fingerprint LIKE ? OR v.summary LIKE ?)"); args += [f"%{keyword}%", f"%{keyword}%"]
    rows = list(con.execute(
        f"select s.*, v.path, v.shade, v.category, v.method, v.summary, v.duration,"
        f" (s.t_end-s.t_start) as segdur from segments s join videos v on v.clip_id=s.clip_id"
        f" where {' and '.join(where)}", args))
    def dur(r): return r['segdur'] if (r['segdur'] or 0) > 0 else (r['duration'] or 0)
    rows = [r for r in rows if min_dur <= dur(r) <= max_dur or dur(r) == 0]
    w = ROLE_W.get(role, lambda v,h,p: v)
    def score(r):
        s = w(r['vis_quality'] or 5, r['hook'] or 5, r['proof'] or 5)
        if need_text and r['text_safe'] and need_text not in (r['text_safe'] or ''): s -= 3
        if r['human_review']: s -= 1
        return s
    rows.sort(key=score, reverse=True)
    out, seen_fp, seen_clip = [], [], set(exclude_clips)
    for r in rows:
        if r['clip_id'] in seen_clip: continue
        fp = set((r['fingerprint'] or '').lower().split())
        if any(len(fp & s) >= 4 for s in seen_fp): continue          # skip near-duplicate shots
        out.append((r, round(score(r), 1))); seen_clip.add(r['clip_id']); seen_fp.append(fp)
        if len(out) >= limit: break
    return out

def plan(con, beats):
    """Run a list of beat-requests into a draft EDL, avoiding repeated clips."""
    used, edl = set(), []
    for b in beats:
        cands = retrieve(con, exclude_clips=used, limit=3, **{k:v for k,v in b.items() if k!='name'})
        pick = cands[0] if cands else None
        if pick: used.add(pick[0]['clip_id'])
        edl.append((b, pick, cands[1:]))
    return edl

DEMO = [  # ~22s Instant Gels ad: hook -> problem -> reveal -> demo -> proof -> payoff -> cta
    dict(name="HOOK (pattern interrupt)", role='hook', category='hooks', max_dur=3, need_text='center'),
    dict(name="PROBLEM (agitate)",        role='problem', max_dur=3),
    dict(name="REVEAL (product)",         role='reveal', category='product_shots', shade='All Eyes on Me'),
    dict(name="DEMO (application)",        role='demo', category='application', shade='All Eyes on Me'),
    dict(name="PROOF (durability)",       role='proof', category='durability'),
    dict(name="PAYOFF (lifestyle)",       role='payoff', category='posing_lifestyle', shade='All Eyes on Me'),
    dict(name="CTA (support)",            role='cta_support'),
]

def fmt(pick):
    r, sc = pick
    nm = pathlib.Path(r['path']).name
    return (f"{nm[:40]:40} {r['t_start']:.1f}-{r['t_end']:.1f}s | {r['category']:14} | {r['shade'][:16]:16}"
            f" | score {sc:5} | text-safe:{(r['text_safe'] or '').strip('[]').replace(chr(34),'')}")

if __name__ == '__main__':
    con = sqlite3.connect(DB)
    print("=== DRAFT EDL: sample Instant Gels script ===\n")
    for b, pick, alts in plan(con, DEMO):
        print(f"▸ {b['name']}")
        print(f"    {fmt(pick) if pick else 'NO MATCH'}")
        if pick: print(f"      '{pick[0]['summary']}'")
        for a in alts[:1]: print(f"    alt {fmt(a)}")
        print()
