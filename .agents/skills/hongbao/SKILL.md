---
name: hongbao
description: 按主题/照片在已登录的 ChatGPT 网页生成静态红包封面，并将静态原图或 Flow/GIF 视频规范化为微信静态 JPEG、动态 MP4、封面/挂件 PNG 序列帧 ZIP，辅助微信平台上传。
---

# Hongbao · 微信红包封面（网页版优先，静态 + 动态）

默认无需 API Key。默认使用已登录 ChatGPT 网页交接：Codex 生成提示词并打开默认浏览器；用户自行粘贴、上传参考照和保存原图；程序负责本地处理。不要抓取 ChatGPT 网页生成输出、Cookie，不绕过任何验证码。

## 路线 A：静态封面

1. 主题或授权照片：python -m hongbao chatgpt --theme "春节橘猫抱元宝" --style "东方剪纸" --output-dir output/cat（参考照加 --reference 照片路径）。
2. 用户在浏览器打开的 ChatGPT 粘贴 prompt.txt，可手动上传照片，保存完成原图。
3. python -m hongbao import "下载图片路径" --output-dir output/cat。生成 cover.jpg（957×1278、500KB 内）、preview.png。
4. 如果用户明确要求辅助上传：python -m hongbao upload output/cat/cover.jpg --short-name "本人有权使用的简称"。本人扫码；未知页面由本人操作，最终提交需本人确认。

## 路线 B：动态 MP4 封面

动态封面推荐 1–3 秒；从 Flow、其他视频或 GIF 选择 3 秒片段转码：

    python -m hongbao motion "Flow下载的10秒视频.mp4" output/cat/dynamic.mp4 --start 2 --duration 3
    python -m hongbao check-video output/cat/dynamic.mp4
    python -m hongbao poster output/cat/dynamic.mp4 output/cat/poster.png

没有视频时，基于已确认的静态原图制作**轻微数字推镜（不是 AI 逐帧人物动画）**：

    python -m hongbao motion output/cat/cover.jpg output/cat/dynamic.mp4 --duration 3 --effect zoom

MP4 输出 960×1280（严格 3:4、偶数宽高以兼容 yuv420p）、24fps、H.264、无音轨。视频按已公开的 1–3 秒、≤20MB、≤3000 kbit/s 规范检验。具体以平台现行要求为准。动态素材即使本地合格，也不能保证微信审核通过。

## 路线 C：PNG 序列帧封面/透明挂件

视频/GIF 转封面序列帧：

    python -m hongbao frames "素材.gif" output/cat/cover-frames.zip --kind cover --duration 3
    python -m hongbao check-frames output/cat/cover-frames.zip --kind cover

有透明通道的 GIF/PNG 等输入素材可制成**透明挂件**：

    python -m hongbao frames "透明素材.gif" output/cat/ornament.zip --kind ornament --duration 3
    python -m hongbao check-frames output/cat/ornament.zip --kind ornament

覆盖式封面序列帧应是 957×1278，透明挂件是 1053×1746，24fps，24–72 张，5 位连续文件名；ZIP 限制分别为 50MB / 20MB。透明挂件必须确实有透明背景，不会对普通视频凭空抠图。

## 微信上传与限制

    python -m pip install -e ".[browser]"
    python -m playwright install chromium
    python -m hongbao upload output/cat/dynamic.mp4 --short-name "授权简称"
    python -m hongbao upload output/cat/ornament.zip --kind ornament --short-name "授权简称"

用户本人扫码登录。静态封面可以尝试自动寻找唯一上传输入框；**动态 MP4 和 ZIP 暂时只辅助打开定制网页、填简称、检查文件，用户必须在页面手动选择正确动态/挂件栏目并上传。** 网站未知布局不应猜测；脚本不代替用户提交审核、购买或发放，亦不可假称已上传成功。

## 安装

    python -m pip install -e .

MP4 与 PNG 序列帧转码需操作系统安装 FFmpeg + ffprobe，两者都要在 PATH 中（不是 Python 依赖）。可选 API 模式使用 OPENAI_API_KEY 和 pip install -e ".[images]"，但不是默认方案。

## 边界

- 不复制 Chrome Profile，不从网页版抓取图片；已有登录状态只用于通过默认浏览器打开 ChatGPT。
- 不把 MP4 的宽度强制改为静态封面的 957 像素：H.264 yuv420p 需要偶数宽高，输出视频 960×1280；PNG 帧使用 957×1278。
- 上传规则、账号资格、版权材料、AI 生成材料要求，以微信当前平台页面为准。
- 工作区输出中的照片、视频与 Cookie 不得进入公开 Git 仓库。
- 阅读 README.md、docs/animation.md 与 docs/platform.md。
