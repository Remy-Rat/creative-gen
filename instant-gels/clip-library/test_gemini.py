#!/usr/bin/env python3
"""Quick Gemini connectivity + video-understanding test for the Instant Gels indexer.

Usage:
    python3 test_gemini.py                # connectivity + list flash models + text ping
    python3 test_gemini.py path/to/clip.mp4   # also test real video understanding

Reads the API key from $GEMINI_API_KEY / $GOOGLE_API_KEY, or a .env file next to this script.
See GEMINI_SETUP.md.
"""
import os
import sys
import time
import pathlib


def load_key():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    env = pathlib.Path(__file__).with_name(".env")
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY") and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("No API key. Set GEMINI_API_KEY or add it to .env (see GEMINI_SETUP.md).")


def main():
    try:
        from google import genai
    except ImportError:
        sys.exit("google-genai not installed. Run: python3 -m pip install --user --upgrade google-genai")

    client = genai.Client(api_key=load_key())

    # 1) list Flash models available to this key
    print("Flash models available to your key:")
    flash = []
    for m in client.models.list():
        name = getattr(m, "name", "")
        if "flash" in name.lower():
            flash.append(name)
            print("  -", name)
    if not flash:
        print("  (none found — check the key's project)")

    # pick newest non-lite flash as a sensible default for the text ping
    model = os.environ.get("GEMINI_MODEL")
    if not model:
        non_lite = [f for f in flash if "lite" not in f.lower()]
        model = (non_lite or flash or ["gemini-flash-latest"])[0].replace("models/", "")
    print(f"\nUsing model: {model}")

    # 2) text ping
    r = client.models.generate_content(model=model, contents="Reply with exactly: GEMINI OK")
    print("Text test:", (r.text or "").strip())

    # 3) optional video understanding test
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if not pathlib.Path(path).exists():
            sys.exit(f"File not found: {path}")
        print(f"\nUploading {path} via Files API ...")
        f = client.files.upload(file=path)
        while getattr(f.state, "name", str(f.state)) == "PROCESSING":
            time.sleep(2)
            f = client.files.get(name=f.name)
        print("File state:", getattr(f.state, "name", f.state))
        prompt = ("In ONE sentence say what happens in this video, and give the start and end as MM:SS "
                  "timestamps. This confirms you can watch the video and report timing.")
        r = client.models.generate_content(model=model, contents=[f, prompt])
        print("Video test:", (r.text or "").strip())
        print("\nAll good — Gemini can watch video and return timestamps.")
    else:
        print("\n(!) No clip passed. Re-run with a clip path to test video understanding:")
        print("    python3 test_gemini.py /path/to/clip.mp4")


if __name__ == "__main__":
    main()
