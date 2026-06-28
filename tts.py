import edge_tts
import asyncio
from pathlib import Path


async def _generate(
    text: str,
    output_path: str,
    voice: str,
    rate: str,
    volume: str,
) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(
        text=text.strip(),
        voice=voice,
        rate=rate,
        volume=volume,
    )
    await communicate.save(output_path)


def generate_narration(
    text: str,
    output_path: str,
    voice: str = "en-US-GuyNeural",
    rate: str = "-5%",
    volume: str = "+0%",
) -> None:
    if not text or not text.strip():
        raise ValueError("Narration text cannot be empty.")

    asyncio.run(_generate(text, output_path, voice, rate, volume))
