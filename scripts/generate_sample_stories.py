"""
Sample Story Generator for Taleora (Satisfies Requirement: 2 Complete Stories).
Generates two full illustrated, narrated, and verified stories with complete
JSON, images, Edge TTS audio, background music, PDFs, and MP4 videos.
"""
import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from modules.prompt_engine import StoryBook, Scene, Character
from modules.story_generator import StoryGenerator
from modules.image_generator import ImageGenerator
from modules.audio_generator import AudioGenerator
from modules.music_generator import MusicGenerator
from modules.export_manager import ExportManager
from modules.blip_verifier import BLIPVerifier
from modules.safety_filter import ChildSafetyFilter
from modules.originality_checker import OriginalityChecker


def build_story_one() -> StoryBook:
    """Story 1: Fantasy genre for Kids (6-8)."""
    char = Character(
        name="Barnaby",
        role="Protagonist",
        visual_appearance="small brown barn owl crafted with polished bronze gears and soft golden feathers",
        signature_clothing="cozy forest-green wool scarf fastened with a tiny brass acorn pin",
        distinct_accessories="gleaming round monocle over his curious right amber eye",
        personality_trait="curious, punctual, and deeply loyal"
    )

    scenes = [
        Scene(
            scene_number=1,
            title="The Clockwork Attic",
            narrative_text="High above the sleepy village of Oakhaven, Barnaby fluttered his bronze feathers across stacks of ancient leather-bound books in the secret attic library.",
            audio_script="High above the sleepy village of Oakhaven, Barnaby fluttered his bronze feathers across stacks of ancient leather-bound books in the secret attic library.",
            characters_present=["Barnaby"],
            image_prompt="whimsical storybook illustration, cozy sunlit attic library filled with antique books and clocks, Barnaby (small bronze owl with golden feathers, wearing forest-green wool scarf with brass acorn pin, round monocle over right eye), warm golden dust motes in sunbeam, storybook art",
            music_mood="whimsical ticking clockwork"
        ),
        Scene(
            scene_number=2,
            title="The Floating Key",
            narrative_text="Beneath an antique grandfather clock, a soft golden light shimmered. Suspended in mid-air was an ornate brass key humming with quiet enchantment.",
            audio_script="Beneath an antique grandfather clock, a soft golden light shimmered. Suspended in mid-air was an ornate brass key humming with quiet enchantment.",
            characters_present=["Barnaby"],
            image_prompt="whimsical storybook illustration, antique grandfather clock in warm attic, glowing ornate brass key floating in mid-air, Barnaby (small bronze owl with golden feathers, forest-green scarf, monocle) looking with wonder, magical sparkles, storybook art",
            music_mood="gentle mystery and wonder"
        ),
        Scene(
            scene_number=3,
            title="The Secret Doorway",
            narrative_text="Guided by the key's gentle glow, Barnaby discovered a hidden keyhole carved into the spine of a massive indigo encyclopedia of forgotten tales.",
            audio_script="Guided by the key's gentle glow, Barnaby discovered a hidden keyhole carved into the spine of a massive indigo encyclopedia of forgotten tales.",
            characters_present=["Barnaby"],
            image_prompt="whimsical storybook illustration, Barnaby (small bronze owl, forest-green scarf, monocle) inserting glowing brass key into a giant indigo book with ornate gold filigree, soft blue and golden light spilling from the opening door, storybook art",
            music_mood="curious exploration"
        ),
        Scene(
            scene_number=4,
            title="The Garden of Lost Stories",
            narrative_text="The book opened into an enchanted indoor conservatory where paper birds sang and forgotten stories bloomed like luminous lanterns among emerald leaves.",
            audio_script="The book opened into an enchanted indoor conservatory where paper birds sang and forgotten stories bloomed like luminous lanterns among emerald leaves.",
            characters_present=["Barnaby"],
            image_prompt="whimsical storybook illustration, magical indoor conservatory garden made of paper flowers and glowing lantern fruit, Barnaby the bronze owl perched on a branch, origami birds flying, rich magical colors, storybook art",
            music_mood="lush orchestral wonder"
        ),
        Scene(
            scene_number=5,
            title="The Keeper of Wonder",
            narrative_text="Barnaby realized that every story needed a reader to bring it back to life. With a joyful flutter, he vowed to share the magic with every child in the village.",
            audio_script="Barnaby realized that every story needed a reader to bring it back to life. With a joyful flutter, he vowed to share the magic with every child in the village.",
            characters_present=["Barnaby"],
            image_prompt="whimsical storybook illustration, Barnaby (small bronze owl, forest-green scarf, monocle) surrounded by open glowing storybooks, warm radiant sunlight streaming into the attic library, peaceful happy ending, storybook art",
            music_mood="uplifting heartwarming resolution"
        )
    ]

    return StoryBook(
        title="Barnaby and the Whispering Key",
        logline="A curious clockwork owl discovers a floating key that unlocks an attic filled with forgotten living stories.",
        genre="Fantasy",
        target_audience="Kids (Ages 6-8)",
        keywords=["Clockwork Owl", "Floating Key", "Secret Attic Library"],
        character_bible=[char],
        scenes=scenes,
        moral_or_takeaway="Curiosity opens doors, but sharing our stories brings true magic to life."
    )


