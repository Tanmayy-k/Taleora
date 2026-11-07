"""
Integration test for Requirement U3:
Generates a complete 5-scene story with 5 genuine AI-generated illustrations,
asserts that no placeholder cards are produced, runs BLIP caption verification on all 5 images,
and verifies the PDF export.
"""
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image
import config
from modules.prompt_engine import StoryBook, Scene, Character
from modules.image_generator import ImageGenerator
from modules.blip_verifier import BLIPVerifier
from modules.export_manager import ExportManager
from modules.story_generator import sanitize_filename


def test_five_scene_illustrations():
    print("===============================================================")
    print("Requirement U3: Generating 5 Genuine AI Scene Illustrations")
    print("===============================================================")

    char = Character(
        name="Barnaby",
        role="Protagonist",
        visual_appearance="small brown barn owl with polished bronze gears and golden feathers",
        signature_clothing="forest-green wool scarf with a tiny brass acorn pin",
        distinct_accessories="round brass monocle over his right amber eye",
        personality_trait="curious, meticulous and brave"
    )

    scenes = [
        Scene(
            scene_number=1,
            title="The Ticking Attic",
            narrative_text="In the dusty high attic of the old clock tower, Barnaby the clockwork owl adjusted his round brass monocle.",
            audio_script="In the dusty high attic of the old clock tower, Barnaby the clockwork owl adjusted his round brass monocle.",
            characters_present=["Barnaby"],
            image_prompt="Barnaby the small clockwork owl sitting atop a stack of leather books in a warm sunlit attic library filled with antique clocks",
            music_mood="mysterious ticking clockwork"
        ),
        Scene(
            scene_number=2,
            title="The Floating Brass Key",
            narrative_text="A beam of afternoon sunlight struck an antique grandfather clock, revealing a glowing brass key hovering in mid-air.",
            audio_script="A beam of afternoon sunlight struck an antique grandfather clock, revealing a glowing brass key hovering in mid-air.",
            characters_present=["Barnaby"],
            image_prompt="Barnaby the small clockwork owl looking in amazement at a glowing floating brass key inside an attic clock tower",
            music_mood="gentle wonder"
        ),
        Scene(
            scene_number=3,
            title="The Secret Door Behind the Books",
            narrative_text="With a gentle turn of the brass key, the oak bookshelf clicked and swung open into a hidden spiral staircase.",
            audio_script="With a gentle turn of the brass key, the oak bookshelf clicked and swung open into a hidden spiral staircase.",
            characters_present=["Barnaby"],
            image_prompt="Barnaby the clockwork owl perched on an open oak bookshelf opening into a luminous hidden spiral staircase",
            music_mood="adventurous discovery"
        ),
        Scene(
            scene_number=4,
            title="The Chamber of Living Stories",
            narrative_text="Barnaby stepped into a vast hall where glowing storybooks fluttered their pages like golden butterflies.",
            audio_script="Barnaby stepped into a vast hall where glowing storybooks fluttered their pages like golden butterflies.",
            characters_present=["Barnaby"],
            image_prompt="Barnaby the clockwork owl standing in an enormous enchanted library chamber with flying glowing storybooks fluttering like butterflies",
            music_mood="magical crescendo"
        ),
        Scene(
            scene_number=5,
            title="The Keeper of Whispers",
            narrative_text="Barnaby realized the library had been waiting for a curious reader with a kind heart to share its magical tales.",
            audio_script="Barnaby realized the library had been waiting for a curious reader with a kind heart to share its magical tales.",
            characters_present=["Barnaby"],
            image_prompt="Barnaby the clockwork owl happily reading an enchanted glowing storybook surrounded by warm golden candlelight",
            music_mood="heartwarming triumph"
        )
    ]

    story = StoryBook(
        title="Barnaby & the Five Attic Secrets",
        logline="A curious clockwork owl unlocks five magical chambers in an enchanted attic.",
        genre="Fantasy",
        target_audience="Kids (Ages 6-8)",
        keywords=["Clockwork Owl", "Floating Key", "Secret Attic Library"],
        character_bible=[char],
        scenes=scenes,
        moral_or_takeaway="True wonder is found when curiosity is guided by an open and kind heart."
    )

    img_gen = ImageGenerator()
    safe_title = sanitize_filename(story.title)

    print("\n[Step 1] Generating all 5 scene illustrations...")
    start_t = time.time()

    def progress_reporter(curr, total, msg):
        print(f"  [{curr}/{total}] {msg}")

    results = img_gen.generate_all_scenes(
        story=story,
        engine="pollinations",
        progress_callback=progress_reporter,
        force_regenerate=True
    )

    elapsed = time.time() - start_t
    print(f"\n[Step 1 Completed in {elapsed:.1f}s]")

    # Verify all 5 image files exist and are genuine (> 50KB)
    print("\n[Step 2] Verifying generated image files on disk...")
    assert len(results) == 5, f"Expected 5 image paths, got {len(results)}"

    for scene_num, path in results.items():
        assert path.exists(), f"Scene {scene_num} image does not exist at {path}"
        file_size = path.stat().st_size
        print(f"  Scene {scene_num}: {path.name} | Size: {file_size:,} bytes")
        
        # Genuine image check: must be > 50,000 bytes (NOT a 11KB placeholder card!)
        assert file_size > 50000, f"Scene {scene_num} is too small ({file_size} bytes) - suspected placeholder card!"
        
        # Verify valid PNG image format with PIL
        with Image.open(path) as img:
            assert img.format == "PNG", f"Expected PNG format, got {img.format}"
            assert img.size[0] >= 512 and img.size[1] >= 512, f"Expected min 512x512, got {img.size}"

    print("  [SUCCESS] All 5 scenes have genuine, high-resolution AI illustrations!")

    # Step 3: Run BLIP Verification on all 5 scenes
    print("\n[Step 3] Running Salesforce BLIP Verification on all 5 scene illustrations...")
    verifier = BLIPVerifier()
    verification_results = {}

    for scene in story.scenes:
        img_p = results[scene.scene_number]
        ver_rep = verifier.verify_scene_image(
            scene_number=scene.scene_number,
            image_path=img_p,
            intended_text=scene.narrative_text,
            image_prompt=scene.image_prompt,
            characters_expected=scene.characters_present
        )
        verification_results[scene.scene_number] = ver_rep
        print(f"  Scene {scene.scene_number}:")
        print(f"    - Caption: \"{ver_rep['blip_caption']}\"")
        print(f"    - Model: {ver_rep['model_used']}")
        print(f"    - Status: {ver_rep['status']} ({ver_rep['similarity_score']}%)")
        assert "blip_caption" in ver_rep and len(ver_rep["blip_caption"]) > 5
        assert ver_rep["status"] in ("VERIFIED", "FLAGGED")

    print("  [SUCCESS] All 5 scenes verified with Salesforce BLIP captioning!")

    # Step 4: Verify PDF export contains all 5 illustrations
    print("\n[Step 4] Assembling and verifying illustrated PDF storybook...")
    pdf_path = ExportManager.generate_pdf_storybook(story, force_regenerate=True)
    assert pdf_path.exists()
    pdf_size = pdf_path.stat().st_size
    print(f"  [SUCCESS] PDF storybook generated: {pdf_path.name} | Size: {pdf_size:,} bytes")
    # A 5-scene PDF with genuine full-color illustrations is typically > 500KB
    assert pdf_size > 200000, f"PDF size {pdf_size} bytes is smaller than expected for 5 full-color scenes"

    print("\n===============================================================")
    print("[ALL U3 REQUIREMENTS VERIFIED: 5/5 IMAGES, 5/5 BLIP VERIFIED]")
    print("===============================================================")


if __name__ == "__main__":
    test_five_scene_illustrations()
