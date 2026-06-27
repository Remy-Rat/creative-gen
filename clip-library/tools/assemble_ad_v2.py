#!/usr/bin/env python3
"""
GlamrDip Ad Assembler v2 - "YOU DIDN'T KNOW" concept
Transcript-aligned timing from ElevenLabs word-level JSON.

Section timing (from transcript):
  HOOK:    0.00 -  4.76s  (4.76s)  "Nobody told me..."
  BODY1:   4.76 - 15.46s  (10.70s) "Most polishes...losing layers."
  BODY2:  15.46 - 26.58s  (11.12s) "Then I found Glamour Dip...nourish your nails"
  BODY3:  26.58 - 36.04s  (9.46s)  "I'm talking gel-like shine...three dollars each."
  BODY4:  36.04 - 40.38s  (4.34s)  "Do the salon maths..." + gap before CTA
  CTA:    40.38 - 54.00s  (13.62s) "Right now..." through "...something better." + pad
"""

import subprocess
import os
import json

WORK = "/sessions/eloquent-busy-albattani/ad_build_v2"
INDEXED = "/sessions/eloquent-busy-albattani/mnt/Video-ad-test/clip-library/indexed"
VOICEOVER = "/sessions/eloquent-busy-albattani/mnt/uploads/ElevenLabs_2026-03-31T12_43_16_Ava – Eager, Helpful and Understanding_pvc_sp100_s50_sb75_se36_b_m2.mp3"
OUTPUT = "/sessions/eloquent-busy-albattani/mnt/Video-ad-test/clip-library/YOU_DIDNT_KNOW_v2.mp4"

os.makedirs(WORK, exist_ok=True)

# ============================================================
# TRANSCRIPT-ALIGNED EDIT DECISION LIST
#
# Key voiceover phrase boundaries (word-level from ElevenLabs):
#   0.14  "Nobody"
#   4.76  end "...making them worse."
#   4.76  "Most polishes..."
#  12.10  end "...over time."
#  13.14  "I had no idea..."
#  15.46  end "...losing layers."
#  16.58  "Then I found Glamour Dip."  (ends 16.80)
#  19.50  end "...harsh chemicals,"
#  20.88  end "...UV lamp,"
#  26.58  end "...while you wear it."
#  26.58  "I'm talking gel-like shine..."
#  31.42  end "...six weeks,"
#  36.04  end "...three dollars each."
#  37.52  "Do the salon maths..."  (ends 38.94)
#  40.38  "Right now, every Glamour Dip kit..."
#  45.80  end "...plus free shipping."
#  47.28  "And if you don't love it..."
#  50.02  end "...money back guarantee."
#  51.36  "Click the link..."
#  53.62  end "...something better."
# ============================================================

