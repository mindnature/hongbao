from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from hongbao.video import check_frames, check_video, render_frames, render_motion, VIDEO_SIZE


def test_frames_detects_malformed_zip(tmp_path: Path):
    file = tmp_path / "empty.zip"
    with zipfile.ZipFile(file, "w") as z:
        z.writestr("not.png", "hello")
    result = check_frames(file)
    assert not result.valid
    assert "24–72" in " ".join(result.issues)


def test_frames_checks_images_and_numbering(tmp_path: Path):
    file = tmp_path / "bad.zip"
    with zipfile.ZipFile(file, "w") as z:
        for i in range(24):
            z.writestr(f"{i:05d}.png", b"not png data")
    assert not check_frames(file).valid


def test_duration_range(tmp_path: Path):
    with pytest.raises(ValueError):
        render_motion(tmp_path / "missing.png", tmp_path / "out.mp4", duration=5)
    with pytest.raises(ValueError):
        render_frames(tmp_path / "missing.png", tmp_path / "out.zip", duration=0.5)


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="需要 FFmpeg")
def test_still_to_mp4_and_poster(tmp_path: Path):
    from hongbao.video import make_poster
    image = tmp_path / "original.png"
    Image.new("RGB", (640, 800), (210, 44, 45)).save(image)
    movie = tmp_path / "dynamic.mp4"
    result = render_motion(image, movie, duration=1, effect="zoom")
    assert result.valid, result.issues
    assert (result.details["width"], result.details["height"]) == VIDEO_SIZE
    assert check_video(movie).valid
    poster = make_poster(movie, tmp_path / "poster.png")
    with Image.open(poster) as picture:
        assert picture.size == VIDEO_SIZE


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="需要 FFmpeg")
def test_cover_sequence_png_zip(tmp_path: Path):
    image = tmp_path / "original.png"
    Image.new("RGB", (240, 320), (198, 32, 29)).save(image)
    result = render_frames(image, tmp_path / "cover_frames.zip",
                           duration=1, kind="cover")
    assert result.valid, result.issues
    assert result.details["frames"] == 24
    assert check_frames(tmp_path / "cover_frames.zip").valid


def test_ornament_transparency_required(tmp_path: Path):
    file = tmp_path / "ornament.zip"
    image = tmp_path / "frame.png"
    Image.new("RGBA", (1053, 1746), (255, 0, 0, 255)).save(image)
    with zipfile.ZipFile(file, "w") as archive:
        for i in range(1, 25):
            archive.write(image, f"{i:05d}.png")
    result = check_frames(file, kind="ornament")
    assert not result.valid
    assert any("透明" in item for item in result.issues)
