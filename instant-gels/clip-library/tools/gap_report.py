#!/usr/bin/env python3
"""What can't the library serve? Flags the b-roll we must generate (Higgsfield) to assemble full ads.
Brand rule: generated = faceless, no product, no proof — problem/abstract/transition only."""
import sqlite3, pathlib
cx = sqlite3.connect(pathlib.Path(__file__).parent.parent / 'index.db')

def role_n(role):
    return cx.execute("select count(*) from segments where role like ?", (f'%"{role}"%',)).fetchone()[0]
def cat_n(cat):
    return cx.execute("select count(*) from videos where category=?", (cat,)).fetchone()[0]
def kw_n(words):
    cl = " or ".join(["v.summary like ?" for _ in words] + ["s.fingerprint like ?" for _ in words])
    args = [f"%{w}%" for w in words] * 2
    return cx.execute(f"select count(distinct s.clip_id) from segments s join videos v on v.clip_id=s.clip_id where {cl}", args).fetchone()[0]

def verdict(n, thin=15, gap=5):
    return "GAP  ✗" if n < gap else ("THIN ~" if n < thin else "OK   ✓")

NEEDS = [
 ("Problem / agitation: lifting, chipping, bulky, peeling", kw_n(['lifting','chip','bulky','peel','crack','snap'])),
 ("Competitor 'bad press-on' contrast (fake/thick/stiff)",  kw_n(['fake','plastic','thick','stiff','obvious'])),
 ("Damaged / brittle NATURAL nail (the 'before')",          kw_n(['brittle','damaged','bare natural','weak nail','ridged'])),
 ("Abstract value/time concept (calendar, clock, 2 weeks)", kw_n(['calendar','clock','timer','two weeks','days'])),
 ("Money / value concept (salon price, cash, coins)",       kw_n(['money','cash','coin','salon price','dollar','receipt'])),
 ("Transitions / motion bridges",                           role_n('transition')),
 ("CTA / pack-hero support",                                 role_n('cta_support') ),
 ("Lifestyle context (mirror, getting ready, night out)",   kw_n(['mirror','getting ready','night out','outfit','party','date'])),
 ("Clean text-plate backgrounds (negative space)",          kw_n(['white background','negative space','clean background','plain'])),
]

print(f"{'NEED':56} {'have':>5}  verdict")
print("-"*78)
gaps=[]
for name,n in NEEDS:
    v=verdict(n); print(f"{name:56} {n:>5}  {v}")
    if "GAP" in v or "THIN" in v: gaps.append((name,n))

print("\n>>> HIGGSFIELD GENERATION BRIEF (faceless, no product, no proof) <<<")
for name,n in gaps:
    print(f"  - {name}  (have {n})")
print("\nLibrary strengths (already covered, do NOT generate):")
print(f"  application {cat_n('application')} | removal {cat_n('removal')} | posing {cat_n('posing_lifestyle')}"
      f" | durability {cat_n('durability')} | demo-role {role_n('demo')} | proof-role {role_n('proof')} | reveal {role_n('reveal')}")
