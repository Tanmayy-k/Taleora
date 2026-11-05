"""
Story Generator Module for Taleora (Satisfies Requirement U2).
Uses Google Gemini API to generate structured stories with character bibles,
scene breakdowns, narration scripts, and image prompts.
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from google import genai
from google.genai import types

import config
from modules.prompt_engine import (
    StoryBook,
    validate_keywords,
    build_system_prompt,
    build_story_prompt,
)
from modules.character_manager import guarantee_scene_character_consistency


def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be safely used as a filename."""
    clean = re.sub(r'[\\/*?:"<>| ]', "_", name)
    return clean[:50].strip("_")


class StoryGenerator:
    """Orchestrates story generation using Google Gemini with structured output."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model_name = model_name or config.DEFAULT_GEMINI_MODEL
        self._client: Optional[genai.Client] = None

    def get_client(self) -> genai.Client:
        """Initializes or retrieves the Google GenAI client."""
        if not self.api_key:
            raise ValueError(
                "Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file "
                "or enter it in the Taleora application sidebar."
            )
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate_story(
        self,
        keywords: list[str],
        genre: str,
        audience: str,
        extra_notes: str = ""
    ) -> StoryBook:
        """
        Generates a complete structured storybook adhering to genre, audience,
        and character consistency requirements.
        """
        # Validate 3 keywords
        is_valid, err_msg, cleaned_kws = validate_keywords(keywords)
        if not is_valid:
            raise ValueError(err_msg)

        client = self.get_client()

        # Build prompts
        system_instruction = build_system_prompt(genre, audience)
        user_prompt = build_story_prompt(cleaned_kws, genre, audience, extra_notes)

        # Call Gemini with structured schema
        config_options = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=StoryBook,
            temperature=0.75,
        )

        response = client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=config_options,
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response. Please try again.")

        # Parse JSON into Pydantic StoryBook
        story_data = json.loads(response.text)
        storybook = StoryBook.model_validate(story_data)

        # Post-process image prompts to lock in character consistency and art style
        genre_info = config.GENRES.get(genre, config.GENRES["Fantasy"])
        visual_style = genre_info["visual_style"]

        for scene in storybook.scenes:
            scene.image_prompt = guarantee_scene_character_consistency(
                image_prompt=scene.image_prompt,
                characters_present=scene.characters_present,
                character_bible=storybook.character_bible,
                visual_style=visual_style
            )

        # Automatically save story JSON
        self.save_story_to_disk(storybook)

        return storybook

    def save_story_to_disk(self, storybook: StoryBook) -> Path:
        """Saves the generated StoryBook to the outputs/stories directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = sanitize_filename(storybook.title)
        filename = f"{timestamp}_{safe_title}.json"
        filepath = config.STORIES_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(storybook.model_dump(), f, indent=2, ensure_ascii=False)

        return filepath

    @staticmethod
    def list_saved_stories() -> list[Path]:
        """Lists previously saved story JSON files ordered by newest first."""
        return sorted(config.STORIES_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    @staticmethod
    def load_story_from_disk(filepath: Path) -> StoryBook:
        """Loads a StoryBook from a saved JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return StoryBook.model_validate(data)
