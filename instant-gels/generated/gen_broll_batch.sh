#!/bin/bash
# Batch the remaining needed VIDEO b-roll via Higgsfield Veo 3.1, 9:16, 8s.
# Pain/reaction beats only (no real footage for these). Emits one status line per clip (for Monitor).
export PATH="$HOME/.nvm/versions/node/v22.18.0/bin:$PATH"
cd "/Users/remy-m4/Desktop/Video-ad-test/instant-gels/generated" || exit 1
mkdir -p broll-video
MODEL="${MODEL:-veo3_1}"
G="Vertical 9:16 social ad footage, realistic premium UGC aesthetic, shot on modern smartphone, soft natural lighting, shallow depth of field, clean neutral apartment or nail salon setting, realistic hands and fingernails, subtle handheld camera movement, no text, no subtitles, no logos, no branded packaging, leave upper third relatively clean for captions."
gen(){
  name="$1"; shift; prompt="$1 $G"
  [ -f "broll-video/$name.mp4" ] && { echo "SKIP $name (exists)"; return; }
  echo "START $name ($MODEL)"
  higgsfield generate create "$MODEL" --prompt "$prompt" --aspect_ratio 9:16 --duration 8 --wait --wait-timeout 15m --json > "broll-video/_$name.json" 2>"broll-video/_$name.err"
  URL=$(python3 -c "import json,re,sys;d=open('broll-video/_$name.json').read();m=re.findall(r'https?://[^\"\\\\ ]+\.mp4',d);print((m+[''])[0])" 2>/dev/null)
  if [ -n "$URL" ]; then
    curl -s -L -o "broll-video/$name.mp4" "$URL" && echo "DONE $name ($(du -h broll-video/$name.mp4 2>/dev/null|cut -f1))"
  else
    echo "FAIL $name -- $(head -c 200 broll-video/_$name.err 2>/dev/null | tr '\n' ' ')"
  fi
}
gen uvlamp "Macro beauty shot of a hand slowly sliding underneath a generic white UV nail curing lamp at a nail salon. Soft blue-purple curing light illuminates the fingers. The shot should feel clinical and repetitive rather than luxurious, focus on the hand entering the lamp, no logos or visible text on the device."
gen filing "Extreme macro close-up of a generic electric nail file being used on a bare natural fingernail during a salon manicure. Fine nail dust is visible in the air, the motion looks slightly harsh and repetitive but realistic. Professional nail salon lighting, tight crop focused only on fingers, nail file and dust, no blood, no injury, no logos."
gen foilacetone "Close-up UGC footage of a woman at home removing old gel polish using cotton pads and foil wraps around her fingertips. She carefully unwraps a fingertip, looks at the messy residue and reacts with a frustrated sigh. Natural daylight, ordinary bathroom or bedroom vanity, realistic beauty routine, no brands."
gen couchfrustration "Casual vertical UGC video of a stylish woman in her twenties sitting on a neutral couch at home in the evening. She looks down at an uneven DIY manicure, gives a small frustrated laugh, shakes her head and drops her hands into her lap as if giving up. Soft lamp lighting, candid smartphone feel, believable and understated performance."
echo "ALL_BATCH_DONE"
