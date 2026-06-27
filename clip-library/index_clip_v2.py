#!/usr/bin/env python3
"""
GlamrDip Clip Indexer v2.0
===========================
Extracts keyframes, detects scenes, analyses audio, and generates a v2 schema
skeleton JSON index ready for AI vision review.

Changes from v1:
  - v2 schema: script_roles, emotional_beat, visual_energy, hook_strength,
    usable_range, action_climax, visual_fingerprint, pairs_with_topics
  - Audio analysis: detects voice, music, silence, ASMR potential
  - Platform metadata: aspect ratio, crop suitability, subject position
  - Flat tag structure with type prefixes
  - Performance tracking block (initialised empty)

Usage:
    python3 index_clip_v2.py <video_file>
    python3 index_clip_v2.py <video_file> --clip-id CLIP-0015
    python3 index_clip_v2.py --batch <folder_of_videos>

Output:
    - clip-library/indexes_v2/CLIP-XXXX.json  (skeleton index)
    - clip-library/frames/CLIP-XXXX/          (extracted keyframe images for AI review)

The skeleton has TODO fields for visual descriptions, roles, and scoring.
Review extracted frames (manually or via AI vision) to fill these in.
"""

import subprocess
import json
import sys
import os
import re
import glob
import argparse
from pathlib import Path
from datetime import datetime


def get_next_clip_id(index_dir):
    """Find the next available CLIP-XXXX ID across both v1 and v2 indexes."""
    # Check both index dirs to avoid ID collisions
    patterns = [
        os.path.join(index_dir, "CLIP-*.json"),
        os.path.join(os.path.dirname(index_dir), "indexes", "CLIP-*.json"),
    ]
    numbers = []
    for pattern in patterns:
        for f in glob.glob(pattern):
            match = re.search(r'CLIP-(\d+)', os.path.basename(f))
            if match:
                numbers.append(int(match.group(1)))

    next_num = max(numbers) + 1 if numbers else 1
    return f"CLIP-{next_num:04d}"


def get_video_metadata(video_path):
    """Extract video metadata using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


def detect_scenes(video_path, threshold=0.3):
    """Detect scene changes using ffmpeg's scene detection filter."""
    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-vf', f"select='gt(scene,{threshold})',showinfo",
        '-vsync', 'vfr',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, capture_output=True)
    stderr_text = result.stderr.decode('utf-8', errors='replace')

    scenes = []
    for line in stderr_text.split('\n'):
        if 'pts_time' in line and 'showinfo' in line:
            match = re.search(r'pts_time:([\d.]+)', line)
            if match:
                scenes.append(float(match.group(1)))

    return scenes