edl = [
    # ── HOOK: 0.00 - 4.76s (4.76s total) ──────────────────────
    # "Nobody told me that everything I was putting on my nails
    #  was actually making them worse."
    {
        "name": "hook_1_brittle",
        "source": f"{INDEXED}/02_problem_comparison/CLIP-0009_problem_brittle-damaged-nail-closeup.mov",
        "start": 0.0, "duration": 1.6,
        "notes": "0.00-1.60 | Brittle damaged nail macro - shock opening on 'Nobody told me'"
    },
    {
        "name": "hook_2_peeling",
        "source": f"{INDEXED}/02_problem_comparison/CLIP-0006_problem_pink-nail-peeling-off.mov",
        "start": 1.0, "duration": 1.3,
        "notes": "1.60-2.90 | Nail peeling - 'everything I was putting on my nails'"
    },
    {
        "name": "hook_3_reveal",
        "source": f"{INDEXED}/03_application_process/CLIP-0001_process_red-french-tip-full-application.mp4",
        "start": 10.8, "duration": 1.86,
        "notes": "2.90-4.76 | Red french tip reveal - contrast on 'making them worse'"
    },

    # ── BODY 1: 4.76 - 15.46s (10.70s total) ─────────────────
    # "Most polishes and gel systems are loaded with chemicals
    #  like HEMA and TPO that literally weaken your nails over time."
    # "I had no idea until I started losing layers."
    {
        "name": "body1_1_tedious",
        "source": f"{INDEXED}/02_problem_comparison/CLIP-0007_problem_tedious-polish-application-frustrated.mov",
        "start": 0.0, "duration": 1.32,
        "notes": "4.76-6.08 | Tedious polish application on 'Most polishes and gel systems'"
    },
    {
        "name": "body1_2_uv_lamp",
        "source": f"{INDEXED}/02_problem_comparison/CLIP-0008_problem_uv-lamp-frustration-smash.mov",
        "start": 0.0, "duration": 3.68,
        "notes": "6.08-9.76 | UV lamp frustration on 'loaded with chemicals like HEMA and TPO'"
    },
    {
        "name": "body1_3_uv_exasperated",
        "source": f"{INDEXED}/02_problem_comparison/CLIP-0008_problem_uv-lamp-frustration-smash.mov",
        "start": 2.5, "duration": 2.34,
        "notes": "9.76-12.10 | Exasperation on 'literally weaken your nails over time'"
    },
    {
        "name": "body1_4_peeling_full",
        "source": f"{INDEXED}/02_problem_comparison/CLIP-0006_problem_pink-nail-peeling-off.mov",
        "start": 0.0, "duration": 2.0,
        "notes": "12.10-14.10 | Peel sequence on 'I had no idea until I started'"
    },
    {
        "name": "body1_5_brittle_again",
        "source": f"{INDEXED}/02_problem_comparison/CLIP-0009_problem_brittle-damaged-nail-closeup.mov",
        "start": 0.0, "duration": 1.36,
        "notes": "14.10-15.46 | Brittle close-up on 'losing layers'"
    },

    # ── BODY 2: 15.46 - 26.58s (11.12s total) ────────────────
    # "Then I found Glamour Dip." (16.58-16.80)
    # "It's completely free from harsh chemicals," (ends 19.50)
    # "doesn't need a UV lamp," (ends 20.88)
    # "and it's packed with vitamin E, jojoba oil, and calcium
    #  that actually nourish your nails while you wear it." (ends 26.58)
    {
        "name": "body2_1_transition",
        "source": f"{INDEXED}/03_application_process/CLIP-0010_process_hp-purple-bg-daydream-dip-macro.mp4",
        "start": 0.0, "duration": 1.92,
        "notes": "15.46-17.38 | Purple BG dip macro - beat + 'Then I found Glamour Dip'"
    },
    {
        "name": "body2_2_base_apply",
        "source": f"{INDEXED}/03_application_process/CLIP-0001_process_red-french-tip-full-application.mp4",
        "start": 0.0, "duration": 2.12,
        "notes": "17.38-19.50 | Base glaze on 'completely free from harsh chemicals'"
    },
    {
        "name": "body2_3_red_dip",
        "source": f"{INDEXED}/03_application_process/CLIP-0001_process_red-french-tip-full-application.mp4",
        "start": 1.3, "duration": 1.38,
        "notes": "19.50-20.88 | Dipping red powder on 'doesn't need a UV lamp'"
    },
    {
        "name": "body2_4_seal",
        "source": f"{INDEXED}/03_application_process/CLIP-0001_process_red-french-tip-full-application.mp4",
        "start": 9.3, "duration": 2.33,
        "notes": "20.88-23.21 | Seal/glaze coat on 'packed with vitamin E, jojoba oil'"
    },
    {
        "name": "body2_5_heal",
        "source": f"{INDEXED}/03_application_process/CLIP-0013_process_heal-application-blackout-outdoor.mov",
        "start": 0.0, "duration": 3.37,
        "notes": "23.21-26.58 | Heal application on 'calcium that actually nourish your nails while you wear it'"
    },

    # ── BODY 3: 26.58 - 36.04s (9.46s total) ─────────────────
    # "I'm talking gel-like shine with acrylic-level strength
    #  that lasts up to six weeks," (ends 31.42)
    # "and each kit gives you up to a year's worth of manis
    #  for about three dollars each." (ends 36.04)
    {
        "name": "body3_1_whiteboard",
        "source": f"{INDEXED}/01_hooks/text_reveals/CLIP-0004_hooks_text-whiteboard-5weeks-easy-removal.mov",
        "start": 0.0, "duration": 2.18,
        "notes": "26.58-28.76 | Whiteboard 5 weeks on 'gel-like shine with acrylic-level strength'"
    },
    {
        "name": "body3_2_5finger",
        "source": f"{INDEXED}/01_hooks/5_finger_dips/CLIP-0005_hooks_5finger-dip-pastel-rainbow-v1pt1.mov",
        "start": 0.0, "duration": 2.50,
        "notes": "28.76-31.26 | 5 finger pastel dip on 'lasts up to six weeks'"
    },
    {
        "name": "body3_3_before_after",
        "source": f"{INDEXED}/03_application_process/CLIP-0011_process_cx-before-after-boujee-nude-coffin.mp4",
        "start": 0.0, "duration": 3.49,
        "notes": "31.42-34.91 | Before/after Boujee on 'each kit gives you up to a year's worth'"
    },
    {
        "name": "body3_4_blackout_beauty",
        "source": f"{INDEXED}/03_application_process/CLIP-0013_process_heal-application-blackout-outdoor.mov",
        "start": 1.2, "duration": 1.13,
        "notes": "34.91-36.04 | Blackout nails sunlight on 'about three dollars each'"
    },

    # ── BODY 4: 36.04 - 40.38s (4.34s total) ─────────────────
    # "Do the salon maths on that one." (37.52-38.94)
    # + silence gap before CTA
    {
        "name": "body4_1_baby_hand",
        "source": f"{INDEXED}/01_hooks/eye_catching_nails/CLIP-0002_hooks_baby-hand-glitter-zoom.mov",
        "start": 0.0, "duration": 0.78,
        "notes": "36.04-36.82 | Baby hand glitter - quick lifestyle flash"
    },
    {
        "name": "body4_2_removal_chill",
        "source": f"{INDEXED}/03_application_process/CLIP-0012_process_easy-removal-couch-tv-lifestyle.mov",
        "start": 0.5, "duration": 2.0,
        "notes": "36.82-38.82 | Couch removal on 'Do the salon maths on that one'"
    },
    {
        "name": "body4_3_powder_tease",
        "source": f"{INDEXED}/01_hooks/eye_catching_product/CLIP-0003_hooks_purple-powder-pour-plate.mov",
        "start": 0.0, "duration": 1.56,
        "notes": "38.82-40.38 | Purple powder pour tease - bridge to CTA silence"
    },

    # ── CTA: 40.38 - ~54.5s (14.12s total) ───────────────────
    # "Right now, every Glamour Dip kit comes with a free mystery
    #  gift worth fifty dollars, plus free shipping." (40.38-45.80)
    # "And if you don't love it, you're covered by our money back
    #  guarantee." (47.28-50.02)
    # "Click the link and treat your nails to something better."
    #  (51.36-53.62) + ~1s pad
    {
        "name": "cta_1_powder_pour",
        "source": f"{INDEXED}/01_hooks/eye_catching_product/CLIP-0003_hooks_purple-powder-pour-plate.mov",
        "start": 1.5, "duration": 3.0,
        "notes": "40.38-43.38 | Powder pour beauty on 'every Glamour Dip kit comes with a free mystery gift'"
    },
    {
        "name": "cta_2_powder_spread",
        "source": f"{INDEXED}/01_hooks/eye_catching_product/CLIP-0003_hooks_purple-powder-pour-plate.mov",
        "start": 3.5, "duration": 2.17,
        "notes": "43.38-45.55 | Powder spread on 'worth fifty dollars, plus free shipping'"
    },
    {
        "name": "cta_3_5finger_dip",
        "source": f"{INDEXED}/01_hooks/5_finger_dips/CLIP-0005_hooks_5finger-dip-pastel-rainbow-v1pt1.mov",
        "start": 0.5, "duration": 1.73,
        "notes": "45.55-47.28 | Pastel dip - visual bridge in silence gap"
    },
    {
        "name": "cta_4_dip_macro",
        "source": f"{INDEXED}/03_application_process/CLIP-0010_process_hp-purple-bg-daydream-dip-macro.mp4",
        "start": 0.5, "duration": 2.04,
        "notes": "47.28-49.32 | Daydream dip on 'money back guarantee'"
    },
    {
        "name": "cta_5_red_reveal",
        "source": f"{INDEXED}/03_application_process/CLIP-0001_process_red-french-tip-full-application.mp4",
        "start": 10.0, "duration": 2.60,
        "notes": "49.32-51.92 | Red reveal - visual bridge in silence gap"
    },
    {
        "name": "cta_6_final_hero",
        "source": f"{INDEXED}/03_application_process/CLIP-0001_process_red-french-tip-full-application.mp4",
        "start": 10.8, "duration": 2.58,
        "notes": "51.92-54.50 | Final hero shot on 'Click the link...something better' + pad"
    },
]

