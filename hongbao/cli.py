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

    gen = sub.add_parser("generate", help="使用图像 API 从主题/参考图片生成原画")
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

    upload = sub.add_parser("upload", help="扫码后通过可见浏览器辅助上传")
    upload.add_argument("cover")
    upload.add_argument("--short-name", required=True)
    upload.add_argument("--profile-dir", default=".hongbao/browser-profile")
    upload.add_argument("--screenshots-dir", default=".hongbao/screenshots")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command == "generate":
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
