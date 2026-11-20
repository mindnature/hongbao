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
    web.add_argument("--mode", choices=("still", "gif"), default="still", help="动态图请选择 gif")
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


    animation = sub.add_parser("animate", help="不需要 Flow：静态图片直接生成程序化动画 MP4")
    animation.add_argument("source", help="静态 PNG/JPEG/WebP")
    animation.add_argument("destination", help="新的 MP4 文件名")
    animation.add_argument("--preset", choices=(
        "zoom", "pan", "festive-glow", "sparkle", "petals",
        "lantern-sway", "cloud-drift", "parallax",
    ), default="festive-glow")
    animation.add_argument("--duration", type=float, default=3.0, help="1–3 秒")
    animation.add_argument("--fps", type=int, choices=(24,), default=24)
    animation.add_argument("--intensity", type=float, default=0.55, help="效果强度 0–1")
    animation.add_argument("--seed", type=int, default=7, help="粒子与花瓣随机种子")
    animation.add_argument("--focus-x", type=float, default=0.5, help="横向裁切焦点 0–1")
    animation.add_argument("--focus-y", type=float, default=0.5, help="纵向裁切焦点 0–1")
    animation.add_argument("--poster", help="可选：同时导出 PNG 预览帧")

    gif = sub.add_parser("gif2mp4", help="检查多帧 GIF 并转为短视频 MP4")
    gif.add_argument("source", help="下载的动画 .gif")
    gif.add_argument("destination", help="生成的 .mp4 路径")
    gif.add_argument("--duration", type=float, default=3.0, help="时长 1–3 秒；短 GIF 自动循环")

    gifcheck = sub.add_parser("check-gif", help="检查 GIF 的帧数、时长和解码状态")
    gifcheck.add_argument("source")

    motion = sub.add_parser("motion", help="将 Flow 视频/GIF/静态原图转换为 1–3 秒 MP4 动态封面")
    motion.add_argument("source", help="源 MP4/MOV/GIF 或静态图片")
    motion.add_argument("destination", help="目标 .mp4")
    motion.add_argument("--start", type=float, default=0.0, help="视频片段起始秒数")
    motion.add_argument("--duration", type=float, default=3.0, help="输出时长，1–3 秒")
    motion.add_argument("--effect", choices=("zoom", "none"), default="zoom",
                        help="仅针对静态图：轻微推镜 zoom 或纯静止 none")

    vcheck = sub.add_parser("check-video", help="校验 MP4 格式、时长、码率、分辨率与帧率")
    vcheck.add_argument("source")

    poster = sub.add_parser("poster", help="为动态视频提取 PNG 预览帧")
    poster.add_argument("source")
    poster.add_argument("destination")
    poster.add_argument("--at", type=float, default=0.0)

    frames = sub.add_parser("frames", help="将视频/GIF/静态图导出连续命名的 PNG ZIP 序列帧")
    frames.add_argument("source")
    frames.add_argument("destination", help="目标 .zip")
    frames.add_argument("--kind", choices=("cover", "ornament"), default="cover",
                        help="cover=动态封面，ornament=透明封面挂件")
    frames.add_argument("--start", type=float, default=0.0)
    frames.add_argument("--duration", type=float, default=3.0)

    fcheck = sub.add_parser("check-frames", help="校验动态封面/挂件 PNG 序列帧 ZIP")
    fcheck.add_argument("source")
    fcheck.add_argument("--kind", choices=("cover", "ornament"), default="cover")

    upload = sub.add_parser("upload", help="微信平台辅助上传（动态素材需人工选择准确栏目）")
    upload.add_argument("cover")
    upload.add_argument("--short-name", required=True)
    upload.add_argument("--kind", choices=("cover", "ornament"), default="cover")
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
                reference=args.reference, mode=args.mode,
                open_browser=not args.no_open, copy_clipboard=not args.no_copy)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print("请在网页中粘贴 prompt.txt 的内容；如果提供了照片，请自行上传。")
            print("GIF 模式下载后运行 gif2mp4；静态模式下载后运行 import。")
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
        elif args.command == "animate":
            from .animate import render_animated_cover
            result = render_animated_cover(
                args.source, args.destination, preset=args.preset,
                duration=args.duration, fps=args.fps, intensity=args.intensity,
                seed=args.seed, focus_x=args.focus_x, focus_y=args.focus_y,
                poster=args.poster,
            )
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        elif args.command == "check-gif":
            from .gif_workflow import check_gif
            result = check_gif(args.source)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
            if not result.valid:
                return 2
        elif args.command == "gif2mp4":
            from .gif_workflow import gif_to_mp4
            result = gif_to_mp4(args.source, args.destination, duration=args.duration)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        elif args.command == "motion":
            from .video import render_motion
            print(json.dumps(asdict(render_motion(
                args.source, args.destination, start=args.start,
                duration=args.duration, effect=args.effect)), ensure_ascii=False, indent=2))
        elif args.command == "check-video":
            from .video import check_video
            result = check_video(args.source)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
            if not result.valid:
                return 2
        elif args.command == "poster":
            from .video import make_poster
            print(str(make_poster(args.source, args.destination, at=args.at)))
        elif args.command == "frames":
            from .video import render_frames
            print(json.dumps(asdict(render_frames(
                args.source, args.destination, kind=args.kind,
                start=args.start, duration=args.duration)), ensure_ascii=False, indent=2))
        elif args.command == "check-frames":
            from .video import check_frames
            result = check_frames(args.source, kind=args.kind)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
            if not result.valid:
                return 2
        elif args.command == "upload":
            from .uploader import assist_upload
            result = assist_upload(args.cover, args.short_name, kind=args.kind,
                                   profile_dir=args.profile_dir,
                                   screenshots_dir=args.screenshots_dir)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, FileNotFoundError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