# Verify total EDL duration
total_edl = sum(c['duration'] for c in edl)
print(f"Total EDL duration: {total_edl:.2f}s (target: ~54.5s)")

# Target format: 1080x1920 portrait, 30fps
TARGET_W = 1080
TARGET_H = 1920
TARGET_FPS = 30

print("=" * 60)
print("  GlamrDip Ad Assembly v2 - 'YOU DIDN'T KNOW'")
print("  Transcript-aligned timing")
print("=" * 60)

# Step 1: Extract and normalise each clip segment
print("\n[1/3] Extracting and normalising clip segments...\n")

segment_files = []
for i, cut in enumerate(edl):
    outfile = f"{WORK}/seg_{i:02d}_{cut['name']}.mp4"
    segment_files.append(outfile)

    if os.path.exists(outfile):
        print(f"  [{i+1:02d}/{len(edl)}] SKIP (exists): {cut['name']}")
        continue

    src = cut['source']
    if not os.path.exists(src):
        print(f"  [{i+1:02d}/{len(edl)}] ERROR - source not found: {src}")
        continue

    vf = (
        f"fps={TARGET_FPS},"
        f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1"
    )

    cmd = [
        'ffmpeg', '-y',
        '-ss', str(cut['start']),
        '-i', src,
        '-t', str(cut['duration']),
        '-vf', vf,
        '-an',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-pix_fmt', 'yuv420p',
        outfile
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        size = os.path.getsize(outfile)
        print(f"  [{i+1:02d}/{len(edl)}] OK: {cut['name']} ({size//1024}KB)")
    else:
        print(f"  [{i+1:02d}/{len(edl)}] FAIL: {cut['name']}")
        print(f"    {result.stderr[-200:]}")

# Step 2: Create concat file and check durations
print("\n[2/3] Creating concat list...\n")

concat_file = f"{WORK}/concat_list.txt"
with open(concat_file, 'w') as f:
    for seg in segment_files:
        if os.path.exists(seg):
            f.write(f"file '{seg}'\n")

total_dur = 0
for seg in segment_files:
    if os.path.exists(seg):
        probe = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', seg],
            capture_output=True, text=True
        )
        try:
            d = json.loads(probe.stdout)
            dur = float(d['format']['duration'])
            total_dur += dur
        except:
            pass

