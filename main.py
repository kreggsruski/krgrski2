import os
import re
import datetime
import subprocess
import random
from pathlib import Path
from urllib.parse import quote
import requests
import time
from dotenv import load_dotenv

load_dotenv()
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# ---------------- CONFIG ----------------

# LANGUAGE SETTINGS (Change this for different languages)
LANGUAGE_CONFIG = {
    "name": "Russian",
    "native_name": "на русском языке",
    "voice": "ru-RU-SvetlanaNeural",
    "vosk_model": "vosk-model-small-ru-0.22",
    "vosk_url": "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip",
    "vosk_zip": "vosk-model-ru.zip",
    "subtitle_font": "Arial"
}

NUM_IMAGES = 8  # 8 unique scenes (faster generation)
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920
IMAGE_MODEL = "zimage"

STORY_MAX_WORDS = 130

TOPICS_FILE = "topics.txt"

IMAGES_DIR = Path("images")
OUTPUT_DIR = Path("output")
AUDIO_DIR = Path("audio")

MUSIC_FILE = AUDIO_DIR / "music.mp3"

NARRATION_FILE = OUTPUT_DIR / "narration.mp3"
STORY_FILE = OUTPUT_DIR / "story.txt"
SCENES_FILE = OUTPUT_DIR / "scenes.txt"
SUBS_FILE = OUTPUT_DIR / "subtitles.ass"
ANIMATED_VIDEO = OUTPUT_DIR / "animated.mp4"
VIDEO_WITH_SUBS = OUTPUT_DIR / "video_with_subs.mp4"
FINAL_VIDEO = OUTPUT_DIR / "final_video.mp4"

WHISPER_MODEL_NAME = "small"

# ----------------------------------------

def ensure_dirs():
    IMAGES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    AUDIO_DIR.mkdir(exist_ok=True)
    
    # Clean old images
    for f in IMAGES_DIR.glob("*.jpg"):
        f.unlink()
        
    # Clean old output files to prevent stale state
    for f in OUTPUT_DIR.glob("*"):
        if f.is_file() and f.name != ".gitkeep":
            try:
                f.unlink()
            except Exception:
                pass

MIN_TOPICS_THRESHOLD = 30

def refill_topics_if_needed():
    """Auto-refill topics if running low, avoiding used duplicates."""
    from generate_topics import generate_topics_in_batches, save_topics_to_file, get_fallback_topics

    if not os.path.exists(TOPICS_FILE):
        remaining = 0
    else:
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            remaining = len([line.strip() for line in f if line.strip()])

    if remaining >= MIN_TOPICS_THRESHOLD:
        return

    print(f"[topics] ⚠️ Only {remaining} topics left (threshold: {MIN_TOPICS_THRESHOLD}). Auto-refilling...")

    used = set()
    if os.path.exists("used_topics.txt"):
        with open("used_topics.txt", "r", encoding="utf-8") as f:
            used = {line.strip().lower() for line in f if line.strip()}

    existing = []
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            existing = [line.strip() for line in f if line.strip()]

    new_topics = generate_topics_in_batches(total=100, batch_size=50)

    combined = existing.copy()
    seen = {t.lower() for t in combined}
    for topic in new_topics:
        tl = topic.lower()
        if tl not in seen and tl not in used:
            combined.append(topic)
            seen.add(tl)

    if len(combined) < MIN_TOPICS_THRESHOLD:
        for topic in get_fallback_topics():
            tl = topic.lower()
            if tl not in seen and tl not in used:
                combined.append(topic)
                seen.add(tl)

    save_topics_to_file(combined, filename=TOPICS_FILE)
    print(f"[topics] ✅ Refilled: now have {len(combined)} topics")

def get_all_used_topics():
    """Get all previously used topics to prevent duplicates."""
    used = set()
    if os.path.exists("used_topics.txt"):
        with open("used_topics.txt", "r", encoding="utf-8") as f:
            for line in f:
                if ": " in line:
                    topic = line.split(": ", 1)[1].strip()
                    used.add(topic.lower())
                else:
                    used.add(line.strip().lower())
    return used

