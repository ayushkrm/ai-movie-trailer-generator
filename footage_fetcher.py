import os
from pathlib import Path

import requests
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent
for env_path in (ROOT_DIR / ".env", ROOT_DIR / "ai-movie-trailer-generator" / ".env"):
    if env_path.exists():
        load_dotenv(env_path)


def _download(url: str, output_path: str) -> bool:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(url, stream=True, timeout=45) as response:
            response.raise_for_status()
            with destination.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)
        return True
    except requests.RequestException as error:
        print(f"  Video download failed: {error}")
        if destination.exists():
            destination.unlink()
        return False


def _pexels_url(query: str) -> str | None:
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        return None

    response = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": api_key},
        params={"query": query, "per_page": 1, "orientation": "landscape"},
        timeout=25,
    )
    response.raise_for_status()
    videos = response.json().get("videos", [])
    if not videos:
        return None

    files = [
        item
        for item in videos[0].get("video_files", [])
        if item.get("file_type") == "video/mp4" and item.get("link")
    ]
    if not files:
        return None

    best = max(files, key=lambda item: item.get("width", 0))
    return best["link"]


def _pixabay_url(query: str) -> str | None:
    api_key = os.getenv("PIXABAY_API_KEY")
    if not api_key:
        return None

    response = requests.get(
        "https://pixabay.com/api/videos/",
        params={"key": api_key, "q": query, "per_page": 3, "video_type": "film"},
        timeout=25,
    )
    response.raise_for_status()
    hits = response.json().get("hits", [])
    if not hits:
        return None

    videos = hits[0].get("videos", {})
    for quality in ("large", "medium", "small", "tiny"):
        video = videos.get(quality)
        if video and video.get("url"):
            return video["url"]
    return None


def fetch_video_clip(query: str, output_path: str) -> bool:
    if Path(output_path).exists():
        return True

    for provider in (_pexels_url, _pixabay_url):
        try:
            url = provider(query)
        except requests.RequestException as error:
            print(f"  Stock search failed for '{query}': {error}")
            continue

        if url and _download(url, output_path):
            return True

    return False
