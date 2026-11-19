# ChatGPT 网页版模式：已登录 Chrome 交接方案

更新：2026-11-19

## 目标

充分利用用户本人已登录的 ChatGPT 网站会话，避免强制绑定 OpenAI API Key；同时让图片规范化、预览与微信上传成为可复用的本地流程。

## 实际边界

- 程序使用 Python 标准库 webbrowser.open('https://chatgpt.com/') 打开**操作系统默认浏览器**，如果 Chrome 是默认浏览器即可复用已登录会话。
- 程序不会接管 Chrome 的页面，也不会获取浏览器 Cookie、令牌、会话内容或自动提取图片。
- 用户自己粘贴已准备的 prompt.txt；如指定 --reference，用户自己在 ChatGPT 网页上传参考照片；图片生成后通过 ChatGPT 的原生“保存”/下载操作取得文件。
- 本地执行 import 自动复制原图、裁切/压缩至 957×1278 JPEG、生成模拟预览、校验大小。
- 现有 chatgpt 命令**不会**把提示词自动发送到 ChatGPT 网页，也不会自动下载 ChatGPT 的生成内容。CLI 的 copied_to_clipboard 仅表示本机系统剪贴板操作成功，不代表网页提交成功。
- 手动下载文件不是浏览器接口提取；无需额外的独立 Chrome Profile，也无意伪装为 API。

## 为什么不直接附加到现有 Chrome？

从 Chrome 136 开始，远程调试端口/管道不会对浏览器默认用户数据目录生效；用正常 Chrome 登录配置直接附加 CDP 并不具备可移植性，且可能危及已登录状态的安全。Chrome 官方建议远程调试使用独立用户数据目录。不能为了复用账号去复制或导出真实 Profile/Cookie。

即使技术上有独立浏览器自动化，ChatGPT 网站访问仍受 OpenAI 使用条款约束，网页程序化提取输出可能不被允许。该项目不实现自动抓取生图结果、伪造接口、模拟隐藏鉴权或绕过防护。

参考：
- https://developer.chrome.com/blog/remote-debugging-port
- https://openai.com/policies/terms-of-use/
- https://help.openai.com/en/articles/11084440-images-in-chatgpt

## Windows 示例

    python -m hongbao chatgpt --theme "国风仙鹤与祥云" --output-dir output/scene1
    # 在 ChatGPT 页面贴入 prompt.txt，生成图片后手动下载。
    python -m hongbao import "$HOME\Downloads\ChatGPT Image.png" --output-dir output/scene1

PowerShell 的路径如包含空格，请用双引号。可通过文件资源管理器“复制为路径”粘贴图片路径。

## 验收

- 关闭 API Key 后执行 chatgpt 命令，成功生成 prompt.txt，无 API 请求。
- 默认浏览器为 Chrome 时可打开已登录 ChatGPT。
- 用户手动下载 PNG/JPEG/WebP，执行 import 后产生原图、cover.jpg、preview.png。
- 异常输入和同名文件冲突需明确报错，不覆盖用户原始照片。
- 不应把“打开网页”或“复制到剪贴板”报告成“已自动生图”。
- 使用 API 是另一个明确选择的命令，不应作为网页模式的隐式回退。