def choose_topic_for_today():
    """Select and consume a topic from topics.txt. Auto-generates new unique topics when running low."""
    if not os.path.exists(TOPICS_FILE):
        print(f"[topics] {TOPICS_FILE} not found! Generating initial topics...")
        from generate_topics import generate_russian_selfhelp_topics, save_topics_to_file
        new_topics = generate_russian_selfhelp_topics(100)
        save_topics_to_file(new_topics)

    try:
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            topics = [line.strip() for line in f if line.strip()]
        print(f"[topics] Loaded {len(topics)} topics")
    except Exception as e:
        print(f"[topics] ERROR reading {TOPICS_FILE}: {e}")
        return "Самопомощь и позитивная психология"

    if len(topics) < 30:
        print(f"[topics] Only {len(topics)} topics left. Generating 100 new unique topics...")
        from generate_topics import generate_russian_selfhelp_topics

        used_topics = get_all_used_topics()
        existing_topics_lower = set(t.lower() for t in topics)
        all_existing = used_topics.union(existing_topics_lower)

        print(f"[topics] Already used/existing: {len(all_existing)} topics")
        attempts = 0
        new_unique_topics = []
        while len(new_unique_topics) < 100 and attempts < 5:
            batch = generate_russian_selfhelp_topics(150)
            for topic in batch:
                if topic.lower() not in all_existing:
                    new_unique_topics.append(topic)
                    all_existing.add(topic.lower())
                    if len(new_unique_topics) >= 100:
                        break
            attempts += 1

        print(f"[topics] Generated {len(new_unique_topics)} unique new topics (0 duplicates)")
        topics.extend(new_unique_topics)
        try:
            with open(TOPICS_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(topics) + "\n")
                f.flush()
                os.fsync(f.fileno())
            print(f"[topics] Now {len(topics)} topics available")
        except Exception as e:
            print(f"[topics] ERROR saving new topics: {e}")

    if not topics:
        print("[topics] No topics available! Using fallback.")
        return "Самопомощь и позитивная психология"

    selected_topic = topics[0]
    remaining_topics = topics[1:]

    print(f"[topics] Topic selected: {selected_topic}")
    print(f"[topics] Remaining: {len(remaining_topics)}")

    try:
        with open(TOPICS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(remaining_topics) + "\n")
            f.flush()
            os.fsync(f.fileno())
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            verification = [line.strip() for line in f if line.strip()]
        if selected_topic in verification:
            print(f"[topics] WARNING: Topic still in file after removal!")
        else:
            print(f"[topics] Topic successfully removed from topics.txt")
    except Exception as e:
        print(f"[topics] ERROR updating {TOPICS_FILE}: {e}")

    try:
        today = datetime.datetime.now()
        with open("used_topics.txt", "a", encoding="utf-8") as f:
            f.write(f"{today.strftime('%Y-%m-%d')}: {selected_topic}\n")
            f.flush()
        print(f"[topics] Topic logged to used_topics.txt")
    except Exception as e:
        print(f"[topics] WARNING: Could not log topic: {e}")

    return selected_topic

def generate_story_with_pollinations(topic: str) -> str:
    """Generate a self-help / psychological reflection in Russian for adults."""
    
    base_url = "https://gen.pollinations.ai/text/"
    
    lang_name = LANGUAGE_CONFIG["name"]
    
    full_prompt = (
        f"Write a short self-help and positive psychology reflection in {lang_name} language "
        f"on the topic: {topic}. "
        f"Speak directly to the reader. "
        f"Be warm, psychologically insightful, and motivating. "
        f"Incorporate principles from positive psychology, mindfulness, and self-compassion. "
        f"Give practical, everyday wisdom. "
        f"Length: 80-120 words. No title. Only the content."
    )
    
    url = base_url + quote(full_prompt)
    params = {"model": "openai", "seed": random.randint(1, 99999), "temperature": 1.3}

    print(f"[story] Generating self-help text ({lang_name}): {topic}")
    
    if not POLLINATIONS_API_KEY:
        raise ValueError("❌ POLLINATIONS_API_KEY is missing!")

    max_retries = 3
    headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}"}
    
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=60)
            r.raise_for_status()
            text = r.text.strip()

            words = text.split()
            
            if len(words) < 50:
                print(f"[story] ⚠️ Too short ({len(words)} words), retrying {attempt + 1}/{max_retries}...")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    raise ValueError(f"Story too short after {max_retries} attempts: {len(words)} words")
            
            if len(words) > STORY_MAX_WORDS:
                text = " ".join(words[:STORY_MAX_WORDS])
                words = text.split()

            with open(STORY_FILE, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"[story] ✅ Generated ({len(words)} words)")
            return text
            
        except Exception as e:
            print(f"[story] ❌ Error attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                fallback = (
                    f"Иногда мы забываем, насколько мы сильны на самом деле. {topic} "
                    f"Можно позволить себе время. Можно сказать нет. "
                    f"Чувства важны. Потребности имеют значение. "
                    f"Каждый день — это новый шанс стать ближе к себе. "
                    f"Будьте нежны с собой. Растите в своём темпе. "
                    f"Вы достаточны, именно такие, какие есть."
                )
                print(f"[story] ⚠️ Using fallback")
                with open(STORY_FILE, "w", encoding="utf-8") as f:
                    f.write(fallback)
                return fallback