print(f"  Total video duration: {total_dur:.2f}s")
print(f"  Voiceover ends at:    53.62s")
print(f"  Target video length:  ~54.5s")

# Step 3: Concatenate all segments and add voiceover
print("\n[3/3] Assembling final ad...\n")

concat_video = f"{WORK}/concat_video.mp4"
cmd_concat = [
    'ffmpeg', '-y',
    '-f', 'concat', '-safe', '0',
    '-i', concat_file,
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
    '-pix_fmt', 'yuv420p',
    '-an',
    concat_video
]
result = subprocess.run(cmd_concat, capture_output=True, text=True)
if result.returncode != 0:
    print(f"  CONCAT FAILED: {result.stderr[-300:]}")
else:
    probe = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', concat_video],
        capture_output=True, text=True
    )
    d = json.loads(probe.stdout)
    print(f"  Video concatenated OK ({float(d['format']['duration']):.2f}s)")

# Combine with voiceover - use -shortest so it trims to whichever is shorter
# Since our video should now be >= voiceover length, the audio determines length
cmd_final = [
    'ffmpeg', '-y',
    '-i', concat_video,
    '-i', VOICEOVER,
    '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '192k',
    '-shortest',
    '-movflags', '+faststart',
    OUTPUT
]
result = subprocess.run(cmd_final, capture_output=True, text=True)
if result.returncode != 0:
    print(f"  FINAL MUX FAILED: {result.stderr[-300:]}")
else:
    size = os.path.getsize(OUTPUT) / (1024 * 1024)
    # Get final duration
    probe = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', OUTPUT],
        capture_output=True, text=True
    )
    d = json.loads(probe.stdout)
    final_dur = float(d['format']['duration'])
    print(f"  FINAL AD EXPORTED: {OUTPUT}")
    print(f"  Duration: {final_dur:.2f}s")
    print(f"  File size: {size:.1f}MB")

print("\n" + "=" * 60)
print("  Assembly v2 complete!")
print("=" * 60)
