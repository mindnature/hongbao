# Hongbao 🧧

**用 ChatGPT 网页版生成微信红包封面｜照片改造｜自动规范化｜预览｜扫码后辅助上传**

Hongbao 是一个开源 Codex Skill。**默认使用已登录的 ChatGPT 网页版，不要求 OpenAI API Key。** Codex 根据文字或参考照片制作绘图指令并打开默认浏览器；你在 ChatGPT 保存生成的图片，再由 Hongbao 自动导入、裁切、导出、检查并生成红包模拟预览。微信平台的浏览器辅助上传仍为可选功能。

> 不是微信官方产品。现阶段网页版生图为**人工操作网页 + 本地自动处理**，不是后台自动调用 ChatGPT 网站，也没有从浏览器抓取输出的功能。微信上传页面未完成真实端到端验证，审核是否通过以官方平台为准。

## 1. 安装到 Codex

可直接向 Codex 说：

    请安装 https://github.com/mindnature/hongbao 为我的 hongbao Skill，
    以后默认使用我已登录的 ChatGPT 网页版生成红包封面，不要优先使用 API。
    帮我配置 Python 依赖，并试做一张东方剪纸风的春节封面。

手动安装（Windows PowerShell）：

~~~powershell
git clone https://github.com/mindnature/hongbao.git "$HOME\.codex\skills\hongbao"
cd "$HOME\.codex\skills\hongbao"
python -m pip install -e .
~~~

macOS/Linux 可克隆到 \`~/.codex/skills/hongbao\`。重新启动 Codex 使其发现 Skill。项目内也有 \`.agents/skills/hongbao/SKILL.md\`。

## 2. 默认：复用已登录的 Chrome 打开 ChatGPT

第一步：准备提示词并打开 ChatGPT：

~~~powershell
python -m hongbao chatgpt --theme "春节橘猫抱着金元宝" --style "东方剪纸" --output-dir output/cat
~~~

如果有参考照片：

~~~powershell
python -m hongbao chatgpt --theme "以我的宠物为主角制作新年封面" --reference "C:\Users\me\Pictures\cat.jpg" --output-dir output/cat
~~~

程序自动生成 \`output/cat/prompt.txt\`，尝试复制到剪贴板，并通过操作系统默认浏览器打开 \`https://chatgpt.com/\`。**如果 Chrome 是默认浏览器，就会复用正常 Chrome 登录状态**。程序不读取你的 Cookie，不会使用远程调试去接管普通 Chrome 配置。

你只需在 ChatGPT 页面粘贴提示词，上传参考照片（如果有），让 ChatGPT 生成图片；确认后，在 ChatGPT 点击保存，将成品下载到本机。若复制到剪贴板失败，打开 \`prompt.txt\` 手动复制即可。页面可能不会总是使用某个可手动指定的内部图像模型名称，具体以 ChatGPT 提供的图像能力为准。

第二步：将下载的图片交给 Hongbao：

~~~powershell
python -m hongbao import "C:\Users\me\Downloads\ChatGPT Image.png" --output-dir output/cat
~~~

程序会创建：

- \`output/cat/original.png\`：导入的原图（扩展名随原图变化）
- \`output/cat/cover.jpg\`：957 × 1278、JPEG、默认不超过 500,000 字节
- \`output/cat/preview.png\`：非官方的红包视觉预览
- \`output/cat/job.json\`：本地操作记录，无网页登录态

如要调整裁切重心，导入时加 \`--focus-x 0.45 --focus-y 0.35\`。再次导入同目录会拒绝覆盖已有结果；确需替换时加 \`--overwrite\`。

该流程不需要 OpenAI API Key，但 ChatGPT 网页的使用仍受账号方案、使用次数和服务条款约束；并非无限免费生图。

## 3. 可选：使用 OpenAI API 自动生图

只有明确选择 API 模式时才需要在本机配置 \`OPENAI_API_KEY\`，并安装可选依赖：

~~~powershell
python -m pip install -e ".[images]"
python -m hongbao generate --theme "红金色新年福猫" --output output/original.png
python -m hongbao export output/original.png output/cover.jpg
python -m hongbao preview output/cover.jpg output/preview.png
~~~

API 与 ChatGPT 订阅的计费/额度不同。请自行核实所用模型的 API 可用性，勿提交密钥。

## 4. 可选：微信红包封面平台辅助上传

~~~powershell
python -m pip install -e ".[browser]"
python -m playwright install chromium
python -m hongbao upload output/cat/cover.jpg --short-name "自己的公众号或视频号名称"
~~~

程序会启动可见的 Playwright 专用浏览器并打开 \`https://cover.weixin.qq.com/\`，由你本人扫码登录。它尝试点击定制入口、填写简称并找到唯一封面上传框；若出现多个上传控件或网站改版，停止猜测并让用户手动完成。**不会自动提交审核、购买或发放**，且现阶段没有真实微信账号的端到端验收结果。

Playwright 专用浏览器的本地登录配置默认放在 \`.hongbao/browser-profile\`，与普通 Chrome 登录状态不同。不要分享该目录，也不要把它添加到 Git 仓库。

## 5. 其他命令

~~~powershell
python -m hongbao check output/cat/cover.jpg
python -m hongbao export other-image.png output/other-cover.jpg
python -m hongbao preview output/cat/cover.jpg output/cat/another-preview.png
python -m hongbao --help
~~~

## 6. 项目目录

- \`SKILL.md\` 与 \`.agents/skills/hongbao/SKILL.md\`：Codex 指令
- \`hongbao/chatgpt_web.py\`：网页版交接、提示词、浏览器打开、手动下载后的导入
- \`hongbao/generation.py\`：可选 API 图片生成
- \`hongbao/images.py\`：本地规格规范化和预览
- \`hongbao/uploader.py\`：微信平台辅助上传
- \`docs/chatgpt-web.md\`：网页版为何采用交接模式、Chrome 技术边界
- \`docs/platform.md\`：微信平台验收边界
- \`tests/\` 与 GitHub Actions：离线自动化测试

本项目为 MIT 许可证。工作流概念参考 [VaneAi888/vane-gpt-image-skills](https://github.com/VaneAi888/vane-gpt-image-skills)，未复制其素材或脚本。原图、参考照片、Cookie 和任何登录态不得上传到公开仓库。