def generate_visual_prompts(story: str) -> list:
    """Generate stickman scene descriptions for self-help content."""
    print(f"[scenes] Generating stickman scene descriptions in English...")
    
    url = "https://gen.pollinations.ai/text/"
    
    lang_name = LANGUAGE_CONFIG["name"]
    
    prompt = (
        f"Read this {lang_name} self-help text: '{story}'\n"
        f"Generate exactly {NUM_IMAGES} UNIQUE stickman scene descriptions in ENGLISH "
        f"that visually explain the concepts from the text. "
        f"Each scene shows a CLEAN, WELL-DRAWN stick figure on a soft pastel background doing an action. "
        f"Be CREATIVE and make each scene DIFFERENT from any other. "
        f"Think of original metaphors and actions based on the text. "
        f"Vary the background colors, the stickman poses, and the symbolic elements. "
        f"IMPORTANT: No books, no letters, no signs, no labels, no screens, no writing in the scene. "
        f"No visible text, no words, no letters anywhere. "
        f"Output ONLY {NUM_IMAGES} descriptions, one per line. No numbering."
    )
    
    final_url = url + quote(prompt)
    
    try:
        if not POLLINATIONS_API_KEY:
            raise ValueError("❌ POLLINATIONS_API_KEY is missing!")

        headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}"}
        r = requests.get(final_url, params={"model": "openai", "temperature": 1.3, "seed": random.randint(1, 999999)}, headers=headers, timeout=60)
        
        if r.status_code != 200:
             raise Exception(f"API Error: {r.status_code}")
             
        text = r.text.strip()
        
        lines = [line.strip().lstrip('0123456789.- ') for line in text.split('\n') if line.strip()]
        
        if len(lines) < NUM_IMAGES:
            while len(lines) < NUM_IMAGES:
                lines.append(lines[-1] + " close up view" if lines else "Stickman in peaceful pose")
        
        scenes = lines[:NUM_IMAGES]
        
    except Exception as e:
        print(f"[scenes] Error generating prompts: {e}")
        scenes = [
            "Stickman meditating with glowing peaceful thoughts above head, soft blue background",
            "Stickman looking in a mirror seeing their best self reflected, warm pink background",
            "Stickman climbing steps toward a shining star, sunset gradient background",
            "Stickman watering a small plant growing from the ground, soft green background",
            "Stickman releasing a balloon labeled fear into the sky, lavender background",
            "Stickman writing goals in a journal at a desk, cozy warm background",
            "Stickman walking through an open door into bright light, golden background",
            "Stickman standing tall with arms open wide, soft teal background",
        ]

    with open(SCENES_FILE, "w", encoding="utf-8") as f:
        for i, scene in enumerate(scenes):
            f.write(f"{i+1}. {scene}\n")
    
    print(f"[scenes] Created {len(scenes)} visual descriptions")
    return scenes

