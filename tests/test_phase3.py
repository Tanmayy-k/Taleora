"""
Unit and integration tests for Phase 3:
TTS narration, MusicGen background music, PDF export, and MP4 video generation (Requirement U4).
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from modules.prompt_engine import StoryBook, Scene, Character
from modules.audio_generator import AudioGenerator
from modules.music_generator import MusicGenerator
from modules.export_manager import ExportManager


def run_phase3_tests():
    print("========================================")
    print("Testing Phase 3: Audio, Music & Exports")
    print("========================================")

    # 1. Create a dummy test storybook
    char = Character(
        name="Barnaby",
        role="Protagonist",
        visual_appearance="brown barn owl with bronze brass gears",
        signature_clothing="tiny green wool scarf with copper pin",
        distinct_accessories="monocle over right amber eye",
        personality_trait="curious and punctual"
    )

    scene1 = Scene(
        scene_number=1,
        title="The Whispering Attic",
        narrative_text="Barnaby fluttered his bronze wings and listened to the gentle ticking of the clockwork attic.",
        audio_script="Barnaby fluttered his bronze wings and listened to the gentle ticking of the clockwork attic.",
        characters_present=["Barnaby"],
        image_prompt="Barnaby the owl in an attic",
        music_mood="mysterious ticking clockwork"
    )

    scene2 = Scene(
        scene_number=2,
        title="The Brass Key",
        narrative_text="A glowing brass key turned in the lock, opening a world of forgotten wonder and friendly stories.",
        audio_script="A glowing brass key turned in the lock, opening a world of forgotten wonder and friendly stories.",
        characters_present=["Barnaby"],
        image_prompt="Barnaby looking at a glowing key",
        music_mood="gentle wonder"
    )

    story = StoryBook(
        title="The Secret of the Clockwork Attic",
        logline="A brave little clockwork owl finds a key that unlocks forgotten stories.",
        genre="Fantasy",
        target_audience="Kids (Ages 6-8)",
        keywords=["Clockwork Owl", "Floating Key", "Secret Attic Library"],
        character_bible=[char],
        scenes=[scene1, scene2],
        moral_or_takeaway="Curiosity and perseverance unlock the greatest wonders."
    )

    # 2. Test Audio Generation (Edge TTS)
    print("\n[Step 1] Testing Edge TTS Narration Generation...")
    audio_gen = AudioGenerator()
    scene1_audio = audio_gen.generate_scene_narration(scene1, story.title, force_regenerate=True)
    assert scene1_audio.exists(), f"Audio file not found at {scene1_audio}"
    audio_size = scene1_audio.stat().st_size
    print("  [SUCCESS] Generated narration audio:", scene1_audio.name, f"({audio_size} bytes)")
    assert audio_size > 1000

    scene2_audio = audio_gen.generate_scene_narration(scene2, story.title, force_regenerate=True)
    assert scene2_audio.exists()

    # 3. Test Music Generation (Harmonic Ambient Synthesizer)
    print("\n[Step 2] Testing Background Music Generation...")
    music_gen = MusicGenerator()
    music_path, model_used = music_gen.generate_story_music(story, duration_seconds=10, force_regenerate=True)
    assert music_path.exists(), f"Music file not found at {music_path}"
    music_size = music_path.stat().st_size
    print("  [SUCCESS] Generated background music:", music_path.name, f"({music_size} bytes)")
    print("  Model Used:", model_used)
    assert music_size > 5000

    # 4. Test PDF Export (ReportLab)
    print("\n[Step 3] Testing Illustrated PDF Storybook Export...")
    pdf_path = ExportManager.generate_pdf_storybook(story, force_regenerate=True)
    assert pdf_path.exists(), f"PDF not found at {pdf_path}"
    pdf_size = pdf_path.stat().st_size
    print("  [SUCCESS] Generated PDF Storybook:", pdf_path.name, f"({pdf_size} bytes)")
    assert pdf_size > 2000

    # 5. Test MP4 Video Assembly (MoviePy + FFmpeg)
    print("\n[Step 4] Testing MP4 Video Generation (MoviePy + FFmpeg)...")
    video_path = ExportManager.generate_mp4_video(story, bg_music_path=music_path, force_regenerate=True)
    assert video_path.exists(), f"Video not found at {video_path}"
    video_size = video_path.stat().st_size
    print("  [SUCCESS] Generated MP4 Video:", video_path.name, f"({video_size} bytes)")
    assert video_size > 10000

    print("\n========================================")
    print("[SUCCESS] ALL PHASE 3 TESTS COMPLETED SUCCESSFULLY!")
    print("========================================")


if __name__ == "__main__":
    run_phase3_tests()
