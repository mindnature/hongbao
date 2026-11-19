"""Best-effort supervised browser automation, without private API calls or login bypass."""

from __future__ import annotations

import re
from pathlib import Path

from .images import check_cover

PORTAL = "https://cover.weixin.qq.com/"


def _click_create(page) -> bool:
    names = re.compile(r"定制封面|定制新的封面|创建封面|新建封面")
    for role in ("button", "link"):
        candidates = page.get_by_role(role, name=names)
        if candidates.count() == 1:
            candidates.click(timeout=5000)
            return True
    texts = page.get_by_text("定制封面", exact=True)
    if texts.count() == 1:
        texts.click(timeout=5000)
        return True
    return False


def _fill_short_name(page, short_name: str) -> bool:
    candidates = [
        page.get_by_label("封面简称", exact=False),
        page.get_by_placeholder(re.compile("封面简称|填写简称|请输入简称")),
    ]
    for locator in candidates:
        if locator.count() == 1:
            locator.fill(short_name, timeout=5000)
            return True
    return False


def _upload_image(page, cover: Path) -> bool:
    inputs = page.locator('input[type="file"]')
    eligible = []
    for i in range(inputs.count()):
        element = inputs.nth(i)
        accept = (element.get_attribute("accept") or "").lower()
        if not accept or any(s in accept for s in ("image", ".jpg", ".jpeg", ".png")):
            eligible.append(element)
    # Multiple candidate inputs might be for logos, story art or cover.
    if len(eligible) != 1:
        return False
    eligible[0].set_input_files(str(cover.resolve()), timeout=10000)
    return True


def _check_material(path: Path, kind: str) -> str:
    """Validate before launching the browser, never guess a dynamic upload field."""
    if kind not in ("cover", "ornament"):
        raise ValueError("kind 必须是 cover 或 ornament")
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        if kind != "cover":
            raise ValueError("静态 JPEG 不是透明挂件")
        report = check_cover(path)
        if not report.valid:
            raise ValueError("静态文件不合格：" + "；".join(report.issues))
        return "static-cover"
    from .video import check_frames, check_video
    if suffix == ".mp4":
        if kind != "cover":
            raise ValueError("MP4 动态封面不是透明挂件；请提供挂件 ZIP 序列帧")
        report = check_video(path)
        if not report.valid:
            raise ValueError("动态 MP4 不合格：" + "；".join(report.issues))
        return "dynamic-cover"
    if suffix == ".zip":
        report = check_frames(path, kind=kind)
        if not report.valid:
            raise ValueError("PNG 序列帧不合格：" + "；".join(report.issues))
        return "dynamic-cover-frames" if kind == "cover" else "dynamic-ornament"
    raise ValueError("支持 JPEG 静态封面、MP4 动态封面或 PNG 序列帧 ZIP")


def assist_upload(cover: str | Path, short_name: str, *,
                  kind: str = "cover",
                  profile_dir: str | Path = ".hongbao/browser-profile",
                  screenshots_dir: str | Path = ".hongbao/screenshots") -> dict:
    cover = Path(cover)
    material_type = _check_material(cover, kind)
    if not short_name.strip():
        raise ValueError("必须填写获得使用授权的封面简称")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError('缺少 playwright：pip install -e ".[browser]"') from exc

    profile_dir, screenshots_dir = Path(profile_dir), Path(screenshots_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    result = {"material_type": material_type, "created": False,
              "short_name_filled": False, "uploaded": False,
              "submitted": False, "manual_upload_required": material_type != "static-cover"}
    print("将打开微信红包封面开放平台；请在自己的电脑上用本人微信扫码登录。")
    print("账号、密码、会话令牌不要交给本项目或第三方。")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir.resolve()), headless=False,
            viewport={"width": 1280, "height": 900})
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(PORTAL, wait_until="domcontentloaded", timeout=30000)
            input("请完成扫码、认证和必要验证；登录后按 Enter 继续：")
            try:
                result["created"] = _click_create(page)
            except Exception as exc:
                print(f"未能自动进入定制页：{exc}")
            if not result["created"]:
                print("未找到唯一的定制封面入口，请在浏览器手动打开封面定制页。")
                input("进入正确的封面上传表单后按 Enter 继续：")
            try:
                result["short_name_filled"] = _fill_short_name(page, short_name)
            except Exception as exc:
                print(f"简称自动填写失败：{exc}")
            if material_type == "static-cover":
                try:
                    result["uploaded"] = _upload_image(page, cover)
                except Exception as exc:
                    print(f"自动选择静态文件失败：{exc}")
            else:
                print("动态素材页面未经适配，为避免误传至 logo/封面故事栏目，")
                print(f"请在动态封面或挂件对应栏目手动选择文件：{cover.resolve()}")
                print("选择并核对平台预览后，按需自行提交。脚本不会声称已完成上传。")
            shot = screenshots_dir / "upload-page.png"
            page.screenshot(path=str(shot), full_page=False)
            result["screenshot"] = str(shot)
            if material_type == "static-cover" and not result["uploaded"]:
                print("未找到唯一的封面文件输入框，请手动上传封面。")
            print("程序没有点击提交审核、购买或发布。请检查页面上的所有预览和必填字段。")
            print("当前进展：", result)
            input("检查完毕后按 Enter 关闭本程序启动的浏览器：")
        finally:
            context.close()
    return result
