"""
Taleora — Illustrated Audio Storybook Generator
Main Streamlit Application (Phase 3: U1, U2, U3, & U4 Complete)
"""
import streamlit as st
import json
from pathlib import Path
from PIL import Image

import config
from modules.prompt_engine import validate_keywords, StoryBook
from modules.character_manager import format_character_bible_markdown
from modules.story_generator import StoryGenerator, sanitize_filename
from modules.image_generator import ImageGenerator
from modules.blip_verifier import BLIPVerifier
from modules.audio_generator import AudioGenerator
from modules.music_generator import MusicGenerator
from modules.export_manager import ExportManager
from modules.safety_filter import ChildSafetyFilter, SafetyReport
from modules.originality_checker import OriginalityChecker, OriginalityReport

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

    .story-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 1.2rem;
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

    .status-verified {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        font-weight: 700;
        display: inline-block;
    }

    .status-flagged {
        background-color: #fff1f2;
        color: #9f1239;
        border: 1px solid #fecdd3;
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        font-weight: 700;
        display: inline-block;
    }

    .export-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1.5rem;
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

    hf_token_input = st.text_input(
        "Hugging Face Token (Optional)",
        value=config.HF_TOKEN,
        type="password",
        help="Recommended for cloud BLIP & HF SDXL/MusicGen models."
    )

    selected_model = st.selectbox(
        "Gemini Model",
        options=["gemini-2.0-flash", "gemini-1.5-flash"],
        index=0
    )

    image_engine = st.selectbox(
        "Image Generation Engine (U3)",
        options=["pollinations", "huggingface"],
        format_func=lambda x: "Pollinations (Fast & Free, No Key)" if x == "pollinations" else "Hugging Face SDXL (Requires HF Token)",
        index=0
    )

    selected_voice = st.selectbox(
        "TTS Narrator Voice (U4)",
        options=list(config.TTS_VOICES.keys()),
        index=0
    )
    voice_code = config.TTS_VOICES[selected_voice]

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
                    st.session_state["verification_results"] = {}
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


# Path helper functions
def get_scene_image_path(story_title: str, scene_number: int) -> Path:
    safe_title = sanitize_filename(story_title)
    return config.IMAGES_DIR / f"{safe_title}_scene_{scene_number}.png"

def get_scene_audio_path(story_title: str, scene_number: int) -> Path:
    safe_title = sanitize_filename(story_title)
    return config.AUDIO_DIR / f"{safe_title}_scene_{scene_number}_narration.mp3"

def get_story_music_path(story_title: str) -> Path:
    safe_title = sanitize_filename(story_title)
    return config.AUDIO_DIR / f"{safe_title}_bg_music.wav"

def get_story_pdf_path(story_title: str) -> Path:
    safe_title = sanitize_filename(story_title)
    return config.PDFS_DIR / f"{safe_title}_storybook.pdf"

def get_story_video_path(story_title: str) -> Path:
    safe_title = sanitize_filename(story_title)
    return config.VIDEOS_DIR / f"{safe_title}_storybook.mp4"