def download_image_from_drive(idx: int) -> Path:
    """Pick a random stickman image from Google Drive folder (weighted by least-used)."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    out = IMAGES_DIR / f"scene_{idx:02d}.jpg"

    service_key = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    folder_id = os.environ.get(
        "GOOGLE_DRIVE_FOLDER_ID",
        "1E9NZSg5Ef-bcRIwMVcrJ-KsrmG0R1Zgv",
    ).strip().strip('"').strip("'")
    if not service_key:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY environment variable required")
    if not folder_id:
        raise ValueError("GOOGLE_DRIVE_FOLDER_ID environment variable required")

    cred = service_account.Credentials.from_service_account_info(
        json.loads(service_key), scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=cred)

    all_files = []
    page_token = None
    while True:
        r = service.files().list(
            q=f"'{folder_id}' in parents and mimeType contains 'image/'",
            fields="files(id, name)", pageSize=200, pageToken=page_token
        ).execute()
        all_files.extend(r.get("files", []))
        page_token = r.get("nextPageToken")
        if not page_token:
            break

    if not all_files:
        raise RuntimeError(f"No image files found in Google Drive folder: {folder_id}")

    used_log = Path("used_images.json")
    usage = {}
    if used_log.exists():
        try:
            usage = json.loads(used_log.read_text())
        except Exception:
            usage = {}

    for f in all_files:
        if f["name"] not in usage:
            usage[f["name"]] = 0

    min_usage = min(usage.values())
    weights = [1.0 / (usage[f["name"]] - min_usage + 1) for f in all_files]
    chosen = random.choices(all_files, weights=weights, k=1)[0]
    usage[chosen["name"]] += 1
    used_log.write_text(json.dumps(usage, indent=2))

    print(f"[image] Loading image from Google Drive: {chosen['name']} ...", flush=True)
    request = service.files().get_media(fileId=chosen["id"])
    from googleapiclient.http import MediaIoBaseDownload
    import io
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    out.write_bytes(fh.read())
    print(f"  Saved: {out.name} ({out.stat().st_size // 1024} KB)", flush=True)
    return out

def generate_image(scene: str, idx: int, topic: str = "") -> Path:
    """Pick image randomly from Google Drive instead of AI generation."""
    return download_image_from_drive(idx)

def generate_images(scenes: list, topic: str = ""):
    """Download random images from Google Drive for each scene."""
    print(f"[image] Downloading {NUM_IMAGES} random images from Google Drive...")
    return [generate_image(scene, i, topic) for i, scene in enumerate(scenes)]
            images.append(img)
        except Exception as e:
            print(f"[image] ⚠️ Bild {i+1} fehlgeschlagen: {e}")
            from PIL import Image, ImageDraw, ImageFont, ImageFilter
            placeholder = IMAGES_DIR / f"scene_{i:02d}.jpg"
            img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            palettes = [(210, 230, 255), (255, 220, 230), (220, 255, 220), (255, 230, 200), (230, 220, 255), (255, 240, 210), (210, 240, 240), (240, 220, 240)]
            r1, g1, b1 = palettes[i % 8]
            r2 = min(r1 + 60, 255); g2 = min(g1 + 50, 255); b2 = min(b1 + 40, 255)
            for y in range(IMAGE_HEIGHT):
                t = y / IMAGE_HEIGHT
                r = int(r1 + (r2 - r1) * t)
                g = int(g1 + (g2 - g1) * t)
                b = int(b1 + (b2 - b1) * t)
                draw.line([(0, y), (IMAGE_WIDTH, y)], fill=(r, g, b))
            img = img.filter(ImageFilter.GaussianBlur(radius=5))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except Exception:
                font = ImageFont.load_default()
            draw.text((IMAGE_WIDTH//2 - 250, IMAGE_HEIGHT//2 - 30), f"Scene {i+1}", fill=(80, 60, 120), font=font)
            img.save(str(placeholder), 'JPEG', quality=90)
            images.append(placeholder)
            print(f"[image] Platzhalter {i+1} erstellt")
    if not images:
        raise Exception("Keine Bilder konnten generiert werden!")
    return images

def generate_tts(story: str):
    """Generate narration using edge-tts (free Microsoft TTS)."""
    import asyncio
    try:
        import edge_tts
    except ImportError:
        subprocess.run(["pip", "install", "edge-tts"], check=True)
        import edge_tts
    
    lang_name = LANGUAGE_CONFIG["name"]
    voice = LANGUAGE_CONFIG["voice"]
    print(f"[tts] Generating narration ({lang_name}) with edge-tts...")
    
    async def generate():
        communicate = edge_tts.Communicate(story, voice)
        await communicate.save(str(NARRATION_FILE))
    
    asyncio.run(generate())
    print(f"[tts] Narration saved to {NARRATION_FILE}")

def generate_word_subtitles():
    """Generate WORD-BY-WORD subtitles using Vosk (lightweight!)."""
    print("[subs] Generating word-by-word subtitles with Vosk...")
    
    import json
    import wave
    from vosk import Model, KaldiRecognizer
    import os
    
    # Download Vosk model if not exists
    model_name = LANGUAGE_CONFIG["vosk_model"]
    model_url = LANGUAGE_CONFIG["vosk_url"]
    zip_path = LANGUAGE_CONFIG["vosk_zip"]
    
    if not os.path.exists(model_name):
        print(f"[subs] Downloading Vosk model ({model_name})...")
        import urllib.request
        import zipfile
        
        urllib.request.urlretrieve(model_url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        os.remove(zip_path)
        print("[subs] Model downloaded!")
    
    # Convert MP3 to WAV for Vosk
    wav_file = "output/narration.wav"
    os.system(f'ffmpeg -y -i {NARRATION_FILE} -ar 16000 -ac 1 {wav_file}')
    
    # Load Vosk model
    model = Model(model_name)
    
    # Open WAV file
    wf = wave.open(wav_file, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)  # Enable word-level timestamps
    
    # Process audio
    words = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if 'result' in result:
                for word_info in result['result']:
                    words.append({
                        'word': word_info['word'].upper(),
                        'start': word_info['start'],
                        'end': word_info['end']
                    })
    
    # Final result
    final_result = json.loads(rec.FinalResult())
    if 'result' in final_result:
        for word_info in final_result['result']:
            words.append({
                'word': word_info['word'].upper(),
                'start': word_info['start'],
                'end': word_info['end']
            })
    
    font_name = LANGUAGE_CONFIG.get("subtitle_font", "Arial")
    
    # Create ASS subtitle file - white bold text with thick black outline
    ass_content = f"""[Script Info]
