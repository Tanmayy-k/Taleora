"""
Prompt Engineering Module for Taleora (Satisfies Requirement U1).
Builds structured prompts enforcing genre conventions, audience constraints,
and mandatory 3-keyword integration.
"""
from typing import List, Tuple
from pydantic import BaseModel, Field
import config


# ---------------------------------------------------------
# Pydantic Schemas for Guaranteed Structured JSON Output
# ---------------------------------------------------------

class Character(BaseModel):
    name: str = Field(description="Name of the character")
    role: str = Field(description="Role in the story (e.g., Protagonist, Mentor, Playful Sidekick)")
    visual_appearance: str = Field(
        description="Fixed physical features: hair color/style, eye color, age/stature, species/race, fur/skin tone"
    )
    signature_clothing: str = Field(
        description="Exact clothing items and specific colors (must stay constant across all scenes)"
    )
    distinct_accessories: str = Field(
        description="Constant props, bags, glasses, hats, or distinctive emblems"
    )
    personality_trait: str = Field(description="1-2 core personality traits")


class Scene(BaseModel):
    scene_number: int = Field(description="Sequential scene number starting from 1")
    title: str = Field(description="Short descriptive scene title")
    narrative_text: str = Field(
        description="Story narrative text calibrated for the target age group reading level"
    )
    audio_script: str = Field(
        description="Clean voice narration script (no stage directions, pauses, or sound effects, suitable for TTS)"
    )
    characters_present: List[str] = Field(
        description="Names of characters appearing in this specific scene"
    )
    image_prompt: str = Field(
        description=(
            "Detailed text-to-image prompt. MUST include: art style tags, the scene setting, "
            "lighting, emotional atmosphere, and the EXACT physical appearance + clothing descriptions "
            "from the character bible for every character present in this scene to preserve visual consistency."
        )
    )
    music_mood: str = Field(
        description="Ambient musical mood tag (e.g. 'whimsical orchestral flute', 'mysterious slow piano', 'triumphant strings')"
    )


class StoryBook(BaseModel):
    title: str = Field(description="Captivating, age-appropriate title of the storybook")
    logline: str = Field(description="One-sentence story summary")
    genre: str = Field(description="Selected story genre")
    target_audience: str = Field(description="Selected target age tier")
    keywords: List[str] = Field(description="The three required keywords seamlessly integrated into the plot")
    character_bible: List[Character] = Field(
        description="List of 1 to 3 primary characters with invariant visual and wardrobe attributes"
    )
    scenes: List[Scene] = Field(
        description="Sequential list of scenes forming the complete story arc"
    )
    moral_or_takeaway: str = Field(
        description="Heartwarming lesson, theme, or positive emotional takeaway of the story"
    )


# ---------------------------------------------------------
# Keyword Validation & Prompt Construction
# ---------------------------------------------------------

def validate_keywords(keywords_input: List[str]) -> Tuple[bool, str, List[str]]:
    """
    Validates that exactly 3 non-empty keywords are provided.
    Cleans leading/trailing whitespace.
    """
    cleaned = [k.strip() for k in keywords_input if k and k.strip()]
    if len(cleaned) != 3:
        return False, f"Expected exactly 3 keywords, but received {len(cleaned)}.", cleaned
    
    # Check for empty tokens or unreasonable length
    for kw in cleaned:
        if len(kw) < 2:
            return False, f"Keyword '{kw}' is too short. Please use meaningful words.", cleaned
        if len(kw) > 30:
            return False, f"Keyword '{kw}' is too long. Please keep keywords concise.", cleaned

    return True, "Valid keywords", cleaned


def build_system_prompt(genre: str, audience: str) -> str:
    """
    Generates system-level instructions for Gemini, strictly enforcing
    the genre DNA, vocabulary tier, sentence length, and character consistency rules.
    """
    genre_info = config.GENRES.get(genre, config.GENRES["Fantasy"])
    audience_info = config.AUDIENCES.get(audience, config.AUDIENCES["Kids (Ages 6-8)"])

    system_prompt = f"""You are Taleora's Master Children's Author and Visual Storyboard Director.
Your task is to craft an original, emotionally resonant, beautifully paced storybook.

GENRE DIRECTIVE: {genre}
- Description: {genre_info['description']}
- Visual Style DNA: {genre_info['visual_style']}
- Tone: {genre_info['tone']}

TARGET AUDIENCE DIRECTIVE: {audience}
- Vocabulary Level: {audience_info['vocabulary_level']}
- Sentence Structure: {audience_info['sentence_structure']}
- Narrative Complexity: {audience_info['complexity']}
- Target Scene Count: {audience_info['scenes_count']} scenes
- Max Words Per Scene: ~{audience_info['max_words_per_scene']} words

MANDATORY RULES:
1. INTEGRATE KEYWORDS NATURALLY: The 3 user keywords must be central elements of the plot, wonder, or problem-solving, not merely mentioned in passing.
2. CHARACTER CONSISTENCY BIBLE: You MUST create 1 to 2 memorable main characters. Define their physical traits (hair, eyes, skin/fur) and wardrobe (exact colors, garment names) with high specificity.
3. SCENE IMAGE PROMPTS: Every scene's `image_prompt` MUST explicitly restate the character's exact visual appearance and clothing from the character bible whenever that character is in the scene. Also include the visual style DNA: "{genre_info['visual_style']}".
4. CHILD SAFETY: The story must be 100% wholesome, inspiring, and free of violence, cruelty, profanity, or adult themes.
5. CLEAN AUDIO SCRIPT: Each scene must include an `audio_script` containing only spoken narrative words (no sound effects, stage cues, or parentheticals) ready for text-to-speech narration.
6. OUTPUT FORMAT: You must return clean structured JSON conforming exactly to the requested StoryBook schema.
"""
    return system_prompt.strip()


def build_story_prompt(keywords: List[str], genre: str, audience: str, extra_notes: str = "") -> str:
    """
    Builds the user prompt requesting a full story from the 3 keywords.
    """
    audience_info = config.AUDIENCES.get(audience, config.AUDIENCES["Kids (Ages 6-8)"])
    scene_count = audience_info["scenes_count"]

    prompt = f"""Please create a complete {scene_count}-scene storybook based on these three keywords:
1. "{keywords[0]}"
2. "{keywords[1]}"
3. "{keywords[2]}"

Genre: {genre}
Target Audience: {audience}

{f"Additional Creative Guidance: {extra_notes}" if extra_notes else ""}

Requirements:
- Ensure the 3 keywords have meaningful, imaginative roles in the narrative arc.
- Establish a complete arc across {scene_count} scenes (Beginning / Catalyst -> Discovery / Rising Adventure -> Climax / Creative Solution -> Heartwarming Conclusion).
- Create a distinct character bible so illustrations remain visually consistent across all {scene_count} scenes.
- Formulate each scene's `image_prompt` with extreme visual clarity, restating the character's clothing and physical details.
- Provide clean `audio_script` for each scene for Edge TTS narration.
"""
    return prompt.strip()
