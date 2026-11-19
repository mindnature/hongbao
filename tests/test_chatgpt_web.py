from pathlib import Path

import pytest
from PIL import Image

from hongbao.chatgpt_web import (
    build_chatgpt_prompt,
    import_chatgpt_image,
    prepare_chatgpt_job,
)
from hongbao.images import check_cover


def test_prompt_has_theme_safe_zone_and_reference_guidance():
    prompt = build_chatgpt_prompt("橘猫招财", "东方剪纸", has_reference=True)
    assert "橘猫招财" in prompt
    assert "东方剪纸" in prompt
    assert "参考照片" in prompt
    assert "3:4" in prompt
    assert "二维码" in prompt


def test_prompt_rejects_empty_theme():
    with pytest.raises(ValueError):
        build_chatgpt_prompt("   ")


def test_prepare_does_not_open_website_or_require_api(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Test explicitly disables browser access, clipboard and network.
    job = prepare_chatgpt_job("水墨仙鹤", tmp_path / "job",
                              open_browser=False, copy_clipboard=False)
    assert Path(job["prompt"]).is_file()
    assert job["browser_open_requested"] is False
    assert job["copied_to_clipboard"] is False
    assert (tmp_path / "job" / "job.json").exists()


def test_reference_is_checked_before_creating_job(tmp_path):
    with pytest.raises(FileNotFoundError):
        prepare_chatgpt_job("我的猫", tmp_path / "job",
                            reference=tmp_path / "not-found.jpg",
                            open_browser=False, copy_clipboard=False)
    assert not (tmp_path / "job").exists()


def test_web_import_prepares_cover_and_preview(tmp_path):
    image = tmp_path / "downloaded.png"
    Image.new("RGB", (1100, 1300), (180, 90, 30)).save(image)
    job_dir = tmp_path / "job"
    prepare_chatgpt_job("橘猫招财", job_dir, open_browser=False, copy_clipboard=False)
    result = import_chatgpt_image(image, job_dir)
    assert result["check"]["valid"]
    assert check_cover(result["cover"]).valid
    assert Path(result["original"]).is_file()
    assert Path(result["preview"]).is_file()


def test_web_import_refuses_overwrite_by_default(tmp_path):
    image = tmp_path / "downloaded.png"
    Image.new("RGB", (1100, 1300), (180, 90, 30)).save(image)
    directory = tmp_path / "job"
    import_chatgpt_image(image, directory)
    with pytest.raises(ValueError, match="已存在"):
        import_chatgpt_image(image, directory)
    overwrite = import_chatgpt_image(image, directory, overwrite=True)
    assert overwrite["check"]["valid"]


def test_web_prepare_refuses_existing_cover(tmp_path):
    directory = tmp_path / "job"
    directory.mkdir()
    (directory / "cover.jpg").write_bytes(b"test")
    with pytest.raises(ValueError, match="已有"):
        prepare_chatgpt_job("春节", directory, open_browser=False, copy_clipboard=False)
