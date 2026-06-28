from pathlib import Path
from typing import Any

try:
    from moviepy import AudioFileClip, ColorClip, VideoFileClip, concatenate_videoclips
except ImportError:
    from moviepy.editor import AudioFileClip, ColorClip, VideoFileClip, concatenate_videoclips


VIDEO_SIZE = (1280, 720)
FALLBACK_COLORS = [
    (15, 23, 42),
    (88, 28, 135),
    (127, 29, 29),
    (20, 83, 45),
    (30, 64, 175),
]


def _make_fallback_clip(index: int, duration: float):
    return ColorClip(
        size=VIDEO_SIZE,
        color=FALLBACK_COLORS[index % len(FALLBACK_COLORS)],
        duration=duration,
    )


def _make_video_clip(path: Path, index: int, duration: float):
    if not path.exists():
        return _make_fallback_clip(index, duration)

    try:
        clip = VideoFileClip(str(path)).without_audio()
        clip = clip.resized(height=VIDEO_SIZE[1])
        if clip.w < VIDEO_SIZE[0]:
            clip = clip.resized(width=VIDEO_SIZE[0])
        clip = clip.cropped(
            x_center=clip.w / 2,
            y_center=clip.h / 2,
            width=VIDEO_SIZE[0],
            height=VIDEO_SIZE[1],
        )
        return clip.subclipped(0, min(duration, clip.duration))
    except Exception as error:
        print(f"  Could not load video {path}: {error}")
        return _make_fallback_clip(index, duration)


def _attach_audio(clip, audio_path: Path):
    if not audio_path.exists():
        return clip

    try:
        audio = AudioFileClip(str(audio_path))
        return clip.with_audio(audio).with_duration(min(clip.duration, audio.duration))
    except Exception as error:
        print(f"  Could not load audio {audio_path}: {error}")
        return clip


def assemble_trailer(
    scenes: list[dict[str, Any]],
    title: str,
    tagline: str,
    output_path: str = "trailer.mp4",
) -> None:
    clips = []

    for index, scene in enumerate(scenes):
        duration = float(scene.get("duration", 10))
        video_path = Path("clips") / f"scene_{index}.mp4"
        audio_path = Path("clips") / f"audio_{index}.mp3"

        clip = _make_video_clip(video_path, index, duration)
        clip = _attach_audio(clip, audio_path)
        clips.append(clip)

    if not clips:
        clips.append(_make_fallback_clip(0, 5))

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
    )

    final.close()
    for clip in clips:
        clip.close()
