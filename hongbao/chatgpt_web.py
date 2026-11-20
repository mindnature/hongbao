"""ChatGPT website handoff: prompt creation + user-directed local image import.

Does not automate chatgpt.com, extract browser content, or inspect cookies.
"""

from __future__ import annotations

import json
import shutil
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from .images import MAX_BYTES, check_cover, export_cover, make_preview

CHATGPT_URL = "https://chatgpt.com/"
DEFAULT_DIR = "output/chatgpt"


def build_chatgpt_prompt(theme: str, style: str = "", has_reference: bool = False,
                         mode: str = "still") -> str:
    if not theme.strip():
        raise ValueError("主题不能为空")
    if mode not in ("still", "gif"):
        raise ValueError("mode 必须为 still 或 gif")
    if mode == "gif":
        lines = [
            "请使用 ChatGPT Images 的 GIF 动画生成功能，直接生成真正可下载的多帧循环 GIF；不要只给文字、单张图片或静态九宫格。",
            "如我的账号尚未开放 GIF 生成功能，请直接说明，不要把静态图伪称为 GIF。",
            "用途：微信动态红包封面艺术创作，竖版 3:4，完整独立画作，不是微信界面截图。",
            f"主题：{theme.strip()}。",
        ]
        if style.strip():
            lines.append(f"风格：{style.strip()}。")
        if has_reference:
            lines.append("我会上传自己拥有使用权的参考照片，请保持其主体、人物或宠物的可辨识特征在每一帧稳定。")
        lines.extend([
            "请创作约 2–3 秒、首尾自然衔接的无缝循环动画，动作真实可辨而克制。",
            "让主题中的局部元素运动，比如花瓣飘落、祥云轻移、凤凰缓缓舒翼、灯笼轻晃、鎏金闪烁；避免整张画面仅做推镜。",
            "不要让角色变脸、肢体畸变、背景忽明忽暗、动作跳切、物体凭空消失。",
            "关键主体、脸部和精细装饰避开顶部约 20% 和底部约 18% 的可能遮挡区。",
            "禁止二维码、微信红包 UI、商标、水印、文字字幕、拼图及边框。",
            "请直接生成一张可以保存到本地的真正动态 GIF 文件，我会在本地将其转换为 MP4。",
        ])
        return "\n".join(lines)
    lines = [
        "请直接使用 ChatGPT 的图片生成功能创作一张全新图片，不要仅给我文字提示词。",
        "用途：中国微信红包封面的原创艺术原画，竖版 3:4 构图，",
        "画面是完整的艺术原图，不是放在手机或微信界面里的效果图。",
        f"主题：{theme.strip()}。",
    ]
    if style.strip():
        lines.append(f"风格：{style.strip()}。")
    if has_reference:
        lines.append(
            "我会在本条消息上传自有或已获授权的参考照片。请根据照片创作，"
            "保留人物/宠物的关键可辨识特征，优先保护脸部、姿态的自然与真实性；"
            "不要自行添加与原照不相符的人物。"
        )
    lines.extend([
        "构图要求：主体集中在画面中间区域，人物脸部和关键细节避开最上方约 20% 与最下方约 18%，"
        "四周保留适度视觉安全边界，避免最终按 3:4 比例裁切时截断主体。",
        "设计要求：有完整的色彩层次和细节，清晰高级；"
        "不画微信红包按钮、头像、聊天气泡、扫码框、二维码、联系方式、商标或水印。",
        "除非主题明确要求祝福语，否则不要生成文字。不要生成九宫格、拼图或多个方案。",
        "请只输出一张可以单独保存的成品原图。"
    ])
    return "\n".join(lines)


def copy_to_clipboard(text: str) -> bool:
    """Optional convenience; failure must not prevent the workflow."""
    try:
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        try:
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
        finally:
            root.destroy()
        return True
    except (ImportError, OSError, RuntimeError, Exception):
        return False


