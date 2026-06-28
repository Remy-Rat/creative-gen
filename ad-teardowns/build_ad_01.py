#!/usr/bin/env python3
"""Build IG-AD-01: GLAMRDiP Instant Gels ad on the Doonails teardown structure (original copy),
mapped to our real indexed clips via retrieve.py. Outputs a build manifest + readable brief + VO
script + b-roll gap list. Original script — same proven 5-phase arc, our words/product/footage."""
import sys, json, sqlite3, pathlib, collections
sys.path.insert(0, '/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/tools')
import retrieve
OUT = pathlib.Path(__file__).parent / 'output'
con = sqlite3.connect(retrieve.DB); con.row_factory = sqlite3.Row

# pick a hero shade = best coverage across application+posing+product (for cohesive beats)
cov = collections.Counter()
for r in con.execute("select shade,count(*) c from videos where category in ('application','posing_lifestyle','product_shots') group by shade"):
    cov[r['shade']] += r['c']
HERO = cov.most_common(1)[0][0]

# BEATS — original GLAMRDiP copy on the 5-phase arc. q = retrieval query; gap = needs Higgsfield b-roll.
B = [
 # HOOK — pattern interrupt (shade variety) + confession
 dict(n=1, phase="HOOK", dur=1.3, vo="I gave up on press-ons years ago.", cap="I gave up on press-ons", cap_style="SUB-02 clean reader", sfx="", trans="hard cut", q=dict(role='hook', category='hooks')),
 dict(n=2, phase="HOOK", dur=1.0, vo="Too fake. Too bulky.", cap="too fake. too bulky.", cap_style="SUB-03 kinetic", sfx="", trans="hard cut", q=dict(role='hook', category='hooks')),
 dict(n=3, phase="HOOK", dur=1.4, vo="Then these changed my mind.", cap="then these changed my mind", cap_style="SUB-04 karaoke (hl: changed my mind)", sfx="", trans="flash", q=dict(role='reveal', category='posing_lifestyle', shade=HERO)),
 # PROBLEM — old/competitor press-on flaws (red X + buzzer). Mostly b-roll gaps.
 dict(n=4, phase="PROBLEM", dur=2.2, vo="You know the type —", cap="you know the type", cap_style="SUB-02 clean reader", sfx="", trans="hard cut", gap="Faceless macro: a thick, bulky generic plastic press-on sitting high off the nail (NOT our product). Red ✗."),
 dict(n=5, phase="PROBLEM", dur=1.8, vo="thick plastic that just sits on top.", cap="thick plastic", cap_style="ANN-03 sticker + red ✗", sfx="buzzer", trans="hard cut", gap="Faceless macro: side angle showing a chunky press-on's gap/ledge above the natural nail. Red ✗."),
 dict(n=6, phase="PROBLEM", dur=1.8, vo="Gaps at the cuticle.", cap="gaps at the cuticle", cap_style="ANN-02 leader callout + red ✗", sfx="", trans="hard cut", gap="Faceless extreme-macro: visible gap/lifting under a press-on at the cuticle. Red ✗."),
 dict(n=7, phase="PROBLEM", dur=2.0, vo="Popped off by lunch — and everyone could tell.", cap="popped off by lunch", cap_style="SUB-03 kinetic", sfx="buzzer", trans="hard cut", gap="Faceless: a generic press-on popping/peeling off easily. Red ✗."),
 # SOLUTION — reveal, soft gel not plastic, zero-edge (green ✓ + ding)
 dict(n=8, phase="SOLUTION", dur=1.6, vo="Instant Gels are different.", cap="Instant Gels are different", cap_style="HOOK-01 stamp", sfx="ding", trans="flash", q=dict(role='reveal', category='product_shots')),
 dict(n=9, phase="SOLUTION", dur=2.2, vo="Pre-cured soft gel — not stiff plastic.", cap="soft gel — not plastic", cap_style="PROD-04 tech callout", sfx="", trans="hard cut", q=dict(role='reveal', category='product_shots')),
 dict(n=10, phase="SOLUTION", dur=2.6, vo="A zero-edge base that sits flush to your cuticle.", cap="zero-edge: sits flush, no lift", cap_style="ANN-02 leader callout + green ✓", sfx="", trans="hard cut", q=dict(role='proof', keyword='cuticle')),
 dict(n=11, phase="SOLUTION", dur=1.8, vo="No gap. No lift. No lamp.", cap="no gap. no lift. no lamp.", cap_style="PROD-01 benefit stack", sfx="ding", trans="hard cut", q=dict(role='demo', category='application', shade=HERO)),
 # DEMO & BENEFITS
 dict(n=12, phase="DEMO", dur=1.6, vo="Application's stupid simple.", cap="stupid simple", cap_style="SUB-02 clean reader", sfx="", trans="hard cut", q=dict(role='demo', category='application', method='tabs', shade=HERO)),
 dict(n=13, phase="DEMO", dur=2.4, vo="Size it, press it, done.", cap="size · press · done", cap_style="PROD-02 step rail", sfx="", trans="hard cut", q=dict(role='demo', category='application', shade=HERO)),
 dict(n=14, phase="DEMO", dur=1.8, vo="About ten minutes — no appointment.", cap="~10 minutes, no appointment", cap_style="SUB-05 side label", sfx="", trans="hard cut", q=dict(role='payoff', category='posing_lifestyle', shade=HERO)),
 dict(n=15, phase="DEMO", dur=1.8, vo="Sixteen sizes, so it actually fits.", cap="16 sizes — your perfect fit", cap_style="PROD-01 benefit stack", sfx="", trans="hard cut", q=dict(role='reveal', category='product_shots')),
 dict(n=16, phase="DEMO", dur=2.4, vo="Two weeks of wear. Glass-gloss finish.", cap="2 weeks wear · glass gloss", cap_style="ANN-03 stat sticker", sfx="", trans="hard cut", q=dict(role='lifestyle', category='posing_lifestyle', shade=HERO)),
 dict(n=17, phase="DEMO", dur=2.6, vo="Want to switch? Soak, lift, reuse.", cap="soak · lift · reuse", cap_style="PROD-02 step rail", sfx="", trans="hard cut", q=dict(role='demo', category='removal')),
 # CTA
 dict(n=18, phase="CTA", dur=2.2, vo="Sworn off press-ons? These will change your mind.", cap="change your mind", cap_style="SUB-04 karaoke", sfx="", trans="hard cut", q=dict(role='payoff', category='posing_lifestyle', shade=HERO)),
 dict(n=19, phase="CTA", dur=2.0, vo="Get the starter set today.", cap="shop the starter set", cap_style="CTA-01 pulse button", sfx="ding", trans="hard cut", q=dict(role='reveal', category='product_shots')),
 dict(n=20, phase="CTA", dur=3.0, vo="", cap="Salon-gel nails. Zero salon.  ·  glamrdip.com", cap_style="CTA-02 brand end card", sfx="", trans="none", q=dict(role='reveal', category='product_shots')),
]

