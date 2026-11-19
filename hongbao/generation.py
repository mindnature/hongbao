"""Optional OpenAI image API engine. API charges are independent of this Skill."""

from __future__ import annotations

import base64
import os
from pathlib import Path

DEFAULT_MODEL = "gpt-image-2.6-sunburst"


def build_prompt(theme: str, style: str = "") -> str:
    if not theme.strip():
        raise ValueError("主题不能为空")
    style_part = f"视觉风格：{style}。" if style.strip() else ""
    return (
        "制作一张原创、高质量的中国微信红包封面艺术原画，竖向3:4构图。"
        "仅绘制艺术画面，不要微信界面、按钮、头像框、二维码、商标或水印。"
        "主题清晰、配色协调、质感精美。上方约20%和下方约18%避免关键人脸、"
        "主体和小字，以兼容可能的UI遮挡。重要内容尽量靠中心，"
        "不自动生成中文文字，除非主题明确要求。"
        f"{style_part}创作主题：{theme.strip()}"
    )


def generate_image(theme: str, destination: str | Path, *,
                   reference: str | Path | None = None,
                   style: str = "", model: str = DEFAULT_MODEL) -> Path:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("缺少 OPENAI_API_KEY。也可用已有的图像生成工具先制作原画。")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError('缺少 openai：请执行 pip install -e ".[images]"') from exc

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    client = OpenAI()
    prompt = build_prompt(theme, style)
    if reference:
        reference = Path(reference)
        if not reference.is_file():
            raise FileNotFoundError(reference)
        prompt += "。将上传照片作为被编辑的主要参照，尽可能保持主体可辨识身份特征。"
        with reference.open("rb") as image_file:
            response = client.images.edit(model=model, image=image_file, prompt=prompt,
                                          size="1024x1536", output_format="png")
    else:
        response = client.images.generate(model=model, prompt=prompt,
                                          size="1024x1536", output_format="png")
    if not response.data or not response.data[0].b64_json:
        raise RuntimeError("图像 API 未返回可写入的图片")
    destination.write_bytes(base64.b64decode(response.data[0].b64_json))
    return destination
