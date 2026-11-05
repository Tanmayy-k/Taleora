"""
End-to-End Master Pipeline Verification for Taleora.
Tests requirements U1 through U5 in a single unified integration suite.
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from modules.prompt_engine import validate_keywords, build_system_prompt, build_story_prompt, StoryBook, Scene, Character
from modules.character_manager import guarantee_scene_character_consistency, format_character_bible_markdown
from modules.image_generator import ImageGenerator
from modules.blip_verifier import BLIPVerifier
from modules.audio_generator import AudioGenerator
from modules.music_generator import MusicGenerator
from modules.export_manager import ExportManager
from modules.safety_filter import ChildSafetyFilter
from modules.originality_checker import OriginalityChecker


def run_e2e_test():
    print("=================================================================")
    print("TALEORA: Complete End-to-End Pipeline Verification (U1 - U5)")
    print("=================================================================")

    # -------------------------------------------------------------
    # U1: PROMPT ENGINEERING & KEYWORD VALIDATION
    # -------------------------------------------------------------
    print("\n[U1] Testing Keyword Validation & Structured Prompt Engineering...")
    keywords = ["Golden Acorn", "Clockwork Owl", "Secret Attic Library"]
    valid, msg, cleaned_kws = validate_keywords(keywords)
    assert valid, f"Keyword validation failed: {msg}"
    print(f"  [PASS] 3 Keywords validated: {cleaned_kws}")

    sys_prompt = build_system_prompt("Fantasy", "Kids (Ages 6-8)")
    assert "Fantasy" in sys_prompt and "Kids (Ages 6-8)" in sys_prompt
    print("  [PASS] Dynamic system prompt constructed adhering to age & genre constraints.")

    # -------------------------------------------------------------
    # U2: STORY GENERATION & CHARACTER BIBLE CONSISTENCY
    # -------------------------------------------------------------
    print("\n[U2] Testing Story Schema & Character Consistency Bible...")
    char = Character(
        name="Barnaby",
        role="Protagonist",
        visual_appearance="small bronze owl with polished gears and golden feathers",
        signature_clothing="forest-green wool scarf with brass acorn pin",
        distinct_accessories="round monocle over right eye",
        personality_trait="curious and brave"
    )
    bible_md = format_character_bible_markdown([char])
    assert "Barnaby" in bible_md
    print("  [PASS] Character Bible formatted.")

    raw_scene_prompt = "Barnaby reading an antique book in a secret attic library"
    injected_prompt = guarantee_scene_character_consistency(
        image_prompt=raw_scene_prompt,
        characters_present=["Barnaby"],
        character_bible=[char],
        visual_style=config.GENRES["Fantasy"]["visual_style"]
    )
    assert "forest-green wool scarf" in injected_prompt
    print("  [PASS] Character consistency visual signature successfully injected into prompt.")

    scene = Scene(
        scene_number=1,
        title="The Attic Awakening",
        narrative_text="Barnaby fluttered his bronze feathers as sunlight bathed the secret attic library in golden wonder.",
        audio_script="Barnaby fluttered his bronze feathers as sunlight bathed the secret attic library in golden wonder.",
        characters_present=["Barnaby"],
        image_prompt=injected_prompt,
        music_mood="whimsical ticking clockwork"
    )

    story = StoryBook(
        title="E2E Pipeline Test Story",
        logline="A little clockwork owl finds the golden acorn in a forgotten attic.",
        genre="Fantasy",
        target_audience="Kids (Ages 6-8)",
        keywords=cleaned_kws,
        character_bible=[char],
        scenes=[scene],
        moral_or_takeaway="Curiosity guided by kindness brings joy to all."
    )
    assert len(story.scenes) == 1
    print("  [PASS] StoryBook schema validated.")

    # -------------------------------------------------------------
    # U3: IMAGE GENERATION & BLIP VERIFICATION
    # -------------------------------------------------------------
    print("\n[U3] Testing Scene Image Generation & Salesforce BLIP Verification...")
    img_gen = ImageGenerator()
    img_path = img_gen.generate_scene_image(scene, story.title, force_regenerate=True, seed=999)
    assert img_path.exists()
    print(f"  [PASS] Scene illustration generated: {img_path.name} ({img_path.stat().st_size} bytes)")

    verifier = BLIPVerifier()
    v_report = verifier.verify_scene_image(scene.scene_number, img_path, scene.narrative_text, scene.image_prompt, scene.characters_present)
    assert "status" in v_report and "similarity_score" in v_report
    print(f"  [PASS] BLIP inspection complete: Status={v_report['status']}, Score={v_report['similarity_score']}%, Engine={v_report['model_used']}")

    # -------------------------------------------------------------
    # U4: TTS NARRATION, MUSICGEN, PDF & MP4 EXPORT
    # -------------------------------------------------------------
    print("\n[U4] Testing Narration (Edge TTS), MusicGen, PDF & MP4 Exports...")
    audio_gen = AudioGenerator()
    audio_path = audio_gen.generate_scene_narration(scene, story.title, force_regenerate=True)
    assert audio_path.exists()
    print(f"  [PASS] Edge TTS Narration generated: {audio_path.name} ({audio_path.stat().st_size} bytes)")

    music_gen = MusicGenerator()
    music_path, music_model = music_gen.generate_story_music(story, duration_seconds=10, force_regenerate=True)
    assert music_path.exists()
    print(f"  [PASS] Background music generated: {music_path.name} ({music_model})")

    pdf_path = ExportManager.generate_pdf_storybook(story, force_regenerate=True)
    assert pdf_path.exists() and pdf_path.stat().st_size > 2000
    print(f"  [PASS] Illustrated PDF Storybook compiled: {pdf_path.name} ({pdf_path.stat().st_size} bytes)")

    video_path = ExportManager.generate_mp4_video(story, bg_music_path=music_path, force_regenerate=True)
    assert video_path.exists() and video_path.stat().st_size > 5000
    print(f"  [PASS] Complete MP4 Video assembled: {video_path.name} ({video_path.stat().st_size} bytes)")

    # -------------------------------------------------------------
    # U5: CHILD SAFETY & ORIGINALITY AUDITS
    # -------------------------------------------------------------
    print("\n[U5] Testing Child Safety Guardrail & Originality Checking...")
    safety_filter = ChildSafetyFilter()
    s_rep = safety_filter.evaluate_story_safety(story)
    assert s_rep.is_safe and s_rep.safety_score >= 80
    print(f"  [PASS] Child Safety Audit: Score={s_rep.safety_score}%, Rating='{s_rep.safety_rating}'")

    orig_checker = OriginalityChecker()
    o_rep = orig_checker.evaluate_story_originality(story)
    assert o_rep.originality_score >= 70
    print(f"  [PASS] Originality Audit: Score={o_rep.originality_score}%, Status='{o_rep.status}', Closest='{o_rep.closest_archetype}' ({o_rep.similarity_percentage}% match)")

    print("\n=================================================================")
    print("[SUCCESS] ALL MANDATORY REQUIREMENTS (U1 TO U5) VERIFIED 100%!")
    print("=================================================================")


if __name__ == "__main__":
    run_e2e_test()
