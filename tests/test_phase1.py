import config
from modules.prompt_engine import (
    validate_keywords,
    build_system_prompt,
    build_story_prompt,
    Character,
    Scene,
    StoryBook,
)
from modules.character_manager import (
    guarantee_scene_character_consistency,
    format_character_bible_markdown,
)

def run_tests():
    print("Testing Keyword Validation...")
    valid, msg, kws = validate_keywords(["Clockwork Owl", "Floating Key", "Attic Library"])
    assert valid, msg
    print(f"  Passed! Cleaned keywords: {kws}")

    # Test invalid keyword count
    invalid, err, _ = validate_keywords(["One", "Two"])
    assert not invalid
    print(f"  Passed negative test: {err}")

    print("\nTesting Character Bible Formatting...")
    char = Character(
        name="Barnaby",
        role="Protagonist",
        visual_appearance="brown barn owl with bronze brass gears",
        signature_clothing="tiny green wool scarf with copper pin",
        distinct_accessories="monocle over right amber eye",
        personality_trait="curious and punctual"
    )
    md = format_character_bible_markdown([char])
    assert "Barnaby" in md
    print("  Passed Character Bible Markdown rendering.")

    print("\nTesting Character Consistency Prompt Injection...")
    injected = guarantee_scene_character_consistency(
        image_prompt="Barnaby sits on an antique mahogany bookshelf",
        characters_present=["Barnaby"],
        character_bible=[char],
        visual_style="whimsical storybook illustration"
    )
    assert "tiny green wool scarf" in injected
    assert "whimsical storybook illustration" in injected
    print(f"  Passed! Injected prompt sample:\n  '{injected}'")

    print("\nTesting StoryBook Schema Validation...")
    scene = Scene(
        scene_number=1,
        title="The Hidden Clock",
        narrative_text="Barnaby fluttered his bronze wings.",
        audio_script="Barnaby fluttered his bronze wings.",
        characters_present=["Barnaby"],
        image_prompt=injected,
        music_mood="whimsical clockwork ticking"
    )
    story = StoryBook(
        title="The Secret of the Clockwork Attic",
        logline="A brave little clockwork owl finds a key that unlocks forgotten stories.",
        genre="Fantasy",
        target_audience="Kids (Ages 6-8)",
        keywords=kws,
        character_bible=[char],
        scenes=[scene],
        moral_or_takeaway="Curiosity and perseverance unlock the greatest wonders."
    )
    assert len(story.scenes) == 1
    print("  Passed! StoryBook Pydantic model successfully validated.")

    print("\n[SUCCESS] ALL PHASE 1 TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
