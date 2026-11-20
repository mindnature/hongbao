"""Sticker dual input modes and technical exports."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from hongbao.cli import make_parser, main
from hongbao.stickers import (
    build_sticker_prompt, check_sticker, export_sticker, import_sticker,
    prepare_sticker_job, prepare_sticker_pack, STICKER_SIZE
)


@pytest.fixture
def transparent_art(tmp_path: Path) -> Path:
    path = tmp_path / "art.png"
    img = Image.new("RGBA", (420, 320), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((75, 35, 340, 295), fill=(215, 40, 50, 255))
    img.save(path)
    return path


@pytest.fixture
def animated_art(tmp_path: Path) -> Path:
    path = tmp_path / "art.gif"
    frames = []
    for x in (60, 95, 120, 95):
        image = Image.new("RGBA", (180, 200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((x - 35, 60, x + 35, 130), fill=(245, 85, 65, 255))
        frames.append(image)
    frames[0].save(path, "GIF", save_all=True, append_images=frames[1:],
                   duration=120, loop=0, disposal=2)
    return path


def test_theme_prompt_emphasizes_single_character():
    prompt = build_sticker_prompt(theme="国风橘猫", emotion="无语", caption="收到")
    assert "国风橘猫" in prompt
    assert "无语" in prompt and "收到" in prompt
    assert "单图" in prompt
    assert "透明" in prompt


def test_reference_prompt_emphasizes_identity():
    prompt = build_sticker_prompt(reference="some-cat.jpg", emotion="哈哈", animated=True)
    assert "参考图片" in prompt and "可辨识" in prompt
    assert "多帧" in prompt and "GIF" in prompt
    assert "逐帧" in prompt


@pytest.mark.parametrize("theme,reference", [
    (None, None), ("一只猫", "cat.jpg"),
])
def test_input_mode_is_exclusive(theme, reference):
    with pytest.raises(ValueError):
        build_sticker_prompt(theme=theme, reference=reference)


def test_reference_mode_requires_existing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        prepare_sticker_job(tmp_path / "out", reference=tmp_path / "missing.jpg",
                            open_browser=False, copy_clipboard=False)
    assert not (tmp_path / "out").exists()


def test_sticker_job_theme_and_reference(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    ref = tmp_path / "cat.png"
    Image.new("RGB", (30, 30), "orange").save(ref)
    a = prepare_sticker_job(tmp_path / "theme", theme="熊猫", emotion="抱抱",
                            open_browser=False, copy_clipboard=False)
    b = prepare_sticker_job(tmp_path / "ref", reference=ref, emotion="无语",
                            animated=True, open_browser=False, copy_clipboard=False)
    assert a["mode"] == "theme" and b["mode"] == "reference"
    assert b["animated"] is True
    assert json.loads((tmp_path / "ref" / "job.json").read_text())["reference"] == str(ref)
    with pytest.raises(ValueError, match="已有"):
        prepare_sticker_job(tmp_path / "theme", theme="重复",
                            open_browser=False, copy_clipboard=False)


def test_pack_writes_separate_prompts(tmp_path: Path):
    result = prepare_sticker_pack(tmp_path / "pack", theme="一只小狐狸",
                                  emotions="哈哈,无语,抱抱,点赞",
                                  open_browser=False, copy_clipboard=False)
    assert result["count"] == 4
    manifest = json.loads((tmp_path / "pack" / "pack.json").read_text())
    assert len(manifest["items"]) == 4
    for i in range(1, 5):
        assert (tmp_path / "pack" / "prompts" / f"{i:02d}.txt").is_file()
    with pytest.raises(ValueError):
        prepare_sticker_pack(tmp_path / "duplicate", theme="狐狸",
                             emotions="开心,开心", open_browser=False, copy_clipboard=False)


def test_static_export_preserves_transparency(transparent_art: Path, tmp_path: Path):
    dest = tmp_path / "sticker.png"
    result = export_sticker(transparent_art, dest)
    assert result["valid"] and result["format"] == "PNG"
    assert result["width"] == 240 and result["height"] == 240
    assert result["transparent"]
    with Image.open(dest) as final:
        assert final.getpixel((0, 0))[3] == 0
    with pytest.raises(ValueError, match="已存在"):
        export_sticker(transparent_art, dest)


def test_nontransparent_source_warns(tmp_path: Path):
    art = tmp_path / "photo.jpg"
    Image.new("RGB", (600, 600), (250, 250, 250)).save(art)
    result = export_sticker(art, tmp_path / "out.png")
    assert result["valid"] and not result["transparent"]
    assert "透明" in "".join(result["warnings"])


def test_animated_gif_export( animated_art: Path, tmp_path: Path):
    dest = tmp_path / "sticker.gif"
    result = export_sticker(animated_art, dest)
    assert result["valid"], result["issues"]
    assert result["frames"] >= 2
    assert result["bytes"] <= 500_000
    with Image.open(dest) as final:
        assert final.size == STICKER_SIZE
        assert getattr(final, "n_frames", 1) >= 2


def test_import_keeps_original_and_updates_manifest(transparent_art: Path, tmp_path: Path):
    folder = tmp_path / "sticker-job"
    prepare_sticker_job(folder, theme="小猫", open_browser=False, copy_clipboard=False)
    result = import_sticker(transparent_art, folder)
    assert result["check"]["valid"]
    assert Path(result["original"]).is_file()
    assert Path(result["sticker"]).is_file()
    assert json.loads((folder / "job.json").read_text())["status"] == "exported_locally"


def test_cli_two_modes_and_check(tmp_path: Path, transparent_art: Path, capsys):
    parser = make_parser()
    assert parser.parse_args(["sticker", "--theme", "小猫"]).theme == "小猫"
    assert parser.parse_args(["sticker", "--reference", "cat.png"]).reference == "cat.png"
    with pytest.raises(SystemExit):
        parser.parse_args(["sticker", "--theme", "猫", "--reference", "cat.png"])
    assert main(["sticker", "--theme", "虎头帽宝宝", "--emotion", "开心",
                 "--output-dir", str(tmp_path / "job"),
                 "--no-open", "--no-copy"]) == 0
    assert main(["sticker-export", str(transparent_art),
                 str(tmp_path / "result.png")]) == 0
    assert main(["sticker-check", str(tmp_path / "result.png")]) == 0


def test_check_rejects_wrong_size(transparent_art: Path):
    report = check_sticker(transparent_art)
    assert not report["valid"]