def prepare_chatgpt_job(theme: str, directory: str | Path = DEFAULT_DIR, *,
                        style: str = "", reference: str | Path | None = None,
                        mode: str = "still", open_browser: bool = True,
                        copy_clipboard: bool = True) -> dict:
    prompt = build_chatgpt_prompt(theme, style, has_reference=bool(reference), mode=mode)
    reference_path: Path | None = None
    if reference is not None:
        reference_path = Path(reference).expanduser()
        if not reference_path.is_file():
            raise FileNotFoundError(reference_path)
        reference_path = reference_path.resolve()

    directory = Path(directory).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    prompt_path = directory / "prompt.txt"
    manifest_path = directory / "job.json"
    # Do not silently mix a new request with an already imported cover.
    if (directory / "cover.jpg").exists() or (directory / "preview.png").exists():
        raise ValueError("输出目录已有封面结果。请指定新的 --output-dir，避免混淆作品。")
    prompt_path.write_text(prompt, encoding="utf-8")
    manifest = {
        "workflow": "chatgpt-web-handoff",
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "theme": theme,
        "style": style,
        "reference": str(reference_path) if reference_path else None,
        "status": "awaiting_user_generated_download",
        "prompt_file": str(prompt_path.resolve()),
        "chatgpt_url": CHATGPT_URL,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    clipboard_ok = copy_to_clipboard(prompt) if copy_clipboard else False
    opened = bool(webbrowser.open(CHATGPT_URL, new=2)) if open_browser else False
    return {
        "step": "prepare",
        "prompt": str(prompt_path.resolve()),
        "reference": str(reference_path) if reference_path else None,
        "copied_to_clipboard": clipboard_ok,
        "browser_open_requested": open_browser,
        "browser_open_succeeded": opened,
        "chatgpt_url": CHATGPT_URL,
        "next": (
            (f'在 ChatGPT 网页生成 GIF 并手动下载，然后运行：'
             f'python -m hongbao import-gif "下载的动画.gif" --output-dir "{directory}" --duration 3；'
             f'如只需单独转码也可使用 gif2mp4')
            if mode == "gif" else
            (f'在 ChatGPT 网页生成静态图并手动下载，然后运行：'
             f'python -m hongbao import "下载图片路径" --output-dir "{directory}"')
        ),
    }


def import_chatgpt_image(source: str | Path, directory: str | Path = DEFAULT_DIR, *,
                         focus_x: float = 0.5, focus_y: float = 0.5,
                         max_bytes: int = MAX_BYTES, overwrite: bool = False) -> dict:
    source = Path(str(source).strip().strip('"').strip("'")).expanduser()
    if not source.is_file():
        raise FileNotFoundError(source)
    directory = Path(directory).expanduser()
    directory.mkdir(parents=True, exist_ok=True)

    # Validate the image content, not just the file extension.
    from PIL import Image
    with Image.open(source) as image:
        image.verify()
    original = directory / ("original" + source.suffix.lower())
    cover = directory / "cover.jpg"
    preview = directory / "preview.png"
    conflicts = [p for p in (original, cover, preview) if p.exists() and p.resolve() != source.resolve()]
    if conflicts and not overwrite:
        raise ValueError("输出文件已存在，为避免覆盖请换 --output-dir 或明确添加 --overwrite："
                         + ", ".join(str(p) for p in conflicts))
    if source.resolve() != original.resolve():
        shutil.copy2(source, original)
    report = export_cover(original, cover, focus_x=focus_x, focus_y=focus_y,
                          max_bytes=max_bytes)
    if not report.valid:
        raise ValueError("导出结果未通过本地检查：" + "；".join(report.issues))
    make_preview(cover, preview)
    manifest_path = directory / "job.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["status"] = "locally_exported"
        manifest["imported_at"] = datetime.now(timezone.utc).isoformat()
        manifest["original"] = str(original.resolve())
        manifest["cover"] = str(cover.resolve())
        manifest["preview"] = str(preview.resolve())
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "step": "import",
        "source": str(source.resolve()),
        "original": str(original.resolve()),
        "cover": str(cover.resolve()),
        "preview": str(preview.resolve()),
        "check": {
            "valid": check_cover(cover, max_bytes=max_bytes).valid,
            "size": f"{report.width}x{report.height}",
            "bytes": report.size_bytes,
        },
        "note": "已完成本地导出和模拟预览；未自动访问、上传或提交微信平台。",
    }
