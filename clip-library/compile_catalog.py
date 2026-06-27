#!/usr/bin/env python3
"""
GlamrDip Catalog Compiler v1.0
================================
Reads all CLIP-XXXX.json index files (v2 schema) and generates a lightweight
catalog.json that an AI can read to select clips without loading every full index.

The catalog strips out heavy scene descriptions and keeps only what the AI
assembler needs for clip selection:
  - clip_id, duration, orientation, category, colours, quality
  - per-scene: script_roles, emotional_beat, visual_energy, hook_strength,
    usable_range, action_climax, visual_fingerprint, pairs_with_topics, process_step
  - tags (flat list)
  - platform suitability
  - audio assembly recommendation
  - performance data (if any)

Usage:
    python3 compile_catalog.py
    python3 compile_catalog.py --index-dir path/to/indexes_v2
    python3 compile_catalog.py --output path/to/catalog.json

The AI workflow is:
  1. Read catalog.json (lightweight) to select clips for an ad script
  2. Load full CLIP-XXXX.json only for selected clips (for exact timestamps, descriptions)
  3. Build the EDL from the full indexes
"""

import json
import os
import glob
import argparse
from datetime import datetime


def compile_scene_summary(scene):
    """Extract only the fields the AI assembler needs from a scene."""
    return {
        "scene_number": scene["scene_number"],
        "start": scene["timestamp_start"],
        "end": scene["timestamp_end"],
        "duration": scene.get("duration_seconds", 0),
        "script_roles": scene.get("script_roles", []),
        "emotional_beat": scene.get("emotional_beat", ""),
        "visual_energy": scene.get("visual_energy", 3),
        "hook_strength": scene.get("hook_strength", 1),
        "usable_range": scene.get("usable_range", {}),
        "action_climax": scene.get("action_climax", {}),
        "visual_fingerprint": scene.get("visual_fingerprint", ""),
        "pairs_with_topics": scene.get("pairs_with_topics", []),
        "process_step": scene.get("process_step"),
        "framing": scene.get("visual_content", {}).get("framing", ""),
        "subject": scene.get("visual_content", {}).get("subject", "")
    }


def compile_clip_entry(index_data):
    """Compile a single clip index into a lightweight catalog entry."""

    file_info = index_data.get("file", {})
    metadata = index_data.get("metadata", {})
    platform = index_data.get("platform", {})
    audio = index_data.get("audio", {})
    performance = index_data.get("performance", {})

    # Compile scene summaries
    scenes = [compile_scene_summary(s) for s in index_data.get("scenes", [])]

    # Collect all unique script_roles across scenes
    all_roles = set()
    for s in scenes:
        all_roles.update(s.get("script_roles", []))

    # Get max hook_strength across all scenes
    max_hook = max((s.get("hook_strength", 1) for s in scenes), default=1)

    entry = {
        "clip_id": index_data["clip_id"],
        "duration": file_info.get("duration_seconds", 0),
        "orientation": file_info.get("orientation", "unknown"),
        "resolution": file_info.get("resolution", ""),
        "category": metadata.get("category", ""),
        "nail_style": metadata.get("nail_style", ""),
        "colours": metadata.get("colours", []),
        "products_visible": metadata.get("products_visible", []),
        "process_steps": metadata.get("process_steps_shown", []),
        "summary": metadata.get("content_summary", ""),
        "quality": metadata.get("quality", {}).get("overall_production", ""),
        "lighting": metadata.get("quality", {}).get("lighting_quality", ""),

        "platform": {
            "native_ratio": platform.get("aspect_ratio_native", ""),
            "crop_9_16": platform.get("crop_suitability", {}).get("9_16", ""),
            "crop_4_5": platform.get("crop_suitability", {}).get("4_5", ""),
            "subject_position": platform.get("subject_position", ""),
            "safe_zone_clear": platform.get("safe_zone_clear", False)
        },

        "audio": {
            "has_asmr": audio.get("has_asmr", False),
            "has_voice": audio.get("has_voice", False),
            "has_music": audio.get("has_music", False),
            "recommendation": audio.get("assembly_recommendation", "strip")
        },

        "all_script_roles": sorted(list(all_roles)),
        "max_hook_strength": max_hook,
        "tags": index_data.get("tags", []),
        "scenes": scenes,

        "best_segments": index_data.get("ai_recommendations", {}).get("best_segments", []),
        "pairs_well_with": index_data.get("ai_recommendations", {}).get("pairs_well_with", []),

        "performance": {
            "times_used": performance.get("times_used", 0),
            "best_position": performance.get("best_position", ""),
            "notes": performance.get("notes", "")
        }
    }

    return entry


