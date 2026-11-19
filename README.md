# Hongbao 🧧

**一句话生成微信红包封面｜上传照片改造｜规格校验｜模拟预览｜扫码后辅助上传**

Hongbao 是一个独立开源的 Codex Skill，支持使用 GPT Image 2.6 生成/编辑红包封面，使用 Pillow 处理上传文件，并在本地通过 Playwright 打开微信红包封面开放平台完成可识别的上传操作。

> 非微信官方产品。图片符合程序的尺寸与大小检查，不代表获得平台审核通过。浏览器自动化尚未在真实微信账号的当前页面上完成端到端验证，必须以页面提示为准。

## 1. 在 Codex 安装

把下面这句话粘贴给有文件和终端操作权限的 Codex：

    请安装 https://github.com/mindnature/hongbao 作为我的 hongbao Skill。
    将仓库克隆到 ~/.codex/skills/hongbao，安装项目依赖，
    然后用 $hongbao 帮我生成一张春节红包封面。

或自行安装（macOS/Linux）：

~~~bash
git clone https://github.com/mindnature/hongbao.git ~/.codex/skills/hongbao
cd ~/.codex/skills/hongbao
python -m pip install -e ".[images,browser]"
python -m playwright install chromium
~~~

Windows PowerShell 可将目标文件夹改为 $HOME\.codex\skills\hongbao，重新启动 Codex 使其发现 Skill。在仓库内部开发时也提供 .agents/skills/hongbao/SKILL.md。

## 2. 两种生成方法

设置自己的 OPENAI_API_KEY（在系统环境变量中配置，不得写进仓库、截屏或提交）。默认图像模型为 gpt-image-2.6-sunburst，也可通过 --model 改用 gpt-image-2.6-flare。API 单独计费，不是无限免费生图。也可用 Codex 当前可用的其他图像工具生成原图，再直接使用第 3 步。

~~~bash
# 文字生成
python -m hongbao generate --theme "红金色新年福猫，抱着金元宝" --style "东方剪纸" --output output/original.png

# 上传自己的照片并以照片为参考
python -m hongbao generate --theme "将宠物变为喜庆的招财猫，保留脸部特征" --reference ./my-cat.jpg --output output/original.png
~~~

未经许可不得使用他人肖像、商标或受保护的作品。

## 3. 导出和检查

~~~bash
python -m hongbao export output/original.png output/cover.jpg
python -m hongbao check output/cover.jpg
python -m hongbao preview output/cover.jpg output/preview.png
~~~

- 生成图或参考照片可以是其他尺寸；导出按比例裁剪缩放为 **957 × 1278**、JPEG、默认最大 **500,000 字节**，不拉伸人物。
- 可以用 --focus-x/--focus-y (0 到 1) 调整裁剪重心；裁切与遮挡区域需要肉眼检查。
- preview 是自制近似示意，不是微信官方预览、也不能用作上传素材。
- 平台规则可能改变；务必以实际上传页面为准。

## 4. 浏览器辅助上传

~~~bash
python -m hongbao upload output/cover.jpg --short-name "自己的公众号或视频号名称"
~~~

程序会检查文件、启动**本地可见浏览器**并进入 https://cover.weixin.qq.com/。需要本人在微信中扫码登录；程序尝试点击“定制封面”、填写简称及上传 JPEG。页面布局若变动，会停在当前页并提示用户手动选择，且保存诊断截图。

**自动化边界：** 不能无感代替用户完成扫码/平台认证；不处理验证码、短信验证、实名认证、审核提交、购买、发放等敏感环节；没有接入微信官方上传 API，也不保证网页字段稳定。真实平台适配仍待登录账号测试。

浏览器持久登录数据默认保存在 .hongbao/browser-profile（被 .gitignore 忽略），仅存用户本地，请勿分享该文件夹。不输入微信密码或将 cookie 发给助手。

## 5. 项目结构

- SKILL.md：可直接安装的 Codex Skill 入口
- .agents/skills/hongbao/SKILL.md：工作区技能入口
- hongbao/generation.py：GPT Image 2.6 图像生成与参考图编辑
- hongbao/images.py：裁切、导出、规格校验与模拟预览
- hongbao/uploader.py：Playwright 本地扫码后辅助上传
- tests/：离线图像检查测试
- docs/platform.md：平台限制和验收清单

## 许可证与来源

本项目代码独立编写，许可证为 MIT。概念参考 [VaneAi888/vane-gpt-image-skills](https://github.com/VaneAi888/vane-gpt-image-skills) 的红包封面制作工作流；未复制其脚本、图库或风格图片。感谢原作者开源。

如未安装相关可选依赖，命令会提示所缺项目。GitHub 仓库开源免费，但 OpenAI 图像 API 调用及微信封面平台的购买/发放可能产生独立费用。
