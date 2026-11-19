# Hongbao V0.4.0｜静态图片程序化动画预设

此功能使用 Pillow 逐帧绘制和 FFmpeg H.264 编码，让一张静态画作直接产生 1–3 秒 MP4。无需 Flow、无需 OpenAI API Key。这不是语义视频生成，不能让原图人物自然眨眼、动物走动或自动识别三维景深。

## 快速开始

系统安装 FFmpeg（同时包含 ffprobe），将两个可执行文件加入 PATH。通过现有 ChatGPT 网页模式生图、下载，并使用 hongbao import 将原图规范化之后，运行：

    python -m hongbao animate output/chatgpt/cover.jpg output/chatgpt/dynamic.mp4 --preset festive-glow --duration 3 --intensity 0.55 --poster output/chatgpt/poster.png
    python -m hongbao check-video output/chatgpt/dynamic.mp4

## 八种动画预设

| 预设 | 效果 | 适用场景 |
| --- | --- | --- |
| zoom | 细微周期推近与回退 | 肖像、静物 |
| pan | 画面缓慢轻移 | 山水、长卷 |
| festive-glow | 轻推镜、边缘暖光呼吸和金色闪点 | 红金春节 |
| sparkle | 边缘金色闪点 | 金箔、珠宝 |
| petals | 两侧少量花瓣循环飘落 | 春日、花神 |
| lantern-sway | 两侧新绘小灯笼轻摇 | 春节民俗 |
| cloud-drift | 两侧柔和薄雾漂移 | 国风水墨 |
| parallax | 中央软遮罩与边缘画面轻微错位 | 有纵深感的画作 |

特效不做面部识别。默认限制新增视觉元素在侧边，以减少对中央人脸和主体的遮挡；仍须人工预览确认。特别说明：lantern-sway 不是识别移动原有灯笼，而是增加边缘灯笼装饰；parallax 是近似伪视差，并非智能抠图或真实深度分层；cloud-drift 不会直接移动原图中的祥云。

## 参数

- --preset：上方八种之一，默认 festive-glow
- --duration：1–3 秒，默认 3 秒
- --fps：固定 24
- --intensity：0–1，默认 0.55；建议 0.3–0.6
- --seed：控制装饰元素分布，默认 7
- --focus-x / --focus-y：0–1，用于调整裁切中心，默认 0.5
- --poster：另外导出 PNG 预览帧（可选）

输出必须是新的 .mp4 文件名；不会覆盖原图或已存在的输出文件。程序在临时目录中生成视频，运行 check_video 检查后才移动到正式输出位置。

## 输出规范与限制

默认 960×1280、3:4、H.264/AVC、yuv420p、24fps、无音轨 MP4。比特率上限预设低于 3000 kbit/s；本地 check_video 依据参考规范检查 1–3 秒和文件体积等。最终接受与否必须以当前微信红包封面开放平台上传页为准。

本命令与 motion 不冲突：animate 专用于静态图片生成程序动画；motion 用于裁剪、转码用户通过 Flow 等工具取得的真正视频。animate 输出的 MP4 也可以进一步用 frames 转为 PNG 序列帧 ZIP。

动态上传现阶段仍需用户在微信后台手动选对动态素材栏目。不能把本地格式通过验证说成微信审核成功。
