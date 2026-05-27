"""
Multi-Platform Upload Script

Uploads videos to:
- YouTube Shorts
- Instagram Reels
- TikTok
- Facebook Reels
- Threads
- Twitter/X
- Telegram
- VK

Each platform requires its own API credentials.
"""

import os
from pathlib import Path
import datetime

# Import platform-specific uploaders
from upload_to_youtube import upload_to_youtube
from upload_instagram import upload_to_instagram
from upload_tiktok import upload_to_tiktok
from upload_facebook import upload_to_facebook
from upload_threads import upload_to_threads
from upload_twitter import upload_to_twitter
from upload_telegram import upload_to_telegram
from upload_vk import upload_to_vk

def main():
    """Upload video to all configured platforms."""
    video_file = Path('output/final_video.mp4')
    
    if not video_file.exists():
        print("[upload] ❌ No video found at output/final_video.mp4")
        return
    
    # Read story for metadata
    story_file = Path('output/story.txt')
    if story_file.exists():
        story = story_file.read_text(encoding='utf-8')
        # Use first sentence as title
        title_parts = story.split('.')
        title = title_parts[0][:100] if title_parts else "Добрая сказка для детей"
        # Use first 2-3 sentences as description snippet
        story_snippet = ". ".join(title_parts[:3])[:300] if len(title_parts) > 2 else story[:300]
    else:
        title = f"Добрая сказка для детей - {datetime.date.today()}"
        story_snippet = ""
    
    desc_parts = [story_snippet] if story_snippet else []
    desc_parts.append(
        "Подпишись на ежедневные добрые сказки! 🐻"
    )
    desc_parts.append(
        "#СказкиДляДетей #ДобрыеСказки #Животные #ДетскиеСказки #СказкаНаНочь #ДляДетей #Мораль #УрокДоброты #Shorts"
    )
    description = "\n\n".join(desc_parts)
    
    tags = [
        'Сказки для Детей', 'Детские Сказки', 'Животные', 'Добрые Истории',
        'Сказка На Ночь', 'Обучение', 'Для Малышей', 'Мораль', 'Дружба',
        'Shorts', 'Анимация', 'Русские Сказки', 'Познавательное'
    ]
    
    results = {}
    
    # Upload to YouTube
    if all([
        os.getenv('YT_CLIENT_ID'),
        os.getenv('YT_CLIENT_SECRET'),
        os.getenv('YT_REFRESH_TOKEN')
    ]):
        print("\n" + "="*60)
        print("📺 Uploading to YouTube...")
        print("="*60)
        try:
            result = upload_to_youtube(video_file, title, description, tags)
            results['youtube'] = result
            print(f"✅ YouTube: https://youtube.com/shorts/{result['id']}")
        except Exception as e:
            print(f"❌ YouTube failed: {e}")
            results['youtube'] = None
    else:
        print("⏭️  Skipping YouTube (credentials not set)")
    
    # Upload to Instagram
    if all([
        os.getenv('IG_ACCESS_TOKEN') or os.getenv('INSTAGRAM_ACCESS_TOKEN'),
        os.getenv('IG_USER_ID') or os.getenv('INSTAGRAM_ACCOUNT_ID')
    ]):
        print("\n" + "="*60)
        print("📸 Uploading to Instagram...")
        print("="*60)
        try:
            result = upload_to_instagram(video_file, description)
            results['instagram'] = result
            print(f"✅ Instagram: Uploaded successfully")
        except Exception as e:
            print(f"❌ Instagram failed: {e}")
            results['instagram'] = None
    else:
        print("⏭️  Skipping Instagram (credentials not set)")
    
    # Upload to TikTok
    if os.getenv('TIKTOK_ACCESS_TOKEN'):
        print("\n" + "="*60)
        print("🎵 Uploading to TikTok...")
        print("="*60)
        try:
            result = upload_to_tiktok(video_file, title, description)
            results['tiktok'] = result
            print(f"✅ TikTok: Uploaded successfully")
        except Exception as e:
            print(f"❌ TikTok failed: {e}")
            results['tiktok'] = None
    else:
        print("⏭️  Skipping TikTok (credentials not set)")
    
    # Upload to Facebook
    if all([
        os.getenv('FB_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN'),
        os.getenv('FB_PAGE_ID') or os.getenv('FACEBOOK_PAGE_ID')
    ]):
        print("\n" + "="*60)
        print("📘 Uploading to Facebook...")
        print("="*60)
        try:
            result = upload_to_facebook(video_file, description)
            results['facebook'] = result
            print(f"✅ Facebook: Uploaded successfully")
        except Exception as e:
            print(f"❌ Facebook failed: {e}")
            results['facebook'] = None
    else:
        print("⏭️  Skipping Facebook (credentials not set)")
    
    # Upload to Threads
    if all([
        os.getenv('THREADS_ACCESS_TOKEN'),
        os.getenv('THREADS_USER_ID')
    ]):
        print("\n" + "="*60)
        print("🧵 Uploading to Threads...")
        print("="*60)
        try:
            result = upload_to_threads(video_file, description)
            results['threads'] = result
            print(f"✅ Threads: Uploaded successfully")
        except Exception as e:
            print(f"❌ Threads failed: {e}")
            results['threads'] = None
    else:
        print("⏭️  Skipping Threads (credentials not set)")
    
    # Upload to Twitter/X
    print("\n" + "="*60)
    print("🐦 Checking Twitter/X credentials...")
    print("="*60)
    
    twitter_api_key = os.getenv('TWITTER_API_KEY')
    twitter_api_secret = os.getenv('TWITTER_API_SECRET')
    twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    twitter_access_secret = os.getenv('TWITTER_ACCESS_SECRET')
    
    # Debug: Show which credentials are set
    print(f"[twitter] API Key: {'✅ Set' if twitter_api_key else '❌ Not set'}")
    print(f"[twitter] API Secret: {'✅ Set' if twitter_api_secret else '❌ Not set'}")
    print(f"[twitter] Access Token: {'✅ Set' if twitter_access_token else '❌ Not set'}")
    print(f"[twitter] Access Secret: {'✅ Set' if twitter_access_secret else '❌ Not set'}")
    
    if all([twitter_api_key, twitter_api_secret, twitter_access_token, twitter_access_secret]):
        print(f"[twitter] ✅ All credentials present!")
        print(f"[twitter] 🚀 Starting upload...")
        try:
            result = upload_to_twitter(video_file, description)
            results['twitter'] = result
            print(f"\n✅ Twitter: Upload successful!")
            print(f"   Tweet ID: {result.get('id', 'N/A')}")
            print(f"   URL: {result.get('url', 'N/A')}")
        except Exception as e:
            print(f"\n❌ Twitter upload FAILED!")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            print(f"   Full error: {repr(e)}")
            
            # Show troubleshooting tips
            print(f"\n🔍 Troubleshooting:")
            print(f"   - Check if Twitter credentials are correct in GitHub Secrets")
            print(f"   - Verify Twitter app has 'Read and Write' permissions")
            print(f"   - Check if Access Token was regenerated after permission change")
            print(f"   - Verify video file exists and is valid")
            
            results['twitter'] = None
    else:
        print(f"[twitter] ⏭️  Skipping Twitter (credentials not set)")
        print(f"[twitter] Missing credentials - add to GitHub Secrets:")
        if not twitter_api_key:
            print(f"   - TWITTER_API_KEY")
        if not twitter_api_secret:
            print(f"   - TWITTER_API_SECRET")
        if not twitter_access_token:
            print(f"   - TWITTER_ACCESS_TOKEN")
        if not twitter_access_secret:
            print(f"   - TWITTER_ACCESS_SECRET")
        results['twitter'] = None
    
    # Upload to Telegram
    if all([
        os.getenv('TELEGRAM_BOT_TOKEN'),
        os.getenv('TELEGRAM_CHANNEL_ID')
    ]):
        print("\n" + "="*60)
        print("✈️ Uploading to Telegram...")
        print("="*60)
        try:
            result = upload_to_telegram(video_file, description)
            results['telegram'] = result
            print(f"✅ Telegram: Uploaded successfully")
        except Exception as e:
            print(f"❌ Telegram failed: {e}")
            results['telegram'] = None
    else:
        print("⏭️  Skipping Telegram (credentials not set)")
    
    # Upload to VK
    if all([
        os.getenv('VK_ACCESS_TOKEN'),
        os.getenv('VK_GROUP_ID')
    ]):
        print("\n" + "="*60)
        print("🇷🇺 Uploading to VK...")
        print("="*60)
        try:
            result = upload_to_vk(video_file, description, title)
            results['vk'] = result
            print(f"✅ VK: {result.get('post_url', 'Uploaded successfully')}")
        except Exception as e:
            print(f"❌ VK failed: {e}")
            results['vk'] = None
    else:
        print("⏭️  Skipping VK (credentials not set)")
    
    # Summary
    print("\n" + "="*60)
    print("📊 Upload Summary")
    print("="*60)
    for platform, result in results.items():
        status = "✅ Success" if result else "❌ Failed"
        print(f"{platform.capitalize()}: {status}")
    print("="*60)

if __name__ == '__main__':
    main()

