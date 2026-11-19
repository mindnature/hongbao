"""Offline tests for still-image procedural animations."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from hongbao.animate import PRESETS, render_animated_cover
from hongbao.video import check_video

FFMPEG_AVAILABLE = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


@pytest.fixture
def artwork(tmp_path: Path) -> Path:
    image = Image.new("RGB", (600, 800), (185, 36, 46))
    d = ImageDraw.Draw(image)
    d.ellipse((120, 135, 480, 535), fill=(243, 193, 97))
    d.rectangle((220, 580, 390, 750), fill=(22, 98, 81))
    path = tmp_path / "art.png"
    image.save(path)
    return path


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="需要 FFmpeg/ffprobe")
@pytest.mark.parametrize("preset", PRESETS)
def test_all_presets_render_valid_mp4(artwork: Path, tmp_path: Path, preset: str):
    dest = tmp_path / f"{preset}.mp4"
    result = render_animated_cover(artwork, dest, preset=preset, duration=1, seed=42)
    assert result.valid, result.issues
    assert result.details["preset"] == preset
    assert result.details["generated_from_still"]
    assert result.details["fps"] == 24
    assert result.details["width"] == 960 and result.details["height"] == 1280
    assert result.details["duration"] == pytest.approx(1.0, abs=0.06)
    assert check_video(dest).valid
    assert dest.stat().st_size < 20_000_000


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="需要 FFmpeg/ffprobe")
def test_poster_and_no_overwrite(artwork: Path, tmp_path: Path):
    dest = tmp_path / "result.mp4"
    poster = tmp_path / "poster.png"
    render_animated_cover(artwork, dest, duration=1, poster=poster)
    with Image.open(poster) as frame:
        assert frame.size == (960, 1280) and frame.format == "PNG"
    with pytest.raises(ValueError, match="已存在"):
        render_animated_cover(artwork, dest, duration=1)


@pytest.mark.parametrize("kwargs", [
    {"duration": .5}, {"duration": 4}, {"intensity": -0.01},
    {"intensity": 1.01}, {"fps": 60}, {"focus_x": -0.1},
    {"focus_y": 2}, {"preset": "unknown"},
])
def test_invalid_settings_fail_fast(artwork: Path, tmp_path: Path, kwargs):
    with pytest.raises(ValueError):
        render_animated_cover(artwork, tmp_path / "result.mp4", **kwargs)
    assert not (tmp_path / "result.mp4").exists()


def test_source_protection_and_format_checks(artwork: Path, tmp_path: Path):
    with pytest.raises(ValueError):
        render_animated_cover(artwork, artwork)
    with pytest.raises(FileNotFoundError):
        render_animated_cover(tmp_path / "missing.png", tmp_path / "out.mp4")
