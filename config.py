"""
Configuration management for Taleora.
Handles paths, model settings, genres, and audience tiers.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
MODULES_DIR = BASE_DIR / "modules"
OUTPUTS_DIR = BASE_DIR / "outputs"
STORIES_DIR = OUTPUTS_DIR / "stories"
IMAGES_DIR = OUTPUTS_DIR / "images"
AUDIO_DIR = OUTPUTS_DIR / "audio"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
PDFS_DIR = OUTPUTS_DIR / "pdfs"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure all output directories exist
for folder in [STORIES_DIR, IMAGES_DIR, AUDIO_DIR, VIDEOS_DIR, PDFS_DIR, ASSETS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Helper to load secrets safely from environment or Streamlit secrets
def get_secret(key: str, default: str = "") -> str:
    """Retrieves secret from environment variables or Streamlit deployment secrets."""
    val = os.getenv(key, "")
    if not val:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                val = str(st.secrets[key])
        except Exception:
            pass
    return val or default

# API Keys & Endpoints (backend-only, never exposed to user interface)
GEMINI_API_KEY = get_secret("GEMINI_API_KEY", "")
HF_TOKEN = get_secret("HF_TOKEN", "")
POLLINATIONS_API_KEY = get_secret("POLLINATIONS_API_KEY", "")
DEFAULT_GEMINI_MODEL = get_secret("GEMINI_MODEL", "gemini-2.5-flash")

# Story Genres & Visual/Narrative DNA
GENRES = {
    "Fantasy": {
        "description": "Magical realms, enchanting creatures, mythical quests, and wonder.",
        "visual_style": "award-winning fantasy storybook illustration, painterly gouache and soft watercolor texture, glowing magical flora, luminous rim lighting, warm ethereal atmosphere, rich vibrant tones, cinematic depth",
        "tone": "magical, wonder-filled, inspiring"
    },
    "Sci-Fi": {
        "description": "Futuristic adventures, friendly robots, outer space, and invention.",
        "visual_style": "retro-futuristic children's storybook illustration, soft painterly digital gouache, warm starlight and gentle neon glow, celestial vistas, whimsical gadgetry, friendly rounded mechanical design, rich cosmic palette",
        "tone": "curious, innovative, exciting"
    },
    "Adventure": {
        "description": "Exploration, hidden treasures, daring journeys, and courage.",
        "visual_style": "dynamic storybook adventure illustration, rich golden hour sunlight, volumetric sunbeams, painterly lush landscape, expressive character posture, warm earthy and sky-blue palette, cinematic framing",
        "tone": "brave, energetic, spirited"
    },
    "Mystery": {
        "description": "Curious puzzles, gentle detective work, clues, and discoveries.",
        "visual_style": "cozy storybook mystery illustration, warm amber lantern glow, deep navy shadows, atmospheric interior details, curious magnifying perspective, soft storybook textures, rich detailed atmosphere",
        "tone": "intriguing, cozy, inquisitive"
    },
    "Fairy Tale": {
        "description": "Classic folklore motifs, gentle morals, talking animals, and enchanted forests.",
        "visual_style": "classic European folklore storybook illustration, delicate gouache and textured watercolor wash, whimsical fairytale flora, soft magical twilight, ornate storybook aesthetic, vibrant enchanting colors",
        "tone": "timeless, gentle, heartwarming"
    },
    "Bedtime Story": {
        "description": "Calming rhythms, soothing themes, gentle comfort, and sleepy resolutions.",
        "visual_style": "dreamy bedtime storybook illustration, soothing pastel palette, velvet midnight blues, gentle crescent moonlight, soft stardust glow, calming painterly textures, tranquil atmosphere",
        "tone": "soothing, lyrical, tranquil"
    }
}

# Target Audiences & Linguistic Constraints
AUDIENCES = {
    "Early Childhood (Ages 3-5)": {
        "label": "Early Childhood (3-5)",
        "vocabulary_level": "very simple, sensory, repetitive phrases, rhythmic sounds",
        "sentence_structure": "short 4-8 word sentences, active voice, friendly cadence",
        "complexity": "1 simple conflict with comforting, immediate resolution",
        "scenes_count": 4,
        "max_words_per_scene": 35
    },
    "Kids (Ages 6-8)": {
        "label": "Kids (6-8)",
        "vocabulary_level": "accessible vocabulary with a few delightful descriptive words",
        "sentence_structure": "compound sentences, dynamic dialogue, playful rhythm",
        "complexity": "clear beginning, problem, team effort/ingenuity, positive moral",
        "scenes_count": 5,
        "max_words_per_scene": 50
    },
    "Middle Grade (Ages 9-12)": {
        "label": "Middle Grade (9-12)",
        "vocabulary_level": "rich vocabulary, figurative language, vivid sensory metaphors",
        "sentence_structure": "varied sentence pacing, internal thoughts, engaging dialogue",
        "complexity": "multilayered dilemma, character growth, clever twist or discovery",
        "scenes_count": 6,
        "max_words_per_scene": 75
    },
    "Young Adult (Ages 13+)": {
        "label": "Young Adult (13+)",
        "vocabulary_level": "sophisticated, evocative, thematic depth, atmospheric prose",
        "sentence_structure": "expressive and nuanced prose with atmospheric scene setting",
        "complexity": "thematic journey, emotional stakes, self-realization",
        "scenes_count": 6,
        "max_words_per_scene": 90
    }
}

# Edge TTS Voice Mappings (Natural high-quality neural voices)
TTS_VOICES = {
    "Female - Storyteller (Ana)": "en-US-AnaNeural",
    "Female - Warm & Expressive (Jenny)": "en-US-JennyNeural",
    "Male - Wise Narrator (Christopher)": "en-US-ChristopherNeural",
    "Male - Friendly & Upbeat (Guy)": "en-US-GuyNeural",
    "Female - British Gentle (Sonia)": "en-GB-SoniaNeural",
    "Male - British Storyteller (Ryan)": "en-GB-RyanNeural"
}

DEFAULT_VOICE = "en-US-AnaNeural"
