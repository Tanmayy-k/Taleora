"""
Audio Generator Module for Taleora (Satisfies Requirement U4).
Generates high-quality neural voice narration for story scenes using Microsoft Edge TTS.
"""
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Callable
import edge_tts

import config
from modules.prompt_engine import StoryBook, Scene
from modules.story_generator import sanitize_filename


class AudioGenerator:
    """Manages scene narration synthesis and audio compilation."""

    def __init__(self, voice: Optional[str] = None):
        self.default_voice = voice or config.DEFAULT_VOICE

    async def _synthesize_edge_tts(self, text: str, output_path: Path, voice: str) -> Path:
        """Asynchronously synthesizes speech using Edge TTS and saves to MP3."""
        clean_text = text.strip()
        if not clean_text:
            clean_text = "..."

        communicate = edge_tts.Communicate(text=clean_text, voice=voice)
        await communicate.save(str(output_path))
        return output_path

    def generate_scene_narration(
        self,
        scene: Scene,
        story_title: str,
        voice: Optional[str] = None,
        force_regenerate: bool = False
    ) -> Path:
        """
        Generates and saves the narration MP3 file for a specific scene.
        """
        voice = voice or self.default_voice
        safe_title = sanitize_filename(story_title)
        filename = f"{safe_title}_scene_{scene.scene_number}_narration.mp3"
        filepath = config.AUDIO_DIR / filename

        if filepath.exists() and not force_regenerate:
            return filepath

        # Use clean audio_script, fallback to narrative_text
        narration_text = scene.audio_script or scene.narrative_text

        # Run async TTS synchronously
        try:
            asyncio.run(self._synthesize_edge_tts(narration_text, filepath, voice))
        except Exception as e:
            # Fallback for nested event loops
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._synthesize_edge_tts(narration_text, filepath, voice))

        return filepath

    def generate_all_narrations(
        self,
        story: StoryBook,
        voice: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        force_regenerate: bool = False
    ) -> Dict[int, Path]:
        """
        Generates narration for all scenes sequentially in a StoryBook.
        """
        voice = voice or self.default_voice
        results = {}
        total = len(story.scenes)

        for idx, scene in enumerate(story.scenes):
            if progress_callback:
                progress_callback(idx + 1, total, f"Voicing Scene {scene.scene_number}: {scene.title}...")

            audio_path = self.generate_scene_narration(
                scene=scene,
                story_title=story.title,
                voice=voice,
                force_regenerate=force_regenerate
            )
            results[scene.scene_number] = audio_path

        return results
