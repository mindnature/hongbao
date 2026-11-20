# ChatGPT GIF → MP4：一条命令完成本地处理

## 推荐（动态红包默认）

ChatGPT 网页可以在账号具备 GIF 生成功能时直接生成循环动画。无需先制作 PNG，也无需 Flow 或 OpenAI API Key。实际 GIF 能力取决于当前登录账号。

第一步，准备 GIF 绘图提示词并打开系统默认浏览器：

    python -m hongbao dynamic --theme "红金凤凰与流动祥云" --style "东方国风" --output-dir output/phoenix

命令保存 prompt.txt；尝试复制提示词到剪贴板，并打开 chatgpt.com。用户在网页粘贴提示词、可按需上传有权使用的参考图片，然后直接生成并手动下载真正的多帧 GIF。

第二步，交给 Codex 一条命令完成下载文件的处理：

    python -m hongbao import-gif "C:\Users\me\Downloads\animation.gif" --output-dir output/phoenix --duration 3

上述命令先检查 GIF 实际帧数与时长，拒绝单帧 GIF；接着复制保留原 GIF，用 FFmpeg 将其循环或截取为 3 秒 960×1280、H.264、yuv420p、24fps、无音轨 MP4；用 check_video 核验并自动提取 poster.png。最终在输出目录形成 original.gif、dynamic.mp4、poster.png、job.json。

不得声称该工具自行访问了 ChatGPT 账号、上传图片、下载浏览器文件或完成微信平台审核。ChatGPT 图片下载仍由本人在网页完成；微信平台动态上传也需本人登录、选择动态素材栏目并确认。

## 兼容旧命令

- python -m hongbao chatgpt --mode gif --theme "主题"：与 dynamic 入口同样生成 GIF 提示词
- python -m hongbao gif2mp4 animation.gif dynamic.mp4：只负责独立转码，不自动创建预览
- python -m hongbao check-gif animation.gif：只检查 GIF
- python -m hongbao animate cover.jpg dynamic.mp4：没有 GIF 时，用静态画生成程序化动画
- python -m hongbao motion flow.mp4 dynamic.mp4：需要复杂自然动作时，转换 Flow 等视频

MP4 转换不能修复 GIF 256 色调色板、循环跳变、物体错位或人物变形。所有本地视频规则均以微信平台现行素材审核要求为最终依据。
