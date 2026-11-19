"""hongbao command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .images import check_cover, export_cover, make_preview


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hongbao", description="微信红包封面创作和辅助上传")
    sub = parser.add_subparsers(dest="command", required=True)

    web = sub.add_parser("chatgpt", help="默认网页版：准备提示词并打开已登录的默认浏览器")
    web.add_argument("--theme", required=True)
    web.add_argument("--style", default="")
    web.add_argument("--reference", help="仅在本机保存路径；需在 ChatGPT 网页手动上传")
    web.add_argument("--output-dir", default="output/chatgpt")
    web.add_argument("--no-open", action="store_true", help="不自动打开 ChatGPT 网页")
    web.add_argument("--no-copy", action="store_true", help="不尝试复制提示词到系统剪贴板")

    imp = sub.add_parser("import", help="导入用户从 ChatGPT 网页保存的图片，并自动导出 JPEG 和预览图")
    imp.add_argument("source", help="手动下载的 JPG/PNG/WebP 图片路径")
    imp.add_argument("--output-dir", default="output/chatgpt")
    imp.add_argument("--focus-x", type=float, default=0.5)
    imp.add_argument("--focus-y", type=float, default=0.5)
    imp.add_argument("--max-bytes", type=int, default=500_000)
    imp.add_argument("--overwrite", action="store_true", help="明确允许覆盖已有结果")

    gen = sub.add_parser("generate", help="可选 API 模式（非默认），需要 OPENAI_API_KEY")
    gen.add_argument("--theme", required=True)
    gen.add_argument("--style", default="")
    gen.add_argument("--reference")
    gen.add_argument("--model", default="gpt-image-2.6-sunburst")
    gen.add_argument("--output", default="output/original.png")

    exp = sub.add_parser("export", help="导出上传用的 JPEG")
    exp.add_argument("source")
    exp.add_argument("destination")
    exp.add_argument("--focus-x", type=float, default=0.5)
    exp.add_argument("--focus-y", type=float, default=0.5)
    exp.add_argument("--max-bytes", type=int, default=500_000)

    chk = sub.add_parser("check", help="离线检查尺寸、格式、文件大小")
    chk.add_argument("cover")
    chk.add_argument("--max-bytes", type=int, default=500_000)

    prev = sub.add_parser("preview", help="生成仅供参考的模拟红包预览图")
    prev.add_argument("cover")
    prev.add_argument("destination")

    upload = sub.add_parser("upload", help="扫码后通过可见浏览器辅助上传微信平台")
    upload.add_argument("cover")
    upload.add_argument("--short-name", required=True)
    upload.add_argument("--profile-dir", default=".hongbao/browser-profile")
    upload.add_argument("--screenshots-dir", default=".hongbao/screenshots")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command == "chatgpt":
            from .chatgpt_web import prepare_chatgpt_job
            result = prepare_chatgpt_job(
                args.theme, args.output_dir, style=args.style,
                reference=args.reference, open_browser=not args.no_open,
                copy_clipboard=not args.no_copy)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print("请在网页中粘贴 prompt.txt 的内容；如果提供了照片，请自行上传。")
            print("在 ChatGPT 保存原图后，用 import 命令导入本地文件。")
        elif args.command == "import":
            from .chatgpt_web import import_chatgpt_image
            result = import_chatgpt_image(
                args.source, args.output_dir, focus_x=args.focus_x,
                focus_y=args.focus_y, max_bytes=args.max_bytes,
                overwrite=args.overwrite)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "generate":
            from .generation import generate_image
            p = generate_image(args.theme, args.output, style=args.style,
                               reference=args.reference, model=args.model)
            print(str(p))
        elif args.command == "export":
            result = export_cover(args.source, args.destination,
                                  focus_x=args.focus_x, focus_y=args.focus_y,
                                  max_bytes=args.max_bytes)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        elif args.command == "check":
            result = check_cover(args.cover, max_bytes=args.max_bytes)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
            if not result.valid:
                return 2
        elif args.command == "preview":
            print(make_preview(args.cover, args.destination))
        elif args.command == "upload":
            from .uploader import assist_upload
            result = assist_upload(args.cover, args.short_name,
                                   profile_dir=args.profile_dir,
                                   screenshots_dir=args.screenshots_dir)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, FileNotFoundError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