Title: Self-Help
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},16,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,0,2,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    for word in words:
        start = word['start']
        end = word['end']
        text = word['word']
        
        start_time = f"{int(start//3600)}:{int((start%3600)//60):02d}:{start%60:.2f}"
        end_time = f"{int(end//3600)}:{int((end%3600)//60):02d}:{end%60:.2f}"
        
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
    
    # Save ASS file
    with open(SUBS_FILE, "w", encoding="utf-8") as f:
        f.write(ass_content)
    
    print(f"[subs] Subtitles saved ({len(words)} words)")

def get_audio_duration(audio_file):
    """Get duration of audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def create_animated_slideshow(image_paths):
    """Create animated slideshow with Ken Burns zoom effect."""
    print("[video] Creating animated slideshow with Ken Burns effect...")
    
    # Get audio duration to match video length
    duration = get_audio_duration(NARRATION_FILE)
    per_image = duration / len(image_paths)
    
    # Create individual animated clips with zoom effect
    clips = []
    for i, img_path in enumerate(image_paths):
        clip_file = OUTPUT_DIR / f"clip_{i:02d}.mp4"
        clips.append(clip_file)
        
        # Calculate frames (30 fps)
        frames = max(int(per_image * 30), 60)
        
        # Alternate between zoom in and zoom out for variety
        if i % 2 == 0:
            # Zoom in effect
            zoom_start = 1.0
            zoom_end = 1.3
        else:
            # Zoom out effect  
            zoom_start = 1.3
            zoom_end = 1.0
        
        # Simple zoom with scale filter (more reliable on Windows)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", (
                f"scale=8000:-1,"
                f"zoompan=z='if(lte(on,1),{zoom_start},{zoom_start}+(({zoom_end}-{zoom_start})/{frames})*on)':"
                f"d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={IMAGE_WIDTH}x{IMAGE_HEIGHT}:fps=30"
            ),
            "-t", str(per_image),
            "-c:v", "libx264",
            "-preset", "slow",  # Better quality
            "-crf", "18",  # High quality (lower = better, 18-23 is good)
            "-pix_fmt", "yuv420p",
            str(clip_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[video] Zoom failed for clip {i+1}, using fallback...")
            # Fallback: simple static with slight movement
            cmd_fallback = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(img_path),
                "-vf", f"scale={IMAGE_WIDTH}:{IMAGE_HEIGHT}:force_original_aspect_ratio=increase,crop={IMAGE_WIDTH}:{IMAGE_HEIGHT},fps=30",
                "-t", str(per_image),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(clip_file)
            ]
            subprocess.run(cmd_fallback, check=True, capture_output=True)
        
        print(f"[video] Animated clip {i+1}/{len(image_paths)}")
    
    # Create concat list
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")
    
    # Concatenate all clips
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(ANIMATED_VIDEO)
    ]
    subprocess.run(cmd, check=True)
    print(f"[video] Animated slideshow saved to {ANIMATED_VIDEO}")
    
    # Cleanup individual clips
    for clip in clips:
        if clip.exists():
            clip.unlink()

def add_subtitles():
    """Overlay ASS subtitles on video."""
    print("[video] Adding UPPERCASE subtitles...")
    
    # Windows path needs special handling for FFmpeg filter
    subs_path = str(SUBS_FILE.resolve()).replace("\\", "/").replace(":", "\\:")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(ANIMATED_VIDEO),
        "-vf", f"ass='{subs_path}'",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(VIDEO_WITH_SUBS)
    ]
    subprocess.run(cmd, check=True)
    print(f"[video] Video with subtitles saved to {VIDEO_WITH_SUBS}")

def merge_audio():
    """Merge video with narration and background music."""
    print("[merge] Merging audio with background music...")
    
    if MUSIC_FILE.exists():
        # Merge narration + background music (music at lower volume)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(VIDEO_WITH_SUBS),
            "-i", str(NARRATION_FILE),
            "-i", str(MUSIC_FILE),
            "-filter_complex", "[2:a]volume=0.25[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-shortest",
            "-c:v", "copy",
            str(FINAL_VIDEO)
        ]
    else:
        print("[merge] No music.mp3 found, using narration only")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(VIDEO_WITH_SUBS),
            "-i", str(NARRATION_FILE),
            "-map", "0:v",
            "-map", "1:a",
            "-shortest",
            "-c:v", "copy",
            str(FINAL_VIDEO)
        ]
    
    subprocess.run(cmd, check=True)
    print(f"[merge] Final video saved to {FINAL_VIDEO}")

def main():
    ensure_dirs()

    topic = choose_topic_for_today()
    print("=" * 60)
    print(f"=== Topic: {topic}")
    print("=" * 60)

    # 1. Generate story with Pollinations AI
    story = generate_story_with_pollinations(topic)
    
    # 2. Generate detailed ENGLISH visual prompts from the story
    scenes = generate_visual_prompts(story)
    
    # 3. Generate unique images for each scene
    images = generate_images(scenes, topic)

    # 4. Generate narration with TTS
    generate_tts(story)
    
    # VALIDATION: Check audio duration to prevent short videos
    audio_duration = get_audio_duration(NARRATION_FILE)
    print(f"[validation] 🎵 Audio duration: {audio_duration:.2f} seconds")
    
    if audio_duration < 10:
        raise ValueError(f"❌ Audio too short ({audio_duration:.2f}s)! Minimum 10 seconds required. Check story and TTS generation.")
    
    print(f"[validation] ✅ Audio duration valid ({audio_duration:.2f}s)")
    
    # 5. Generate word-level UPPERCASE subtitles with Vosk
    generate_word_subtitles()
    
    # 6. Create animated slideshow with Ken Burns effect
    create_animated_slideshow(images)
    
    # 7. Add subtitles overlay
    add_subtitles()
    
    # 8. Merge audio (narration + background music)
    merge_audio()

    print("=" * 60)
    print(f"✅ DONE. Video ready: {FINAL_VIDEO}")
    print(f"📊 Final duration: {audio_duration:.2f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    main()
