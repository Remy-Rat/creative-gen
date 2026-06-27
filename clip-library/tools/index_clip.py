#!/usr/bin/env python3
"""
GlamrDip Clip Indexer v1.0
==========================
Extracts keyframes from video clips using scene detection + interval sampling,
and generates a skeleton JSON index ready for AI analysis.

Usage:
    python3 index_clip.py <video_file>
    python3 index_clip.py <video_file> --clip-id CLIP-0002
    python3 index_clip.py --batch <folder_of_videos>

Output:
    - clip-library/indexes/CLIP-XXXX.json  (skeleton index with file metadata + scene timestamps)
    - clip-library/frames/CLIP-XXXX/       (extracted keyframe images for AI review)

The skeleton index includes all file metadata and scene timestamps auto-detected.
Visual descriptions, tags, and AI recommendations should be filled in by reviewing
the extracted frames (either manually or via AI vision model).
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
    """Find the next available CLIP-XXXX ID."""
    existing = glob.glob(os.path.join(index_dir, "CLIP-*.json"))
    if not existing:
        return "CLIP-0001"

    numbers = []
    for f in existing:
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
    result = subprocess.run(cmd, capture_output=True, text=True)

    scenes = []
    for line in result.stderr.split('\n'):
        if 'pts_time' in line and 'showinfo' in line:
            match = re.search(r'pts_time:([\d.]+)', line)
            if match:
                scenes.append(float(match.group(1)))

    return scenes


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

    # Count extracted frames
    frame_count = len(glob.glob(os.path.join(output_dir, '*.png')))
    return frame_count


def format_timestamp(seconds):
    """Convert seconds to MM:SS.mmm format."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:06.3f}"


def build_skeleton_index(video_path, clip_id, probe_data, scene_times):
    """Build a skeleton JSON index with metadata and scene timestamps."""

    # Parse video stream info
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

    # Calculate FPS
    fps_str = video_stream.get('r_frame_rate', '30/1')
    fps_parts = fps_str.split('/')
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(fps_parts[0])

    duration = float(fmt.get('duration', video_stream.get('duration', 0)))
    total_frames = int(video_stream.get('nb_frames', int(duration * fps)))

    # Parse creation date
    created = fmt.get('tags', {}).get('creation_time', '')
    created_date = created[:10] if created else datetime.now().strftime('%Y-%m-%d')

    # Build scene list from detected timestamps
    all_times = [0.0] + scene_times + [duration]
    all_times = sorted(set(all_times))

    scenes = []
    for i in range(len(all_times) - 1):
        start = all_times[i]
        end = all_times[i + 1]
        scene_duration = end - start

        start_frame = int(start * fps)
        end_frame = int(end * fps)

        scenes.append({
            "scene_number": i + 1,
            "timestamp_start": format_timestamp(start),
            "timestamp_end": format_timestamp(end),
            "duration_seconds": round(scene_duration, 3),
            "frame_range": {
                "start": start_frame,
                "end": end_frame
            },
            "description": "TODO: Review extracted frames and describe visual content",
            "visual_content": {
                "subject": "TODO",
                "framing": "close_up",
                "dominant_colours": [],
                "text_overlays": [],
                "props_visible": []
            },
            "motion": {
                "camera_movement": "static",
                "subject_movement": "TODO: Describe hand/finger movement",
                "transition_in": "cut" if i > 0 else "none",
                "transition_out": "cut" if i < len(all_times) - 2 else "none",
                "movement_intensity": "slow"
            },
            "process_step": "TODO",
            "ai_editing_notes": "TODO: Add notes for AI editor"
        })

    # Build the full index
    index = {
        "clip_id": clip_id,
        "file": {
            "filename": os.path.basename(str(video_path)),
            "format": f"mp4 ({video_stream.get('codec_name', 'unknown')}/{audio_stream.get('codec_name', 'unknown') if audio_stream else 'no_audio'})",
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
            "category": "TODO: tutorial|product_showcase|before_after|testimonial|lifestyle|unboxing|comparison|raw_footage",
            "nail_style": "TODO: e.g. french_tip, solid_colour, ombre, glitter, nail_art",
            "colours": [],
            "products_visible": [],
            "process_steps_shown": [],
            "content_summary": "TODO: 1-2 sentence summary",
            "ad_suitability": {
                "hero_shot": False,
                "process_footage": False,
                "close_up_quality": "good",
                "lighting_quality": "good",
                "background": "TODO: Describe background"
            }
        },
        "scenes": scenes,
        "tags": {
            "visual_tags": [],
            "mood_tags": [],
            "technique_tags": [],
            "ad_use_tags": []
        },
        "ai_recommendations": {
            "best_segments": [],
            "voiceover_alignment_hints": []
        }
    }

    return index


def index_single_clip(video_path, clip_id=None, library_dir=None):
    """Index a single video clip."""
    video_path = Path(video_path).resolve()

    if not video_path.exists():
        print(f"Error: File not found: {video_path}")
        return None

    if library_dir is None:
        library_dir = video_path.parent / "clip-library"
    else:
        library_dir = Path(library_dir)

    index_dir = library_dir / "indexes"
    frames_dir = library_dir / "frames"

    os.makedirs(index_dir, exist_ok=True)
    os.makedirs(frames_dir, exist_ok=True)

    if clip_id is None:
        clip_id = get_next_clip_id(str(index_dir))

    print(f"\n{'='*60}")
    print(f"  Indexing: {video_path.name}")
    print(f"  Clip ID: {clip_id}")
    print(f"{'='*60}\n")

    # Step 1: Get metadata
    print("[1/4] Extracting video metadata...")
    probe_data = get_video_metadata(video_path)

    # Step 2: Detect scenes
    print("[2/4] Detecting scene changes...")
    scene_times = detect_scenes(video_path)
    print(f"       Found {len(scene_times)} scene changes")

    # Step 3: Extract frames
    clip_frames_dir = frames_dir / clip_id
    print(f"[3/4] Extracting keyframes to {clip_frames_dir}/")
    frame_count = extract_frames(video_path, str(clip_frames_dir), scene_times)
    print(f"       Extracted {frame_count} frames")

    # Step 4: Build skeleton index
    print("[4/4] Building skeleton index...")
    index = build_skeleton_index(video_path, clip_id, probe_data, scene_times)

    # Save index
    index_path = index_dir / f"{clip_id}.json"
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"\n  Index saved: {index_path}")
    print(f"  Frames saved: {clip_frames_dir}/")
    print(f"  Scenes detected: {len(index['scenes'])}")
    print(f"  Duration: {index['file']['duration_seconds']}s")
    print(f"\n  NOTE: Review extracted frames and fill in TODO fields in the index.")
    print(f"        Or feed the frames + skeleton to an AI vision model for auto-fill.\n")

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
    print(f"  Batch complete: {len(results)}/{len(videos)} clips indexed")
    print(f"{'='*60}\n")

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='GlamrDip Clip Indexer - Extract and index video clips for AI ad production'
    )
    parser.add_argument('input', help='Video file path or folder (with --batch)')
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
