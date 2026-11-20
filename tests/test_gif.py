"""GIF input validation and local end-to-end MP4 conversion."""
from __future__ import annotations
import shutil
from pathlib import Path
import pytest
from PIL import Image
from hongbao.chatgpt_web import build_chatgpt_prompt, prepare_chatgpt_job
from hongbao.cli import make_parser
from hongbao.gif_workflow import check_gif, gif_to_mp4
from hongbao.video import check_video

@pytest.fixture
def moving_gif(tmp_path: Path) -> Path:
    frames = [Image.new("RGB", (180, 240), color)
              for color in [(180, 40, 40), (40, 180, 40), (40, 40, 180), (210, 170, 25)]]
    path = tmp_path / "animation.gif"
    frames[0].save(path, format="GIF", save_all=True, append_images=frames[1:],
                   duration=[200, 150, 150, 200], loop=0)
    return path

def test_gif_prompt_is_distinct_and_animation_focused():
    prompt = build_chatgpt_prompt("牛郎织女", "东方剪纸", mode="gif", has_reference=True)
    assert "GIF" in prompt and "多帧" in prompt
    assert "牛郎织女" in prompt and "参考照片" in prompt
    assert "首尾" in prompt and "二维码" in prompt

def test_chatgpt_gif_no_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    job = prepare_chatgpt_job("花神", tmp_path / "job", mode="gif",
                              open_browser=False, copy_clipboard=False)
    assert "gif2mp4" in job["next"]
    assert Path(job["prompt"]).exists()
    assert not (tmp_path / "job" / "dynamic.mp4").exists()

def test_new_cli_commands():
    p = make_parser()
    assert p.parse_args(["chatgpt", "--mode", "gif", "--theme", "锦鲤"]).mode == "gif"
    assert p.parse_args(["gif2mp4", "a.gif", "b.mp4"]).duration == 3.0
    assert p.parse_args(["check-gif", "a.gif"]).command == "check-gif"

def test_frame_count_and_playback_duration(moving_gif):
    result = check_gif(moving_gif)
    assert result.valid, result.issues
    assert result.details["frames"] == 4
    assert result.details["duration_seconds"] == pytest.approx(.7, abs=.01)

def test_single_frame_gif_rejected(tmp_path):
    source = tmp_path / "single.gif"
    Image.new("RGB", (50, 60), "red").save(source, format="GIF")
    assert not check_gif(source).valid
    with pytest.raises(ValueError, match="只有一帧"):
        gif_to_mp4(source, tmp_path / "output.mp4")
    assert not (tmp_path / "output.mp4").exists()

def test_corrupt_gif_rejected(tmp_path):
    fake = tmp_path / "invalid.gif"
    fake.write_bytes(b"not an image")
    assert not check_gif(fake).valid

@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg/ffprobe absent")
def test_animated_gif_to_mp4_and_loop(moving_gif, tmp_path):
    dest = tmp_path / "dynamic.mp4"
    result = gif_to_mp4(moving_gif, dest, duration=3)
    assert result.valid, result.issues
    assert result.details["gif_frames"] == 4
    assert result.details["duration"] == pytest.approx(3.0, abs=.05)
    assert check_video(dest).valid
    assert dest.stat().st_size < 20_000_000
    assert moving_gif.exists()
    with pytest.raises(ValueError, match="已存在"):
        gif_to_mp4(moving_gif, dest, duration=3)


def test_dynamic_is_gif_first_and_no_browser(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from hongbao.cli import main
    target = tmp_path / "new-gif-job"
    assert main(["dynamic", "--theme", "金色凤凰", "--output-dir", str(target),
                 "--no-open", "--no-copy"]) == 0
    import json
    job = json.loads((target / "job.json").read_text(encoding="utf-8"))
    assert job["mode"] == "gif"
    assert "GIF" in (target / "prompt.txt").read_text(encoding="utf-8")


def test_import_gif_rejects_invalid_before_creating_output(tmp_path):
    from hongbao.gif_workflow import import_chatgpt_gif
    bad = tmp_path / "bad.gif"
    Image.new("RGB", (30, 40), "red").save(bad, "GIF")
    out = tmp_path / "new-folder"
    with pytest.raises(ValueError, match="只有一帧"):
        import_chatgpt_gif(bad, out)
    assert not out.exists()


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="FFmpeg/ffprobe absent")
def test_import_gif_one_step(moving_gif, tmp_path):
    import json
    from hongbao.gif_workflow import import_chatgpt_gif
    from hongbao.chatgpt_web import prepare_chatgpt_job
    folder = tmp_path / "gift"
    prepare_chatgpt_job("国风锦鲤", folder, mode="gif", open_browser=False,
                        copy_clipboard=False)
    result = import_chatgpt_gif(moving_gif, folder, duration=1)
    assert result["video_check"]["valid"]
    assert result["gif_check"]["valid"]
    assert Path(result["mp4"]).is_file()
    assert Path(result["poster"]).is_file()
    assert Path(result["gif"]).is_file()
    assert moving_gif.exists()
    assert check_video(result["mp4"]).valid
    with Image.open(result["poster"]) as im:
        assert im.format == "PNG" and im.size == (960, 1280)
    manifest = json.loads((folder / "job.json").read_text(encoding="utf-8"))
    assert manifest["mode"] == "gif" and manifest["status"] == "locally_converted"
    with pytest.raises(ValueError, match="已存在"):
        import_chatgpt_gif(moving_gif, folder, duration=1)
