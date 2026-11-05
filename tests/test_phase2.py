"""
Unit and integration tests for Phase 2:
Image generation (U3) and BLIP verification (U3).
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image

import config
from modules.prompt_engine import Scene
from modules.image_generator import ImageGenerator
from modules.blip_verifier import BLIPVerifier


def run_phase2_tests():
    print("========================================")
    print("Testing Phase 2: Image Gen & BLIP Verifier")
    print("========================================")

    # 1. Test Scene Setup
    test_scene = Scene(
        scene_number=1,
        title="Barnaby Finds the Brass Key",
        narrative_text="In the dusty attic, Barnaby the owl spotted a glowing brass key nestled inside an antique oak clock.",
        audio_script="In the dusty attic, Barnaby the owl spotted a glowing brass key nestled inside an antique oak clock.",
        characters_present=["Barnaby"],
        image_prompt=(
            "whimsical storybook illustration, cozy attic library with antique books and oak clocks, "
            "Barnaby (a brown owl with bronze gears, wearing a tiny green scarf), looking at a floating glowing brass key, "
            "warm golden lighting, masterwork children's book art"
        ),
        music_mood="mysterious ticking"
    )

    print("\n[Step 1] Testing Image Generation (Pollinations engine)...")
    img_gen = ImageGenerator()
    test_title = "Test Barnaby Story"
    saved_img = img_gen.generate_scene_image(
        scene=test_scene,
        story_title=test_title,
        engine="pollinations",
        force_regenerate=True,
        seed=12345
    )

    assert saved_img.exists(), f"Image was not saved at {saved_img}"
    print(f"  [SUCCESS] Image generated and saved to: {saved_img}")

    # Validate image format with Pillow
    with Image.open(saved_img) as pil_img:
        width, height = pil_img.size
        img_format = pil_img.format
        print(f"  [SUCCESS] Valid PIL image: format={img_format}, dimensions={width}x{height}")
        assert width > 0 and height > 0
        assert img_format == "PNG"

    print("\n[Step 2] Testing BLIP Verifier Token Matching & Scoring Logic...")
    verifier = BLIPVerifier()

    # Test token extraction
    tokens = verifier._extract_meaningful_tokens("A little brown owl sitting by an antique oak clock")
    assert "owl" in tokens
    assert "clock" in tokens
    print(f"  [SUCCESS] Meaningful tokens extracted: {tokens}")

    print("\n[Step 3] Testing Scene Image Verification...")
    verification = verifier.verify_scene_image(
        scene_number=test_scene.scene_number,
        image_path=saved_img,
        intended_text=test_scene.narrative_text,
        image_prompt=test_scene.image_prompt,
        characters_expected=test_scene.characters_present
    )

    print("  BLIP Caption:", verification['blip_caption'])
    print("  Model Used:", verification['model_used'])
    print("  Similarity Score:", str(verification['similarity_score']) + "%")
    print("  Status:", verification['status'])
    print("  Matched Tokens:", verification['matched_tokens'])
    print("  Matched Characters:", verification['matched_characters'])
    print("  Recommendation:", verification['recommendation'])

    assert "similarity_score" in verification
    assert verification["status"] in ["VERIFIED", "FLAGGED"]
    print("  [SUCCESS] Verification structure and evaluation passed!")

    print("\n========================================")
    print("[SUCCESS] ALL PHASE 2 TESTS COMPLETED SUCCESSFULLY!")
    print("========================================")


if __name__ == "__main__":
    run_phase2_tests()
