"""
Export Manager Module for Taleora (Satisfies Requirement U4).
Generates illustrated PDF storybooks using ReportLab and assembled MP4 videos
using MoviePy and FFmpeg.
"""
from pathlib import Path
from typing import Optional, Dict, List
from PIL import Image as PILImage, ImageDraw, ImageFont

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether
)

import config
from modules.prompt_engine import StoryBook
from modules.story_generator import sanitize_filename


class ExportManager:
    """Handles multi-format export of Taleora storybooks to PDF and MP4 video."""

    @staticmethod
    def _create_placeholder_image(scene_title: str, text: str, output_path: Path) -> Path:
        """Creates a clean visual card if a scene illustration was not generated."""
        img = PILImage.new("RGB", (1024, 1024), color=(30, 27, 75))
        draw = ImageDraw.Draw(img)
        # Draw decorative border
        draw.rectangle([(30, 30), (994, 994)], outline=(254, 240, 138), width=6)
        draw.text((100, 450), scene_title, fill=(254, 240, 138))
        draw.text((100, 520), text[:80] + "...", fill=(224, 231, 255))
        img.save(output_path, format="PNG")
        return output_path

    # =====================================================
    # PDF STORYBOOK GENERATOR (ReportLab)
    # =====================================================
    @classmethod
    def generate_pdf_storybook(cls, story: StoryBook, force_regenerate: bool = False) -> Path:
        """
        Creates an illustrated, formatted PDF storybook with cover page,
        character profiles, and scene-by-scene illustrations.
        """
        safe_title = sanitize_filename(story.title)
        pdf_path = config.PDFS_DIR / f"{safe_title}_storybook.pdf"

        if pdf_path.exists() and not force_regenerate:
            return pdf_path

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        # Custom Taleora Typography Styles
        title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            textColor=colors.HexColor("#1e1b4b"),
            alignment=1,  # Centered
            spaceAfter=15
        )

        subtitle_style = ParagraphStyle(
            "CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#475569"),
            alignment=1,
            spaceAfter=25
        )

        meta_style = ParagraphStyle(
            "CoverMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
            alignment=1
        )

        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#312e81"),
            spaceBefore=15,
            spaceAfter=10
        )

        scene_title_style = ParagraphStyle(
            "SceneTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1e1b4b"),
            spaceAfter=8
        )

        body_style = ParagraphStyle(
            "StoryBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=12
        )

        moral_style = ParagraphStyle(
            "StoryMoral",
            parent=styles["Normal"],
            fontName="Helvetica-BoldOblique",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#065f46"),
            alignment=1,
            spaceBefore=15
        )

        elements = []

        # ---------------------------------------------
        # 1. COVER PAGE
        # ---------------------------------------------
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(f"✨ {story.title} ✨", title_style))
        elements.append(Paragraph(story.logline, subtitle_style))

        # Check for first scene image to use as cover illustration
        first_img_path = config.IMAGES_DIR / f"{safe_title}_scene_1.png"
        if first_img_path.exists():
            elements.append(RLImage(str(first_img_path), width=4.5 * inch, height=4.5 * inch))
            elements.append(Spacer(1, 20))

        kw_text = " • ".join(story.keywords)
        meta_html = (
            f"<b>Genre:</b> {story.genre} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Audience:</b> {story.target_audience}<br/>"
            f"<b>Keywords:</b> {kw_text}"
        )
        elements.append(Paragraph(meta_html, meta_style))
        elements.append(PageBreak())

        # ---------------------------------------------
        # 2. CHARACTER BIBLE PAGE
        # ---------------------------------------------
        elements.append(Paragraph("👥 Cast of Characters", section_heading))
        elements.append(Spacer(1, 10))

        for char in story.character_bible:
            char_data = [
                [Paragraph(f"<b>{char.name}</b> ({char.role})", styles["Normal"])],
                [Paragraph(f"<b>Appearance:</b> {char.visual_appearance}", styles["Normal"])],
                [Paragraph(f"<b>Signature Outfit:</b> {char.signature_clothing}", styles["Normal"])],
                [Paragraph(f"<b>Props & Accessories:</b> {char.distinct_accessories}", styles["Normal"])],
                [Paragraph(f"<b>Personality:</b> <i>{char.personality_trait}</i>", styles["Normal"])]
            ]
            t = Table(char_data, colWidths=[7.0 * inch])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 10))

        elements.append(PageBreak())

        # ---------------------------------------------
        # 3. SCENES (ONE OR TWO PER PAGE)
        # ---------------------------------------------
        for scene in story.scenes:
            scene_elements = []
            scene_elements.append(Paragraph(f"Scene {scene.scene_number}: {scene.title}", scene_title_style))

            img_file = config.IMAGES_DIR / f"{safe_title}_scene_{scene.scene_number}.png"
            if img_file.exists():
                scene_elements.append(RLImage(str(img_file), width=5.0 * inch, height=5.0 * inch))
                scene_elements.append(Spacer(1, 12))

            scene_elements.append(Paragraph(scene.narrative_text, body_style))
            scene_elements.append(Spacer(1, 10))

            elements.append(KeepTogether(scene_elements))
            elements.append(PageBreak())

        # ---------------------------------------------
        # 4. FINAL TAKEAWAY / COLOPHON
        # ---------------------------------------------
        elements.append(Spacer(1, 100))
        elements.append(Paragraph("🌟 Moral & Heartwarming Takeaway", section_heading))
        elements.append(Paragraph(f'"{story.moral_or_takeaway}"', moral_style))
        elements.append(Spacer(1, 50))
        elements.append(Paragraph("Crafted with Taleora • Illustrated Audio Storybook Generator", meta_style))

        # Build PDF
        doc.build(elements)
        return pdf_path

    # =====================================================
    # MP4 VIDEO GENERATOR (MoviePy + FFmpeg)
    # =====================================================
    @classmethod
    def generate_mp4_video(
        cls,
        story: StoryBook,
        bg_music_path: Optional[Path] = None,
        force_regenerate: bool = False
    ) -> Path:
        """
        Assembles scene illustrations, TTS voice narration, and background music
        into a complete 720p/1080p MP4 storybook video.
        """
        # Lazy import of MoviePy to save memory when not generating video
        import moviepy.editor as mp

        safe_title = sanitize_filename(story.title)
        video_path = config.VIDEOS_DIR / f"{safe_title}_storybook.mp4"

        if video_path.exists() and not force_regenerate:
            return video_path

        scene_video_clips = []

        for scene in story.scenes:
            # 1. Scene Image
            img_path = config.IMAGES_DIR / f"{safe_title}_scene_{scene.scene_number}.png"
            if not img_path.exists():
                img_path = cls._create_placeholder_image(scene.title, scene.narrative_text, img_path)

            # 2. Scene Narration Audio
            audio_path = config.AUDIO_DIR / f"{safe_title}_scene_{scene.scene_number}_narration.mp3"
            
            # If narration was not generated yet, generate it on the fly
            if not audio_path.exists():
                from modules.audio_generator import AudioGenerator
                audio_gen = AudioGenerator()
                audio_path = audio_gen.generate_scene_narration(scene, story.title)

            # Load audio clip and calculate duration
            audio_clip = mp.AudioFileClip(str(audio_path))
            clip_duration = audio_clip.duration + 0.6  # 0.6s gentle transition pause

            # Create image clip matching audio duration
            img_clip = mp.ImageClip(str(img_path)).set_duration(clip_duration)
            img_clip = img_clip.set_audio(audio_clip)

            scene_video_clips.append(img_clip)

        # Concatenate all scene clips
        final_video = mp.concatenate_videoclips(scene_video_clips, method="compose")

        # 3. Add Background Music if available
        if bg_music_path and bg_music_path.exists():
            try:
                bg_audio = mp.AudioFileClip(str(bg_music_path))
                # Loop background music to cover entire video length
                if bg_audio.duration < final_video.duration:
                    loops = int(final_video.duration / bg_audio.duration) + 1
                    bg_audio = mp.concatenate_audioclips([bg_audio] * loops)

                bg_audio = bg_audio.subclip(0, final_video.duration)
                # Duck background music volume down to 12% so voice narration is prominent
                bg_audio = bg_audio.volumex(0.12)

                # Composite spoken audio with background music
                combined_audio = mp.CompositeAudioClip([final_video.audio, bg_audio])
                final_video = final_video.set_audio(combined_audio)
            except Exception:
                pass  # Keep original narration audio if music mix encounters an issue

        # Write output MP4 video
        final_video.write_videofile(
            str(video_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2,
            logger=None
        )

        # Close all clips to release file handles
        final_video.close()
        for c in scene_video_clips:
            c.close()

        return video_path
