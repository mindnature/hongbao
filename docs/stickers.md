# Hongbao 表情包 V0.7：文字模式与参考图模式

## 概览

本项目在原有微信红包封面工作流之外，新增独立的「表情包」功能。二者不使用同一组导出规格：

- 红包封面：现有静态 JPEG、动态 MP4，以及封面/挂件 PNG ZIP。
- 表情包：静态 **PNG** 或动态 **GIF**，默认输出 **240×240**、**不超过 500KB**（仅为本地技术目标，正式投稿要以微信表情开放平台实时指引为准）。

ChatGPT 网站负责绘图；用户负责在网页粘贴提示词、上传参考图（如有）并下载成品；Hongbao 在本地处理格式、尺寸、文件大小与质量检查。它不会自动操控已经登录的 Chrome、读取 Cookie 或下载网页私有资源，不需要 API Key。

## 模式 A：文字主题

例如原创国风狐狸的「无语」表情：

~~~powershell
python -m hongbao sticker --theme "戴红色围巾的Q版小狐狸" --emotion "无语" --text "无语了" --style "软萌东方手绘" --output-dir output/fox-wuyu
~~~

执行后得到 output/fox-wuyu/prompt.txt 和 job.json。程序打开默认浏览器并尝试把提示词复制到剪贴板；在 ChatGPT 网页粘贴提示词，生成并保存单枚 PNG。

## 模式 B：参考图片

例如以用户自己宠物的照片为母版，制作「抱抱」表情：

~~~powershell
python -m hongbao sticker --reference "C:\Users\me\Pictures\cat.png" --emotion "抱抱" --text "抱抱" --style "真实特征保留+萌系化" --output-dir output/cat-hug
~~~

程序先验证参考图文件存在，只在本地记录文件路径。用户需要**手动把参考图添加到 ChatGPT 网页对话**。提示词强调面孔、毛色、关键服饰、比例、神态和角色一致性。无法承诺每一张生成结果 100% 不变形。

## 动态 GIF 版本

在上面任何一个生成命令后加 --animated，提示 ChatGPT 生成真正多帧动画，要求有明显角色表演而非整图移动。ChatGPT 网页实际是否支持 GIF 取决于当前可用功能。

~~~powershell
python -m hongbao sticker --theme "Q版橘猫打工人" --emotion "哈哈" --animated --output-dir output/cat-laugh
~~~

最终动态表情输出 **GIF**，不是 MP4。GIF 的调色板与透明通道可能受限，程序只进行合理缩放、帧数保留和大小压缩，不负责 AI 抠图或修复原画角色变化。

## 本地导入、导出与检查

~~~powershell
# 下载后自动识别静态或多帧 GIF，保留原图并导出目标尺寸
python -m hongbao sticker-import "C:\Users\me\Downloads\result.png" --output-dir output/fox-wuyu

# 直接转码单文件（不涉及 ChatGPT 任务）
python -m hongbao sticker-export "input.gif" "sticker.gif"

# 单独检查大小、格式、尺寸与透明度
python -m hongbao sticker-check output/fox-wuyu/sticker.png
~~~

静态图片使用等比居中放入透明 240×240 画布，不直接裁断主体；源图本身若是 JPG 或其他不透明背景，背景不会自动变透明。压缩后的动态图若仍无法低于大小限制，会明确失败，而不是输出超规格成品。文件不会默默覆盖，遇到同名文件请使用新输出目录。

## 批量准备（不自动混合九宫格）

文字模式：

~~~powershell
python -m hongbao sticker-pack --theme "国风锦鲤宝宝" --emotions "哈哈,无语,抱抱,点赞" --output-dir output/jinli
~~~

参考图模式：

~~~powershell
python -m hongbao sticker-pack --reference "角色母版.png" --emotions "开心,委屈,惊讶,睡觉" --animated --output-dir output/character
~~~

生成 prompts/01.txt、02.txt 等独立提示词以及 pack.json 清单。请按编号逐个贴到 ChatGPT 中，让每一枚表情单独保存，以维持角色一致性。同一角色推荐反复附上同一张母版。生成后分别用 sticker-import 导出，暂不提供自动提交专辑和全部审核附件的功能。

## 限制与参考

- 微信开放平台投稿要求可变；本工具只使用公开规格作为参考，不能代替账号资格、版权、审核或表情包完整性检查。
- 正式专辑可能要求规定数量、静动态不可混用、封面、聊天面板图标、横幅等独立素材；当前版本还不是一键上架工具。
- 字幕由 ChatGPT 绘制，若文字出错应要求其重做；本模块不会冒用未经授权的字体。
- 参考图涉及真人或宠物时，用户应拥有必要的使用或肖像授权。

官方平台：https://sticker.weixin.qq.com/
