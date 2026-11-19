# 动态微信红包封面（MP4 / PNG 序列帧 / 透明挂件）

更新：2026-11-19

微信动态红包封面已经开放定制，但不是简单把 GIF 扔到静态上传框；需要选择平台对应的动态素材类型。**非官方工具，后台最新表单字段仍需账号验收。**

## 已公开的常见规格

| 类型 | 文件 | 时长/帧数 | 大小/尺寸 | 备注 |
| --- | --- | --- | --- | --- |
| 静态封面 | JPEG/PNG | 单图 | 957×1278，≤500KB | 本项目默认 JPEG |
| 动态封面 | MP4/H.264，yuv420p | 1–3秒，≤30fps | ≤20MB，码率≤3000kbit/s，建议3:4 | 本项目输出 960×1280 24fps |
| 动态封面序列帧 | 连续编号 PNG ZIP | 24fps，24–72帧 | 957×1278，ZIP≤50MB | 00001.png 起 |
| 动态透明挂件 | 连续编号透明 PNG ZIP | 24fps，24–72帧 | 1053×1746，ZIP≤20MB | 素材必须有真正的透明像素 |

规格来自微信动态封面开放时的公开资料转述，可能变化，平台实际上传提示优先：
- https://www.ithome.com/0/746/235.htm
- https://www.pmtemple.com/pm-ceri/tencent/18030/
- https://developer.cloud.tencent.com/news/1299136

**注意：** 视频编码 H.264 yuv420p 通常要求偶数宽高，故 MP4 输出 960×1280（同为 3:4），不使用静态 PNG 的奇数宽 957。后者仅用于静态图和序列帧。动态视频不可被误当作 15 秒封面故事。

## 从 Flow 10秒作品变成3秒动态封面

    python -m hongbao motion "flow-10s.mp4" output/final.mp4 --start 4 --duration 3
    python -m hongbao check-video output/final.mp4
    python -m hongbao poster output/final.mp4 output/final-poster.png

--start 是从原片的第几秒开始截取；请挑选最稳定的 1–3 秒镜头。动画中人物/主体尽量保持中心，顶端和底端保留安全区域。变速、无缝循环等属于后续增强功能。

## 从静态 ChatGPT 作品产生轻微推镜

    python -m hongbao motion "output/chatgpt/cover.jpg" "output/chatgpt/dynamic.mp4" --duration 3 --effect zoom

该特效只是**数字镜头推近**，不会让主体眨眼或真实动作。要让人物/宠物动起来，应先用有授权的视频生成工具制作视频，再交给 motion 转码。也可使用 --effect none 创建不动的 MP4 作为技术性测试。

## GIF 或透明素材转为序列帧

    python -m hongbao frames "material.gif" output/cover-frames.zip --kind cover --duration 3
    python -m hongbao frames "transparent.gif" output/ornament.zip --kind ornament --duration 3
    python -m hongbao check-frames output/ornament.zip --kind ornament

透明挂件转换不会自动抠图。检查器要求每帧确实有透明区域；如果是普通 JPG 或无透明度的 MP4，输出会被拒绝。可先设计真正透明背景的 PNG/APNG/GIF（使用授权素材）。

## 页面上传边界

    python -m hongbao upload output/final.mp4 --short-name "合法简称"
    python -m hongbao upload output/ornament.zip --kind ornament --short-name "合法简称"

动态 MP4 和 ZIP 的上传控件位置未经微信正式页面验证。程序仅**检查材料、打开网页、支持本人扫码、尝试填写简称**，要求用户自行选择对应动态封面或挂件栏目上传，不自动操作未知控件；检查本地文件不等于微信已接受。

## 技术依赖

- 系统安装 FFmpeg（含 ffprobe），检查命令：ffmpeg -version 与 ffprobe -version。
- Python 3.10+，Pillow。
- 不需要 OpenAI API Key，也不需要视频生成 API。
- 默认不覆盖任何已有视频和 ZIP。
- 视频转换仅保留视频轨道，自动去掉音频；防止不必要的授权与平台兼容问题。