used = set(); rows = []; gaps = []; t = 0.0
for b in B:
    assigned = None
    if 'gap' in b:
        gaps.append((b['n'], b['gap'], b['vo']))
    else:
        cands = retrieve.retrieve(con, exclude_clips=used, limit=2, **b['q'])
        if cands:
            r, sc = cands[0]; used.add(r['clip_id'])
            assigned = dict(clip=pathlib.Path(r['path']).name, path=r['path'], t_in=r['t_start'], t_out=r['t_end'],
                            shade=r['shade'], category=r['category'], score=sc)
        else:
            gaps.append((b['n'], f"No clip matched {b['q']}", b['vo']))
    rows.append(dict(beat=b, t_start=round(t,1), t_end=round(t+b['dur'],1), clip=assigned, is_gap=('gap' in b or assigned is None)))
    t += b['dur']

manifest = dict(ad_id="IG-AD-01", source_template="competitor-ad-01 (Doonails) teardown",
                hero_shade=HERO, total_duration=round(t,1), beat_count=len(B),
                caption_system="white sans, top, line-by-line fade (motion-kit IDs per beat)",
                sound="upbeat electronic bed ducked under VO; buzzer on problem, ding on solution",
                vo_voice="AUS GM (eleven_v3) — warm AU female; see vo/SKILL.md",
                beats=[dict(n=r['beat']['n'], phase=r['beat']['phase'], t=f"{r['t_start']}-{r['t_end']}s",
                            vo=r['beat']['vo'], caption=r['beat']['cap'], caption_style=r['beat']['cap_style'],
                            sfx=r['beat']['sfx'], transition=r['beat']['trans'],
                            clip=r['clip'], broll_gap=r['is_gap']) for r in rows])
OUT.mkdir(exist_ok=True)
(OUT/"ig-ad-01.manifest.json").write_text(json.dumps(manifest, indent=2))

# readable brief
L=[f"# IG-AD-01 — build brief\n",
   f"*GLAMRDiP Instant Gels · structure from the Doonails teardown · original copy · hero shade **{HERO}** · ~{round(t)}s · {len(B)} beats*\n",
   f"Captions: white sans, top, line-by-line fade. Sound: upbeat electronic, duck under VO, buzzer/ding. VO: AUS GM (eleven_v3).\n",
   "| # | Phase | Time | VO | Caption (style) | SFX | Clip / B-ROLL |",
   "|--|--|--|--|--|--|--|"]
for r in rows:
    b=r['beat']; c=r['clip']
    clip = f"⚠️ B-ROLL: {b.get('gap','no match')[:60]}" if r['is_gap'] else f"{c['clip'][:30]} ({c['shade']}, {c['category']})"
    L.append(f"| {b['n']} | {b['phase']} | {r['t_start']}-{r['t_end']}s | {b['vo'] or '—'} | {b['cap']} _({b['cap_style']})_ | {b['sfx'] or '—'} | {clip} |")
(OUT/"ig-ad-01.brief.md").write_text("\n".join(L))

# VO script (for the ElevenLabs skill)
vo=[f"# IG-AD-01 VO script — AUS GM (eleven_v3)\n",
    "Per vo/SKILL.md: confirm + GO before generating. Sections grouped by phase.\n"]
ph=None
for r in rows:
    b=r['beat']
    if not b['vo']: continue
    if b['phase']!=ph: ph=b['phase']; vo.append(f"\n## {ph}")
    vo.append(f"{b['vo']}")
(OUT/"ig-ad-01.vo.md").write_text("\n".join(vo))

# b-roll gaps (Higgsfield brief)
g=[f"# IG-AD-01 — b-roll gaps to generate (Higgsfield)\n",
   "All faceless, no GLAMRDiP product, no proof. QA: must look PHOTOREAL — reject AI/CGI tells (warped texture, fake sheen).\n"]
for n,brief,vo_line in gaps:
    g.append(f"- **Beat {n}** (VO: \"{vo_line}\"): {brief}")
(OUT/"ig-ad-01.broll-gaps.md").write_text("\n".join(g))

print(f"hero shade: {HERO} | {len(B)} beats | ~{round(t)}s | real clips: {len(B)-len(gaps)} | b-roll gaps: {len(gaps)}")
print("wrote: ig-ad-01.manifest.json, .brief.md, .vo.md, .broll-gaps.md")
