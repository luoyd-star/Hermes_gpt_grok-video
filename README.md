# Hermes + GPT-5.5 + Grok Imagine workflow

中文说明见：[README.zh-CN.md](README.zh-CN.md)

A practical workflow for using Hermes Agent with a strong driver model (for example GPT-5.5 / Codex route) while delegating image and video generation to xAI Grok Imagine.

The key idea: the chat/agent model and the media-generation backend are separate.

- Driver model: understands the task, writes prompts, calls tools, verifies outputs.
- Media backend: xAI Grok Imagine generates images/videos through Hermes tools/plugins.
- Result: keep your best agent model for reasoning, while using Grok for visual generation.

## Why this matters

You do **not** need to switch the main Hermes conversation model to xAI/Grok in order to generate with Grok.

A typical setup looks like this:

```text
User request
  ↓
Hermes Agent driven by GPT-5.5 / Codex / Claude / OpenRouter model
  ↓
Hermes image_generate or video_generate tool
  ↓
xAI Grok Imagine backend
  ↓
Generated media + local QA + manifest
```

## Tested setup

Example tested configuration:

```yaml
model:
  provider: openai-codex
  default: gpt-5.5

image_gen:
  provider: xai
  xai:
    model: grok-imagine-image-quality
    resolution: 2k

video_gen:
  provider: xai
  model: grok-imagine-video
  duration: 8
  aspect_ratio: "16:9"

plugins:
  enabled:
    - image_gen/xai
    - video_gen/xai
```

Authentication can use xAI/Grok OAuth or `XAI_API_KEY`, depending on your Hermes/xAI plugin setup.

## Enable the tools

```bash
hermes plugins list | grep -Ei 'image_gen/xai|video_gen/xai'
hermes tools enable image_gen
hermes tools enable video_gen
hermes config set image_gen.provider xai
hermes config set video_gen.provider xai
hermes config set video_gen.model grok-imagine-video
```

After changing toolsets, start a new Hermes session or reset the current one so the tool schema is refreshed.

## Minimal video-generation script

This repository includes a small Python example that calls the local Hermes xAI video plugin directly:

```bash
cd /path/to/hermes-agent/repo
source venv/bin/activate
python /path/to/this-repo/scripts/generate_xai_video.py \
  --prompt "A premium 6-second vertical intro for a Top 10 AI/market short-video series, dark cinematic style, cyan and gold, no text, no logos" \
  --duration 6 \
  --aspect-ratio 9:16 \
  --resolution 720p \
  --out ./out/top10_intro.mp4
```

In normal Hermes use, you can let the agent call `image_generate` or `video_generate` directly.

## Recommended production pattern

For repeatable content work, keep a manifest next to every generated asset:

```text
project/
  manifest.json
  assets/raw/
  assets/processed/
  renders/
  review/
```

Recommended QA steps:

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,duration,codec_name \
  -show_entries format=duration,size,bit_rate \
  -of json renders/final.mp4

ffmpeg -v info -t 3 -i renders/final.mp4 \
  -af volumedetect -f null - 2>&1 | grep -E 'mean_volume|max_volume'

ffmpeg -y -i renders/final.mp4 \
  -vf "select='eq(n,0)+eq(n,24)+eq(n,48)+eq(n,72)+eq(n,108)+eq(n,140)',scale=360:640,tile=3x2" \
  -frames:v 1 review/contact_sheet.jpg
```

## 30-second chained demo

See [`examples/explorer-forager-30s`](examples/explorer-forager-30s) for a generated demo: a modern explorer enters a prehistoric forager tribe camp and observes daily life.

The demo is built as 3 x 10s Grok Imagine Video generations:

1. Segment 1: text-to-video.
2. Extract the final frame.
3. Segment 2: image-to-video, using segment 1's final frame as the starting image.
4. Extract the final frame.
5. Segment 3: image-to-video, using segment 2's final frame as the starting image.
6. Concatenate the three MP4 files with ffmpeg.

This is the key pattern for working around single-generation duration limits while keeping visual continuity.

## Example: Top 10 intro workflow

1. Ask Hermes to make a Top10 series intro.
2. Hermes writes an English Grok prompt for a clean motion background, avoiding text/logos/watermarks.
3. Grok Imagine Video generates a 9:16 background.
4. Hermes downloads the MP4 locally.
5. Hermes overlays stable typography locally with ffmpeg/Remotion, rather than relying on generated text.
6. Hermes adds a short audio bed so the intro is not silent.
7. Hermes runs ffprobe, volumedetect, and contact-sheet review.
8. Hermes writes a manifest that links prompt, raw asset, final render, and QA notes.

Important lesson: use Grok for visuals, but add typography locally for reliability.

## Notes and pitfalls

- Do not put API keys or OAuth tokens in the repo.
- Grok-generated text inside images/videos is often unreliable; prefer local overlays.
- Video toolset changes may require a new Hermes session before the tool is visible.
- If using web/SuperGrok UI manually, that is browser automation, not the same as the Hermes xAI plugin path.
- For batch production, keep each output's prompt, request ID, local path, and QA evidence in a manifest.

## License

MIT