def build_story_two() -> StoryBook:
    """Story 2: Sci-Fi genre for Middle Grade (9-12)."""
    char = Character(
        name="Astro",
        role="Protagonist",
        visual_appearance="palm-sized explorer robot with brushed sky-blue chrome plating and expressive round teal optics",
        signature_clothing="utility belt made of solar-yellow synthetic weave with magnetic pouches",
        distinct_accessories="glowing bronze starlight compass antenna on his crown",
        personality_trait="inventive, optimistic, and quick-thinking"
    )

    scenes = [
        Scene(
            scene_number=1,
            title="Drifting in the Nebula",
            narrative_text="Astro hummed softly as his small scout ship coasted through the iridescent lilac clouds of the Orion Nebula, scanning for rare cosmic frequencies.",
            audio_script="Astro hummed softly as his small scout ship coasted through the iridescent lilac clouds of the Orion Nebula, scanning for rare cosmic frequencies.",
            characters_present=["Astro"],
            image_prompt="retro-futuristic storybook art, cozy spaceship cockpit overlooking glowing purple nebula and twinkling stars, Astro (palm-sized sky-blue robot with round teal eyes and yellow belt), starlight compass glowing, sleek futuristic shapes, storybook art",
            music_mood="ambient cosmic synthesizer"
        ),
        Scene(
            scene_number=2,
            title="The Song of the Stars",
            narrative_text="Suddenly, his starlight compass spun wildly. A warm melody echoed through his communication console—gentle chimes carrying a rhythmic galactic song.",
            audio_script="Suddenly, his starlight compass spun wildly. A warm melody echoed through his communication console, gentle chimes carrying a rhythmic galactic song.",
            characters_present=["Astro"],
            image_prompt="retro-futuristic storybook art, Astro the sky-blue robot looking at glowing soundwaves on a holographic screen, starlight compass on his crown pulsing with golden light, starry space vista outside cockpit, storybook art",
            music_mood="mysterious celestial bells"
        ),
        Scene(
            scene_number=3,
            title="The Crystalline Wanderer",
            narrative_text="Following the soundwaves, Astro encountered an ancient asteroid covered in glowing blue harmonic crystals that resonated with every passing solar wind.",
            audio_script="Following the soundwaves, Astro encountered an ancient asteroid covered in glowing blue harmonic crystals that resonated with every passing solar wind.",
            characters_present=["Astro"],
            image_prompt="retro-futuristic storybook art, majestic floating asteroid covered in giant glowing sapphire crystals in deep space, Astro the small robot floating gently with magnetic thrusters, cosmic glow, vibrant, storybook art",
            music_mood="resonant crystalline pads"
        ),
        Scene(
            scene_number=4,
            title="A Broken Harmony",
            narrative_text="Astro noticed a rogue meteor had jammed the central crystalline spire. With careful robotic precision and his toolkit, he cleared the obstruction and tuned the crystal node.",
            audio_script="Astro noticed a rogue meteor had jammed the central crystalline spire. With careful robotic precision and his toolkit, he cleared the obstruction and tuned the crystal node.",
            characters_present=["Astro"],
            image_prompt="retro-futuristic storybook art, Astro the sky-blue robot using tiny laser toolkit on glowing crystal spire on asteroid surface, dazzling blue and gold light beams radiating into space, storybook art",
            music_mood="dynamic rhythmic tension"
        ),
        Scene(
            scene_number=5,
            title="The Symphony of the Cosmos",
            narrative_text="The asteroid burst into full celestial melody, guiding lost starships safely through the nebula. Astro smiled, his compass spinning in perfect harmony with the galaxy.",
            audio_script="The asteroid burst into full celestial melody, guiding lost starships safely through the nebula. Astro smiled, his compass spinning in perfect harmony with the galaxy.",
            characters_present=["Astro"],
            image_prompt="retro-futuristic storybook art, Astro sitting happily atop glowing singing asteroid, brilliant beams of melodic light reaching distant friendly starships, vast colorful cosmic horizon, triumph and peace, storybook art",
            music_mood="triumphant celestial orchestra"
        )
    ]

    return StoryBook(
        title="Astro and the Singing Asteroid",
        logline="A daring pocket robot follows a starlight compass into deep space to heal a singing asteroid that guides lost travelers.",
        genre="Sci-Fi",
        target_audience="Middle Grade (Ages 9-12)",
        keywords=["Pocket Robot", "Starlight Compass", "Singing Asteroid"],
        character_bible=[char],
        scenes=scenes,
        moral_or_takeaway="When we listen closely and repair what is broken, our actions create harmony across the universe."
    )


