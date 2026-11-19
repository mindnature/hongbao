---
name: hongbao
description: 生成微信红包封面。支持主题描述或参考照片，使用 GPT Image 2.6 生成、规范化导出、模拟预览，并在用户本人扫码登录后辅助在微信红包封面开放平台上传。适用于想制作个人、宠物、节庆或品牌红包封面的用户。
---

# Hongbao · 微信红包封面

工作原则：默认一张；先完成作品，再导出；实际上传要求与平台网页提示优先。本 Skill 不是微信官方产品，不能保证平台资格或审核结果。

## 先识别用户意图

- 文字主题：询问或自行确定主要主体、艺术风格、配色。
- 参考照片：只有用户有使用权或取得同意时才编辑；不能假定持有商标、肖像或版权授权。
- 用户未明确要求上传时，停留在预览和导出。
- 用户要求上传时：先检查产物，再启动本人扫码登录和浏览器辅助上传；决不索取微信密码、导出会话令牌、绕过验证码或代替用户最终提交审核。
- 可以生成原图、规范化上传图、模拟预览图，三者分别保存，不将预览图上传。

## 环境检查

从项目根目录安装：

    python -m pip install -e ".[images,browser]"
    python -m playwright install chromium

需要 OPENAI_API_KEY 才能用本项目自带的图像 API 调用，调用可能计费。若 Codex 当前环境已有经过授权的图像生成工具，也可用该工具生成原始图片，再通过本项目 export/check/preview/upload，不必使用 OpenAI API。

## 推荐工作流

1. 确定主题、风格，设计为 3:4 竖版原画。画面不能绘制微信界面的头像、打开按钮、官方 Logo 或二维码；主体远离遮挡区，减少文字。
2. 有 API key：执行 python -m hongbao generate --theme "主题" --style "风格" --output output/original.png；参考照加 --reference /path/to/photo.jpg。没有图像工具和 key 时，明确说明无法生成，不要伪称已生成。
3. 展示生成的原图。若用户要求连续制作，可自动继续；否则先请用户确认。
4. 执行 python -m hongbao export output/original.png output/cover.jpg，再执行 python -m hongbao check output/cover.jpg。
5. 执行 python -m hongbao preview output/cover.jpg output/preview.png；向用户明确预览仅为近似演示。
6. 用户同意上传且有平台注册资格时：python -m hongbao upload output/cover.jpg --short-name "获授权的简称"。在本机浏览器由本人扫码；程序尝试导航及上传。未识别的字段由用户人工完成，不自动提交审核、付款或发布。
7. 交付原图、上传 JPEG、预览 PNG、检查结果和平台完成情况，说明任何未自动化/未验证的环节。

## 约束

- JPEG 默认 957×1278，文件不超过 500,000 bytes，安全区和具体规格仍以平台当前提示为准。
- 任何敏感登录状态仅可保留在本机 .hongbao/ 浏览器目录，严禁上传到 Git 仓库或发给第三方。
- 审核不通过时依据平台驳回理由修改，不要规避风控。
- 如果微信网站 UI 变化使定位器失效，停止对应自动操作，让用户接管网页，不能随意猜测按钮。
- 请阅读 README.md 和 docs/platform.md 的最新限制。
