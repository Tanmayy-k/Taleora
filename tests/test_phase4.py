"""
Unit and integration tests for Phase 4:
Child safety filtering and originality checking (Requirement U5).
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from modules.prompt_engine import StoryBook, Scene, Character
from modules.safety_filter import ChildSafetyFilter, SafetyReport
from modules.originality_checker import OriginalityChecker, OriginalityReport


def run_phase4_tests():
    print("========================================")
    print("Testing Phase 4: Safety & Originality (U5)")
    print("========================================")

    # 1. Setup clean test story
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
        title="The Attic Library",
        narrative_text="Barnaby fluttered to the old oak shelf, admiring the gently glowing books filled with happy tales.",
        audio_script="Barnaby fluttered to the old oak shelf, admiring the gently glowing books filled with happy tales.",
        characters_present=["Barnaby"],
        image_prompt="Barnaby looking at books",
        music_mood="gentle wonder"
    )

    clean_story = StoryBook(
        title="Barnaby and the Golden Compass",
        logline="A wise owl finds an old compass that points toward kindness and courage.",
        genre="Fantasy",
        target_audience="Kids (Ages 6-8)",
        keywords=["Clockwork Owl", "Golden Compass", "Secret Attic Library"],
        character_bible=[char],
        scenes=[scene1],
        moral_or_takeaway="True friendship is the compass that guides us home."
    )

    # 2. Test Lexical Screening
    print("\n[Step 1] Testing Lexical Child Safety Screening...")
    clean_lex = ChildSafetyFilter.run_lexical_screen(clean_story.scenes[0].narrative_text)
    assert clean_lex["is_clean"], "Clean text incorrectly flagged!"
    print("  [SUCCESS] Clean text verified: is_clean=True, detected=", clean_lex["detected_keywords"])

    unsafe_lex = ChildSafetyFilter.run_lexical_screen("The evil monster had a bloody sword to kill the hero.")
    assert not unsafe_lex["is_clean"], "Unsafe text was not caught!"
    print("  [SUCCESS] Unsafe text correctly flagged:", unsafe_lex["detected_keywords"])

    # 3. Test Full Safety Evaluation
    print("\n[Step 2] Testing Storybook Safety Evaluation...")
    safety_filter = ChildSafetyFilter()
    safety_report: SafetyReport = safety_filter.evaluate_story_safety(clean_story)
    assert isinstance(safety_report, SafetyReport)
    assert safety_report.safety_score >= 80
    assert safety_report.is_safe
    print("  [SUCCESS] Safety Score:", f"{safety_report.safety_score}%")
    print("  Rating:", safety_report.safety_rating)
    print("  Explanation:", safety_report.explanation)

    # 4. Test Algorithmic Corpus Similarity
    print("\n[Step 3] Testing Originality Corpus Similarity...")
    checker = OriginalityChecker()
    closest_tale, sim = checker.compute_corpus_similarity(clean_story.scenes[0].narrative_text)
    print("  Closest Tale:", closest_tale, f"({sim}% lexical overlap)")
    assert sim < 25, "Original story showed abnormally high similarity to classic tale!"

    # Test Cinderella copycat detection
    cinderella_text = "The wicked stepmother made her clean while the stepsisters went to the royal palace ball in a pumpkin coach with a glass slipper."
    c_tale, c_sim = checker.compute_corpus_similarity(cinderella_text)
    print("  Copycat test: Closest Tale:", c_tale, f"({c_sim}% lexical overlap)")
    assert c_tale == "Cinderella", f"Expected Cinderella, got {c_tale}"
    assert c_sim >= 30, f"Expected higher similarity for Cinderella snippet, got {c_sim}%"
    print("  [SUCCESS] Successfully identified Cinderella archetype with high similarity!")

    # 5. Test Full Story Originality Evaluation
    print("\n[Step 4] Testing Full Story Originality Evaluation...")
    orig_report: OriginalityReport = checker.evaluate_story_originality(clean_story)
    assert isinstance(orig_report, OriginalityReport)
    assert orig_report.originality_score >= 70
    print("  [SUCCESS] Originality Score:", f"{orig_report.originality_score}%")
    print("  Status:", orig_report.status)
    print("  Closest Archetype:", orig_report.closest_archetype)
    print("  Novelty Highlights:", orig_report.novelty_highlights)

    print("\n========================================")
    print("[SUCCESS] ALL PHASE 4 TESTS COMPLETED SUCCESSFULLY!")
    print("========================================")


if __name__ == "__main__":
    run_phase4_tests()
