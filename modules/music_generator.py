"""
Music Generator Module for Taleora (Satisfies Requirement U4).
Generates ambient instrumental background music using Meta MusicGen (HF Inference API)
with procedural harmonic ambient audio synthesis as a zero-setup fallback.
"""
import math
import io
import requests
import numpy as np
from scipy.io import wavfile
from pathlib import Path
from typing import Optional, Tuple

import config
from modules.prompt_engine import StoryBook
from modules.story_generator import sanitize_filename


class MusicGenerator:
    """Generates ambient instrumental background music tailored to story genre and mood."""

    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token or config.HF_TOKEN

    def _generate_musicgen_hf(self, mood_prompt: str, duration_seconds: int = 15) -> bytes:
        """Calls Meta MusicGen on Hugging Face Inference API."""
        if not self.hf_token:
            raise ValueError("HF_TOKEN is required for Meta MusicGen inference.")

        api_url = "https://router.huggingface.co/hf-inference/models/facebook/musicgen-small"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {
            "inputs": f"calm gentle children's storybook instrumental, {mood_prompt}, soft acoustic, relaxing, no vocals"
        }

        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.content

        raise RuntimeError(f"HF MusicGen error (HTTP {response.status_code}): {response.text[:150]}")

    def _generate_procedural_ambient(self, genre: str, duration_seconds: int = 20) -> bytes:
        """
        Synthesizes a pleasant, gentle harmonic instrumental ambient track.
        Zero dependencies on external GPUs or paid services.
        Produces multi-tonal soothing chords with smooth envelopes.
        """
        sample_rate = 22050
        total_samples = sample_rate * duration_seconds
        t = np.linspace(0, duration_seconds, total_samples, endpoint=False)

        # Base chord progressions based on genre
        genre_chords = {
            "Fantasy": [261.63, 329.63, 392.00, 523.25],       # C major chord (magical harp)
            "Sci-Fi": [220.00, 277.18, 329.63, 440.00],        # A major pad (space wonder)
            "Adventure": [293.66, 369.99, 440.00, 587.33],     # D major (spirited)
            "Mystery": [220.00, 261.63, 329.63, 440.00],       # A minor (curious)
            "Fairy Tale": [261.63, 329.63, 392.00, 493.88],    # C maj7 (whimsical)
            "Bedtime Story": [196.00, 246.94, 293.66, 392.00]  # G major (sleepy lullaby)
        }

        chords = genre_chords.get(genre, genre_chords["Fantasy"])

        # Create multi-frequency layered harmonic wave
        audio = np.zeros(total_samples, dtype=np.float32)
        for i, freq in enumerate(chords):
            # Slow LFO tremolo for gentle movement
            lfo = 0.5 + 0.5 * np.sin(2 * math.pi * 0.2 * t + (i * 0.5))
            # Primary sine note + soft bell overtone
            note = np.sin(2 * math.pi * freq * t) * 0.6 + np.sin(2 * math.pi * freq * 2 * t) * 0.15
            audio += note * lfo

        # Apply smooth attack and release envelope
        envelope = np.ones(total_samples, dtype=np.float32)
        fade_samples = sample_rate * 2  # 2 second fade in and fade out
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        audio = audio * envelope

        # Normalize and convert to 16-bit PCM WAV
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.6  # Master volume headroom

        audio_int16 = (audio * 32767).astype(np.int16)

        buffer = io.BytesIO()
        wavfile.write(buffer, sample_rate, audio_int16)
        return buffer.getvalue()

    def generate_story_music(
        self,
        story: StoryBook,
        duration_seconds: int = 25,
        force_regenerate: bool = False
    ) -> Tuple[Path, str]:
        """
        Generates background music for the story and returns (filepath, model_name).
        """
        safe_title = sanitize_filename(story.title)
        filepath = config.AUDIO_DIR / f"{safe_title}_bg_music.wav"

        if filepath.exists() and not force_regenerate:
            return filepath, "Cached Background Music"

        # Try Meta MusicGen if HF_TOKEN is available
        if self.hf_token:
            try:
                mood_prompt = story.scenes[0].music_mood if story.scenes else story.genre
                raw_bytes = self._generate_musicgen_hf(mood_prompt, duration_seconds)
                with open(filepath, "wb") as f:
                    f.write(raw_bytes)
                return filepath, "Meta MusicGen (Hugging Face API)"
            except Exception:
                pass

        # Procedural Harmonic Ambient Synthesizer (Zero-cost, instant, reliable)
        raw_bytes = self._generate_procedural_ambient(story.genre, duration_seconds)
        with open(filepath, "wb") as f:
            f.write(raw_bytes)

        return filepath, "Taleora Harmonic Ambient Synthesizer"