def analyse_audio(video_path, duration):
    """Analyse audio stream for voice, music, silence, and ASMR potential."""
    audio_info = {
        "has_voice": False,
        "has_asmr": False,
        "has_music": False,
        "audio_quality": "silent",
        "asmr_moments": [],
        "assembly_recommendation": "strip"
    }

    # Check if audio stream exists
    cmd = [
        'ffprobe', '-v', 'quiet', '-select_streams', 'a',
        '-show_entries', 'stream=codec_name,sample_rate,bit_rate',
        '-print_format', 'json', str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    probe = json.loads(result.stdout)

    if not probe.get('streams'):
        return audio_info

    # Detect silence to understand audio content
    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-af', 'silencedetect=noise=-35dB:d=0.3',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, capture_output=True)
    stderr_text = result.stderr.decode('utf-8', errors='replace')

    # Parse silence segments
    silence_starts = re.findall(r'silence_start: ([\d.]+)', stderr_text)
    silence_ends = re.findall(r'silence_end: ([\d.]+)', stderr_text)

    total_silence = 0
    for start, end in zip(silence_starts, silence_ends):
        total_silence += float(end) - float(start)

    silence_ratio = total_silence / duration if duration > 0 else 1.0

    # Detect volume levels for non-silent sections
    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-af', 'volumedetect',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, capture_output=True)
    stderr_text = result.stderr.decode('utf-8', errors='replace')

    mean_volume = -100
    max_volume = -100
    mean_match = re.search(r'mean_volume: ([-\d.]+)', stderr_text)
    max_match = re.search(r'max_volume: ([-\d.]+)', stderr_text)
    if mean_match:
        mean_volume = float(mean_match.group(1))
    if max_match:
        max_volume = float(max_match.group(1))

    # Classify audio based on analysis
    if silence_ratio > 0.9 or mean_volume < -50:
        audio_info["audio_quality"] = "silent"
        audio_info["assembly_recommendation"] = "strip"
    elif mean_volume > -25:
        # Loud audio - likely has music or voice
        audio_info["audio_quality"] = "clean"
        audio_info["has_music"] = True  # TODO: mark for human review
        audio_info["assembly_recommendation"] = "mute"
    elif mean_volume > -40:
        # Moderate audio - could be ASMR/ambient
        audio_info["audio_quality"] = "usable"
        audio_info["has_asmr"] = True  # TODO: mark for human review
        audio_info["assembly_recommendation"] = "keep_and_duck"
    else:
        audio_info["audio_quality"] = "noisy"
        audio_info["assembly_recommendation"] = "mute"

    return audio_info


def calculate_platform_suitability(width, height, orientation):
    """Determine crop suitability for Meta ad placements."""
    ratio = width / height if height > 0 else 1

    platform = {
        "aspect_ratio_native": "",
        "crop_suitability": {
            "9_16": "unsuitable",
            "4_5": "unsuitable",
            "1_1": "unsuitable"
        },
        "subject_position": "centre",
        "safe_zone_clear": True  # TODO: mark for human review
    }

    # Determine native ratio
    if abs(ratio - 9/16) < 0.05:
        platform["aspect_ratio_native"] = "9:16"
        platform["crop_suitability"]["9_16"] = "native"
        platform["crop_suitability"]["4_5"] = "crop_safe"
        platform["crop_suitability"]["1_1"] = "crop_risky"
    elif abs(ratio - 4/5) < 0.05:
        platform["aspect_ratio_native"] = "4:5"
        platform["crop_suitability"]["9_16"] = "crop_risky"
        platform["crop_suitability"]["4_5"] = "native"
        platform["crop_suitability"]["1_1"] = "crop_safe"
    elif abs(ratio - 1) < 0.05:
        platform["aspect_ratio_native"] = "1:1"
        platform["crop_suitability"]["9_16"] = "crop_risky"
        platform["crop_suitability"]["4_5"] = "crop_safe"
        platform["crop_suitability"]["1_1"] = "native"
    elif abs(ratio - 16/9) < 0.05:
        platform["aspect_ratio_native"] = "16:9"
        platform["crop_suitability"]["9_16"] = "unsuitable"
        platform["crop_suitability"]["4_5"] = "crop_risky"
        platform["crop_suitability"]["1_1"] = "crop_safe"
    else:
        platform["aspect_ratio_native"] = f"{width}:{height}"
        # Guess based on orientation
        if orientation == "portrait":
            platform["crop_suitability"]["9_16"] = "crop_safe"
            platform["crop_suitability"]["4_5"] = "crop_safe"
        elif orientation == "landscape":
            platform["crop_suitability"]["4_5"] = "crop_risky"
            platform["crop_suitability"]["1_1"] = "crop_safe"

    return platform


def extract_frames(video_path, output_dir, scene_times, interval=1.0):
    """Extract frames at scene changes and regular intervals."""
    os.makedirs(output_dir, exist_ok=True)

    # Extract scene-change frames
    for i, t in enumerate(scene_times):
        output = os.path.join(output_dir, f"scene_{i+1:03d}.png")
        cmd = [
            'ffmpeg', '-y', '-ss', str(t), '-i', str(video_path),
            '-vframes', '1', '-q:v', '2', output
        ]
        subprocess.run(cmd, capture_output=True)

    # Extract interval frames
    cmd = [
        'ffmpeg', '-y', '-i', str(video_path),
        '-vf', f'fps=1/{interval}',
        os.path.join(output_dir, 'interval_%03d.png')
    ]
    subprocess.run(cmd, capture_output=True)

    frame_count = len(glob.glob(os.path.join(output_dir, '*.png')))
    return frame_count


def format_timestamp(seconds):
    """Convert seconds to MM:SS.mmm format."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:06.3f}"


def build_skeleton_index(video_path, clip_id, probe_data, scene_times, audio_info):
    """Build a v2 skeleton JSON index."""

    video_stream = None
    audio_stream = None
    for stream in probe_data.get('streams', []):
        if stream['codec_type'] == 'video' and not video_stream:
            video_stream = stream
        elif stream['codec_type'] == 'audio' and not audio_stream:
            audio_stream = stream

    fmt = probe_data.get('format', {})

    width = int(video_stream.get('width', 0))
    height = int(video_stream.get('height', 0))

    if width > height:
        orientation = 'landscape'
    elif height > width:
        orientation = 'portrait'
    else:
        orientation = 'square'

    fps_str = video_stream.get('r_frame_rate', '30/1')
    fps_parts = fps_str.split('/')
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(fps_parts[0])

    duration = float(fmt.get('duration', video_stream.get('duration', 0)))
    total_frames = int(video_stream.get('nb_frames', int(duration * fps)))

    created = fmt.get('tags', {}).get('creation_time', '')
    created_date = created[:10] if created else datetime.now().strftime('%Y-%m-%d')

    codec_v = video_stream.get('codec_name', 'unknown')
    codec_a = audio_stream.get('codec_name', 'no_audio') if audio_stream else 'no_audio'

    # Build scene list
    all_times = [0.0] + scene_times + [duration]
    all_times = sorted(set(all_times))

    scenes = []
    for i in range(len(all_times) - 1):
        start = all_times[i]
        end = all_times[i + 1]
        scene_duration = round(end - start, 3)

        start_frame = int(start * fps)
        end_frame = int(end * fps)

        # Calculate usable range defaults
        min_use = max(0.5, round(scene_duration * 0.4, 1))
        sweet = round(scene_duration * 0.7, 1)

        scenes.append({
            "scene_number": i + 1,
            "timestamp_start": format_timestamp(start),
            "timestamp_end": format_timestamp(end),
            "duration_seconds": scene_duration,
            "frame_range": {"start": start_frame, "end": end_frame},

            "description": "TODO: Review extracted frames and describe visual content",

            "script_roles": ["TODO: pick from: hook_shock, hook_curiosity, hook_beauty, problem_visual, problem_frustration, problem_damage, product_intro, product_hero, product_branding, process_step, process_montage, process_satisfying_moment, result_reveal, result_before_after, result_durability, social_proof, lifestyle, ugc_authentic, cta_visual, transition_filler"],

            "emotional_beat": "TODO: pick from: shock, empathy, curiosity, satisfaction, desire, trust, urgency",

            "visual_energy": 3,
            "hook_strength": 1,

            "usable_range": {
                "min_seconds": min_use,
                "max_seconds": round(scene_duration, 1),
                "sweet_spot": sweet
            },

            "action_climax": {
                "timestamp": format_timestamp(start + scene_duration * 0.5),
                "action": "TODO: describe peak visual moment"
            },

            "visual_content": {
                "subject": "TODO",
                "framing": "close_up",
                "dominant_colours": [],
                "props_visible": []
            },

            "motion": {
                "camera_movement": "static",
                "subject_movement": "TODO: describe hand/finger movement",
                "movement_intensity": "slow"
            },

            "visual_fingerprint": "TODO: short unique visual description for dedup",

            "process_step": "TODO: pick from: prep, tips_application, bond, base_application, dip_clear, dip_colour, brush_dust, seal, glow, care, final_reveal, removal (see products.json)",

            "pairs_with_topics": [],

            "hook_strength": 1
        })

    # Calculate platform suitability
    platform = calculate_platform_suitability(width, height, orientation)

    # Build the full v2 index
    index = {
        "clip_id": clip_id,

        "file": {
            "filename": os.path.basename(str(video_path)),
            "renamed_to": "",
            "original_path": str(video_path),
            "indexed_path": "",
            "format": f"{Path(video_path).suffix[1:]} ({codec_v}/{codec_a})",
            "resolution": f"{width}x{height}",
            "orientation": orientation,
            "fps": round(fps, 2),
            "duration_seconds": round(duration, 2),
            "total_frames": total_frames,
            "file_size_mb": round(int(fmt.get('size', 0)) / (1024 * 1024), 2),
            "has_audio": audio_stream is not None,
            "created_date": created_date
        },

        "metadata": {
            "category": "TODO: pick from: hooks, problem_comparison, application_process, product_showcase, results_reveals, ugc_testimonial, text_overlay_base, lifestyle, raw_footage",
            "nail_style": "TODO",
            "colours": [],
            "products_visible": "TODO: pick from: bond_bottle, base_bottle, seal_bottle, glow_bottle, care_bottle, soak_bottle, clear_powder_pot, colour_powder_pot, 180_grit_file, 240_grit_file, cuticle_pusher, dust_brush, pre_shaped_tips, removal_solution, purple_kit_box, instruction_booklet, other",
            "process_steps_shown": "TODO: pick from: prep, tips_application, bond, base_application, dip_clear, dip_colour, brush_dust, seal, glow, care, final_reveal, removal",
            "content_summary": "TODO: 1-2 sentence summary",
            "quality": {
                "close_up_quality": "good",
                "lighting_quality": "good",
                "background": "TODO: describe background",
                "overall_production": "TODO: professional, semi_pro, casual, raw"
            }
        },

        "platform": platform,
        "audio": audio_info,
        "scenes": scenes,

        "tags": [
            "TODO: add tags with prefixes - visual:xxx, mood:xxx, technique:xxx, role:xxx"
        ],

        "ai_recommendations": {
            "best_segments": [],
            "pairs_well_with": []
        },

        "performance": {
            "times_used": 0,
            "ads_used_in": [],
            "best_position": "",
            "notes": ""
        }
    }

    return index


def index_single_clip(video_path, clip_id=None, library_dir=None):
    """Index a single video clip with v2 schema."""
    video_path = Path(video_path).resolve()

    if not video_path.exists():
        print(f"Error: File not found: {video_path}")
        return None

    if library_dir is None:
        library_dir = video_path.parent / "clip-library"
    else:
        library_dir = Path(library_dir)

    index_dir = library_dir / "indexes_v2"
    frames_dir = library_dir / "frames"

    os.makedirs(index_dir, exist_ok=True)
    os.makedirs(frames_dir, exist_ok=True)

    if clip_id is None:
        clip_id = get_next_clip_id(str(index_dir))

    print(f"\n{'='*60}")
    print(f"  Indexing (v2): {video_path.name}")
    print(f"  Clip ID: {clip_id}")
    print(f"{'='*60}\n")

    # Step 1: Metadata
    print("[1/5] Extracting video metadata...")
    probe_data = get_video_metadata(video_path)

    # Step 2: Scene detection
    print("[2/5] Detecting scene changes...")
    scene_times = detect_scenes(video_path)
    print(f"       Found {len(scene_times)} scene changes")

    # Step 3: Audio analysis
    duration = float(probe_data.get('format', {}).get('duration', 0))
    print("[3/5] Analysing audio...")
    audio_info = analyse_audio(video_path, duration)
    print(f"       Audio: quality={audio_info['audio_quality']}, "
          f"asmr={audio_info['has_asmr']}, voice={audio_info['has_voice']}, "
          f"recommendation={audio_info['assembly_recommendation']}")

    # Step 4: Extract frames
    clip_frames_dir = frames_dir / clip_id
    print(f"[4/5] Extracting keyframes to {clip_frames_dir}/")
    frame_count = extract_frames(video_path, str(clip_frames_dir), scene_times)
    print(f"       Extracted {frame_count} frames")

    # Step 5: Build skeleton
    print("[5/5] Building v2 skeleton index...")
    index = build_skeleton_index(video_path, clip_id, probe_data, scene_times, audio_info)

    # Save
    index_path = index_dir / f"{clip_id}.json"
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"\n  Index saved:    {index_path}")
    print(f"  Frames saved:   {clip_frames_dir}/")
    print(f"  Scenes:         {len(index['scenes'])}")
    print(f"  Duration:       {index['file']['duration_seconds']}s")
    print(f"  Orientation:    {index['file']['orientation']}")
    print(f"  Platform 9:16:  {index['platform']['crop_suitability']['9_16']}")
    print(f"  Platform 4:5:   {index['platform']['crop_suitability']['4_5']}")
    print(f"  Audio:          {audio_info['assembly_recommendation']}")
    print(f"\n  NOTE: Review frames and fill in TODO fields.")
    print(f"        Feed frames + skeleton to AI vision for auto-fill.\n")

    return index


def batch_index(folder_path, library_dir=None):
    """Index all video files in a folder."""
    folder = Path(folder_path)
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}

    videos = [f for f in folder.iterdir()
              if f.suffix.lower() in video_extensions and not f.name.startswith('.')]

    if not videos:
        print(f"No video files found in {folder}")
        return

    print(f"\nFound {len(videos)} video(s) to index:\n")
    for v in sorted(videos):
        print(f"  - {v.name}")

    results = []
    for video in sorted(videos):
        try:
            index = index_single_clip(video, library_dir=library_dir)
            if index:
                results.append(index)
        except Exception as e:
            print(f"\nError indexing {video.name}: {e}")

    print(f"\n{'='*60}")
    print(f"  Batch complete: {len(results)}/{len(videos)} clips indexed (v2 schema)")
    print(f"{'='*60}\n")

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='GlamrDip Clip Indexer v2 - Index clips for AI ad assembly'
    )
    parser.add_argument('input', help='Video file or folder (with --batch)')
    parser.add_argument('--clip-id', help='Override clip ID (default: auto-increment)')
    parser.add_argument('--batch', action='store_true', help='Index all videos in a folder')
    parser.add_argument('--library-dir', help='Override clip library directory')
    parser.add_argument('--scene-threshold', type=float, default=0.3,
                       help='Scene detection sensitivity (0.0-1.0, lower = more scenes)')

    args = parser.parse_args()

    if args.batch:
        batch_index(args.input, library_dir=args.library_dir)
    else:
        index_single_clip(args.input, clip_id=args.clip_id, library_dir=args.library_dir)
