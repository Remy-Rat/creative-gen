#!/usr/bin/env python3
"""IG-AD-02 — structural twin of competitor-ad-01 for a side-by-side SYSTEM quality check.
Uses the teardown's EXACT 42-beat timings + sfx + transitions; ORIGINAL GLAMRDiP copy per beat
(not the competitor's words); each beat mapped to a real indexed clip (or a b-roll-gap slate)."""
import json, sqlite3, pathlib, collections, sys
sys.path.insert(0, '/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/tools')
import retrieve
OUT = pathlib.Path(__file__).parent / 'output'
con = sqlite3.connect(retrieve.DB); con.row_factory = sqlite3.Row
TL = {b['idx']: b for b in json.loads((OUT/'competitor-ad-01.json').read_text())['timeline']}
cov = collections.Counter()
for r in con.execute("select shade,count(*) c from videos where category in ('application','posing_lifestyle','product_shots') group by shade"):
    cov[r['shade']] += r['c']
HERO = cov.most_common(1)[0][0]

def Q(**k): return ("q", k)
def G(desc): return ("gap", desc)
# OURS: idx -> (vo, caption, kind). Original copy paralleling each teardown beat's FUNCTION.
OURS = {
 1:("I swore off press-ons.","I swore off press-ons",Q(role='hook',category='hooks')),
 2:("Every set looked fake.","every set looked fake",Q(role='hook',category='hooks')),
 3:("Or felt like plastic.","or felt like plastic",Q(role='reveal',category='posing_lifestyle')),
 4:("Here's the honest truth —","the honest truth",Q(role='reveal',category='posing_lifestyle')),
 5:("Most press-ons are bulky plastic","most are bulky plastic",G("Hand picking up a generic bulky press-on box (competitor stand-in), retail/clean bg. Red ✗.")),
 6:("that never sit right.","never sits right",G("Ill-fitting generic french-tip press-ons with visible misfit. Red ✗.")),
 7:("Gaps at the cuticle.","gaps at the cuticle",G("Extreme-macro gap/lifting under a generic press-on at the cuticle. Red ✗.")),
 8:("Pop-offs.","pop-offs",G("A generic press-on popping off easily. Red ✗.")),
 9:("Obviously fake.","obviously fake",G("Peeling a fake-looking generic press-on. Red ✗.")),
 10:("And too much for real life.","too much for real life",G("Tossing a generic press-on box into a bin. Red ✗.")),
 11:("So when I found these —","so when I found these",G("Awkward typing with long fake nails (competitor stand-in).")),
 12:("GLAMRDiP Instant Gels.","GLAMRDiP Instant Gels",Q(role='reveal',category='product_shots')),
 13:("I couldn't believe they'd fit","couldn't believe they'd fit",Q(role='reveal',category='product_shots')),
 14:("and look like this.","and look like this",Q(role='demo',category='application',shade=HERO)),
 15:("They're soft gel —","soft gel —",Q(role='reveal',category='posing_lifestyle',shade=HERO)),
 16:("not stiff plastic.","not stiff plastic",Q(role='lifestyle',category='posing_lifestyle')),
 17:("Pre-cured, ready to press.","pre-cured · ready to press",Q(role='demo',category='application')),
 18:("No bending. No cheap shine.","no bending, no cheap shine",G("Bending a cheap generic plastic press-on until it creases. Red ✗.")),
 19:("The short designs —","the short designs",Q(role='reveal',category='product_shots')),
 20:("Bubbly Babe.","Bubbly Babe",Q(role='lifestyle',category='posing_lifestyle',shade='Bubbly Babe')),
 21:("Ruby Rush.","Ruby Rush",Q(role='lifestyle',category='posing_lifestyle',shade='Ruby Rush')),
 22:("All Eyes on Me.","All Eyes on Me",Q(role='lifestyle',category='posing_lifestyle',shade='All Eyes on Me')),
 23:("Almost Nude —","Almost Nude",Q(role='lifestyle',category='posing_lifestyle',shade='Almost Nude')),
 24:("so natural,","so natural",Q(role='reveal',category='posing_lifestyle')),
 25:("people swear it's a salon gel.","they swear it's salon",Q(role='reveal',category='posing_lifestyle')),
 26:("Application's simple:","application's simple",Q(role='reveal',category='product_shots')),
 27:("size it, peel the tab,","size · peel the tab",Q(role='demo',category='application',method='tabs')),
 28:("press, and you're done.","press · done",Q(role='demo',category='application',keyword='press')),
 29:("Ten minutes,","ten minutes",Q(role='payoff',category='posing_lifestyle',shade=HERO)),
 30:("salon nails.","salon nails",Q(role='lifestyle',category='posing_lifestyle',shade='Ruby Rush')),
 31:("Sixteen sizes in every set,","16 sizes in every set",Q(role='lifestyle',category='posing_lifestyle')),
 32:("so they actually fit.","so they actually fit",Q(role='reveal',category='product_shots')),
 33:("Switching is just as easy —","switching is easy",Q(role='demo',category='removal')),
 34:("warm water,","warm water",Q(role='demo',category='removal')),
 35:("a little oil,","a little oil",Q(role='demo',category='removal')),
 36:("and they lift off,","they lift off",Q(role='demo',category='removal')),
 37:("ready to reuse.","ready to reuse",Q(role='proof',category='removal')),
 38:("If you've given up on press-ons,","given up on press-ons?",Q(role='payoff',category='posing_lifestyle',shade=HERO)),
 39:("this is the set that changes your mind.","changes your mind",Q(role='reveal',category='product_shots')),
 40:("Grab the Instant Gels starter set","shop the starter set",Q(role='reveal',category='product_shots')),
 41:("","starter set, sixteen sizes",Q(role='reveal',category='product_shots')),
 42:("","Salon-gel nails. Zero salon.  ·  glamrdip.com",Q(role='reveal',category='product_shots')),
}