def compile_catalog(index_dir, output_path):
    """Compile all v2 index files into a single catalog."""

    index_files = sorted(glob.glob(os.path.join(index_dir, "CLIP-*.json")))

    if not index_files:
        print(f"No CLIP-*.json files found in {index_dir}")
        return

    print(f"Found {len(index_files)} index files\n")

    entries = []
    errors = []

    for filepath in index_files:
        clip_id = os.path.basename(filepath).replace(".json", "")
        try:
            with open(filepath) as f:
                data = json.load(f)
            entry = compile_clip_entry(data)
            entries.append(entry)
            print(f"  OK: {clip_id} ({entry['duration']:.1f}s, {len(entry['scenes'])} scenes, {len(entry['all_script_roles'])} roles)")
        except Exception as e:
            errors.append(f"{clip_id}: {e}")
            print(f"  FAIL: {clip_id} - {e}")

    # Build catalog
    catalog = {
        "catalog_version": "2.0",
        "compiled_at": datetime.now().isoformat(),
        "total_clips": len(entries),
        "total_scenes": sum(len(e["scenes"]) for e in entries),
        "total_duration_seconds": round(sum(e["duration"] for e in entries), 1),

        "summary": {
            "categories": {},
            "all_script_roles": {},
            "all_colours": {},
            "all_process_steps": {}
        },

        "clips": entries
    }

    # Build summary counts
    for e in entries:
        cat = e["category"]
        catalog["summary"]["categories"][cat] = catalog["summary"]["categories"].get(cat, 0) + 1

        for role in e["all_script_roles"]:
            catalog["summary"]["all_script_roles"][role] = catalog["summary"]["all_script_roles"].get(role, 0) + 1

        for colour in e["colours"]:
            catalog["summary"]["all_colours"][colour] = catalog["summary"]["all_colours"].get(colour, 0) + 1

        for step in e["process_steps"]:
            catalog["summary"]["all_process_steps"][step] = catalog["summary"]["all_process_steps"].get(step, 0) + 1

    # Sort summary dicts by count (descending)
    for key in catalog["summary"]:
        catalog["summary"][key] = dict(
            sorted(catalog["summary"][key].items(), key=lambda x: x[1], reverse=True)
        )

    # Write catalog
    with open(output_path, 'w') as f:
        json.dump(catalog, f, indent=2)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"\n{'='*60}")
    print(f"  Catalog compiled: {output_path}")
    print(f"  Clips: {catalog['total_clips']}")
    print(f"  Scenes: {catalog['total_scenes']}")
    print(f"  Total duration: {catalog['total_duration_seconds']:.1f}s")
    print(f"  File size: {size_kb:.1f}KB")
    if errors:
        print(f"  Errors: {len(errors)}")
        for e in errors:
            print(f"    - {e}")
    print(f"{'='*60}\n")

    return catalog


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compile clip indexes into a lightweight catalog for AI ad assembly'
    )
    parser.add_argument('--index-dir', default='indexes_v2',
                       help='Directory containing CLIP-XXXX.json v2 index files')
    parser.add_argument('--output', default='catalog.json',
                       help='Output path for compiled catalog')

    args = parser.parse_args()

    # Resolve paths relative to clip-library dir
    script_dir = os.path.dirname(os.path.abspath(__file__))
    index_dir = os.path.join(script_dir, args.index_dir)
    output_path = os.path.join(script_dir, args.output)

    compile_catalog(index_dir, output_path)
