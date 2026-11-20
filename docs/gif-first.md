# GIF 优先的动态红包封面流程

ChatGPT Images 2.6 支持 GIF 生成，但目前仍是分批开放功能。确认账号能够生成并下载真正的多帧 GIF 后再使用。Hongbao 不读取浏览器 Cookie、不模拟 ChatGPT 私有接口，也不自动抓取输出。

## 使用方法

先在已登录的 ChatGPT 网页准备 GIF 生成任务：

    python -m hongbao chatgpt --mode gif --theme "花神繁花苏醒" --style "东方幻彩" --output-dir output/flower

在 ChatGPT 网页中粘贴 prompt.txt 内容（如有授权参考照片由本人上传），生成循环 GIF 并手动下载。再在 Codex 终端执行：

    python -m hongbao check-gif "animation.gif"
    python -m hongbao gif2mp4 "animation.gif" output/flower/dynamic.mp4 --duration 3
    python -m hongbao check-video output/flower/dynamic.mp4
    python -m hongbao poster output/flower/dynamic.mp4 output/flower/poster.png

check-gif 会核实 GIF 实际编码、帧数、播放时长，拒绝单帧文件。gif2mp4 复用既有 FFmpeg 视频转码器，不另写一套编码逻辑。目标 MP4 为 960×1280、H.264/AVC、yuv420p、24fps、1–3 秒且无音轨。短 GIF 循环到目标时长，长 GIF 截取到目标时长，原始 GIF 保持不变，MP4 不覆盖已有文件。

## 质量与安全提示

GIF 的颜色数有限，转成 MP4 并不会恢复 GIF 之前已经丢失的渐变色彩。循环首尾不连贯、角色面部变化或帧间抖动也不会通过转码自动修复。应先在 ChatGPT 重新生成或调整 GIF，再制作 MP4。

如果账号没有 GIF 生成功能，则使用现有静态图 + animate 预设路线；真正复杂动作可以用 Flow 等视频工具再经 motion 转码。不要把单帧 PNG 改成 .gif 假冒动图。

MP4 通过本地检查不代表微信开放平台审核通过。动态网页上传仍需用户在平台本人扫码并选择正确的素材栏目，程序不自动提交审核、购买或发放。

## 官方参考

- https://help.openai.com/en/articles/11084440-images-in-chatgpt
- https://help.openai.com/en/articles/6825453-chatgpt-release-notes
