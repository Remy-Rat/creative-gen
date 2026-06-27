#!/bin/bash
# Auto-resuming Instant Gels indexing loop. Backs off when Gemini is congested,
# runs full-speed when it recovers, exits (releasing caffeinate) when complete.
cd "/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library" || exit 1
count(){ python3 -c "import sqlite3;print(sqlite3.connect('index.db').execute('select count(*) from videos').fetchone()[0])" 2>/dev/null; }
back=60
for i in $(seq 1 300); do
  c=$(count)
  if [ "${c:-0}" -ge 820 ]; then echo "ALL DONE: $c/826"; break; fi
  echo "== pass $i @ ${c}/826 =="
  python3 tools/index.py --all --workers 5 --limit 80 --budget 300 2>&1 \
    | grep --line-buffered -E 'PASS ok|ERR |budget .* hit|\[[0-9]*[05]0\] '
  c2=$(count)
  if [ "${c2:-0}" -le "${c:-0}" ]; then
    echo "(no progress — Gemini busy; backing off ${back}s)"
    sleep "$back"
    [ "$back" -lt 300 ] && back=$((back+60))
  else
    back=60
  fi
done
echo "LOOP END"
