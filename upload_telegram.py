import os
import requests
from pathlib import Path

def upload_to_telegram():
    """Upload video to Telegram channel."""
    print("-" * 50)
    print("TELEGRAM UPLOAD")
    print("-" * 50)

    # 1. Get credentials
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")

    if not bot_token or not channel_id:
        print("[telegram] ⚠️ TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID not set. Skipping.")
        return

    # 2. Get video file
    video_path = Path("output/final_video.mp4")
    if not video_path.exists():
        print("[telegram] ❌ Video file not found at output/final_video.mp4")
        return

    # 3. Get title/caption
    caption = "🐻 Добрая сказка для детей\n\n#СказкиДляДетей #ДобрыеСказки #Животные"
    try:
        story_path = Path("output/story.txt")
        if story_path.exists():
            text = story_path.read_text(encoding="utf-8").strip()
            # Use first sentence as title if possible
            title = text.split(".")[0]
            if len(title) > 100:
                title = title[:97] + "..."
            caption = f"**{title}**\n\n{text[:300]}\n\n#СказкиДляДетей #ДобрыеСказки #Животные #СказкаНаНочь #ДляДетей\n\nПодпишись на ежедневные добрые сказки! 🐻"
    except Exception as e:
        print(f"[telegram] Warning reading story: {e}")

    # 4. Upload
    print(f"[telegram] Uploading video to {channel_id}...")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    
    try:
        with open(video_path, "rb") as video_file:
            files = {"video": video_file}
            data = {
                "chat_id": channel_id,
                "caption": caption,
                "parse_mode": "Markdown",
                "supports_streaming": "true"
            }
            
            response = requests.post(url, files=files, data=data, timeout=120)
            response.raise_for_status()
            
            print("[telegram] ✅ Upload successful!")
            try:
                result = response.json()
                if result.get("ok"):
                    print(f"[telegram] Message ID: {result['result']['message_id']}")
                else:
                    print(f"[telegram] API returned error: {result}")
            except:
                pass
                
    except Exception as e:
        print(f"[telegram] ❌ Upload failed: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    upload_to_telegram()
