#!/bin/bash
# Generate VIDEO b-roll for the IG ad via Higgsfield Veo 3.1 (veo3_1), 9:16, 8s.
# Prompts come from glamrdip-higgsfield-broll-prompts.md. Emits one status line per clip (for Monitor).
export PATH="$HOME/.nvm/versions/node/v22.18.0/bin:$PATH"
cd "/Users/remy-m4/Desktop/Video-ad-test/instant-gels/generated" || exit 1
mkdir -p broll-video
MODEL="${MODEL:-veo3_1}"
G="Vertical 9:16 social ad footage, realistic premium UGC aesthetic, shot on modern smartphone, soft natural lighting, shallow depth of field, clean neutral apartment or nail salon setting, realistic hands and fingernails, subtle handheld camera movement, no text, no subtitles, no logos, no branded packaging, leave upper third relatively clean for captions."
gen(){
  name="$1"; shift; prompt="$1 $G"
  echo "START $name ($MODEL)"
  higgsfield generate create "$MODEL" --prompt "$prompt" --aspect_ratio 9:16 --duration 8 --wait --wait-timeout 15m --json > "broll-video/_$name.json" 2>"broll-video/_$name.err"
  URL=$(python3 -c "import json,re,sys;d=open('broll-video/_$name.json').read();m=re.findall(r'https?://[^\"\\\\ ]+\.mp4',d);print((m+[''])[0])" 2>/dev/null)
  if [ -n "$URL" ]; then
    curl -s -L -o "broll-video/$name.mp4" "$URL" && echo "DONE $name ($(du -h broll-video/$name.mp4 2>/dev/null|cut -f1))"
  else
    echo "FAIL $name -- $(head -c 200 broll-video/_$name.err 2>/dev/null | tr '\n' ' ')"
  fi
}
# --- proof set: the two hardest-for-AI hand/nail macros ---
gen smudgedpolish "Close-up UGC shot of a young woman at a small vanity trying to paint her own fingernails with deep red nail polish. She accidentally smudges one freshly painted nail with her other hand, pauses in annoyance and looks disappointed. The polish looks slightly messy but believable, ordinary at-home manicure, not glamorous. Camera framed tightly on hands and lower face."
gen cheapnailcrack "Extreme close-up of a visibly cheap, thin generic artificial nail tip bending and cracking between two fingers. The artificial nail looks flimsy and low quality, separate from a real hand manicure. Clean studio tabletop, realistic macro product demonstration, no brands, no words, no logos."
echo "ALL_PROOF_DONE"
