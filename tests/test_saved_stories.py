import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from modules.prompt_engine import Scene, StoryBook
from modules.story_generator import StoryGenerator


def build_story(title: str) -> StoryBook:
    return StoryBook(
        title=title,
        logline="A little story about discovering a hidden library.",
        genre="Fantasy",
        target_audience="Kids (Ages 6-8)",
        keywords=["Clockwork Owl", "Floating Key", "Attic Library"],
        character_bible=[],
        scenes=[
            Scene(
                scene_number=1,
                title="The Discovery",
                narrative_text="A curious owl found a floating key.",
                audio_script="A curious owl found a floating key.",
                characters_present=[],
                image_prompt="A warm, colorful storybook scene.",
                music_mood="gentle and curious",
            )
        ],
        moral_or_takeaway="Curiosity can lead to wonderful discoveries.",
    )


def test_fresh_story_is_saved_listed_and_loadable(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "STORIES_DIR", tmp_path)
    story = build_story("Fresh Test Story")
    client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: SimpleNamespace(
                text=story.model_dump_json()
            )
        )
    )
    generator = StoryGenerator(api_key="test-key")
    monkeypatch.setattr(generator, "get_client", lambda: client)

    generated = generator.generate_story(
        keywords=story.keywords,
        genre=story.genre,
        audience=story.target_audience,
    )

    saved_files = StoryGenerator.list_saved_stories()
    assert len(saved_files) == 1
    assert isinstance(saved_files[0], Path)
    assert saved_files[0].suffix == ".json"
    assert StoryGenerator.load_story_from_disk(saved_files[0]) == generated


def test_saved_story_listing_is_timestamp_ordered_and_ignores_other_files(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(config, "STORIES_DIR", tmp_path)
    oldest = tmp_path / "20261105_164248_Old_Story.json"
    newest = tmp_path / "20261107_163231_New_Story.json"
    oldest.write_text(build_story("Old Story").model_dump_json(), encoding="utf-8")
    newest.write_text(build_story("New Story").model_dump_json(), encoding="utf-8")
    (tmp_path / "not-a-story.txt").write_text("ignore", encoding="utf-8")

    assert StoryGenerator.list_saved_stories() == [newest, oldest]
