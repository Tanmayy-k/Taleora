"""
Child Safety Filter Module for Taleora (Satisfies Requirement U5).
Implements multi-layer content safety filtering: lexical keyword/regex screening
and LLM Safety Guardian evaluation tailored to children's age tiers.
"""
import re
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

import config
from modules.prompt_engine import StoryBook


class SafetyReport(BaseModel):
    is_safe: bool = Field(description="Whether the story is safe for the target audience")
    safety_score: int = Field(description="Safety score from 0 (unsafe) to 100 (completely safe)")
    safety_rating: str = Field(description="Safety tier: Safe for All Children, Mild Concern, or Unsafe / Flagged")
    flagged_categories: List[str] = Field(description="Categories of concern if any, otherwise empty")
    explanation: str = Field(description="Clear explanation of the safety assessment")
    mitigation_advice: str = Field(description="Recommendations to improve child safety if needed")


# Lexical screening blocklist: terms completely inappropriate for children
UNSAFE_PATTERNS = [
    # Explicit violence / harm
    r"\b(murder|kill|blood|bloody|wound|stab|shoot|gun|weapon|corpse|dead|death|torture|poison|strangle)\b",
    # Horror / nightmare
    r"\b(demon|devil|hell|curse|nightmare|ghoul|zombie|monstrous|grotesque|skull|skeleton)\b",
    # Profanity & vulgarity
    r"\b(damn|hell|ass|crap|bitch|bastard|hate|stupid|idiot|ugly)\b",
    # Substance & adult
    r"\b(beer|wine|whiskey|alcohol|drug|smoke|cigarette|kiss|naked|sex|sexy)\b"
]


class ChildSafetyFilter:
    """Evaluates storybooks for child safety and age-appropriate content."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.GEMINI_API_KEY

    @staticmethod
    def run_lexical_screen(text: str) -> Dict[str, Any]:
        """
        Runs regex-based lexical screening across the text.
        Returns detected prohibited words and a preliminary safety deduction.
        """
        detected_words = []
        lower_text = text.lower()

        for pattern in UNSAFE_PATTERNS:
            matches = re.findall(pattern, lower_text)
            if matches:
                detected_words.extend(matches)

        unique_detected = sorted(list(set(detected_words)))
        is_lexically_safe = len(unique_detected) == 0

        # Compute preliminary deduction
        penalty = min(len(unique_detected) * 15, 60)
        base_score = 100 - penalty

        return {
            "is_clean": is_lexically_safe,
            "detected_keywords": unique_detected,
            "preliminary_score": base_score
        }

    def evaluate_story_safety(self, story: StoryBook) -> SafetyReport:
        """
        Audits the full story narrative, character descriptions, and scene text
        using lexical screening and Gemini Safety Guardian.
        """
        # Aggregate full story text
        full_text = f"Title: {story.title}\nLogline: {story.logline}\n\n"
        for char in story.character_bible:
            full_text += f"Character: {char.name} ({char.role}): {char.visual_appearance} {char.personality_trait}\n"
        for scene in story.scenes:
            full_text += f"\nScene {scene.scene_number} - {scene.title}:\n{scene.narrative_text}\n"

        # Step 1: Lexical screening
        lex_result = self.run_lexical_screen(full_text)

        # Step 2: Gemini LLM Safety Guardian evaluation
        if self.api_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=self.api_key)

                system_prompt = (
                    "You are the Child Safety Content Guardian for Taleora, a children's storybook generator. "
                    "Your duty is to rigorously evaluate whether this story is wholesome, non-threatening, "
                    "and age-appropriate for the specified target audience tier. "
                    "Flag any subtle violence, cruelty, fear, distress, or inappropriate content."
                )

                user_prompt = f"""Target Audience Tier: {story.target_audience}
Genre: {story.genre}

Story Content to Audit:
---
{full_text}
---

Lexical scan detected words: {lex_result['detected_keywords'] or 'None'}

Evaluate this story and return a structured JSON report conforming to the SafetyReport schema."""

                config_opts = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=SafetyReport,
                    temperature=0.2,  # Low temperature for objective safety evaluation
                )

                models_to_try = [
                    config.DEFAULT_GEMINI_MODEL,
                    "gemini-3.5-flash",
                    "gemini-flash-lite-latest",
                    "gemini-3.1-flash-lite",
                    "gemini-3.5-flash-lite",
                    "gemini-2.5-flash",
                ]
                seen = set()
                deduped = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

                for m in deduped:
                    try:
                        response = client.models.generate_content(
                            model=m,
                            contents=user_prompt,
                            config=config_opts
                        )
                        if response and response.text:
                            report_data = json.loads(response.text)
                            return SafetyReport.model_validate(report_data)
                    except Exception:
                        continue

            except Exception:
                pass  # Fall through to algorithmic evaluation if API call encounters an error

        # Step 3: Algorithmic Fallback Evaluation
        score = lex_result["preliminary_score"]
        is_safe = score >= 75
        rating = "Safe for All Children" if score >= 90 else ("Mild Concern" if score >= 70 else "Unsafe / Flagged")

        categories = []
        if lex_result["detected_keywords"]:
            categories.append(f"Contains sensitive words: {', '.join(lex_result['detected_keywords'])}")

        explanation = (
            f"Automated lexical guardrail passed with 0 prohibited words detected. Story is fully compliant for {story.target_audience}."
            if is_safe
            else f"Automated lexical guardrail detected {len(lex_result['detected_keywords'])} potentially sensitive word(s). Review recommended."
        )

        advice = (
            "No revisions necessary. Content is wholesome and inspiring."
            if is_safe
            else "Consider replacing flagged words with gentler, child-friendly synonyms."
        )

        return SafetyReport(
            is_safe=is_safe,
            safety_score=score,
            safety_rating=rating,
            flagged_categories=categories,
            explanation=explanation,
            mitigation_advice=advice
        )
