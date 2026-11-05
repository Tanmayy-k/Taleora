"""
TALEORA — Illustrated Audio Storybook Generator
A consumer-facing generative storytelling experience.
"Every great adventure begins with three little words."
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
    page_title="Taleora — Magical Audio Storybook Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a premium consumer storytelling app
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Quicksand:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Quicksand', sans-serif;
    }

    h1, h2, h3, .brand-font {
        font-family: 'Cinzel', serif !important;
        letter-spacing: 0.5px;
    }

    /* Hero Banner */
    .hero-container {
        background: radial-gradient(circle at 10% 20%, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 3rem 2.8rem;
        border-radius: 20px;
        color: #f8fafc;
        box-shadow: 0 16px 36px -10px rgba(30, 27, 75, 0.45);
        margin-bottom: 2.2rem;
        border: 1px solid rgba(255, 255, 255, 0.15);
        text-align: center;
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        color: #fef08a;
        text-shadow: 0 3px 12px rgba(0,0,0,0.5);
    }

    .hero-headline {
        font-size: 1.35rem;
        font-weight: 600;
        color: #ffffff;
        margin-top: 0.8rem;
        font-style: italic;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: #e0e7ff;
        margin-top: 0.5rem;
        max-width: 750px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }

    /* Card styling */
    .storybook-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.8rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.04);
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .storybook-card:hover {
        box-shadow: 0 12px 30px rgba(0,0,0,0.07);
    }

    /* Example Story Showcase Card */
    .showcase-card {
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #cbd5e1;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .showcase-badge {
        display: inline-block;
        padding: 0.3rem 0.75rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
        margin-bottom: 0.8rem;
    }

    .badge-fantasy {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }

    .badge-scifi {
        background: #e0e7ff;
        color: #3730a3;
        border: 1px solid #c7d2fe;
    }

    .keyword-chip {
        display: inline-block;
        background: #f1f5f9;
        color: #475569;
        padding: 0.25rem 0.65rem;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
        border: 1px solid #e2e8f0;
    }

    .page-turner {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.75rem 1.2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }

    .verification-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.4rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }

    .badge-verified {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }

    .badge-flagged {
        background: #fff1f2;
        color: #9f1239;
        border: 1px solid #fecdd3;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }

    .export-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.8rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.03);
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Path Helpers
# ---------------------------------------------------------
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
# Sidebar: Reader & Library Settings (No API Keys / Tech Controls)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ✨ TALEORA")
    st.caption("AI-Powered Illustrated Storybook Generator")
    st.markdown("---")

    # Current Story Overview
    current_story: StoryBook = st.session_state.get("current_story")
    if current_story:
        st.markdown("#### 📖 Active Storybook")
        st.markdown(f"**{current_story.title}**")
        st.caption(f"Genre: {current_story.genre} • {current_story.target_audience}")
        st.markdown("---")

    # Reader Voice Selection
    st.markdown("#### 🎙️ Storyteller Voice")
    voice_labels = {
        "Female - Warm Storyteller (Ana)": "en-US-AnaNeural",
        "Male - Friendly & Upbeat (Guy)": "en-US-GuyNeural",
        "Female - Expressive (Jenny)": "en-US-JennyNeural",
        "Male - Wise Narrator (Christopher)": "en-US-ChristopherNeural",
        "Female - British Gentle (Sonia)": "en-GB-SoniaNeural",
        "Male - British Storyteller (Ryan)": "en-GB-RyanNeural"
    }
    selected_voice_label = st.selectbox(
        "Narrator Personality",
        options=list(voice_labels.keys()),
        index=0,
        help="Choose the reading style for spoken story narration."
    )
    active_voice = voice_labels[selected_voice_label]

    st.markdown("---")

    # Library of Stories (Saved and Featured)
    st.markdown("#### 📚 Storybook Library")
    saved_files = StoryGenerator.list_saved_stories()
    if saved_files:
        story_options = {}
        for f in saved_files:
            clean_display = f.stem
            # Remove timestamp prefix if present for clean display
            if len(clean_display) > 16 and clean_display[:8].isdigit() and clean_display[8] == "_":
                clean_display = clean_display[16:].replace("_", " ")
            else:
                clean_display = clean_display.replace("_", " ")
            story_options[clean_display] = f

        selected_story_name = st.selectbox(
            "Open from library",
            options=["-- Select a storybook --"] + list(story_options.keys())
        )
        if selected_story_name != "-- Select a storybook --":
            if st.button("Open Storybook", use_container_width=True):
                try:
                    loaded = StoryGenerator.load_story_from_disk(story_options[selected_story_name])
                    st.session_state["current_story"] = loaded
                    st.session_state["current_page"] = 1
                    st.session_state["verification_results"] = {}
                    st.session_state["safety_report"] = None
                    st.session_state["originality_report"] = None
                    st.success(f"Opened '{loaded.title}'!")
                    st.rerun()
                except Exception as e:
                    st.error("Could not load the selected story.")
    else:
        st.info("Your library is empty. Generate or explore a story!")

    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>"
        "Taleora Storybook Studio<br>Crafted for young dreamers everywhere."
        "</div>",
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# Hero Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">✨ TALEORA</div>
    <div class="hero-headline">"Every great adventure begins with three little words."</div>
    <div class="hero-subtitle">
        Enter three creative keywords, choose your world and reader age group, and watch Taleora 
        bring your story to life with custom illustrations, neural narration, background music, 
        and keepsake PDF and video books.
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Main Consumer Navigation Tabs
# ---------------------------------------------------------
main_tabs = st.tabs([
    "🏰 Story Studio",
    "📖 Storybook Reader",
    "🛡️ Story Quality & Safety",
    "📦 Keepsakes & Downloads"
])


# =========================================================
# TAB 1: STORY STUDIO (Creation & Showcase)
# =========================================================
with main_tabs[0]:
    # Section A: Featured Storybook Showcase
    st.markdown("### ✨ Featured Storybooks")
    st.caption("Explore these complete, pre-generated master storybooks with one click.")

    sc_col1, sc_col2 = st.columns(2, gap="medium")

    with sc_col1:
        st.markdown("""
        <div class="showcase-card">
            <div>
                <span class="showcase-badge badge-fantasy">✨ Fantasy • Ages 6-8</span>
                <h4 style="margin: 0 0 0.5rem 0; color: #1e1b4b;">Barnaby & the Whispering Key</h4>
                <p style="color: #475569; font-size: 0.95rem; line-height: 1.5;">
                    A curious little clockwork owl finds a floating brass key that unlocks an attic conservatory 
                    filled with living forgotten stories.
                </p>
                <div style="margin-top: 0.5rem;">
                    <span class="keyword-chip">Clockwork Owl</span>
                    <span class="keyword-chip">Floating Key</span>
                    <span class="keyword-chip">Secret Attic Library</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📖 Read & Listen to Barnaby's Story", key="load_barnaby_btn", use_container_width=True):
            for f in saved_files:
                if "Barnaby" in f.name:
                    st.session_state["current_story"] = StoryGenerator.load_story_from_disk(f)
                    st.session_state["current_page"] = 1
                    st.session_state["verification_results"] = {}
                    st.success("Loaded 'Barnaby and the Whispering Key'!")
                    st.rerun()

    with sc_col2:
        st.markdown("""
        <div class="showcase-card">
            <div>
                <span class="showcase-badge badge-scifi">🚀 Sci-Fi • Ages 9-12</span>
                <h4 style="margin: 0 0 0.5rem 0; color: #1e1b4b;">Astro & the Singing Asteroid</h4>
                <p style="color: #475569; font-size: 0.95rem; line-height: 1.5;">
                    An inventive pocket explorer robot follows a starlight compass into deep space to repair 
                    a musical asteroid that guides lost travelers.
                </p>
                <div style="margin-top: 0.5rem;">
                    <span class="keyword-chip">Pocket Robot</span>
                    <span class="keyword-chip">Starlight Compass</span>
                    <span class="keyword-chip">Singing Asteroid</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Read & Listen to Astro's Story", key="load_astro_btn", use_container_width=True):
            for f in saved_files:
                if "Astro" in f.name:
                    st.session_state["current_story"] = StoryGenerator.load_story_from_disk(f)
                    st.session_state["current_page"] = 1
                    st.session_state["verification_results"] = {}
                    st.success("Loaded 'Astro and the Singing Asteroid'!")
                    st.rerun()

    st.markdown("---")

    # Section B: Create a Brand New Story
    st.markdown("### ✍️ Create a Brand New Storybook")
    st.caption("Tell us three inspiring ideas, and our storytelling AI will weave your original book.")

    col_kw, col_theme = st.columns([1.1, 0.9], gap="large")

    with col_kw:
        st.markdown("##### 1. Your Three Words")
        
        # Inspiration presets
        p1, p2, p3 = st.columns(3)
        if p1.button("🌲 Enchanted Woods"):
            st.session_state["in_kw1"] = "Glowing Acorn"
            st.session_state["in_kw2"] = "Talking Fox"
            st.session_state["in_kw3"] = "Crystal Stream"
        if p2.button("🌌 Star Cruiser"):
            st.session_state["in_kw1"] = "Pocket Robot"
            st.session_state["in_kw2"] = "Starlight Compass"
            st.session_state["in_kw3"] = "Singing Asteroid"
        if p3.button("🐬 Coral Kingdom"):
            st.session_state["in_kw1"] = "Golden Shell"
            st.session_state["in_kw2"] = "Friendly Dolphin"
            st.session_state["in_kw3"] = "Sunken Castle"

        user_kw1 = st.text_input("First Word", value=st.session_state.get("in_kw1", "Clockwork Owl"), placeholder="e.g. Clockwork Owl")
        user_kw2 = st.text_input("Second Word", value=st.session_state.get("in_kw2", "Floating Key"), placeholder="e.g. Floating Key")
        user_kw3 = st.text_input("Third Word", value=st.session_state.get("in_kw3", "Secret Attic Library"), placeholder="e.g. Secret Attic Library")

    with col_theme:
        st.markdown("##### 2. Story World & Reader Age")
        selected_genre = st.selectbox(
            "Story World / Genre",
            options=list(config.GENRES.keys()),
            index=0,
            help="Chooses the literary atmosphere, illustrations style, and emotional tone."
        )
        genre_info = config.GENRES[selected_genre]
        st.caption(f"✨ **Atmosphere:** {genre_info['description']}")

        selected_audience = st.selectbox(
            "Reader Age Group",
            options=list(config.AUDIENCES.keys()),
            index=1,
            help="Tunes the vocabulary, sentence pacing, and length to the reader."
        )
        aud_info = config.AUDIENCES[selected_audience]
        st.caption(f"🎯 **Reading Level:** {aud_info['complexity']} (~{aud_info['scenes_count']} illustrated chapters)")

    special_wishes = st.text_input(
        "Special Wishes / Theme (Optional)",
        placeholder="e.g. A story about sharing, bravery, and caring for others",
        value=""
    )

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # Big Action Button
    generate_story_click = st.button("✨ Generate My Storybook", type="primary", use_container_width=True)

    if generate_story_click:
        raw_kws = [user_kw1, user_kw2, user_kw3]
        valid, val_msg, clean_kws = validate_keywords(raw_kws)

        if not valid:
            st.error(f"Please check your keywords: {val_msg}")
        else:
            progress_placeholder = st.empty()
            with progress_placeholder.container():
                st.info("🧙‍♂️ Gathering imagination, writing chapters, and crafting characters...")
                progress_bar = st.progress(0.15)

                try:
                    # 1. Generate Story Structure
                    generator = StoryGenerator()
                    new_story = generator.generate_story(
                        keywords=clean_kws,
                        genre=selected_genre,
                        audience=selected_audience,
                        extra_notes=special_wishes
                    )
                    progress_bar.progress(0.40)
                    st.info(f"🎨 Story written! Now painting illustrations for '{new_story.title}'...")

                    # 2. Generate Illustrations
                    img_gen = ImageGenerator()
                    img_gen.generate_all_scenes(story=new_story, engine="pollinations", force_regenerate=True)
                    progress_bar.progress(0.65)
                    st.info("🎙️ Voicing spoken narration and composing music...")

                    # 3. Generate Audio & Music
                    audio_gen = AudioGenerator(voice=active_voice)
                    audio_gen.generate_all_narrations(story=new_story, voice=active_voice, force_regenerate=True)
                    music_gen = MusicGenerator()
                    music_gen.generate_story_music(story=new_story, duration_seconds=25, force_regenerate=True)
                    progress_bar.progress(0.85)
                    st.info("📦 Assembling illustrated PDF and video book...")

                    # 4. Generate PDF & MP4
                    ExportManager.generate_pdf_storybook(story=new_story, force_regenerate=True)
                    music_file = get_story_music_path(new_story.title)
                    ExportManager.generate_mp4_video(
                        story=new_story,
                        bg_music_path=music_file if music_file.exists() else None,
                        force_regenerate=True
                    )
                    progress_bar.progress(1.0)

                    # Set session state
                    st.session_state["current_story"] = new_story
                    st.session_state["current_page"] = 1
                    st.session_state["verification_results"] = {}
                    st.session_state["safety_report"] = None
                    st.session_state["originality_report"] = None

                    st.balloons()
                    st.success(f"🎉 Your complete storybook **{new_story.title}** is ready! Visit the 'Storybook Reader' tab to enjoy it.")

                except Exception as e:
                    progress_placeholder.empty()
                    err_message = str(e)
                    st.error(
                        f"We couldn't generate a new story right now: {err_message}\n\n"
                        "💡 **Tip:** You can immediately explore and enjoy our pre-generated featured stories above!"
                    )


# =========================================================
# TAB 2: STORYBOOK READER (Page-by-Page Interactive Book)
# =========================================================
with main_tabs[1]:
    if not current_story:
        st.info("👈 Please select or generate a story in the **Story Studio** to begin reading.")
    else:
        st.markdown(f"## 📖 {current_story.title}")
        st.markdown(f"*{current_story.logline}*")

        # Cast of Characters Section
        with st.expander("👥 Meet the Cast of Characters", expanded=False):
            char_cols = st.columns(min(len(current_story.character_bible), 3) or 1)
            for idx, char in enumerate(current_story.character_bible):
                with char_cols[idx % len(char_cols)]:
                    st.markdown(f"""
                    <div style="background: #f8fafc; border-radius: 12px; padding: 1.2rem; border: 1px solid #e2e8f0;">
                        <h4 style="margin: 0; color: #1e1b4b;">👤 {char.name}</h4>
                        <span style="color: #4338ca; font-weight: 600; font-size: 0.85rem;">{char.role}</span>
                        <p style="margin-top: 0.5rem; font-size: 0.92rem; color: #334155;">
                            <strong>Appearance:</strong> {char.visual_appearance}<br>
                            <strong>Outfit:</strong> {char.signature_clothing}<br>
                            <strong>Special Item:</strong> {char.distinct_accessories}<br>
                            <em>"{char.personality_trait}"</em>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")

        # Interactive Page Navigation
        total_pages = len(current_story.scenes)
        current_page_idx = st.session_state.get("current_page", 1)
        if current_page_idx < 1 or current_page_idx > total_pages:
            current_page_idx = 1
            st.session_state["current_page"] = 1

        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        with nav_col1:
            if st.button("⬅️ Previous Chapter", disabled=(current_page_idx <= 1), use_container_width=True):
                st.session_state["current_page"] = max(current_page_idx - 1, 1)
                st.rerun()

        with nav_col2:
            st.markdown(
                f"<div style='text-align: center; font-weight: 700; font-size: 1.1rem; color: #1e1b4b; padding-top: 0.4rem;'>"
                f"Chapter {current_page_idx} of {total_pages}"
                f"</div>",
                unsafe_allow_html=True
            )

        with nav_col3:
            if st.button("Next Chapter ➡️", disabled=(current_page_idx >= total_pages), use_container_width=True):
                st.session_state["current_page"] = min(current_page_idx + 1, total_pages)
                st.rerun()

        # Display Current Page
        current_scene = current_story.scenes[current_page_idx - 1]
        scene_img_path = get_scene_image_path(current_story.title, current_scene.scene_number)
        scene_audio_path = get_scene_audio_path(current_story.title, current_scene.scene_number)

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        page_col_art, page_col_text = st.columns([1, 1.2], gap="large")

        with page_col_art:
            if scene_img_path.exists():
                st.image(str(scene_img_path), caption=f"Chapter {current_scene.scene_number} Illustration", use_container_width=True)
            else:
                st.markdown("""
                <div style="background: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 14px; height: 350px; display: flex; align-items: center; justify-content: center; color: #64748b; font-weight: 600;">
                    🎨 Illustration will appear here
                </div>
                """, unsafe_allow_html=True)

            # Redraw page illustration button
            if st.button(f"🎨 Redraw This Illustration", key=f"redraw_p_{current_scene.scene_number}", use_container_width=True):
                with st.spinner("Creating a fresh illustration for this chapter..."):
                    img_gen = ImageGenerator()
                    import random
                    img_gen.generate_scene_image(
                        scene=current_scene,
                        story_title=current_story.title,
                        engine="pollinations",
                        force_regenerate=True,
                        seed=random.randint(1000, 999999)
                    )
                    st.success("Illustration updated!")
                    st.rerun()

        with page_col_text:
            st.markdown(f"### {current_scene.title}")
            st.markdown(
                f"<div style='font-size: 1.2rem; line-height: 1.8; color: #1e293b; background: #fafafa; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #6366f1; margin: 1rem 0;'>"
                f"{current_scene.narrative_text}"
                f"</div>",
                unsafe_allow_html=True
            )

            # Audio Narration Player
            st.markdown("##### 🎙️ Spoken Narration")
            if scene_audio_path.exists():
                st.audio(str(scene_audio_path))
            else:
                if st.button("🎙️ Voice This Chapter Now", key=f"voice_btn_{current_scene.scene_number}"):
                    audio_gen = AudioGenerator(voice=active_voice)
                    audio_gen.generate_scene_narration(current_scene, current_story.title, voice=active_voice, force_regenerate=True)
                    st.rerun()

            # Background Music Player
            bg_music_file = get_story_music_path(current_story.title)
            if bg_music_file.exists():
                st.markdown("##### 🎶 Story Theme Ambience")
                st.audio(str(bg_music_file))

        # Moral / Takeaway at end of story
        if current_page_idx == total_pages:
            st.markdown("---")
            st.markdown(f"""
            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 14px; padding: 1.5rem; text-align: center; margin-top: 1.5rem;">
                <h4 style="color: #065f46; margin: 0 0 0.5rem 0;">🌟 The Story's Heartwarming Lesson</h4>
                <p style="font-size: 1.15rem; font-style: italic; color: #047857; margin: 0;">
                    "{current_story.moral_or_takeaway}"
                </p>
            </div>
            """, unsafe_allow_html=True)


# =========================================================
# TAB 3: STORY QUALITY & SAFETY (Verification)
# =========================================================
with main_tabs[2]:
    if not current_story:
        st.info("👈 Please select or open a storybook first.")
    else:
        st.markdown("### 🛡️ Storybook Quality & Child Safety")
        st.caption("We review every story to ensure age-appropriate wonder, visual accuracy, and creative originality.")

        v_col1, v_col2, v_col3 = st.columns(3, gap="medium")

        # 1. Child Safety Shield
        with v_col1:
            st.markdown("""
            <div class="verification-card">
                <span class="badge-verified">🛡️ Child Safety Shield</span>
                <h4 style="margin: 0.8rem 0 0.4rem 0;">100% Kid Safe</h4>
                <p style="color: #475569; font-size: 0.9rem; line-height: 1.5;">
                    Audited for age-appropriate language, wholesome themes, positive moral reinforcement, and zero violence.
                </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Run Safety Audit", key="run_safety_btn", use_container_width=True):
                s_filter = ChildSafetyFilter()
                with st.spinner("Reviewing story text..."):
                    rep = s_filter.evaluate_story_safety(current_story)
                    st.session_state["safety_report"] = rep
                    st.success("Safety audit completed!")

        # 2. Visual Alignment Check
        with v_col2:
            st.markdown("""
            <div class="verification-card">
                <span class="badge-verified">🎨 Visual Accuracy</span>
                <h4 style="margin: 0.8rem 0 0.4rem 0;">Art Quality Review</h4>
                <p style="color: #475569; font-size: 0.9rem; line-height: 1.5;">
                    Visual AI inspects every scene illustration to confirm it accurately matches the story and character details.
                </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Inspect Illustrations", key="run_art_btn", use_container_width=True):
                verifier = BLIPVerifier()
                with st.spinner("Reviewing scene illustrations..."):
                    for sc in current_story.scenes:
                        img_p = get_scene_image_path(current_story.title, sc.scene_number)
                        if img_p.exists():
                            res = verifier.verify_scene_image(
                                sc.scene_number, img_p, sc.narrative_text, sc.image_prompt, sc.characters_present
                            )
                            if "verification_results" not in st.session_state:
                                st.session_state["verification_results"] = {}
                            st.session_state["verification_results"][sc.scene_number] = res
                    st.success("Visual review complete!")

        # 3. Originality & Freshness
        with v_col3:
            st.markdown("""
            <div class="verification-card">
                <span class="badge-verified">✨ Story Originality</span>
                <h4 style="margin: 0.8rem 0 0.4rem 0;">Original Concept</h4>
                <p style="color: #475569; font-size: 0.9rem; line-height: 1.5;">
                    Compared against classic fairy tale archetypes to ensure a fresh, imaginative narrative.
                </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Check Originality", key="run_orig_btn", use_container_width=True):
                o_checker = OriginalityChecker()
                with st.spinner("Checking classic fairy tale library..."):
                    o_rep = o_checker.evaluate_story_originality(current_story)
                    st.session_state["originality_report"] = o_rep
                    st.success("Originality check complete!")

        st.markdown("---")

        # Display Detailed Verification Findings if Available
        s_rep: SafetyReport = st.session_state.get("safety_report")
        if s_rep:
            st.markdown("#### 🛡️ Safety Audit Summary")
            st.markdown(f"**Safety Score:** `{s_rep.safety_score}%` — **{s_rep.safety_rating}**")
            st.info(s_rep.explanation)

        o_rep: OriginalityReport = st.session_state.get("originality_report")
        if o_rep:
            st.markdown("#### ✨ Originality Analysis")
            st.markdown(f"**Originality Rating:** `{o_rep.originality_score}%` — **{o_rep.status}**")
            st.caption(f"Closest classic archetype comparison: *{o_rep.closest_archetype}* ({o_rep.similarity_percentage}% overlap)")
            st.markdown(f"*{o_rep.analysis}*")

        v_res_map = st.session_state.get("verification_results", {})
        if v_res_map:
            st.markdown("#### 🎨 Scene-by-Scene Visual Inspection")
            for sc in current_story.scenes:
                if sc.scene_number in v_res_map:
                    sc_res = v_res_map[sc.scene_number]
                    badge_class = "badge-verified" if sc_res["status"] == "VERIFIED" else "badge-flagged"
                    with st.container():
                        st.markdown(f"""
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; margin-bottom: 0.8rem;">
                            <strong>Chapter {sc.scene_number}: {sc.title}</strong> — 
                            <span class="{badge_class}">{sc_res['status']}</span><br>
                            <span style="font-size: 0.9rem; color: #475569;">Visual Content Seen: <em>"{sc_res['blip_caption']}"</em></span>
                        </div>
                        """, unsafe_allow_html=True)


# =========================================================
# TAB 4: KEEPSAKES & DOWNLOADS (PDF & Video)
# =========================================================
with main_tabs[3]:
    if not current_story:
        st.info("👈 Please select or open a storybook first.")
    else:
        st.markdown("### 📦 Keepsakes & Downloads")
        st.caption("Take your storybook anywhere! Download a printable illustrated book or an audio-narrated video.")

        d_col1, d_col2 = st.columns(2, gap="large")

        # ---------------- PDF Keepsake ----------------
        with d_col1:
            st.markdown("""
            <div class="export-box">
                <span style="font-size: 3rem;">📄</span>
                <h3 style="margin: 0.8rem 0 0.4rem 0;">Illustrated PDF Storybook</h3>
                <p style="color: #475569; font-size: 0.95rem; line-height: 1.5;">
                    A beautifully typeset storybook containing the cover page, character cast profiles, 
                    full-color chapter illustrations, and story text.
                </p>
            </div>
            """, unsafe_allow_html=True)

            pdf_file = get_story_pdf_path(current_story.title)
            if not pdf_file.exists():
                if st.button("📄 Generate Storybook PDF", key="gen_pdf_btn", use_container_width=True):
                    with st.spinner("Typesetting illustrated PDF storybook..."):
                        ExportManager.generate_pdf_storybook(current_story, force_regenerate=True)
                        st.success("PDF ready!")
                        st.rerun()
            else:
                pdf_size_mb = round(pdf_file.stat().st_size / (1024 * 1024), 2)
                st.caption(f"Status: **Ready to Read** • File Size: ~{pdf_size_mb} MB")
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        label="📥 Download Illustrated PDF Storybook",
                        data=f.read(),
                        file_name=f"{sanitize_filename(current_story.title)}_storybook.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )

        # ---------------- MP4 Keepsake ----------------
        with d_col2:
            st.markdown("""
            <div class="export-box">
                <span style="font-size: 3rem;">🎬</span>
                <h3 style="margin: 0.8rem 0 0.4rem 0;">Complete Narrated MP4 Video</h3>
                <p style="color: #475569; font-size: 0.95rem; line-height: 1.5;">
                    A full video presentation synchronizing every scene illustration with spoken voice narration 
                    and gentle background music.
                </p>
            </div>
            """, unsafe_allow_html=True)

            video_file = get_story_video_path(current_story.title)
            if not video_file.exists():
                if st.button("🎬 Render Storybook Video", key="gen_vid_btn", use_container_width=True):
                    with st.spinner("Assembling illustrations, narration audio, and music into video..."):
                        bg_m = get_story_music_path(current_story.title)
                        ExportManager.generate_mp4_video(
                            current_story,
                            bg_music_path=bg_m if bg_m.exists() else None,
                            force_regenerate=True
                        )
                        st.success("Video ready!")
                        st.rerun()
            else:
                vid_size_mb = round(video_file.stat().st_size / (1024 * 1024), 2)
                st.caption(f"Status: **Ready to Watch** • File Size: ~{vid_size_mb} MB")
                st.video(str(video_file))

                with open(video_file, "rb") as f:
                    st.download_button(
                        label="📥 Download Storybook MP4 Video",
                        data=f.read(),
                        file_name=f"{sanitize_filename(current_story.title)}_storybook.mp4",
                        mime="video/mp4",
                        type="primary",
                        use_container_width=True
                    )
