import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent
for env_path in (ROOT_DIR / ".env", ROOT_DIR / "ai-movie-trailer-generator" / ".env"):
    if env_path.exists():
        load_dotenv(env_path)


def _fallback_script(concept: str, genre: str) -> dict:
    return {
        "title": f"{concept[:45].strip() or 'Untitled'}",
        "tagline": "Every secret has a final scene.",
        "scenes": [
            {
                "scene_number": 1,
                "search_query": f"{genre} city night",
                "narration": "A quiet world is about to break.",
                "duration": 10,
            },
            {
                "scene_number": 2,
                "search_query": "person running street",
                "narration": "One discovery changes everything.",
                "duration": 11,
            },
            {
                "scene_number": 3,
                "search_query": "storm clouds dramatic",
                "narration": "The closer they get, the darker it becomes.",
                "duration": 11,
            },
            {
                "scene_number": 4,
                "search_query": "dark forest mystery",
                "narration": "Trust fades. Time runs out.",
                "duration": 11,
            },
            {
                "scene_number": 5,
                "search_query": "sunrise cinematic landscape",
                "narration": "This summer, the truth will find you.",
                "duration": 12,
            },
        ],
    }


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _normalize_script(data: dict, concept: str, genre: str) -> dict:
    fallback = _fallback_script(concept, genre)
    title = str(data.get("title") or fallback["title"]).strip()
    tagline = str(data.get("tagline") or fallback["tagline"]).strip()
    raw_scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []

    scenes = []
    for index, scene in enumerate(raw_scenes[:5]):
        if not isinstance(scene, dict):
            continue
        fallback_scene = fallback["scenes"][index]
        duration = scene.get("duration", fallback_scene["duration"])
        try:
            duration = int(duration)
        except (TypeError, ValueError):
            duration = fallback_scene["duration"]

        scenes.append(
            {
                "scene_number": index + 1,
                "search_query": str(scene.get("search_query") or fallback_scene["search_query"]).strip(),
                "narration": str(scene.get("narration") or fallback_scene["narration"]).strip(),
                "duration": max(3, min(duration, 20)),
            }
        )

    while len(scenes) < 5:
        scenes.append(fallback["scenes"][len(scenes)])

    return {"title": title, "tagline": tagline, "scenes": scenes}

def generate_trailer_script(concept: str, genre: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("  Warning: GEMINI_API_KEY missing. Using fallback script.")
        return _fallback_script(concept, genre)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    prompt = f"""
Create a 55-second movie trailer script for: "{concept}" | Genre: {genre}

Respond ONLY with valid JSON, no markdown, no extra text, no code fences:
{{
  "title": "Movie Title",
  "tagline": "Dramatic one-liner",
  "scenes": [
    {{
      "scene_number": 1,
      "search_query": "dark forest night fog",
      "narration": "Short dramatic voiceover text.",
      "duration": 10
    }}
  ]
}}

Rules:
- Exactly 5 scenes
- Total duration = 55 seconds
- search_query: 3-4 simple words for stock video search
- narration: short, punchy, cinematic (max 15 words per scene)
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8}
    }

    try:
        response = requests.post(url, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return _normalize_script(_extract_json(raw), concept, genre)
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as error:
        print(f"  Warning: Gemini script generation failed: {error}")
        print("  Using fallback script instead.")
        return _fallback_script(concept, genre)
