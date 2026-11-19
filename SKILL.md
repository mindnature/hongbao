---
name: hongbao
description: 使用已登录的 ChatGPT 网页或可选 API 按主题/参考照片创作微信红包封面，自动规范化图片、预览，并辅助微信平台上传。
---

# Hongbao · 微信红包封面（网页版优先）

默认无需 API Key。用户已在 Chrome（或其他默认浏览器）登录 ChatGPT 时，首选 **网页交接模式**。不要将 ChatGPT 网页视作免费 API，不做自动爬取图片、不提取 Cookie、不尝试绕过验证码或网页保护措施。

## 基本流程

1. 用户给出主题、风格，或提供有权使用的照片。默认仅创作一张完整 3:4 竖版艺术原图，主体置中，避免顶部/底部 UI 遮挡，不绘制红包按钮或二维码。
2. 从项目根目录运行：python -m hongbao chatgpt --theme "春节橘猫抱金元宝" --style "东方剪纸" --output-dir output/fortune-cat
   如使用参考图，添加 --reference "/绝对路径/我的猫.jpg"。
3. 命令生成 prompt.txt，尝试复制到系统剪贴板，并打开 https://chatgpt.com/ 到默认浏览器。已有登录状态的浏览器可继续使用，但本工具不会读取或接管其登录态。
4. 用户在 ChatGPT 网页粘贴提示词（自动复制不可用时从 prompt.txt 复制），并自行上传参考照片（如有）。请用户在网页生成并确认原图，然后点击保存，把图片下载到自己的电脑。**不让脚本抓取 ChatGPT 生成图片的 URL、页面状态或会话**。
5. 对用户保存的本地原图运行：python -m hongbao import "下载图片完整路径" --output-dir output/fortune-cat。工具自动复制原图、导出 957×1278 JPEG（<=500000 字节）、检查编码与体积、制作本地示意预览。若同名结果已经存在，默认不覆盖；用户确实要替换时加 --overwrite。
6. 先展示原图、cover.jpg、preview.png 给用户确认。预览仅是示意，并非微信官方裁切。
7. 若用户明确要求上传并具有平台资格，安装浏览器可选依赖后运行：python -m hongbao upload output/fortune-cat/cover.jpg --short-name "有使用权的简称"。微信账号由用户本人扫码完成；程序尝试处理稳定字段。未识别的表单让用户接管；不自动提交审核或购买/发放。
8. 交付生成结果与真实执行状态，不得声称网页端已自动生成/下载或微信平台已上传成功，除非实际核实。

## 安装

    python -m pip install -e .

仅上传微信平台的 Playwright 浏览器功能另需：

    python -m pip install -e ".[browser]"
    python -m playwright install chromium

API 是显式可选方案：若用户要求 API 模式并自行配置 OPENAI_API_KEY，使用 python -m hongbao generate --theme "..." --output output/original.png。API 调用单独计费，不是 ChatGPT 订阅内额度。

## 安全与兼容

- 不能直接接管用户正常 Chrome 默认配置、读取 Cookies 或复制用户资料。
- 使用操作系统默认浏览器打开网页，不强制新建或复制 Chrome Profile。Chrome 136 及更新版本限制默认配置的 CDP 调试，不要试图规避。
- ChatGPT 网站布局变化不影响 prepare/import，因为它们不依赖网站 DOM。
- 参考照片路径仅记录在本地工作目录的 job.json，注意其隐私；禁止上传该工作目录到公开仓库。
- 微信上传可能需要另一个 Playwright 专用浏览器及本人首次扫码，不能假定它共享 Chrome 的 ChatGPT 登录状态。
- 规则与尺寸以微信当前平台页面为准；本地检查不能保证审核通过。
- 细节参考 README.md、docs/chatgpt-web.md 和 docs/platform.md。