used=set(); beats=[]; gaps=[]
for i in range(1,43):
    td=TL[i]; vo,cap,(kind,payload)=OURS[i]
    t0,t1=td['t_start'],td['t_end']; clip=None; isgap=(kind=='gap')
    if isgap:
        gaps.append((i,payload,vo))
    else:
        c=retrieve.retrieve(con, exclude_clips=used, limit=2, **payload)
        if c:
            r,_=c[0]; used.add(r['clip_id'])
            clip=dict(clip=pathlib.Path(r['path']).name, path=r['path'], t_in=r['t_start'], shade=r['shade'], category=r['category'])
        else: isgap=True; gaps.append((i,f"no match {payload}",vo))
    beats.append(dict(n=i,t_start=t0,t_end=t1,dur=round(t1-t0,2),vo=vo,caption=cap,
                      sfx=td.get('sfx') and 'buzzer/ding', transition=td.get('transition_to_next'),
                      clip=clip,broll_gap=isgap))

man=dict(ad_id="IG-AD-02",note="structural twin of competitor-ad-01; exact timings; original copy",
         hero_shade=HERO,total_duration=beats[-1]['t_end'],beat_count=42,beats=beats)
(OUT/"ig-ad-02.manifest.json").write_text(json.dumps(man,indent=2))
L=[f"# IG-AD-02 — structural twin (system quality check)\n*42 beats · exact teardown timings · original copy · hero {HERO} · {beats[-1]['t_end']}s · {len(gaps)} b-roll gaps*\n",
   "| # | Time | VO (ours) | Caption | Clip / B-ROLL |","|--|--|--|--|--|"]
for b in beats:
    c=b['clip']; cl=f"⚠️ {[g[1] for g in gaps if g[0]==b['n']][0][:48]}" if b['broll_gap'] else f"{c['clip'][:26]} ({c['shade']})"
    L.append(f"| {b['n']} | {b['t_start']}-{b['t_end']}s | {b['vo'] or '—'} | {b['caption']} | {cl} |")
(OUT/"ig-ad-02.brief.md").write_text("\n".join(L))
print(f"hero {HERO} | 42 beats | {beats[-1]['t_end']}s | real {42-len(gaps)} | gaps {len(gaps)}")
print("wrote ig-ad-02.manifest.json + .brief.md")
