# Demo: Explorer enters a forager tribe camp

这个 demo 展示如何用 Grok Imagine Video 做一个约 30 秒的连续片段。

主题：

> 一个现代探险家意外穿越到史前采集部落，观察部落日常生活：清晨走入营地、采集浆果和植物、火堆旁整理篮筐和石器。

## 方法

这条 demo 不是一次生成 30 秒，而是拆成三段：

1. `segment_01`：text-to-video，生成第 0-10 秒。
2. 抽取 `segment_01` 的最后一帧。
3. `segment_02`：image-to-video，用上一段尾帧作为起始图，生成第 10-20 秒。
4. 抽取 `segment_02` 的最后一帧。
5. `segment_03`：image-to-video，用上一段尾帧作为起始图，生成第 20-30 秒。
6. 用 ffmpeg concat 拼接。

## 文件

- `explorer_forager_30s_demo_480p.mp4`：压缩后的 GitHub 预览版，约 30 秒。
- `contact_sheet_30s.jpg`：9 宫格 QA 帧。
- `manifest.generated.json`：生成 prompt、request_id、本地路径和分段信息。
- `ffprobe_final.json`：最终视频媒体信息。
- `audio_first3s.txt`：前 3 秒音量检测。

本地高码率版本路径：

```text
/Users/bull/Documents/grok-demos/explorer-forager-30s/renders/explorer_forager_30s_demo.mp4
```

## QA 结果

- 最终高码率版本：1280x720，24fps，约 30.15 秒。
- 三段均为 10.04 秒左右。
- 第 2、3 段使用 image-to-video，`modality` 为 `image`，说明尾帧接续方法跑通。
- contact sheet 显示整体场景、森林营地、火堆、篮筐、采集部落日常活动具有较强视觉连续性。

## 观察到的问题

这是一个 workflow demo，不是最终影视级成片。当前版本仍有这些典型 AI 视频问题：

- 探险家位置在不同镜头之间有跳跃。
- 背包、部落人物、火堆和篮筐位置存在轻微变化。
- 部落服装有时偏现代化，不够粗粝。
- 最后一段儿童编织特写很好看，但更像 cutaway，需要前一镜头用视线或动作动机连接。

改进方向：

- 固定探险家造型：同一脸、同一背包、同一靴子和衣服。
- 固定营地图：森林入口、火堆、棚屋、篮筐、儿童位置保持一致。
- 每段 prompt 明确 camera path 和 blocking。
- 如果要更强连续性，可先生成角色/场景参考图，再用 reference image + tail frame 组合约束。
