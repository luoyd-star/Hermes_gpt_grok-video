#!/usr/bin/env python3
"""Continuous 30-second Grok Imagine Video demo.

Goal: make a 30s scene by chaining three 10s generations.

Segment 1: text-to-video.
Segment 2: image-to-video using segment 1's last frame as the first frame.
Segment 3: image-to-video using segment 2's last frame as the first frame.

Notes:
- xAI's image-to-video endpoint needs an image URL. Some setups accept data URLs;
  if your backend rejects data URLs, upload the extracted last frame to a public
  URL and pass that URL as image_url.
- This script calls Hermes' local xAI video provider directly, so run it from a
  Hermes Agent checkout with the Hermes virtualenv active.
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import subprocess
import time
import urllib.request

from plugins.video_gen.xai import XAIVideoGenProvider


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def extract_last_frame(ffmpeg: str, video: pathlib.Path, image: pathlib.Path) -> None:
    image.parent.mkdir(parents=True, exist_ok=True)
    # -sseof avoids decoding the whole file and grabs a frame near the end.
    run([ffmpeg, "-y", "-sseof", "-0.08", "-i", str(video), "-frames:v", "1", "-update", "1", str(image)])


def image_as_data_url(path: pathlib.Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{data}"


def download(url: str, out: pathlib.Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="examples/explorer-forager-demo")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--resolution", default="720p", choices=["480p", "720p"])
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out_dir).expanduser().resolve()
    raw_dir = out_dir / "raw"
    frame_dir = out_dir / "frames"
    render_dir = out_dir / "renders"
    for d in [raw_dir, frame_dir, render_dir]:
        d.mkdir(parents=True, exist_ok=True)

    provider = XAIVideoGenProvider()
    if not provider.is_available():
        raise SystemExit("xAI credentials not available. Configure xAI OAuth or XAI_API_KEY in Hermes.")

    prompts = [
        "A realistic cinematic documentary scene: a modern explorer in simple earth-toned travel clothes quietly emerges from dense forest into a prehistoric forager tribe camp at sunrise. Adults weave baskets, children gather kindling, smoke rises from a small fire, no magic, no fantasy, no text, no logos, natural handheld camera, warm morning light.",
        "Continue from the exact previous frame. The explorer stays at the edge of the camp, respectfully observing. Forager tribe members collect berries and edible roots near woven baskets, a calm daily-life moment, natural gestures, realistic anthropology documentary style, smooth camera drift, no text, no logos, no modern buildings.",
        "Continue from the exact previous frame. Late morning in the same forager camp: people sort gathered plants, repair a basket, shape a stone tool near the fire, the explorer watches quietly without interfering, peaceful everyday life, realistic documentary cinematography, no text, no logos, no fantasy effects.",
    ]

    manifest = {
        "title": "Explorer enters a forager tribe camp — 30s chained Grok demo",
        "method": "3 x 10s generation; segment tail frame becomes next segment start image",
        "segments": [],
    }

    image_url = None
    segment_paths: list[pathlib.Path] = []
    for i, prompt in enumerate(prompts, start=1):
        result = provider.generate(
            prompt=prompt,
            image_url=image_url,
            duration=args.duration,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
        )
        print(json.dumps({"segment": i, "result": result}, ensure_ascii=False, indent=2))
        if not (result.get("success") and result.get("video")):
            raise SystemExit(f"segment {i} failed")

        seg_path = raw_dir / f"segment_{i:02d}.mp4"
        download(result["video"], seg_path)
        segment_paths.append(seg_path)

        tail = frame_dir / f"segment_{i:02d}_tail.jpg"
        extract_last_frame(args.ffmpeg, seg_path, tail)
        image_url = image_as_data_url(tail)

        manifest["segments"].append({
            "index": i,
            "prompt": prompt,
            "request_id": result.get("request_id"),
            "video_url": result.get("video"),
            "local_path": str(seg_path),
            "tail_frame": str(tail),
            "used_image_to_video": i > 1,
            "aspect_ratio": result.get("aspect_ratio"),
            "duration": result.get("duration"),
            "resolution": result.get("resolution"),
        })

    concat_file = out_dir / "concat.txt"
    concat_file.write_text("".join(f"file '{p}'\n" for p in segment_paths))
    final = render_dir / "explorer_forager_30s_demo.mp4"
    run([args.ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(final)])

    manifest["final_video"] = str(final)
    manifest["created_at_unix"] = int(time.time())
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"final: {final}")
    print(f"manifest: {out_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
