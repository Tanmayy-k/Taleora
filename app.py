"""
Taleora — Illustrated Audio Storybook Generator
Main Streamlit Application (Phase 1)
"""
import streamlit as st
import json
from pathlib import Path

import config
from modules.prompt_engine import validate_keywords, StoryBook
from modules.character_manager import format_character_bible_markdown
from modules.story_generator import StoryGenerator

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Taleora — Illustrated Audio Storybook Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for magical, warm, polished storytelling aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Quicksand:wght@400;600;700&display=swap');

    /* Global typography */
    html, body, [class*="css"] {
        font-family: 'Quicksand', sans-serif;
    }

    h1, h2, h3, .brand-title {
        font-family: 'Cinzel', serif !important;
        letter-spacing: 0.5px;
    }

    .hero-container {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 18px;
        color: #f8fafc;
        box-shadow: 0 10px 25px -5px rgba(30, 27, 75, 0.4);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }

    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        color: #fef08a;
        text-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }

    .hero-subtitle {
        font-size: 1.1rem;
        color: #e0e7ff;
        margin-top: 0.5rem;
        margin-bottom: 0;
    }

    /* Card styling */
    .story-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 1.2rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .story-card:hover {
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    }

    .character-badge {
        background: #eef2ff;
        color: #3730a3;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid #c7d2fe;
    }

    .scene-badge {
        background: #fef3c7;
        color: #92400e;
        padding: 0.3rem 0.8rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 0.5rem;
    }

    .prompt-box {
        background: #f8fafc;
        border-left: 4px solid #6366f1;
        padding: 0.8rem 1rem;
        border-radius: 4px;
        font-size: 0.88rem;
        color: #334155;
        margin-top: 0.8rem;
    }

    .keyword-pill {
        display: inline-block;
        background: #fdf2f8;
        color: #9d174d;
        border: 1px solid #fbcfe8;
        padding: 0.25rem 0.65rem;
        border-radius: 12px;
        font-weight: 600;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ✨ TALEORA")
    st.caption("Illustrated Audio Storybook Generator")
    st.markdown("---")

    # API Configuration
    st.subheader("🔑 API Settings")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=config.GEMINI_API_KEY,
        type="password",
        help="Get a free key from Google AI Studio: https://aistudio.google.com/"
    )

    selected_model = st.selectbox(
        "Gemini Model",
        options=["gemini-2.0-flash", "gemini-1.5-flash"],
        index=0
    )

    st.markdown("---")

    # Saved Stories Loader
    st.subheader("📚 Saved Stories")
    saved_files = StoryGenerator.list_saved_stories()
    if saved_files:
        story_options = {f.name: f for f in saved_files}
        chosen_filename = st.selectbox(
            "Load previous story",
            options=["-- Select a saved story --"] + list(story_options.keys())
        )
        if chosen_filename != "-- Select a saved story --":
            if st.button("📖 Load Story", use_container_width=True):
                try:
                    loaded = StoryGenerator.load_story_from_disk(story_options[chosen_filename])
                    st.session_state["current_story"] = loaded
                    st.success(f"Loaded '{loaded.title}'!")
                except Exception as e:
                    st.error(f"Failed to load story: {e}")
    else:
        st.info("No saved stories yet. Generate your first one!")

    st.markdown("---")
    st.caption("College GenAI Project • Requirements U1–U5")


# ---------------------------------------------------------
# Hero Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">✨ TALEORA</div>
    <div class="hero-subtitle">Transform three keywords into a fully illustrated, narrated, and verified storybook.</div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Main Tabs (Covering All Requirements)
# ---------------------------------------------------------
tabs = st.tabs([
    "📖 Create & Story (U1 & U2)",
    "🎨 Illustrations (U3)",
    "🎵 Audio & Narration (U4)",
    "🛡️ Verification & Safety (U3 & U5)",
    "📦 Export & Download (U4)"
])


