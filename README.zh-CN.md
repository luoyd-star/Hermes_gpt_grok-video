# Hermes + GPT-5.5 + Grok Imagine 视频工作流

这个项目记录一个实用工作流：用 Hermes Agent 作为执行层，用 GPT-5.5 / Codex 路线作为“驱动模型”，再把图片和视频生成交给 xAI Grok Imagine 后端。

核心观点：

> 对话模型和生成后端是两件事。Hermes 可以继续由 GPT-5.5 / Codex / Claude 等强推理模型驱动，同时通过工具调用 Grok Imagine 生成图片或视频。

## 工作流结构

```text
用户需求
  ↓
Hermes Agent：理解任务、拆分步骤、写 prompt、调用工具、做 QA
  ↓
GPT-5.5 / Codex route：负责推理和编排
  ↓
image_generate / video_generate 工具
  ↓
xAI Grok Imagine：负责生成图片/视频
  ↓
本地下载、拼接、字幕/标题叠加、ffprobe QA、manifest 记录
```

## 为什么这样做

1. 不需要把 Hermes 主模型切换到 xAI。
2. 可以保留 GPT-5.5 / Codex 的长任务执行、代码、文件和 QA 能力。
3. Grok 专心做视觉生成，Hermes 负责生产流程。
4. 对短视频项目尤其方便：生成素材、剪辑、拼接、检查、归档都能放在同一个 agent 工作流里。

## 已验证配置示例

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

## 启用方式

```bash
hermes plugins list | grep -Ei 'image_gen/xai|video_gen/xai'
hermes tools enable image_gen
hermes tools enable video_gen
hermes config set image_gen.provider xai
hermes config set video_gen.provider xai
hermes config set video_gen.model grok-imagine-video
```

注意：工具集变更后，通常需要新开 Hermes session 或 reset，新的 tool schema 才会进入当前对话。

## 30 秒连续视频 Demo：尾帧接续法

Grok 单次视频生成时长有限。要做 30 秒，可以拆成 3 段：

```text
第 1 段：text-to-video，生成 0-10s
  ↓ 抽取最后一帧
第 2 段：image-to-video，用第 1 段最后一帧作为起始图，生成 10-20s
  ↓ 抽取最后一帧
第 3 段：image-to-video，用第 2 段最后一帧作为起始图，生成 20-30s
  ↓
ffmpeg concat 拼接成 30s
```

这样比单纯写三个 text prompt 更连续，因为后两段有明确的视觉起点。

### Demo 题材

本项目示例 demo：

> 一个现代探险家意外穿越到史前采集部落，观察部落日常生活：清晨走入营地、采集浆果和植物、火堆旁整理篮筐和石器。风格是写实纪录片，不要奇幻魔法，不要现代文字，不要 logo。

### 生产建议

- Grok 负责生成无文字、无 logo、无水印的干净画面。
- 人名、标题、字幕建议本地叠加，不要让模型直接生成文字。
- 每段生成后保存 request_id、prompt、原始 URL、本地路径。
- 拼接后做 QA：
  - ffprobe 检查分辨率、时长、编码
  - contact sheet 看关键帧
  - 如有音频，检查前 3 秒不是静音

## QA 命令

Demo 文件见：[`examples/explorer-forager-30s`](examples/explorer-forager-30s)。其中包含压缩预览版 MP4、contact sheet、manifest 和 ffprobe 输出。

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,duration,codec_name \
  -show_entries format=duration,size,bit_rate \
  -of json renders/final.mp4

ffmpeg -y -i renders/final.mp4 \
  -vf "select='eq(n,0)+eq(n,72)+eq(n,144)+eq(n,216)+eq(n,288)+eq(n,360)+eq(n,432)+eq(n,504)+eq(n,648)',scale=360:202,tile=3x3" \
  -frames:v 1 review/contact_sheet.jpg
```

## 踩坑记录

- 不要把 token、OAuth 文件、`.env`、生成的大视频直接提交到 repo。
- Grok 生成视频里的文字不可控，稳定做法是“模型生成画面，本地加文字”。
- image-to-video 需要可被 xAI 访问的图片 URL；如果使用本地尾帧，需要先放到一个公开可访问的位置，或者用工具支持的 data URL/上传流程。
- 如果远程 GitHub 仓库网页初始化过 README，本地第一次 push 可能被拒绝，需要先 fetch + merge，不要直接 force push。

## 项目内容

- `README.md`：英文说明
- `README.zh-CN.md`：中文说明
- `scripts/generate_xai_video.py`：最小视频生成脚本
- `scripts/continuous_video_demo.py`：连续 3 段视频 demo 脚本
- `examples/`：manifest 示例

## License

MIT
