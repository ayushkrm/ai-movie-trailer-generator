from pathlib import Path
import subprocess
import sys


PROJECT_DIR = Path("ai-movie-trailer-generator")
VENV_DIR = PROJECT_DIR / "venv"
PACKAGES = [
    "google-genai",
    "edge-tts",
    "requests",
    "moviepy",
    "python-dotenv",
    "imageio[ffmpeg]",
]


def run(command: list[str]) -> None:
    print(f"Running: {' '.join(command)}")
    subprocess.run(command, check=True)


def main() -> None:
    PROJECT_DIR.mkdir(exist_ok=True)

    if not VENV_DIR.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])

    print("\nSetup folder created successfully.")
    print("\nNext, run these commands in PowerShell:\n")
    print(r"cd ai-movie-trailer-generator")
    print(r".\venv\Scripts\Activate.ps1")
    print(f"python -m pip install {' '.join(PACKAGES)}")
    print("\nAdd your Gemini API key to a .env file like this:")
    print("GEMINI_API_KEY=your_api_key_here")


if __name__ == "__main__":
    main()

import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()

def generate_trailer_script(concept: str, genre: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

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

    r = requests.post(url, json=payload)
    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Strip code fences if present
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    return json.loads(raw.strip())

import requests