"""
Image Generator Module for Taleora (Satisfies Requirement U3).
Generates high-resolution scene illustrations enforcing character consistency,
with multi-engine support (Pollinations free high-speed SDXL & Hugging Face Inference API).
"""
import urllib.parse
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Callable
from PIL import Image
import io

import config
from modules.prompt_engine import StoryBook, Scene
from modules.story_generator import sanitize_filename


class ImageGenerator:
    """Manages scene illustration generation and disk caching."""

    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token or config.HF_TOKEN
        self.default_engine = "pollinations"  # Default zero-cost, high-speed engine

    def _generate_pollinations(self, prompt: str, width: int = 1024, height: int = 1024, seed: Optional[int] = None) -> bytes:
        """
        Generates an illustration via Pollinations.ai with enhanced storybook prompt tuning.
        100% free, zero authentication required, reliable uptime.
        """
        # Append quality enhancements
        enhanced_prompt = (
            f"{prompt}, award-winning children's storybook illustration, soft painterly gouache and watercolor texture, "
            f"rich vibrant harmonious colors, warm volumetric lighting, storybook cover quality, highly detailed, "
            f"expressive character design, cinematic composition, sharp focus, 8k resolution"
        )
        encoded_prompt = urllib.parse.quote(enhanced_prompt)

        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        if seed is not None:
            url += f"&seed={seed}"

        headers = {
            "User-Agent": "Taleora-Storybook-Generator/1.0"
        }

        response = requests.get(url, headers=headers, timeout=45)
        if response.status_code != 200:
            raise RuntimeError(f"Pollinations image generation failed (HTTP {response.status_code}): {response.text[:200]}")

        return response.content

    def _create_stylized_card(self, title: str, text: str, prompt: str, width: int = 1024, height: int = 1024) -> bytes:
        """Creates a rich, colorful storybook visual card as an emergency offline fallback."""
        from PIL import ImageDraw
        img = Image.new("RGB", (width, height), color=(26, 26, 64))
        draw = ImageDraw.Draw(img)
        # Decorative border
        draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(254, 240, 138), width=6)
        draw.rectangle([(32, 32), (width - 32, height - 32)], outline=(199, 210, 254), width=3)
        # Title and summary
        draw.text((80, 360), title[:40], fill=(254, 240, 138))
        draw.text((80, 440), text[:150] + "...", fill=(241, 245, 249))
        draw.text((80, 580), "Taleora Storybook Illustration", fill=(165, 180, 252))
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _generate_hf(self, prompt: str) -> bytes:
        """
        Generates an illustration via Hugging Face Inference API using SDXL base.
        Requires HF_TOKEN.
        """
        if not self.hf_token:
            raise ValueError("HF_TOKEN is required for Hugging Face Inference engine.")

        api_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": "blurry, low quality, distorted, extra limbs, bad anatomy, text, watermark",
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
        engine: str = "pollinations",
        force_regenerate: bool = False,
        seed: Optional[int] = None
    ) -> Path:
        """
        Generates and saves an illustration for a specific scene.
        Returns the absolute file path of the saved PNG image.
        """
        safe_title = sanitize_filename(story_title)
        filename = f"{safe_title}_scene_{scene.scene_number}.png"
        filepath = config.IMAGES_DIR / filename

        # If image already exists and not forcing regeneration, return existing path
        if filepath.exists() and not force_regenerate:
            return filepath

        prompt = scene.image_prompt

        # Attempt generation with primary engine, fallback if error
        image_bytes = None
        last_error = None

        if engine == "huggingface" and self.hf_token:
            try:
                image_bytes = self._generate_hf(prompt)
            except Exception as e:
                last_error = e
                # Fallback to pollinations
                image_bytes = self._generate_pollinations(prompt, seed=seed)
        else:
            try:
                image_bytes = self._generate_pollinations(prompt, seed=seed)
            except Exception as e:
                last_error = e
                # If pollinations fails and HF token is present, fallback to HF
                if self.hf_token:
                    try:
                        image_bytes = self._generate_hf(prompt)
                    except Exception:
                        pass
                if not image_bytes:
                    image_bytes = self._create_stylized_card(scene.title, scene.narrative_text, prompt)

        if not image_bytes:
            image_bytes = self._create_stylized_card(scene.title, scene.narrative_text, prompt)

        # Validate image content with Pillow and save
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
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
        Generates illustrations for all scenes in a StoryBook sequentially.
        """
        results = {}
        total = len(story.scenes)

        for idx, scene in enumerate(story.scenes):
            if progress_callback:
                progress_callback(idx + 1, total, f"Generating Scene {scene.scene_number}: {scene.title}...")

            img_path = self.generate_scene_image(
                scene=scene,
                story_title=story.title,
                engine=engine,
                force_regenerate=force_regenerate,
                seed=42 + scene.scene_number  # Consistent seed per scene unless regenerated
            )
            results[scene.scene_number] = img_path
            # Polite pause between generations to respect rate limits
            time.sleep(2)

        return results
