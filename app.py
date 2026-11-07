"""
TALEORA — Illustrated Audio Storybook Generator
A minimal, premium generative storytelling experience.
"Turn three words into a story."
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
# Page Configuration & Clean Premium Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Taleora — Illustrated Audio Storybooks",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal, elegant styling for a polished consumer reading experience
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Quicksand:wght@400;500;600;700&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');

    html, body, [class*="css"] {
        font-family: 'Quicksand', sans-serif;
    }

    h1, h2, h3, .brand-font {
        font-family: 'Cinzel', serif !important;
        letter-spacing: 0.5px;
    }

    /* Minimal Hero */
    .hero-container {
        text-align: center;
        padding: 2.2rem 1.5rem 1.5rem 1.5rem;
        margin-bottom: 1.5rem;
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(135deg, #312e81 0%, #4f46e5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-headline {
        font-size: 1.25rem;
        font-weight: 600;
        color: #475569;
        margin-top: 0.4rem;
    }

    /* Centerpiece Illustration Frame */
    .illustration-frame {
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.08);
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }

    /* Story Narrative Typography */
    .story-prose {
        font-family: 'Lora', Georgia, serif;
        font-size: 1.28rem;
        line-height: 1.9;
        color: #1e293b;
        background: #fdfdfd;
        border-left: 4px solid #6366f1;
        padding: 1.5rem 1.8rem;
        border-radius: 12px;
        margin: 1.2rem 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.02);
    }

    /* Minimal Download Cards */
    .download-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.8rem 1.5rem;
        text-align: center;
        box-shadow: 0 4px 18px rgba(0,0,0,0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .download-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    }

    /* Example Story Showcase Card */
    .showcase-pill-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }

    .badge-verified {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 0.25rem 0.65rem;
        border-radius: 14px;
        font-weight: 700;
        font-size: 0.8rem;
    }

    .badge-flagged {
        background: #fff1f2;
        color: #9f1239;
        border: 1px solid #fecdd3;
        padding: 0.25rem 0.65rem;
        border-radius: 14px;
        font-weight: 700;
        font-size: 0.8rem;
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
# Minimal Sidebar (Voice Selection & Library)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ✨ Taleora")
    st.caption("Turn three words into a story.")
    st.markdown("---")

    current_story: StoryBook = st.session_state.get("current_story")
    if current_story:
        st.markdown(f"**📖 Current Story:** {current_story.title}")
        st.caption(f"{current_story.genre} • {current_story.target_audience}")
        st.markdown("---")

    st.markdown("##### 🎙️ Storyteller Voice")
    voice_labels = {
        "Female - Warm Storyteller (Ana)": "en-US-AnaNeural",
        "Male - Friendly & Upbeat (Guy)": "en-US-GuyNeural",
        "Female - Expressive (Jenny)": "en-US-JennyNeural",
        "Male - Wise Narrator (Christopher)": "en-US-ChristopherNeural",
        "Female - Gentle British (Sonia)": "en-GB-SoniaNeural",
        "Male - British Storyteller (Ryan)": "en-GB-RyanNeural"
    }
    selected_voice_label = st.selectbox(
        "Narrator",
        options=list(voice_labels.keys()),
        index=0,
        label_visibility="collapsed"
    )
    active_voice = voice_labels[selected_voice_label]

    st.markdown("---")
    st.markdown("##### 📚 Saved Storybooks")
    saved_files = StoryGenerator.list_saved_stories()
    if saved_files:
        story_options = {}
        for f in saved_files:
            clean_display = f.stem
            if len(clean_display) > 16 and clean_display[:8].isdigit() and clean_display[8] == "_":
                clean_display = clean_display[16:].replace("_", " ")
            else:
                clean_display = clean_display.replace("_", " ")
            story_options[clean_display] = f

        selected_story_name = st.selectbox(
            "Library",
            options=["-- Open a saved book --"] + list(story_options.keys()),
            label_visibility="collapsed"
        )
        if selected_story_name != "-- Open a saved book --":
            if st.button("Open Book", use_container_width=True):
                try:
                    loaded = StoryGenerator.load_story_from_disk(story_options[selected_story_name])
                    st.session_state["current_story"] = loaded
                    st.session_state["current_page"] = 1
                    st.session_state["verification_results"] = {}
                    st.session_state["safety_report"] = None
                    st.session_state["originality_report"] = None
                    st.success(f"Opened '{loaded.title}'!")
                    st.rerun()
                except Exception:
                    st.error("Could not load the selected story.")


# ---------------------------------------------------------
# Clean Branding Header
# ---------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">✨ TALEORA</div>
    <div class="hero-headline">Turn three words into a story.</div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Minimal Navigation (Only 2 Tabs)
# ---------------------------------------------------------
nav_create, nav_read = st.tabs(["✨ Create Story", "📖 My Storybook"])


# =========================================================
# TAB 1: CREATE STORY (STEP 1 — CREATE)
# =========================================================
with nav_create:
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

    # Clickable inspiration presets
    c_p1, c_p2, c_p3 = st.columns(3)
    if c_p1.button("🌲 Try: Enchanted Woods", use_container_width=True):
        st.session_state["kw1"] = "Glowing Acorn"
        st.session_state["kw2"] = "Talking Fox"
        st.session_state["kw3"] = "Crystal Stream"
    if c_p2.button("🌌 Try: Star Cruiser", use_container_width=True):
        st.session_state["kw1"] = "Pocket Robot"
        st.session_state["kw2"] = "Starlight Compass"
        st.session_state["kw3"] = "Singing Asteroid"
    if c_p3.button("🐬 Try: Coral Kingdom", use_container_width=True):
        st.session_state["kw1"] = "Golden Shell"
        st.session_state["kw2"] = "Friendly Dolphin"
        st.session_state["kw3"] = "Sunken Castle"

    # 3 Keyword Inputs
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        kw1 = st.text_input("First Word", value=st.session_state.get("kw1", "Clockwork Owl"), placeholder="First keyword")
    with col_k2:
        kw2 = st.text_input("Second Word", value=st.session_state.get("kw2", "Floating Key"), placeholder="Second keyword")
    with col_k3:
        kw3 = st.text_input("Third Word", value=st.session_state.get("kw3", "Secret Attic Library"), placeholder="Third keyword")

    # Genre and Age Group
    col_g, col_a = st.columns(2)
    with col_g:
        selected_genre = st.selectbox(
            "Genre",
            options=list(config.GENRES.keys()),
            index=0
        )
    with col_a:
        selected_audience = st.selectbox(
            "Age Group",
            options=list(config.AUDIENCES.keys()),
            index=1
        )

    st.markdown("<div style='margin-top: 0.8rem;'></div>", unsafe_allow_html=True)

    # One Prominent Button
    create_button = st.button("✨ Create My Story", type="primary", use_container_width=True)

    if create_button:
        raw_kws = [kw1, kw2, kw3]
        valid, val_msg, clean_kws = validate_keywords(raw_kws)

        if not valid:
            st.error(f"Please provide exactly three keywords: {val_msg}")
        else:
            progress_box = st.empty()
            with progress_box.container():
                p_bar = st.progress(0.15)
                st.info("Writing your original story and establishing characters...")

                try:
                    # 1. Generate Story
                    generator = StoryGenerator()
                    new_story = generator.generate_story(
                        keywords=clean_kws,
                        genre=selected_genre,
                        audience=selected_audience
                    )
                    p_bar.progress(0.40)
                    st.info(f"Painting illustrated storybook pages for '{new_story.title}'...")

                    # 2. Generate Illustrations (1024x1024)
                    img_gen = ImageGenerator()
                    img_gen.generate_all_scenes(story=new_story, engine="pollinations", force_regenerate=True)
                    p_bar.progress(0.70)
                    st.info("Voicing narration and composing background ambience...")

                    # 3. Generate Audio & Music
                    audio_gen = AudioGenerator(voice=active_voice)
                    audio_gen.generate_all_narrations(story=new_story, voice=active_voice, force_regenerate=True)
                    music_gen = MusicGenerator()
                    music_gen.generate_story_music(story=new_story, duration_seconds=25, force_regenerate=True)
                    p_bar.progress(0.85)
                    st.info("Assembling illustrated PDF and video...")

                    # 4. Generate PDF & MP4 Keepsakes
                    ExportManager.generate_pdf_storybook(story=new_story, force_regenerate=True)
                    music_file = get_story_music_path(new_story.title)
                    ExportManager.generate_mp4_video(
                        story=new_story,
                        bg_music_path=music_file if music_file.exists() else None,
                        force_regenerate=True
                    )
                    p_bar.progress(1.0)

                    # Update session state
                    st.session_state["current_story"] = new_story
                    st.session_state["current_page"] = 1
                    st.session_state["verification_results"] = {}
                    st.session_state["safety_report"] = None
                    st.session_state["originality_report"] = None

                    progress_box.empty()
                    st.balloons()
                    st.success(f"🎉 **{new_story.title}** is ready! Click on the **'📖 My Storybook'** tab above to enjoy your story.")

                except Exception as e:
                    progress_box.empty()
                    st.error(f"Could not generate the storybook: {e}")

    st.markdown("---")

    # Example Story Showcase Cards
    st.markdown("##### 🌟 Or Explore a Featured Storybook")
    sc1, sc2 = st.columns(2)

    with sc1:
        st.markdown("""
        <div class="showcase-pill-card">
            <span style="font-size: 0.8rem; font-weight: 700; color: #92400e; background: #fef3c7; padding: 0.2rem 0.6rem; border-radius: 10px;">Fantasy • Ages 6-8</span>
            <h4 style="margin: 0.5rem 0 0.3rem 0; color: #1e1b4b;">Barnaby & the Whispering Key</h4>
            <p style="margin: 0; font-size: 0.92rem; color: #475569;">
                A curious clockwork owl discovers an attic library of living stories.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Read Barnaby's Story", key="load_barnaby_minimal", use_container_width=True):
            for f in saved_files:
                if "Barnaby" in f.name:
                    st.session_state["current_story"] = StoryGenerator.load_story_from_disk(f)
                    st.session_state["current_page"] = 1
                    st.session_state["verification_results"] = {}
                    st.success("Loaded 'Barnaby and the Whispering Key'! Switch to 'My Storybook' tab to read.")
                    st.rerun()

    with sc2:
        st.markdown("""
        <div class="showcase-pill-card">
            <span style="font-size: 0.8rem; font-weight: 700; color: #3730a3; background: #e0e7ff; padding: 0.2rem 0.6rem; border-radius: 10px;">Sci-Fi • Ages 9-12</span>
            <h4 style="margin: 0.5rem 0 0.3rem 0; color: #1e1b4b;">Astro & the Singing Asteroid</h4>
            <p style="margin: 0; font-size: 0.92rem; color: #475569;">
                A pocket robot follows a starlight compass to repair a singing asteroid.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Read Astro's Story", key="load_astro_minimal", use_container_width=True):
            for f in saved_files:
                if "Astro" in f.name:
                    st.session_state["current_story"] = StoryGenerator.load_story_from_disk(f)
                    st.session_state["current_page"] = 1
                    st.session_state["verification_results"] = {}
                    st.success("Loaded 'Astro and the Singing Asteroid'! Switch to 'My Storybook' tab to read.")
                    st.rerun()


# =========================================================
# TAB 2: MY STORYBOOK (STEP 2 — ENJOY & STEP 3 — DOWNLOAD)
# =========================================================
with nav_read:
    if not current_story:
        st.info("👈 No storybook opened yet. Enter three words in **Create Story** or pick a featured storybook to begin!")
    else:
        # Title and Logline
        st.markdown(f"## 📖 {current_story.title}")
        st.markdown(f"*{current_story.logline}*")

        total_pages = len(current_story.scenes)
        page_idx = st.session_state.get("current_page", 1)
        if page_idx < 1 or page_idx > total_pages:
            page_idx = 1
            st.session_state["current_page"] = 1

        current_scene = current_story.scenes[page_idx - 1]
        scene_img_path = get_scene_image_path(current_story.title, current_scene.scene_number)
        scene_audio_path = get_scene_audio_path(current_story.title, current_scene.scene_number)
        bg_music_file = get_story_music_path(current_story.title)

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # -----------------------------------------------------
        # STEP 2 — ENJOY: Centerpiece Reader
        # -----------------------------------------------------
        reader_col_art, reader_col_text = st.columns([1.1, 1], gap="large")

        with reader_col_art:
            if scene_img_path.exists():
                st.image(
                    str(scene_img_path),
                    caption=f"Chapter {current_scene.scene_number}: {current_scene.title}",
                    use_container_width=True
                )
            else:
                st.info("Illustration generating...")

            # Single-click scene redraw
            if st.button("🎨 Redraw this illustration", key=f"redraw_btn_{current_scene.scene_number}", use_container_width=True):
                with st.spinner("Painting a fresh illustration for this chapter..."):
                    import random
                    img_gen = ImageGenerator()
                    img_gen.generate_scene_image(
                        scene=current_scene,
                        story_title=current_story.title,
                        engine="pollinations",
                        force_regenerate=True,
                        seed=random.randint(1000, 999999)
                    )
                    st.success("Fresh illustration painted!")
                    st.rerun()

        with reader_col_text:
            st.markdown(f"### Chapter {current_scene.scene_number}: {current_scene.title}")
            
            # Story prose text
            st.markdown(
                f"<div class='story-prose'>{current_scene.narrative_text}</div>",
                unsafe_allow_html=True
            )

            # Audio Narration Player
            st.markdown("##### 🎙️ Spoken Narration")
            if scene_audio_path.exists():
                st.audio(str(scene_audio_path))
            else:
                if st.button("🎙️ Voice Narration Now", key=f"voice_p_{current_scene.scene_number}"):
                    audio_gen = AudioGenerator(voice=active_voice)
                    audio_gen.generate_scene_narration(current_scene, current_story.title, voice=active_voice, force_regenerate=True)
                    st.rerun()

            # Background Ambience Player
            if bg_music_file.exists():
                st.markdown("##### 🎶 Story Ambience")
                st.audio(str(bg_music_file))

        # Page Navigation Bar
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        nav_c1, nav_c2, nav_c3 = st.columns([1, 2, 1])

        with nav_c1:
            if st.button("⬅️ Previous Page", disabled=(page_idx <= 1), use_container_width=True):
                st.session_state["current_page"] = max(page_idx - 1, 1)
                st.rerun()

        with nav_c2:
            st.markdown(
                f"<div style='text-align: center; font-weight: 700; font-size: 1.15rem; color: #1e1b4b; padding-top: 0.4rem;'>"
                f"Page {page_idx} of {total_pages}"
                f"</div>",
                unsafe_allow_html=True
            )

        with nav_c3:
            if st.button("Next Page ➡️", disabled=(page_idx >= total_pages), use_container_width=True):
                st.session_state["current_page"] = min(page_idx + 1, total_pages)
                st.rerun()

        # Heartwarming Moral (on final page)
        if page_idx == total_pages:
            st.markdown(f"""
            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 14px; padding: 1.4rem; text-align: center; margin-top: 1.5rem;">
                <h4 style="color: #065f46; margin: 0 0 0.4rem 0;">🌟 The Story's Heartwarming Lesson</h4>
                <p style="font-size: 1.15rem; font-style: italic; color: #047857; margin: 0;">
                    "{current_story.moral_or_takeaway}"
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        st.markdown("---")

        # -----------------------------------------------------
        # STEP 3 — DOWNLOAD: Two Clear Options
        # -----------------------------------------------------
        st.markdown("### 📥 Download Your Storybook")

        dl_col1, dl_col2 = st.columns(2, gap="large")

        # Option A: Download PDF
        with dl_col1:
            st.markdown("""
            <div class="download-card">
                <div>
                    <span style="font-size: 2.5rem;">📄</span>
                    <h3 style="margin: 0.6rem 0 0.4rem 0;">Illustrated PDF</h3>
                    <p style="color: #64748b; font-size: 0.95rem; line-height: 1.5;">
                        Full-color printable storybook with cover art, character profiles, and chapter illustrations.
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            pdf_file = get_story_pdf_path(current_story.title)
            if not pdf_file.exists():
                if st.button("📄 Prepare PDF", key="btn_prep_pdf", use_container_width=True):
                    with st.spinner("Typesetting illustrated PDF..."):
                        ExportManager.generate_pdf_storybook(current_story, force_regenerate=True)
                        st.rerun()
            else:
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        label="📥 Download PDF",
                        data=f.read(),
                        file_name=f"{sanitize_filename(current_story.title)}_storybook.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )

        # Option B: Download MP4
        with dl_col2:
            st.markdown("""
            <div class="download-card">
                <div>
                    <span style="font-size: 2.5rem;">🎬</span>
                    <h3 style="margin: 0.6rem 0 0.4rem 0;">Narrated MP4 Video</h3>
                    <p style="color: #64748b; font-size: 0.95rem; line-height: 1.5;">
                        Complete animated video storybook synchronizing illustrations, spoken voice, and music.
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            video_file = get_story_video_path(current_story.title)
            if not video_file.exists():
                if st.button("🎬 Render Video", key="btn_prep_vid", use_container_width=True):
                    with st.spinner("Rendering MP4 video with narration and music..."):
                        bg_m = get_story_music_path(current_story.title)
                        ExportManager.generate_mp4_video(
                            current_story,
                            bg_music_path=bg_m if bg_m.exists() else None,
                            force_regenerate=True
                        )
                        st.rerun()
            else:
                with open(video_file, "rb") as f:
                    st.download_button(
                        label="📥 Download MP4",
                        data=f.read(),
                        file_name=f"{sanitize_filename(current_story.title)}_storybook.mp4",
                        mime="video/mp4",
                        type="primary",
                        use_container_width=True
                    )

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        # -----------------------------------------------------
        # Character Bible & Quality/Safety (Preserving U2 & U5)
        # -----------------------------------------------------
        with st.expander("👥 Meet the Characters (Character Bible)", expanded=False):
            char_cols = st.columns(min(len(current_story.character_bible), 3) or 1)
            for idx, char in enumerate(current_story.character_bible):
                with char_cols[idx % len(char_cols)]:
                    st.markdown(f"""
                    <div style="background: #f8fafc; border-radius: 12px; padding: 1rem; border: 1px solid #e2e8f0;">
                        <h4 style="margin: 0; color: #1e1b4b;">👤 {char.name}</h4>
                        <span style="color: #4338ca; font-weight: 600; font-size: 0.85rem;">{char.role}</span>
                        <p style="margin-top: 0.4rem; font-size: 0.9rem; color: #334155;">
                            <strong>Appearance:</strong> {char.visual_appearance}<br>
                            <strong>Outfit:</strong> {char.signature_clothing}<br>
                            <strong>Special Item:</strong> {char.distinct_accessories}<br>
                            <em>"{char.personality_trait}"</em>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        with st.expander("🛡️ Story Quality & Safety Verification (U3 & U5)", expanded=False):
            q_col1, q_col2, q_col3 = st.columns(3)
            with q_col1:
                st.markdown("##### 🛡️ Child Safety")
                if st.button("Run Safety Check", key="run_safety_subtle", use_container_width=True):
                    s_filter = ChildSafetyFilter()
                    st.session_state["safety_report"] = s_filter.evaluate_story_safety(current_story)
                s_rep: SafetyReport = st.session_state.get("safety_report")
                if s_rep:
                    st.markdown(f"**Score:** `{s_rep.safety_score}%` — **{s_rep.safety_rating}**")
                    st.caption(s_rep.explanation)
                else:
                    st.caption("Audited for age-appropriate language, positive morals, and zero violence.")

            with q_col2:
                st.markdown("##### 🎨 BLIP Visual Accuracy")
                if st.button("Inspect Art", key="run_art_subtle", use_container_width=True):
                    verifier = BLIPVerifier()
                    if "verification_results" not in st.session_state:
                        st.session_state["verification_results"] = {}
                    for sc in current_story.scenes:
                        img_p = get_scene_image_path(current_story.title, sc.scene_number)
                        if img_p.exists():
                            st.session_state["verification_results"][sc.scene_number] = verifier.verify_scene_image(
                                sc.scene_number, img_p, sc.narrative_text, sc.image_prompt, sc.characters_present
                            )
                v_res = st.session_state.get("verification_results", {})
                if v_res and current_scene.scene_number in v_res:
                    res = v_res[current_scene.scene_number]
                    badge = "badge-verified" if res["status"] == "VERIFIED" else "badge-flagged"
                    st.markdown(f"<span class='{badge}'>{res['status']}</span> (Score: {res['similarity_score']}%)", unsafe_allow_html=True)
                    st.caption(f"Seen: *\"{res['blip_caption']}\"*")
                else:
                    st.caption("AI captioning inspects illustrations against intended story details.")

            with q_col3:
                st.markdown("##### ✨ Story Originality")
                if st.button("Check Originality", key="run_orig_subtle", use_container_width=True):
                    o_checker = OriginalityChecker()
                    st.session_state["originality_report"] = o_checker.evaluate_story_originality(current_story)
                o_rep: OriginalityReport = st.session_state.get("originality_report")
                if o_rep:
                    st.markdown(f"**Rating:** `{o_rep.originality_score}%` — **{o_rep.status}**")
                    st.caption(f"Closest archetype: *{o_rep.closest_archetype}* ({o_rep.similarity_percentage}% match)")
                else:
                    st.caption("Checked against 12 classic fairy tale archetypes for creative freshness.")