# ---------------------------------------------------------
# Main Tabs (Covering All Requirements)
# ---------------------------------------------------------
tabs = st.tabs([
    "📖 Create & Story (U1 & U2)",
    "🎨 Illustrations (U3)",
    "🎵 Audio Experience (U4)",
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
                        st.session_state["verification_results"] = {}
                        st.success(f"🎉 Generated story: **{story.title}**!")
                    except Exception as e:
                        st.error(f"❌ Story generation failed: {e}")

    # Display Story if available in session state
    if "current_story" in st.session_state:
        story: StoryBook = st.session_state["current_story"]

        st.markdown("---")
        st.markdown(f"## 📖 {story.title}")
        st.markdown(f"*{story.logline}*")

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

        with st.expander("🔍 Inspect Structured JSON Output (Requirement U2)"):
            st.json(story.model_dump())


# =========================================================
# TAB 2: ILLUSTRATIONS (U3)
# =========================================================
with tabs[1]:
    st.markdown("### 🎨 Scene Image Generation (Requirement U3)")
    st.caption("Generate high-resolution illustrations for each scene while maintaining character consistency.")

    if "current_story" not in st.session_state:
        st.warning("⚠️ Please generate or load a story in the 'Create & Story' tab first.")
    else:
        story: StoryBook = st.session_state["current_story"]

        c_gen_all, c_engine_info = st.columns([1, 2])
        with c_gen_all:
            if st.button("🖼️ Generate All Scene Illustrations", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(curr, total, msg):
                    progress_bar.progress(curr / total)
                    status_text.text(msg)

                img_gen = ImageGenerator(hf_token=hf_token_input.strip() or config.HF_TOKEN)
                with st.spinner("Generating illustrations..."):
                    try:
                        results = img_gen.generate_all_scenes(
                            story=story,
                            engine=image_engine,
                            progress_callback=update_progress,
                            force_regenerate=True
                        )
                        progress_bar.progress(1.0)
                        status_text.text("✨ All illustrations generated successfully!")
                        st.success("All illustrations ready!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Generation error: {e}")

        with c_engine_info:
            st.info(f"Using engine: **{image_engine.capitalize()}**. "
                    f"Generated images are cached in `outputs/images/` and reused automatically.")

        st.markdown("---")

        for scene in story.scenes:
            img_path = get_scene_image_path(story.title, scene.scene_number)
            has_image = img_path.exists()

            with st.container():
                st.markdown(f"#### Scene {scene.scene_number}: {scene.title}")
                col_img, col_desc = st.columns([1, 1], gap="medium")

                with col_img:
                    if has_image:
                        st.image(str(img_path), caption=f"Scene {scene.scene_number} Illustration", use_container_width=True)
                    else:
                        st.markdown("""
                        <div style="background: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 12px; height: 320px; display: flex; align-items: center; justify-content: center; color: #64748b; font-weight: 600;">
                            🖼️ Illustration not yet generated
                        </div>
                        """, unsafe_allow_html=True)

                    regen_key = f"regen_scene_{scene.scene_number}"
                    if st.button(f"🔄 {'Regenerate' if has_image else 'Generate'} Scene {scene.scene_number}", key=regen_key, use_container_width=True):
                        img_gen = ImageGenerator(hf_token=hf_token_input.strip() or config.HF_TOKEN)
                        with st.spinner(f"Generating illustration for Scene {scene.scene_number}..."):
                            try:
                                import random
                                new_seed = random.randint(1000, 999999)
                                img_gen.generate_scene_image(
                                    scene=scene,
                                    story_title=story.title,
                                    engine=image_engine,
                                    force_regenerate=True,
                                    seed=new_seed
                                )
                                if "verification_results" in st.session_state:
                                    st.session_state["verification_results"].pop(scene.scene_number, None)
                                st.success(f"Scene {scene.scene_number} updated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to generate image: {e}")

                with col_desc:
                    st.markdown(f"**Narrative Text:**<br>{scene.narrative_text}", unsafe_allow_html=True)
                    st.markdown(f"**Characters Present:** `{', '.join(scene.characters_present) if scene.characters_present else 'None'}`")
                    st.markdown(f"**Music Mood:** *{scene.music_mood}*")

                    with st.expander("View Image Prompt (Character Consistency Applied)"):
                        st.code(scene.image_prompt, language="text")

                st.markdown("---")


# =========================================================
# TAB 3: AUDIO & NARRATION (U4)
# =========================================================
with tabs[2]:
    st.markdown("### 🎵 Audio Experience: TTS Narration & Background Music (Requirement U4)")
    st.caption("Generate neural speech narration with Microsoft Edge TTS and ambient background music with Meta MusicGen.")

    if "current_story" not in st.session_state:
        st.warning("⚠️ Please generate or load a story first.")
    else:
        story: StoryBook = st.session_state["current_story"]

        # Action Buttons
        c_tts, c_music = st.columns(2)
        with c_tts:
            if st.button("🎙️ Generate All Scene Narrations (Edge TTS)", type="primary", use_container_width=True):
                audio_gen = AudioGenerator(voice=voice_code)
                with st.spinner(f"Synthesizing narration using voice: {selected_voice}..."):
                    try:
                        audio_gen.generate_all_narrations(story, voice=voice_code, force_regenerate=True)
                        st.success("All scene narrations synthesized successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Narration generation failed: {e}")

        with c_music:
            if st.button("🎶 Generate Instrumental Background Music (MusicGen)", use_container_width=True):
                music_gen = MusicGenerator(hf_token=hf_token_input.strip() or config.HF_TOKEN)
                with st.spinner("Synthesizing ambient background music..."):
                    try:
                        m_path, m_model = music_gen.generate_story_music(story, duration_seconds=25, force_regenerate=True)
                        st.session_state["music_model_used"] = m_model
                        st.success(f"Background music generated using: {m_model}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Music generation failed: {e}")

        st.markdown("---")

        # Background Music Player
        music_file = get_story_music_path(story.title)
        if music_file.exists():
            st.markdown(f"#### 🎵 Story Theme Music ({st.session_state.get('music_model_used', 'Harmonic Ambient')})")
            st.audio(str(music_file))
            st.markdown("---")

        # Scene-by-Scene Audio Players
        st.markdown("#### 🎧 Scene Narration Audio Clips")
        for scene in story.scenes:
            audio_path = get_scene_audio_path(story.title, scene.scene_number)
            img_path = get_scene_image_path(story.title, scene.scene_number)

            col_a_img, col_a_play = st.columns([1, 2.5], gap="medium")
            with col_a_img:
                if img_path.exists():
                    st.image(str(img_path), caption=f"Scene {scene.scene_number}", use_container_width=True)
                else:
                    st.caption(f"Scene {scene.scene_number}")

            with col_a_play:
                st.markdown(f"**Scene {scene.scene_number}: {scene.title}**")
                st.markdown(f"*{scene.audio_script or scene.narrative_text}*")

                if audio_path.exists():
                    st.audio(str(audio_path))
                else:
                    st.caption("🎙️ Narration audio not generated yet.")

                if st.button(f"🔄 Voicing Scene {scene.scene_number}", key=f"voice_sc_{scene.scene_number}"):
                    audio_gen = AudioGenerator(voice=voice_code)
                    with st.spinner(f"Voicing Scene {scene.scene_number}..."):
                        try:
                            audio_gen.generate_scene_narration(scene, story.title, voice=voice_code, force_regenerate=True)
                            st.success(f"Scene {scene.scene_number} audio ready!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to generate audio: {e}")

            st.markdown("---")


# =========================================================
# TAB 4: VERIFICATION & SAFETY (U3 & U5)
# =========================================================
with tabs[3]:
    st.markdown("### 🛡️ BLIP Image Captioning & Narrative Verification (Requirement U3)")
    st.caption("Salesforce BLIP inspects each generated image and evaluates visual-semantic alignment against the story.")

    if "current_story" not in st.session_state:
        st.warning("⚠️ Please generate or load a story first.")
    else:
        story: StoryBook = st.session_state["current_story"]

        scenes_with_images = [
            s for s in story.scenes if get_scene_image_path(story.title, s.scene_number).exists()
        ]

        if not scenes_with_images:
            st.warning("⚠️ No scene illustrations found. Please generate illustrations in the 'Illustrations' tab first.")
        else:
            if "verification_results" not in st.session_state:
                st.session_state["verification_results"] = {}

            if st.button("🔍 Run Salesforce BLIP Verification on Generated Illustrations", type="primary"):
                verifier = BLIPVerifier(
                    hf_token=hf_token_input.strip() or config.HF_TOKEN,
                    gemini_api_key=api_key_input.strip() or config.GEMINI_API_KEY
                )
                with st.spinner("🤖 Inspecting illustrations with Salesforce BLIP and calculating alignment scores..."):
                    for sc in scenes_with_images:
                        img_path = get_scene_image_path(story.title, sc.scene_number)
                        res = verifier.verify_scene_image(
                            scene_number=sc.scene_number,
                            image_path=img_path,
                            intended_text=sc.narrative_text,
                            image_prompt=sc.image_prompt,
                            characters_expected=sc.characters_present
                        )
                        st.session_state["verification_results"][sc.scene_number] = res
                    st.success("BLIP verification complete!")

            v_results = st.session_state.get("verification_results", {})
            if v_results:
                total_verified = sum(1 for r in v_results.values() if r["status"] == "VERIFIED")
                total_flagged = sum(1 for r in v_results.values() if r["status"] == "FLAGGED")
                avg_score = int(sum(r["similarity_score"] for r in v_results.values()) / max(len(v_results), 1))

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Scenes Inspected", len(v_results))
                m2.metric("Verified (Match)", total_verified)
                m3.metric("Flagged (Mismatch)", total_flagged)
                m4.metric("Avg Alignment Score", f"{avg_score}%")

                st.markdown("---")

                for scene in story.scenes:
                    if scene.scene_number in v_results:
                        res = v_results[scene.scene_number]
                        img_path = get_scene_image_path(story.title, scene.scene_number)

                        with st.container():
                            col_thumb, col_details = st.columns([1, 2.5], gap="medium")
                            with col_thumb:
                                if img_path.exists():
                                    st.image(str(img_path), caption=f"Scene {scene.scene_number}", use_container_width=True)

                            with col_details:
                                status_class = "status-verified" if res["status"] == "VERIFIED" else "status-flagged"
                                st.markdown(f"""
                                <h4>Scene {scene.scene_number}: {scene.title}</h4>
                                <span class="{status_class}">Status: {res['status']} ({res['similarity_score']}% Match)</span>
                                """, unsafe_allow_html=True)

                                st.markdown(f"**Intended Scene Narrative:**<br>*{scene.narrative_text}*", unsafe_allow_html=True)
                                st.markdown(f"**BLIP Generated Caption:**<br>`{res['blip_caption']}`", unsafe_allow_html=True)
                                st.caption(f"Inspection Model: *{res['model_used']}*")

                                if res["matched_tokens"]:
                                    st.markdown(f"**Matched Visual Elements:** `{', '.join(res['matched_tokens'])}`")
                                if res["matched_characters"]:
                                    st.markdown(f"**Characters Verified:** `{', '.join(res['matched_characters'])}`")

                                st.info(res["recommendation"])

                                if res["status"] == "FLAGGED":
                                    if st.button(f"🔄 Regenerate Scene {scene.scene_number} Illustration", key=f"fix_scene_{scene.scene_number}"):
                                        img_gen = ImageGenerator(hf_token=hf_token_input.strip() or config.HF_TOKEN)
                                        import random
                                        img_gen.generate_scene_image(
                                            scene=scene,
                                            story_title=story.title,
                                            engine=image_engine,
                                            force_regenerate=True,
                                            seed=random.randint(1000, 999999)
                                        )
                                        st.session_state["verification_results"].pop(scene.scene_number, None)
                                        st.rerun()

                            st.markdown("---")

        # ---------------------------------------------------------
        # SECTION 2: CHILD SAFETY FILTER (Requirement U5)
        # ---------------------------------------------------------
        st.markdown("---")
        st.markdown("### 🛡️ Child Safety & Content Filtering (Requirement U5)")
        st.caption("Multi-layer content guardrail combining lexical screening and LLM Safety Guardian evaluation.")

        c_safe_btn, c_safe_space = st.columns([1, 2])
        with c_safe_btn:
            if st.button("🛡️ Run Child Safety Audit", type="primary", use_container_width=True):
                safety_filter = ChildSafetyFilter(api_key=api_key_input.strip() or config.GEMINI_API_KEY)
                with st.spinner("Auditing story content for child safety and age-appropriateness..."):
                    try:
                        s_report = safety_filter.evaluate_story_safety(story)
                        st.session_state["safety_report"] = s_report
                        st.success("Child safety evaluation completed!")
                    except Exception as e:
                        st.error(f"Safety evaluation failed: {e}")

        s_report: SafetyReport = st.session_state.get("safety_report")
        if s_report:
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("Safety Score", f"{s_report.safety_score}%")
            col_s2.metric("Rating", s_report.safety_rating)
            col_s3.metric("Status", "✅ APPROVED" if s_report.is_safe else "⚠️ REVIEW REQUIRED")

            safe_box_color = "#ecfdf5" if s_report.is_safe else "#fff1f2"
            safe_border = "#a7f3d0" if s_report.is_safe else "#fecdd3"
            st.markdown(f"""
            <div style="background: {safe_box_color}; border: 1px solid {safe_border}; border-radius: 12px; padding: 1.2rem; margin-top: 1rem;">
                <p><strong>Evaluation Summary:</strong> {s_report.explanation}</p>
                <p><strong>Guidance / Advice:</strong> {s_report.mitigation_advice}</p>
                {f"<p><strong>Flagged Categories:</strong> {', '.join(s_report.flagged_categories)}</p>" if s_report.flagged_categories else ""}
            </div>
            """, unsafe_allow_html=True)

        # ---------------------------------------------------------
        # SECTION 3: STORY ORIGINALITY CHECKER (Requirement U5)
        # ---------------------------------------------------------
        st.markdown("---")
        st.markdown("### ✨ Story Originality & Uniqueness Audit (Requirement U5)")
        st.caption("Algorithmic corpus comparison against classic tales and LLM semantic novelty analysis.")

        c_orig_btn, c_orig_space = st.columns([1, 2])
        with c_orig_btn:
            if st.button("✨ Run Originality & Uniqueness Audit", type="primary", use_container_width=True):
                orig_checker = OriginalityChecker(api_key=api_key_input.strip() or config.GEMINI_API_KEY)
                with st.spinner("Screening against classic fairy tale corpus and evaluating creative novelty..."):
                    try:
                        o_report = orig_checker.evaluate_story_originality(story)
                        st.session_state["originality_report"] = o_report
                        st.success("Originality audit completed!")
                    except Exception as e:
                        st.error(f"Originality audit failed: {e}")

        o_report: OriginalityReport = st.session_state.get("originality_report")
        if o_report:
            col_o1, col_o2, col_o3 = st.columns(3)
            col_o1.metric("Originality Score", f"{o_report.originality_score}%")
            col_o2.metric("Originality Tier", o_report.status)
            col_o3.metric("Closest Classic Tale", f"{o_report.closest_archetype} ({o_report.similarity_percentage}% match)")

            st.markdown(f"""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.2rem; margin-top: 1rem;">
                <p><strong>Literature Analysis:</strong> {o_report.analysis}</p>
                <strong>Unique Highlights & Creative Twists:</strong>
                <ul>
                    {"".join([f"<li>{h}</li>" for h in o_report.novelty_highlights])}
                </ul>
            </div>
            """, unsafe_allow_html=True)



# =========================================================
# TAB 5: EXPORT & DOWNLOAD (U4)
# =========================================================
with tabs[4]:
    st.markdown("### 📦 Multi-Format Export: Illustrated PDF & MP4 Video (Requirement U4)")
    st.caption("Generate publication-ready illustrated PDF storybooks and synchronized MP4 audio-video presentations.")

    if "current_story" not in st.session_state:
        st.warning("⚠️ Please generate or load a story first.")
    else:
        story: StoryBook = st.session_state["current_story"]

        c_pdf_col, c_video_col = st.columns(2, gap="large")

        # ---------------- PDF EXPORT ----------------
        with c_pdf_col:
            st.markdown("""
            <div class="export-box">
                <h3>📄 Illustrated PDF Storybook</h3>
                <p>Full-color storybook containing the cover page, character profiles, scene-by-scene high-res illustrations, and story text formatted via ReportLab.</p>
            </div>
            """, unsafe_allow_html=True)

            pdf_path = get_story_pdf_path(story.title)
            pdf_exists = pdf_path.exists()

            if st.button("🎨 Build Illustrated PDF Storybook", type="primary", use_container_width=True):
                with st.spinner("Compiling illustrated PDF storybook with ReportLab..."):
                    try:
                        built_pdf = ExportManager.generate_pdf_storybook(story, force_regenerate=True)
                        st.success("PDF Storybook compiled successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate PDF: {e}")

            if pdf_exists:
                file_size_kb = int(pdf_path.stat().st_size / 1024)
                st.caption(f"Status: **Ready** • File Size: ~{file_size_kb} KB")
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Illustrated PDF",
                        data=f.read(),
                        file_name=f"{sanitize_filename(story.title)}_storybook.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

        # ---------------- MP4 EXPORT ----------------
        with c_video_col:
            st.markdown("""
            <div class="export-box">
                <h3>🎬 Complete MP4 Video</h3>
                <p>Synchronized video combining high-resolution scene illustrations, Edge TTS neural narration, and gentle background music assembled via MoviePy & FFmpeg.</p>
            </div>
            """, unsafe_allow_html=True)

            video_path = get_story_video_path(story.title)
            video_exists = video_path.exists()

            if st.button("🎥 Render Assembled MP4 Storybook Video", type="primary", use_container_width=True):
                music_file = get_story_music_path(story.title)
                bg_music_arg = music_file if music_file.exists() else None

                with st.spinner("Assembling scenes, voice narration, and background music into MP4 (MoviePy)..."):
                    try:
                        built_video = ExportManager.generate_mp4_video(
                            story=story,
                            bg_music_path=bg_music_arg,
                            force_regenerate=True
                        )
                        st.success("MP4 Video successfully rendered!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to render video: {e}")

            if video_exists:
                vid_size_mb = round(video_path.stat().st_size / (1024 * 1024), 2)
                st.caption(f"Status: **Ready** • File Size: ~{vid_size_mb} MB")
                st.video(str(video_path))

                with open(video_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Storybook MP4 Video",
                        data=f.read(),
                        file_name=f"{sanitize_filename(story.title)}_storybook.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
