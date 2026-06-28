#!/bin/bash
# Generate faceless salon-method + cheap-plastic b-roll stills for the IG-AD slates (Higgsfield Soul V2).
# Faceless, no GLAMRDiP product, photoreal. Mirrors 07_HIGGSFIELD_BROLL_PROMPTS structure.
export PATH="$HOME/.nvm/versions/node/v22.18.0/bin:$PATH"
cd "/Users/remy-m4/Desktop/Video-ad-test/instant-gels/generated" || exit 1
mkdir -p broll
NEG="No human face, no text, no letters, no logos, no extra fingers, no deformed hands, no watermark, no clutter."
gen(){
  echo "== $1 =="
  higgsfield generate create text2image_soul_v2 --prompt "$2 $NEG" --aspect_ratio 9:16 --quality 2k --wait --json > "/tmp/hf_$1.json" 2>/dev/null
  URL=$(python3 -c "import json,re;print(([u for u in re.findall(r'https?://[^\" ]+\.png',json.dumps(json.load(open('/tmp/hf_$1.json'))))]+[''])[0])" 2>/dev/null)
  if [ -n "$URL" ]; then curl -s -o "broll/$1.png" "$URL" && echo "DONE $1 ($(du -h broll/$1.png 2>/dev/null|cut -f1))"; else echo "FAIL $1"; fi
}
gen polish "Extreme macro of a traditional nail polish brush painting a single fingernail glossy red, a polish bottle beside it, clean white studio bench, soft even diffused light, shallow depth of field, photoreal documentary, hand and fingertip only."
gen shellac "Macro of thick glossy gel shellac polish being brushed onto a single fingernail, wet high shine, clean white studio, soft even light, shallow depth of field, photoreal, fingertips only."
gen acrylic "Macro of acrylic nail powder picked up on a brush and applied to a fingernail, fine white acrylic dust, clinical white background, soft light, photoreal, fingertips only."
gen uvlamp "A hand resting inside a bulky UV LED nail lamp that is switched on, intense purple ultraviolet glow spilling out, clean dark studio, photoreal, fingertips only."
gen filing "Extreme macro of a spinning electric nail drill file buffing the surface of a fingernail, fine nail dust flying off, harsh clinical white background, photoreal, fingertips only."
gen cheapplastic "Extreme macro of a thick cheap generic plastic press-on nail being bent until it creases and turns white, obviously bulky stiff and fake looking, plain neutral grey background, photoreal."
echo "ALL BROLL DONE"