# =========================================================
# TAB 1: CREATE & STORY (U1 & U2)
# =========================================================
with tabs[0]:
    col_input, col_meta = st.columns([1.1, 0.9], gap="large")

    with col_input:
        st.markdown("### 1. Three Story Keywords (U1)")
        st.caption("Enter exactly three creative keywords to spark the adventure.")

        # Preset helper buttons
        c_p1, c_p2, c_p3 = st.columns(3)
        if c_p1.button("✨ Magic Forest"):
            st.session_state["kw1"] = "Glowing Acorn"
            st.session_state["kw2"] = "Talking Fox"
            st.session_state["kw3"] = "Crystal Stream"
        if c_p2.button("🚀 Star Traveler"):
            st.session_state["kw1"] = "Pocket Robot"
            st.session_state["kw2"] = "Starlight Compass"
            st.session_state["kw3"] = "Singing Asteroid"
        if c_p3.button("🌊 Ocean Mystery"):
            st.session_state["kw1"] = "Golden Shell"
            st.session_state["kw2"] = "Friendly Dolphin"
            st.session_state["kw3"] = "Sunken Coral Castle"

        kw1 = st.text_input("Keyword 1", value=st.session_state.get("kw1", "Clockwork Owl"), placeholder="e.g. Clockwork Owl")
        kw2 = st.text_input("Keyword 2", value=st.session_state.get("kw2", "Floating Key"), placeholder="e.g. Floating Key")
        kw3 = st.text_input("Keyword 3", value=st.session_state.get("kw3", "Secret Attic Library"), placeholder="e.g. Secret Attic Library")

    with col_meta:
        st.markdown("### 2. Genre & Audience (U1)")
        genre_choice = st.selectbox(
            "Story Genre",
            options=list(config.GENRES.keys()),
            index=0,
            help="Defines narrative tone, worldbuilding style, and visual illustration DNA."
        )
        genre_details = config.GENRES[genre_choice]
        st.info(f"**Visual & Narrative DNA:** {genre_details['description']}\n\n*Art Style:* `{genre_details['visual_style']}`")

        audience_choice = st.selectbox(
            "Target Audience & Age Group",
            options=list(config.AUDIENCES.keys()),
            index=1,
            help="Controls sentence length, vocabulary complexity, scene count, and themes."
        )
        aud_details = config.AUDIENCES[audience_choice]
        st.caption(f"🎯 **Complexity:** {aud_details['complexity']} | **Scenes:** {aud_details['scenes_count']} scenes (~{aud_details['max_words_per_scene']} w/scene)")

    extra_notes = st.text_input("Optional Creative Notes / Nuances", placeholder="e.g. Focus on kindness and curiosity", value="")

    st.markdown("---")

    # Generate Story Action
    generate_btn = st.button("✨ Generate Story & Character Bible (U1 + U2)", type="primary", use_container_width=True)

    if generate_btn:
        active_api_key = api_key_input.strip() or config.GEMINI_API_KEY
        if not active_api_key:
            st.error("⚠️ Please provide a Google Gemini API Key in the sidebar or in your `.env` file.")
        else:
            raw_keywords = [kw1, kw2, kw3]
            is_valid, validation_msg, cleaned_kws = validate_keywords(raw_keywords)

            if not is_valid:
                st.error(f"⚠️ Keyword validation error: {validation_msg}")
            else:
                with st.spinner("🧙‍♂️ Weaving story, sculpting characters, and directing scene storyboards..."):
                    try:
                        generator = StoryGenerator(api_key=active_api_key, model_name=selected_model)
                        story = generator.generate_story(
                            keywords=cleaned_kws,
                            genre=genre_choice,
                            audience=audience_choice,
                            extra_notes=extra_notes
                        )
                        st.session_state["current_story"] = story
                        st.success(f"🎉 Generated story: **{story.title}**!")
                    except Exception as e:
                        st.error(f"❌ Story generation failed: {e}")

    # Display Story if available in session state
    if "current_story" in st.session_state:
        story: StoryBook = st.session_state["current_story"]

        st.markdown("---")
        st.markdown(f"## 📖 {story.title}")
        st.markdown(f"*{story.logline}*")

        # Story Meta Badges
        kw_html = " ".join([f"<span class='keyword-pill'>🏷️ {k}</span>" for k in story.keywords])
        st.markdown(
            f"**Genre:** `{story.genre}` | **Audience:** `{story.target_audience}`<br>"
            f"**Keywords Integrated:** {kw_html}",
            unsafe_allow_html=True
        )

        st.markdown(f"> **Moral / Takeaway:** {story.moral_or_takeaway}")

        # Character Bible (U2 requirement)
        st.markdown("### 👥 Character Bible (Requirement U2)")
        st.caption("Fixed physical attributes, clothing, and props to ensure visual consistency across all scene illustrations.")

        char_cols = st.columns(min(len(story.character_bible), 3) or 1)
        for idx, char in enumerate(story.character_bible):
            with char_cols[idx % len(char_cols)]:
                st.markdown(f"""
                <div class="story-card">
                    <h4>👤 {char.name}</h4>
                    <span class="character-badge">{char.role}</span>
                    <p><strong>Appearance:</strong> {char.visual_appearance}</p>
                    <p><strong>Signature Outfit:</strong> {char.signature_clothing}</p>
                    <p><strong>Key Props:</strong> {char.distinct_accessories}</p>
                    <p><em>"{char.personality_trait}"</em></p>
                </div>
                """, unsafe_allow_html=True)

        # Scene Breakdown (U2 requirement)
        st.markdown("### 🎬 Sequential Story Scenes (Requirement U2)")
        for scene in story.scenes:
            with st.container():
                st.markdown(f"""
                <div class="story-card">
                    <span class="scene-badge">Scene {scene.scene_number} of {len(story.scenes)}</span>
                    <h4>{scene.title}</h4>
                    <p style="font-size: 1.05rem; line-height: 1.6; color: #1e293b;">{scene.narrative_text}</p>
                    <div style="margin-top: 0.8rem;">
                        <strong>Characters Present:</strong> {", ".join(scene.characters_present) if scene.characters_present else "None"} | 
                        <strong>Musical Mood:</strong> <em>{scene.music_mood}</em>
                    </div>
                    <div class="prompt-box">
                        <strong>🎨 Visual Image Prompt (With Character Consistency):</strong><br>
                        <code>{scene.image_prompt}</code>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Raw JSON expander for validation
        with st.expander("🔍 Inspect Structured JSON Output (Requirement U2)"):
            st.json(story.model_dump())


# =========================================================
# TAB 2: ILLUSTRATIONS (U3 Preview)
# =========================================================
with tabs[1]:
    st.markdown("### 🎨 Scene Image Generation & Verification (Requirement U3)")
    st.info("Phase 2 will implement multi-provider image generation (Hugging Face / Pollinations) and Salesforce BLIP caption verification.")
    if "current_story" in st.session_state:
        st.write(f"Ready to illustrate **{len(st.session_state['current_story'].scenes)}** scenes for story: *{st.session_state['current_story'].title}*.")
    else:
        st.warning("Please generate a story in the first tab to view scene image prompts.")


# =========================================================
# TAB 3: AUDIO & NARRATION (U4 Preview)
# =========================================================
with tabs[2]:
    st.markdown("### 🎵 Narration (Edge TTS) & Background Music (MusicGen) (Requirement U4)")
    st.info("Phase 3 will synthesize clean neural narration for each scene and generate instrumental background music loops.")


# =========================================================
# TAB 4: VERIFICATION & SAFETY (U3 & U5 Preview)
# =========================================================
with tabs[3]:
    st.markdown("### 🛡️ BLIP Verification, Child Safety & Originality Check (U3 & U5)")
    st.info("Phase 4 will inspect generated illustrations with BLIP image captioning, run child-safe content verification, and check story originality.")


# =========================================================
# TAB 5: EXPORT & DOWNLOAD (U4 Preview)
# =========================================================
with tabs[4]:
    st.markdown("### 📦 Export Storybook as PDF & MP4 Video (Requirement U4)")
    st.info("Phase 3 & 4 will render an illustrated PDF storybook using ReportLab and an assembled MP4 video using MoviePy + FFmpeg.")
