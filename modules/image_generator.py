"""
Image Generator Module for Taleora (Satisfies Requirement U3).
Generates high-resolution scene illustrations enforcing character consistency,
with multi-engine support (Pollinations free high-speed SDXL & Hugging Face Inference API).
Strictly generates genuine AI illustrations for every scene with zero placeholder fallbacks.
"""
import urllib.parse
import time
import re
import requests
from pathlib import Path
from typing import Optional, Dict, Callable, List
from PIL import Image
import io

import config
from modules.prompt_engine import StoryBook, Scene, Character
from modules.story_generator import sanitize_filename


class ImageGenerator:
    """Manages scene illustration generation and disk caching."""

    def __init__(self, hf_token: Optional[str] = None, pollinations_api_key: Optional[str] = None):
        self.hf_token = hf_token or config.HF_TOKEN
        self.pollinations_api_key = pollinations_api_key or config.POLLINATIONS_API_KEY
        self.default_engine = "pollinations"

    def _generate_pollinations(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        max_retries: int = 4,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bytes:
        """
        Generates an illustration via Pollinations.ai with enhanced storybook prompt tuning.
        Handles IP rate limits with intelligent retry and cooldown countdown.
        """
        enhanced_prompt = (
            f"{prompt}, award-winning children's storybook illustration, soft painterly gouache and watercolor texture, "
            f"rich vibrant harmonious colors, warm volumetric lighting, storybook cover quality, highly detailed, "
            f"expressive character design, cinematic composition, sharp focus, 8k resolution"
        )
        encoded_prompt = urllib.parse.quote(enhanced_prompt)

        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        if seed is not None:
            url += f"&seed={seed}"
        if self.pollinations_api_key:
            url += f"&key={self.pollinations_api_key}"

        headers = {
            "User-Agent": "Taleora-Storybook-Generator/1.0"
        }
        if self.pollinations_api_key:
            headers["Authorization"] = f"Bearer {self.pollinations_api_key}"

        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=45)

                # Check for rate limit or payment requirement (HTTP 402 or 429)
                if response.status_code in (402, 429):
                    match = re.search(r"Retry after (\d+)s", response.text)
                    cooldown = int(match.group(1)) + 2 if match else 35

                    if attempt < max_retries - 1:
                        # Report cooldown progress every 5 seconds
                        step_interval = 5
                        for s_left in range(cooldown, 0, -step_interval):
                            if progress_callback:
                                progress_callback(f"Free image quota cooldown active. Retrying in {s_left}s...")
                            time.sleep(min(step_interval, s_left))
                        continue
                    else:
                        raise RuntimeError(
                            f"Pollinations rate limit reached after {max_retries} attempts: {response.text[:200]}"
                        )

                if response.status_code != 200:
                    raise RuntimeError(
                        f"Pollinations image generation failed (HTTP {response.status_code}): {response.text[:200]}"
                    )

                # Verify that response is valid image data (not empty or error payload)
                if len(response.content) < 5000:
                    raise RuntimeError(
                        f"Pollinations returned invalid small payload ({len(response.content)} bytes)"
                    )

                return response.content

            except requests.exceptions.RequestException as req_err:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                raise RuntimeError(f"Network error contacting image generator: {req_err}")

        raise RuntimeError("Image generation failed after maximum retries.")

    def _generate_hf(self, prompt: str) -> bytes:
        """
        Generates an illustration via Hugging Face Inference API using SDXL base.
        Requires valid HF_TOKEN.
        """
        if not self.hf_token or self.hf_token == "your_huggingface_api_key_here":
            raise ValueError("A valid HF_TOKEN is required for Hugging Face Inference engine.")

        api_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": "blurry, low quality, distorted, extra limbs, bad anatomy, text, watermark, photo",
            }
        }

        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            raise RuntimeError(f"Hugging Face Inference failed (HTTP {response.status_code}): {response.text[:200]}")

        return response.content

    def generate_scene_image(
        self,
        scene: Scene,
        story_title: str,
        character_bible: Optional[List[Character]] = None,
        engine: str = "pollinations",
        force_regenerate: bool = False,
        seed: Optional[int] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Path:
        """
        Generates and saves a genuine AI illustration for a specific scene.
        Guarantees that placeholder cards are never used.
        Returns the absolute file path of the saved PNG image.
        """
        safe_title = sanitize_filename(story_title)
        filename = f"{safe_title}_scene_{scene.scene_number}.png"
        filepath = config.IMAGES_DIR / filename

        # If image already exists, is a genuine illustration (> 50KB), and not forcing regeneration, return existing path
        if filepath.exists() and not force_regenerate:
            if filepath.stat().st_size > 50000:
                return filepath

        # Build rich, character-consistent prompt
        prompt_parts = [scene.image_prompt]
        if character_bible:
            for char in character_bible:
                if hasattr(char, "name") and (char.name in scene.characters_present or char.name in scene.narrative_text):
                    prompt_parts.append(
                        f"Character {char.name}: {char.visual_appearance}, wearing {char.signature_clothing}, with {char.distinct_accessories}"
                    )

        full_prompt = ", ".join(prompt_parts)

        # Attempt generation with primary engine
        image_bytes = None
        last_error = None

        # 1. Try Hugging Face if explicitly selected and token is configured
        if engine == "huggingface" and self.hf_token and self.hf_token != "your_huggingface_api_key_here":
            try:
                image_bytes = self._generate_hf(full_prompt)
            except Exception as e:
                last_error = e

        # 2. Try Pollinations (primary engine)
        if not image_bytes:
            try:
                image_bytes = self._generate_pollinations(
                    prompt=full_prompt,
                    seed=seed,
                    progress_callback=progress_callback
                )
            except Exception as e:
                last_error = e

        # 3. If Pollinations failed and HF was not tried yet, try HF if token present
        if not image_bytes and self.hf_token and self.hf_token != "your_huggingface_api_key_here":
            try:
                image_bytes = self._generate_hf(full_prompt)
            except Exception as e:
                last_error = e

        # NEVER silently fall back to a placeholder card (Requirements 4 & 5)
        if not image_bytes:
            raise RuntimeError(
                f"Failed to generate genuine AI illustration for Scene {scene.scene_number}: {last_error}"
            )

        # Validate image content with Pillow and save as PNG
        try:
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            pil_image.save(filepath, format="PNG")
        except Exception as e:
            raise RuntimeError(f"Failed to process and save image: {e}")

        return filepath

    def generate_all_scenes(
        self,
        story: StoryBook,
        engine: str = "pollinations",
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        force_regenerate: bool = False
    ) -> Dict[int, Path]:
        """
        Generates genuine illustrations for all scenes in a StoryBook sequentially.
        Ensures each scene has an authentic AI-generated image on disk.
        """
        results = {}
        total = len(story.scenes)

        for idx, scene in enumerate(story.scenes):
            if progress_callback:
                progress_callback(idx + 1, total, f"Painting Chapter {scene.scene_number}/{total}: {scene.title}...")

            def sub_callback(msg: str):
                if progress_callback:
                    progress_callback(idx + 1, total, f"Painting Chapter {scene.scene_number}/{total} ({msg})...")

            img_path = self.generate_scene_image(
                scene=scene,
                story_title=story.title,
                character_bible=story.character_bible,
                engine=engine,
                force_regenerate=force_regenerate,
                seed=42 + scene.scene_number * 17,  # Distinct seed per scene to ensure variety while retaining style
                progress_callback=sub_callback
            )
            results[scene.scene_number] = img_path

        return results
