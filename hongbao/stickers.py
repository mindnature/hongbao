"""Sticker creation handoff and local WeChat-sized PNG/GIF export.

This module never generates images on a website or reads browser sessions.
ChatGPT image generation is a human-supervised browser handoff. Export rules
are local technical targets, not platform approval.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import tempfile
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError

from .chatgpt_web import CHATGPT_URL, copy_to_clipboard

STICKER_SIZE = (240, 240)
STICKER_LIMIT = 500_000
MAX_FRAMES = 180
MAX_SOURCE_PIXELS = 36_000_000


def _mode(theme: str | None, reference: str | Path | None) -> str:
    if bool(theme and theme.strip()) == bool(reference):
        raise ValueError("必须且只能提供 --theme 或 --reference 其中一种")
    return "reference" if reference else "theme"


def build_sticker_prompt(*, theme: str | None = None,
                         reference: str | Path | None = None,
                         emotion: str = "开心", caption: str = "",
                         style: str = "精致可爱、形象统一",
                         animated: bool = False) -> str:
    mode = _mode(theme, reference)
    if not emotion.strip():
        raise ValueError("表情动作/情绪不能为空")
    lines = [
        "请直接使用 ChatGPT 网页的图片生成功能创作一枚独立微信表情，不要仅回复文本或提示词。",
        "正方形 1:1 单图、一个主体、不要多格拼贴、不要手机界面、不要额外 logo 和水印。",
        "请采用清楚的轮廓、夸张且可辨识的面部表情、明确的肢体动作，"
        "画面边缘留安全空间，适合缩小到 240×240 像素后辨认。",
        "请尽量使用真正透明背景，不要把白底棋盘格画成假透明；如果无法提供透明图，请如实说明。",
    ]
    if mode == "theme":
        lines.append(f"原创角色与主题：{theme.strip()}。请从这个描述构建统一稳定的角色形象。")
    else:
        lines.append(
            "我会在 ChatGPT 网页手动上传一张自己拥有使用权的参考图片。"
            "请以图片中主要角色为角色母版：保留面孔、发型、体色、服饰、"
            "关键识别元素和比例，不要在不同画面中随意换角色。"
            "如果原图是真人照片，可转为清晰可爱的风格化人物，但保留可辨识特征。"
        )
    if style.strip():
        lines.append(f"艺术风格：{style.strip()}。")
    lines.append(f"本枚表情的情绪及动作：{emotion.strip()}。请让角色真正做出对应表演。")
    if caption.strip():
        lines.append(f"表情文字：只添加“{caption.strip()}”几个字，清晰可辨且不盖住五官，禁止额外文字。")
    else:
        lines.append("除非情绪动作确实需要，否则不要加文字。")
    if animated:
        lines.extend([
            "请直接生成可下载的真正多帧循环 GIF 动画，不能只生成静态图后改扩展名。",
            "强调逐帧角色表演：表情、四肢、身体姿势在不同帧中发生清楚变化，"
            "而不是简单晃动整张图片。动作连续、节奏有停顿、首尾衔接自然。",
            "若当前 ChatGPT 账号没有 GIF 生成能力，请明确告知并改为生成静态 PNG 供后续处理。",
        ])
    else:
        lines.append("请直接生成一张高质量 PNG 静态表情，优先透明背景。")
    lines.append("请只生成这一枚独立表情，不要一次输出整套拼图。")
    return "\n".join(lines)


def _reference_path(reference: str | Path | None) -> Path | None:
    if reference is None:
        return None
    path = Path(reference).expanduser()
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.resolve()


def prepare_sticker_job(directory: str | Path, *,
                        theme: str | None = None,
                        reference: str | Path | None = None,
                        emotion: str = "开心", caption: str = "",
                        style: str = "精致可爱、形象统一",
                        animated: bool = False,
                        open_browser: bool = True,
                        copy_clipboard: bool = True) -> dict:
    mode = _mode(theme, reference)
    ref = _reference_path(reference)
    prompt = build_sticker_prompt(theme=theme, reference=ref, emotion=emotion,
                                  caption=caption, style=style, animated=animated)
    folder = Path(directory).expanduser()
    if folder.exists() and any((folder / p).exists() for p in
                               ("sticker.png", "sticker.gif", "job.json", "prompt.txt")):
        raise ValueError("目标目录已有表情任务；请换 --output-dir，避免覆盖")
    folder.mkdir(parents=True, exist_ok=True)
    prompt_file, manifest = folder / "prompt.txt", folder / "job.json"
    prompt_file.write_text(prompt, encoding="utf-8")
    payload = {
        "kind": "wechat-sticker",
        "generation_mode": mode,
        "animated": animated,
        "theme": theme.strip() if theme else None,
        "reference": str(ref) if ref else None,
        "emotion": emotion,
        "caption": caption,
        "style": style,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "awaiting_chatgpt_download",
        "prompt_file": str(prompt_file.resolve()),
    }
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    copied = bool(globals()["copy_to_clipboard"](prompt)) if copy_clipboard else False
    opened = bool(webbrowser.open(CHATGPT_URL, new=2)) if open_browser else False
    return {
        "mode": mode, "animated": animated,
        "prompt": str(prompt_file.resolve()),
        "reference": str(ref) if ref else None,
        "copied_to_clipboard": copied,
        "browser_open_requested": open_browser,
        "browser_open_succeeded": opened,
        "next": "在 ChatGPT 网页粘贴提示词，参考图模式需本人上传原图；保存成品后运行 "
                f'python -m hongbao sticker-import "下载素材路径" --output-dir "{folder}"',
    }


def prepare_sticker_pack(directory: str | Path, *,
                         emotions: str, theme: str | None = None,
                         reference: str | Path | None = None,
                         style: str = "精致可爱、形象统一",
                         animated: bool = False,
                         open_browser: bool = True,
                         copy_clipboard: bool = True) -> dict:
    mode = _mode(theme, reference)
    ref = _reference_path(reference)
    items = [s.strip() for s in emotions.split(",") if s.strip()]
    if not (1 <= len(items) <= 24):
        raise ValueError("一次需要指定 1–24 个表情，以英文逗号分隔")
    if len(set(items)) != len(items):
        raise ValueError("存在重复的表情名称")
    folder = Path(directory).expanduser()
    if folder.exists() and any(folder.iterdir()):
        raise ValueError("输出目录非空；请指定新 --output-dir")
    prompts = [build_sticker_prompt(theme=theme, reference=ref, emotion=e,
                                    caption=e, style=style, animated=animated)
               for e in items]
    folder.mkdir(parents=True, exist_ok=True)
    prompt_dir = folder / "prompts"
    prompt_dir.mkdir()
    manifest = {
        "kind": "wechat-sticker-pack",
        "generation_mode": mode, "reference": str(ref) if ref else None,
        "theme": theme.strip() if theme else None,
        "style": style, "animated": animated,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "awaiting_individual_downloads",
        "items": [],
    }
    for i, (emotion, prompt) in enumerate(zip(items, prompts), 1):
        relative = f"prompts/{i:02d}.txt"
        (folder / relative).write_text(prompt, encoding="utf-8")
        manifest["items"].append({"index": i, "emotion": emotion, "prompt": relative})
    (folder / "pack.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    # For packs, open once and copy only first prompt. Each emotion is a
    # separate creation to avoid gridded collages and consistency drift.
    copied = bool(globals()["copy_to_clipboard"](prompts[0])) if copy_clipboard else False
    opened = bool(webbrowser.open(CHATGPT_URL, new=2)) if open_browser else False
    return {
        "mode": mode, "count": len(items), "animated": animated,
        "manifest": str((folder / "pack.json").resolve()),
        "prompts": str(prompt_dir.resolve()),
        "reference": str(ref) if ref else None,
        "copied_first_prompt": copied, "browser_open_requested": open_browser,
        "browser_open_succeeded": opened,
        "next": "依次使用 prompts 中各份提示词；参考图模式每一枚都需上传参考图或前一枚确认的角色母版。"
                "各张成品分别保存，再逐个运行 sticker-import。"
    }


def _contained(frame: Image.Image) -> Image.Image:
    image = ImageOps.contain(frame.convert("RGBA"), STICKER_SIZE,
                             method=Image.Resampling.LANCZOS)
    result = Image.new("RGBA", STICKER_SIZE, (0, 0, 0, 0))
    result.alpha_composite(image, ((240-image.width)//2, (240-image.height)//2))
    return result


def check_sticker(path: str | Path, *, max_bytes: int = STICKER_LIMIT) -> dict:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    issues = []
    warnings = []
    try:
        with Image.open(path) as img:
            fmt = img.format
            count = getattr(img, "n_frames", 1)
            size = img.size
            transparency = False
            if fmt == "PNG":
                transparency = (img.mode in ("RGBA", "LA") and
                                img.getchannel("A").getextrema()[0] < 255)
            elif fmt == "GIF":
                transparency = any("transparency" in f.info for f in
                                   ImageSequence.Iterator(img))
            if size != STICKER_SIZE:
                issues.append("表情尺寸必须为 240×240")
            if fmt not in ("PNG", "GIF"):
                issues.append("只支持静态 PNG 或动态 GIF")
            if fmt == "GIF" and count < 2:
                issues.append("动态 GIF 至少需要两帧")
            if fmt == "PNG" and count != 1:
                issues.append("静态 PNG 只能是一帧")
            if not transparency:
                warnings.append("没有检测到真正透明背景；若投稿要求透明底，请重新生成")
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        issues.append("无法读取表情文件：" + str(exc))
        fmt, count, size, transparency = "unknown", 0, (0, 0), False
    total_bytes = path.stat().st_size
    if total_bytes > max_bytes:
        issues.append(f"表情文件超出限制：{total_bytes} > {max_bytes} 字节")
    return {"path": str(path), "valid": not issues, "issues": issues,
            "warnings": warnings, "format": fmt, "frames": count,
            "width": size[0], "height": size[1],
            "bytes": total_bytes, "transparent": transparency}


def _encode_gif(frames: list[Image.Image], durations: list[int],
                destination: Path, *, colors: int = 128) -> None:
    # Quantize with a shared conceptual palette budget; Pillow keeps alpha for
    # genuinely transparent sources but cannot remove opaque source backgrounds.
    palette_frames = [frame.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
                      for frame in frames]
    palette_frames[0].save(
        destination, "GIF", save_all=True, append_images=palette_frames[1:],
        duration=durations, loop=0, disposal=2, optimize=True,
    )


def export_sticker(source: str | Path, destination: str | Path, *,
                   max_bytes: int = STICKER_LIMIT) -> dict:
    src, dst = Path(source).expanduser(), Path(destination).expanduser()
    if not src.is_file():
        raise FileNotFoundError(src)
    if src.resolve() == dst.resolve():
        raise ValueError("输入和输出不能是同一个文件")
    if dst.exists():
        raise ValueError("输出文件已存在，不会覆盖")
    if max_bytes < 10_000:
        raise ValueError("max_bytes 过小")
    with Image.open(src) as image:
        if image.width * image.height > MAX_SOURCE_PIXELS:
            raise ValueError("素材像素数过大")
        animated = image.format == "GIF" and getattr(image, "n_frames", 1) > 1
        if animated:
            if dst.suffix.lower() != ".gif":
                raise ValueError("多帧 GIF 应输出到 .gif 文件")
            total = image.n_frames
            if total > MAX_FRAMES:
                raise ValueError(f"GIF 超过 {MAX_FRAMES} 帧，请先缩短")
            frames = []
            durations = []
            for item in ImageSequence.Iterator(image):
                item.load()
                frames.append(_contained(item))
                durations.append(max(20, int(item.info.get("duration") or 100)))
        else:
            if dst.suffix.lower() != ".png":
                raise ValueError("静态表情必须输出 .png 文件")
            frames = [_contained(ImageOps.exif_transpose(image))]
            durations = []
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".hongbao-sticker-", dir=dst.parent) as tmp:
        candidate = Path(tmp) / dst.name
        if animated:
            for colors in (128, 96, 64, 48, 32):
                _encode_gif(frames, durations, candidate, colors=colors)
                if check_sticker(candidate, max_bytes=max_bytes)["valid"]:
                    break
            else:
                raise ValueError("GIF 无法压缩至大小限制，请减少画面复杂度或帧数")
        else:
            frames[0].save(candidate, "PNG", optimize=True)
        report = check_sticker(candidate, max_bytes=max_bytes)
        if not report["valid"]:
            raise ValueError("导出表情未通过检查：" + "；".join(report["issues"]))
        shutil.move(str(candidate), str(dst))
    report = check_sticker(dst, max_bytes=max_bytes)
    return report


def import_sticker(source: str | Path, directory: str | Path, *,
                   max_bytes: int = STICKER_LIMIT) -> dict:
    src = Path(str(source).strip().strip('"').strip("'")).expanduser()
    if not src.is_file():
        raise FileNotFoundError(src)
    with Image.open(src) as im:
        animated = im.format == "GIF" and getattr(im, "n_frames", 1) > 1
    folder = Path(directory).expanduser()
    original = folder / ("original" + src.suffix.lower())
    dst = folder / ("sticker.gif" if animated else "sticker.png")
    manifest = folder / "job.json"
    if (original.exists() and original.resolve() != src.resolve()) or dst.exists():
        raise ValueError("目标目录已有成品；请指定新的 --output-dir")
    if manifest.exists():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if payload.get("kind") != "wechat-sticker":
            raise ValueError("此目录不是单张表情任务，请指定新的输出目录")
    else:
        payload = {"kind": "wechat-sticker", "generation_mode": "unknown"}
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".hongbao-sticker-import-", dir=folder) as tmp:
        temp = Path(tmp)
        staged_original = temp / original.name
        staged = temp / dst.name
        shutil.copy2(src, staged_original)
        report = export_sticker(staged_original, staged, max_bytes=max_bytes)
        if src.resolve() != original.resolve():
            shutil.move(str(staged_original), str(original))
        shutil.move(str(staged), str(dst))
    report = check_sticker(dst, max_bytes=max_bytes)
    payload.update({
        "status": "exported_locally",
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "original": str(original.resolve()),
        "sticker": str(dst.resolve()),
        "sticker_format": report["format"],
    })
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    return {"step": "sticker-import", "original": str(original.resolve()),
            "sticker": str(dst.resolve()), "check": report,
            "note": "仅完成本地导出；未自动上传微信表情开放平台。"}