def generate_full_package(story: StoryBook, voice: str):
    """Generates all media assets, verification reports, and exports for a story."""
    print(f"\n=======================================================")
    print(f"Generating Complete Deliverable Package for: '{story.title}'")
    print(f"=======================================================")

    # 1. Save Story JSON
    generator = StoryGenerator()
    json_path = generator.save_story_to_disk(story)
    print(f"  [1/7] Saved Storybook JSON: {json_path.name}")

    # 2. Generate Scene Illustrations (Pollinations)
    print("  [2/7] Generating illustrations for all scenes...")
    img_gen = ImageGenerator()
    img_results = img_gen.generate_all_scenes(
        story=story,
        engine="pollinations",
        force_regenerate=False
    )
    print(f"        Generated {len(img_results)} high-resolution scene illustrations.")

    # 3. Generate Scene Narrations (Edge TTS)
    print(f"  [3/7] Synthesizing neural TTS narration ({voice})...")
    audio_gen = AudioGenerator(voice=voice)
    audio_results = audio_gen.generate_all_narrations(
        story=story,
        voice=voice,
        force_regenerate=False
    )
    print(f"        Synthesized {len(audio_results)} spoken scene audio tracks.")

    # 4. Generate Instrumental Background Music
    print("  [4/7] Synthesizing ambient background music...")
    music_gen = MusicGenerator()
    music_path, music_model = music_gen.generate_story_music(story, duration_seconds=25, force_regenerate=False)
    print(f"        Background music ready: {music_path.name} ({music_model})")

    # 5. Compile Illustrated PDF Storybook (ReportLab)
    print("  [5/7] Compiling illustrated PDF storybook...")
    pdf_path = ExportManager.generate_pdf_storybook(story, force_regenerate=True)
    pdf_size_kb = int(pdf_path.stat().st_size / 1024)
    print(f"        PDF Storybook compiled: {pdf_path.name} (~{pdf_size_kb} KB)")

    # 6. Assemble Full MP4 Video (MoviePy + FFmpeg)
    print("  [6/7] Assembling and rendering MP4 storybook video...")
    video_path = ExportManager.generate_mp4_video(story, bg_music_path=music_path, force_regenerate=True)
    video_size_mb = round(video_path.stat().st_size / (1024 * 1024), 2)
    print(f"        MP4 Video rendered: {video_path.name} (~{video_size_mb} MB)")

    # 7. Run Verification, Safety & Originality Audits
    print("  [7/7] Running BLIP verification, safety, and originality audits...")
    verifier = BLIPVerifier()
    for sc in story.scenes:
        img_p = img_results[sc.scene_number]
        v_res = verifier.verify_scene_image(sc.scene_number, img_p, sc.narrative_text, sc.image_prompt, sc.characters_present)
        print(f"        Scene {sc.scene_number}: BLIP {v_res['status']} ({v_res['similarity_score']}% match)")

    safety_filter = ChildSafetyFilter()
    s_rep = safety_filter.evaluate_story_safety(story)
    print(f"        Child Safety Score: {s_rep.safety_score}% ({s_rep.safety_rating})")

    orig_checker = OriginalityChecker()
    o_rep = orig_checker.evaluate_story_originality(story)
    print(f"        Originality Score: {o_rep.originality_score}% ({o_rep.status}, closest: {o_rep.closest_archetype})")

    print(f"  [SUCCESS] All assets complete for '{story.title}'!\n")


def main():
    print("=================================================================")
    print("Taleora — Generating 2 Complete Submission Storybook Packages")
    print("=================================================================")

    # Story 1: Fantasy / Kids (6-8)
    story1 = build_story_one()
    generate_full_package(story1, voice="en-US-AnaNeural")

    # Story 2: Sci-Fi / Middle Grade (9-12)
    story2 = build_story_two()
    generate_full_package(story2, voice="en-US-GuyNeural")

    print("=================================================================")
    print("[SUCCESS] BOTH COMPLETE STORYBOOK PACKAGES SUCCESSFULLY GENERATED!")
    print("=================================================================")


if __name__ == "__main__":
    main()
