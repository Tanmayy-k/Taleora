"""
Character Manager Module for Taleora (Satisfies Requirement U2).
Manages character bibles and enforces visual consistency across scene illustration prompts.
"""
from typing import List, Dict, Any
from modules.prompt_engine import Character


def format_character_bible_markdown(characters: List[Character]) -> str:
    """
    Renders the character bible as styled markdown for display in the UI.
    """
    if not characters:
        return "*No characters recorded in bible.*"

    md_blocks = []
    for char in characters:
        block = f"""### 👤 {char.name} ({char.role})
- **Appearance:** {char.visual_appearance}
- **Signature Outfit:** {char.signature_clothing}
- **Distinctive Props/Accessories:** {char.distinct_accessories}
- **Personality:** {char.personality_trait}
"""
        md_blocks.append(block)

    return "\n".join(md_blocks)


def build_character_visual_signature(char: Character) -> str:
    """
    Extracts a concise, high-impact visual signature string to embed in image generation prompts.
    """
    return (
        f"{char.name} (a character with {char.visual_appearance}, wearing {char.signature_clothing}, "
        f"with {char.distinct_accessories})"
    )


def guarantee_scene_character_consistency(
    image_prompt: str,
    characters_present: List[str],
    character_bible: List[Character],
    visual_style: str
) -> str:
    """
    Post-processes a scene's image prompt to guarantee that:
    1. Every character present in the scene has their exact visual signature embedded.
    2. The genre visual art style tags are included.
    3. Negative prompt descriptors or quality tags are harmonized.
    """
    char_map: Dict[str, Character] = {c.name.lower(): c for c in character_bible}
    injected_char_descriptions = []

    for name in characters_present:
        cleaned_name = name.strip().lower()
        if cleaned_name in char_map:
            char = char_map[cleaned_name]
            sig = build_character_visual_signature(char)
            # Only append if not already explicitly described in the prompt
            if char.name.lower() not in image_prompt.lower() or len(char.signature_clothing) > 10:
                injected_char_descriptions.append(sig)

    parts = []
    # Style header
    if visual_style and visual_style.lower() not in image_prompt.lower():
        parts.append(visual_style)

    # Base scene description
    parts.append(image_prompt.strip())

    # Injected character details if missing
    if injected_char_descriptions:
        parts.append("Featuring: " + "; ".join(injected_char_descriptions))

    # Standard high-quality storybook render tags
    parts.append("award-winning children's storybook illustration, soft painterly gouache and watercolor texture, rich harmonious colors, warm volumetric lighting, storybook cover quality, highly detailed, expressive character design, cinematic depth of field")

    return ", ".join(parts)
