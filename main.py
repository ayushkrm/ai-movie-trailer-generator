import os
from script_generator import generate_trailer_script
from tts import generate_narration
from footage_fetcher import fetch_video_clip
from music_fetcher import fetch_background_music
from video_assembler import assemble_trailer

def main():
    print("=== AI Movie Trailer Generator ===\n")
    concept = input("Enter your movie concept: ").strip()
    genre = input("Genre (action/horror/thriller/romance/sci-fi/drama): ").strip()

    if not concept:
        concept = "A lone astronaut discovers a hidden signal beneath an alien ocean"
    if not genre:
        genre = "sci-fi"

    os.makedirs("clips", exist_ok=True)

    print("\n[1/4] Generating script with Gemini...")
    script = generate_trailer_script(concept, genre)
    print(f"  Title: {script['title']}")
    print(f"  Tagline: {script['tagline']}")

    print("\n[2/4] Generating narration with Edge TTS...")
    for i, scene in enumerate(script["scenes"]):
        print(f"  Scene {i+1}: {scene['narration'][:40]}...")
        generate_narration(scene["narration"], f"clips/audio_{i}.mp3")

    print("\n[3/4] Fetching stock footage from Pexels/Pixabay...")
    for i, scene in enumerate(script["scenes"]):
        print(f"  Fetching: '{scene['search_query']}'")
        success = fetch_video_clip(scene["search_query"], f"clips/scene_{i}.mp4")
        if not success:
            print(f"  ⚠️  Failed to fetch scene {i+1}, using fallback")

    print("\n[4/4] Assembling trailer with MoviePy...")
    assemble_trailer(
        scenes=script["scenes"],
        title=script["title"],
        tagline=script["tagline"],
        output_path="trailer.mp4"
    )

    print("\n🎬 Done! Open trailer.mp4 to watch your trailer.")

if __name__ == "__main__":
    main()
