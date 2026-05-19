#!/usr/bin/env python3
"""Generate a video through Hermes' xAI Grok Imagine video plugin.

Run from a Hermes Agent checkout with its virtualenv activated, e.g.:

    cd ~/Documents/hermes-agent/repo
    source venv/bin/activate
    python /path/to/generate_xai_video.py --prompt "..." --out ./out/video.mp4

This script intentionally does not read or print secrets. Credentials are resolved by Hermes'
shared xAI resolver: xAI/Grok OAuth first, then XAI_API_KEY if configured.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.request

from plugins.video_gen.xai import XAIVideoGenProvider


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--duration", type=int, default=6)
    parser.add_argument("--aspect-ratio", default="9:16")
    parser.add_argument("--resolution", default="720p", choices=["480p", "720p"])
    args = parser.parse_args()

    provider = XAIVideoGenProvider()
    if not provider.is_available():
        raise SystemExit("xAI credentials not available. Configure xAI OAuth or XAI_API_KEY in Hermes.")

    result = provider.generate(
        prompt=args.prompt,
        duration=args.duration,
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not (result.get("success") and result.get("video")):
        return 1

    out = pathlib.Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(result["video"], out)

    manifest = {
        "generated_at_unix": int(time.time()),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "prompt": args.prompt,
        "request_id": result.get("request_id"),
        "video_url": result.get("video"),
        "local_path": str(out),
        "duration": result.get("duration"),
        "aspect_ratio": result.get("aspect_ratio"),
        "resolution": result.get("resolution"),
        "usage": result.get("usage"),
    }
    out.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"saved: {out}")
    print(f"manifest: {out.with_suffix('.manifest.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
