from pathlib import Path

import pytest
from PIL import Image

from hongbao.generation import build_prompt
from hongbao.images import TARGET, check_cover, export_cover, make_preview


def test_export_check_and_preview(tmp_path: Path):
    source = tmp_path / "source.png"
    dest = tmp_path / "cover.jpg"
    preview = tmp_path / "preview.png"
    Image.new("RGB", (1200, 1200), (196, 35, 42)).save(source)

    report = export_cover(source, dest)
    assert report.valid
    assert (report.width, report.height) == TARGET
    assert report.size_bytes <= 500_000
    assert check_cover(dest).valid
    assert make_preview(dest, preview).is_file()
    with Image.open(preview) as img:
        assert img.size == TARGET and img.format == "PNG"


def test_invalid_file(tmp_path: Path):
    path = tmp_path / "bad.png"
    Image.new("RGB", (100, 200)).save(path)
    report = check_cover(path)
    assert not report.valid
    assert len(report.issues) >= 2


def test_export_never_overwrites_input(tmp_path: Path):
    path = tmp_path / "a.jpg"
    Image.new("RGB", (20, 20)).save(path)
    with pytest.raises(ValueError):
        export_cover(path, path)


def test_focus_bounds(tmp_path: Path):
    with pytest.raises(ValueError):
        export_cover(tmp_path / "nothing", tmp_path / "out.jpg", focus_x=1.5)


def test_prompt_content():
    prompt = build_prompt("橘猫", "绒布风")
    assert "橘猫" in prompt
    assert "绒布风" in prompt
    assert "二维码" in prompt
