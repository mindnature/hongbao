---
name: hongbao
description: 按主题/照片在已登录的 ChatGPT 网页生成静态红包封面，并将静态原图或 Flow/GIF 视频规范化为微信静态 JPEG、动态 MP4、封面/挂件 PNG 序列帧 ZIP，辅助微信平台上传。
---

# Hongbao · 微信红包封面（网页版优先，静态 + 动态）

默认无需 API Key。默认使用已登录 ChatGPT 网页交接：Codex 生成提示词并打开默认浏览器；用户自行粘贴、上传参考照和保存原图；程序负责本地处理。不要抓取 ChatGPT 网页生成输出、Cookie，不绕过任何验证码。

## 动态封面默认首选：ChatGPT 多帧 GIF → MP4

当用户需要动态红包封面，默认先尝试 ChatGPT 网页 GIF 功能，而不是优先使用静态图 animate 或要求 Flow。ChatGPT Images 2.6 GIF 功能仍在逐步开放；如果当前用户账号没有该能力，不要假称已生成 GIF，改用下述 animate 回退方案。

1. 执行 python -m hongbao chatgpt --mode gif --theme "春节凤凰" --style "东方鎏金" --output-dir output/phoenix，生成专用循环动画提示词，并用默认浏览器打开 ChatGPT。
2. 用户自行粘贴 prompt.txt 并上传授权参考照（如有），生成真正多帧循环 GIF，再保存本机。不要抓取 Chrome Cookie、私有 API 或自动提取网页资源。
3. 下载后依次执行：
   python -m hongbao check-gif "下载动画.gif"
   python -m hongbao gif2mp4 "下载动画.gif" output/phoenix/dynamic.mp4 --duration 3
   python -m hongbao check-video output/phoenix/dynamic.mp4
   python -m hongbao poster output/phoenix/dynamic.mp4 output/phoenix/poster.png
4. 检查 GIF 的实际帧数与时长、角色一致性、循环衔接与关键内容遮挡，不将原 GIF 当成可直接上传的微信 MP4。
5. 确认后才能进入微信网页辅助上传；动态素材字段仍由用户手动选择，最终审核、购买和发放需本人确认。

顺序：GIF 动画优先；ChatGPT GIF 尚未开放则使用静态图 + animate；需要复杂镜头或真实动作时可使用 Flow + motion。保留所有原有命令。

## 路线 A：静态封面

1. 主题或授权照片：python -m hongbao chatgpt --theme "春节橘猫抱元宝" --style "东方剪纸" --output-dir output/cat（参考照加 --reference 照片路径）。
2. 用户在浏览器打开的 ChatGPT 粘贴 prompt.txt，可手动上传照片，保存完成原图。
3. python -m hongbao import "下载图片路径" --output-dir output/cat。生成 cover.jpg（957×1278、500KB 内）、preview.png。
4. 如果用户明确要求辅助上传：python -m hongbao upload output/cat/cover.jpg --short-name "本人有权使用的简称"。本人扫码；未知页面由本人操作，最终提交需本人确认。


## 路线 B0：静态图片直接生成程序化动画 MP4（无需 Flow）

当用户只有静态图片或 ChatGPT GIF 功能尚未开放时，才将 animate 作为回退方案。它只绘制镜头运动、边缘灯笼、金粉、薄雾、花瓣和伪视差，不会把图片中的人物变成真实动作。

    python -m hongbao animate output/cat/cover.jpg output/cat/dynamic.mp4 --preset festive-glow --duration 3 --intensity 0.55 --poster output/cat/poster.png
    python -m hongbao check-video output/cat/dynamic.mp4

预设：zoom、pan、festive-glow、sparkle、petals、lantern-sway、cloud-drift、parallax。推荐强度 0.3–0.6；可用 --seed 固定装饰粒子布局，--focus-x / --focus-y 调整裁切中心。输出 960×1280、H.264、yuv420p、24fps、1–3 秒、无音轨；需要本机 FFmpeg + ffprobe，默认不调用 API。

务必区分实际能力：lantern-sway 绘制边缘摇曳小灯笼，不能识别原画里的灯笼；cloud-drift 为新增边缘薄雾；parallax 为软遮罩伪视差而非自动语义分层。任何新增元素可能覆盖画面边缘内容，应检查预览。真实人物运动仍应使用视频生成工具先完成，再用 motion 转码。微信动态素材网页上传仍需用户本人选栏位，不可声称已自动完成审核。

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
- 阅读 README.md、docs/animation.md、docs/animation-presets.md 与 docs/platform.md。
