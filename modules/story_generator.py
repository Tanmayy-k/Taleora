"""
Story Generator Module for Taleora (Satisfies Requirement U2).
Uses Google Gemini API to generate structured stories with character bibles,
scene breakdowns, narration scripts, and image prompts.
Features robust retry with exponential backoff for temporary 429/503 errors,
intelligent multi-model cascade, and specific error diagnostics.
"""
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

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


def parse_gemini_error(e: Exception) -> Dict[str, Any]:
    """
    Extracts detailed diagnostics from Google GenAI API errors.
    Categorizes errors into:
    - 401 / 403: Authentication failed
    - 404: Model not found or deprecated
    - 429: Rate limit (per-minute RPM/TPM) vs Daily Quota Exhausted (requests per day)
    - 503 / 500: Server Overload / Temporary Outage
    """
    err_str = str(e)
    code = getattr(e, "code", None)
    raw_message = getattr(e, "message", "") or err_str

    # Inspect details dictionary if present
    details = getattr(e, "details", {})
    if isinstance(details, dict):
        err_obj = details.get("error", {})
        if isinstance(err_obj, dict):
            code = code or err_obj.get("code")
            raw_message = err_obj.get("message") or raw_message

    # Fallback status code parsing from text if missing
    if not code:
        code_match = re.search(r"\b(400|401|403|404|429|500|503|504)\b", err_str)
        if code_match:
            code = int(code_match.group(1))

    # Parse retry delay / Retry-After if available
    retry_seconds = 0.0
    # 1. From details list
    detail_list = details.get("error", {}).get("details", []) if isinstance(details, dict) else []
    for d in detail_list:
        if isinstance(d, dict) and "retryDelay" in d:
            delay_str = str(d["retryDelay"])
            delay_m = re.search(r"(\d+(?:\.\d+)?)s?", delay_str)
            if delay_m:
                retry_seconds = float(delay_m.group(1))
                break

    # 2. From message string if not found in details
    if retry_seconds == 0.0:
        h_m = re.search(r"retry in (\d+)h(\d+)m", raw_message, re.IGNORECASE)
        if h_m:
            retry_seconds = int(h_m.group(1)) * 3600 + int(h_m.group(2)) * 60
        else:
            s_m = re.search(r"retry in (\d+(?:\.\d+)?)s", raw_message, re.IGNORECASE)
            if s_m:
                retry_seconds = float(s_m.group(1))

    # Determine specific failure mode
    lower_msg = (raw_message.lower() + " " + err_str.lower())

    is_daily_quota_exhausted = (
        code == 429 and (
            "day limit exceeded" in lower_msg
            or "generaterequestsperday" in lower_msg
            or "daily" in lower_msg
            or retry_seconds > 120
        )
    )

    is_rate_limit = (code == 429) and not is_daily_quota_exhausted
    is_server_overload = (code in (500, 503, 504)) or ("unavailable" in lower_msg) or ("high demand" in lower_msg)
    is_not_found = (code == 404) or ("not found" in lower_msg) or ("no longer available" in lower_msg)
    is_auth_error = (code in (401, 403)) or ("unauthenticated" in lower_msg) or ("api key not valid" in lower_msg)

    return {
        "status_code": code or 500,
        "raw_message": raw_message,
        "retry_seconds": retry_seconds,
        "is_daily_quota_exhausted": is_daily_quota_exhausted,
        "is_rate_limit": is_rate_limit,
        "is_server_overload": is_server_overload,
        "is_not_found": is_not_found,
        "is_auth_error": is_auth_error,
    }


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
                "Gemini API key is not configured. Please ensure GEMINI_API_KEY is present in your .env file "
                "or Streamlit deployment secrets."
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
        Implements automatic retries with exponential backoff for temporary rate limits / 503 overloads,
        and cascades to fallback models if daily quota on a specific model is exhausted.
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

        # Model fallback cascade prioritizing active models with healthy quota
        models_to_try = [
            self.model_name,
            "gemini-3.5-flash",
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-flash-latest",
        ]
        # Deduplicate while preserving order
        seen = set()
        deduped_models = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

        response = None
        diagnostics: List[Dict[str, Any]] = []

        for model_candidate in deduped_models:
            model_succeeded = False

            # Try up to 3 attempts with exponential backoff for temporary errors (503 / short 429)
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=model_candidate,
                        contents=user_prompt,
                        config=config_options,
                    )
                    if response and response.text:
                        self.model_name = model_candidate
                        model_succeeded = True
                        break
                except Exception as e:
                    diag = parse_gemini_error(e)
                    diag["model"] = model_candidate

                    # 1. Fatal Auth Error: Immediately raise actionable guidance
                    if diag["is_auth_error"]:
                        raise RuntimeError(
                            f"Gemini API Authentication Failed (HTTP {diag['status_code']}): {diag['raw_message']}. "
                            "Please check your GEMINI_API_KEY in .env."
                        )

                    # 2. Daily Quota Exhausted for this specific model: switch to next model in cascade
                    if diag["is_daily_quota_exhausted"]:
                        diagnostics.append(diag)
                        break

                    # 3. Model Not Found / Retired: switch to next model in cascade
                    if diag["is_not_found"]:
                        diagnostics.append(diag)
                        break

                    # 4. Temporary Rate Limit (Per-Minute / Burst): back off and retry
                    if diag["is_rate_limit"]:
                        if attempt < 2:
                            wait_t = diag["retry_seconds"] if (0 < diag["retry_seconds"] <= 10) else (2 ** (attempt + 1))
                            time.sleep(wait_t)
                            continue
                        else:
                            diagnostics.append(diag)
                            break

                    # 5. Temporary Server Overload (503 / 500): back off and retry
                    if diag["is_server_overload"]:
                        if attempt < 2:
                            wait_t = diag["retry_seconds"] if (0 < diag["retry_seconds"] <= 10) else (2 ** (attempt + 1))
                            time.sleep(wait_t)
                            continue
                        else:
                            diagnostics.append(diag)
                            break

                    # Any other error: record and break to try next model
                    diagnostics.append(diag)
                    break

            if model_succeeded and response and response.text:
                break

        if not response or not response.text:
            # Analyze diagnostic patterns across all models to show the exact cause
            daily_quota_failures = [d for d in diagnostics if d["is_daily_quota_exhausted"]]
            server_overloads = [d for d in diagnostics if d["is_server_overload"]]

            if daily_quota_failures and len(daily_quota_failures) == len(diagnostics):
                max_delay = max(d["retry_seconds"] for d in daily_quota_failures)
                hours_left = max_delay / 3600.0 if max_delay > 0 else 24.0
                raise RuntimeError(
                    f"Gemini Free-Tier Daily Quota Exhausted (HTTP 429 RESOURCE_EXHAUSTED): "
                    f"All evaluated models have reached their free daily limit (resets in approx {hours_left:.1f} hours). "
                    f"API message: {daily_quota_failures[0]['raw_message']}"
                )
            elif server_overloads and len(server_overloads) == len(diagnostics):
                raise RuntimeError(
                    f"Gemini API Temporary Server Overload (HTTP 503 UNAVAILABLE): "
                    f"Google Gemini servers are currently experiencing high demand across all model endpoints. "
                    f"Please try again in a few moments."
                )
            else:
                summary_msgs = [f"[{d['model']}: HTTP {d['status_code']} - {d['raw_message'][:90]}]" for d in diagnostics]
                raise RuntimeError(
                    f"Story generation failed across {len(deduped_models)} Gemini models:\n" + "\n".join(summary_msgs)
                )

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
                visual_style=visual_style,
            )

        # Persist story to disk as JSON artifact
        self.save_story_to_disk(storybook)

        return storybook

    @staticmethod
    def save_story_to_disk(storybook: StoryBook) -> Path:
        """Saves generated story to the outputs/stories directory as formatted JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = sanitize_filename(storybook.title)
        filename = f"{timestamp}_{safe_title}.json"
        filepath = config.STORIES_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(storybook.model_dump_json(indent=2))

        return filepath

    @staticmethod
    def list_saved_stories() -> List[Path]:
        """Returns saved story JSON paths, newest timestamped files first."""
        return sorted(
            config.STORIES_DIR.glob("*.json"),
            key=lambda filepath: filepath.name,
            reverse=True,
        )

    @staticmethod
    def load_story_from_disk(filepath: Path) -> StoryBook:
        """Loads and validates a story JSON file from disk."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return StoryBook.model_validate(data)
