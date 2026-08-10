"""
YouTube Upload Script - Updated for 2025

Uses refresh token from GitHub Secrets to upload videos.
"""

import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import datetime

def get_authenticated_service():
    """Authenticate using refresh token from environment."""
    
    # Get credentials from GitHub Secrets
    client_id = os.getenv('YT_CLIENT_ID')
    client_secret = os.getenv('YT_CLIENT_SECRET')
    refresh_token = os.getenv('YT_REFRESH_TOKEN')
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing credentials! Set these GitHub Secrets:\n"
            "  - YT_CLIENT_ID\n"
            "  - YT_CLIENT_SECRET\n"
            "  - YT_REFRESH_TOKEN"
        )
    
    # Create credentials from refresh token
    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube"]
    )
    
    # Refresh to get access token
    creds.refresh(Request())
    
    return build('youtube', 'v3', credentials=creds)

def upload_to_youtube(video_file, title, description, tags, category_id='22'):
    """Upload video to YouTube and return result."""
    youtube = get_authenticated_service()
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }
    
    if '#Shorts' not in body['snippet']['description']:
        body['snippet']['description'] += '\n\n#Shorts'
    
    media = MediaFileUpload(
        str(video_file),
        chunksize=-1,
        resumable=True,
        mimetype='video/mp4'
    )
    
    print(f"[youtube] Uploading: {title}")
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[youtube] Progress: {int(status.progress() * 100)}%")
    
    print(f"[youtube] âœ… Uploaded! Video ID: {response['id']}")
    print(f"[youtube] URL: https://youtube.com/shorts/{response['id']}")
    
    return response

def main():
    """Upload the generated video to YouTube."""
    video_file = Path('output/final_video.mp4')
    
    if not video_file.exists():
        print("[youtube] âŒ No video found at output/final_video.mp4")
        return
    
    # Read the topic from used_topics.txt (last line is the current topic)
    topic = ""
    used_topics_file = Path('used_topics.txt')
    
    if used_topics_file.exists():
        with open(used_topics_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            if lines:
                topic = lines[-1]  # Get the last used topic
    
    # Use topic as title (or fallback)
    if topic:
        title = topic
    else:
        title = "ÐŸÑÐ¸Ñ…Ð¾Ð»Ð¾Ð³Ð¸Ñ Ð¸ Ð¡Ð°Ð¼Ð¾Ð¿Ð¾Ð¼Ð¾Ñ‰ÑŒ"
    
    # Read story for description snippet
    story_text = ""
    story_file = Path('output/story.txt')
    if story_file.exists():
        story_text = story_file.read_text(encoding='utf-8').strip()[:300]
    
    desc_parts = [story_text] if story_text else []
    desc_parts.append(
        "ÐŸÐ¾Ð´Ð¿Ð¸ÑˆÐ¸ÑÑŒ Ð½Ð° ÐµÐ¶ÐµÐ´Ð½ÐµÐ²Ð½Ñ‹Ðµ ÑÐ¾Ð²ÐµÑ‚Ñ‹ Ð¿Ð¾ Ð¿ÑÐ¸Ñ…Ð¾Ð»Ð¾Ð³Ð¸Ð¸ Ð¸ ÑÐ°Ð¼Ð¾Ð¿Ð¾Ð¼Ð¾Ñ‰Ð¸!"
    )
    desc_parts.append(
        "#ÐŸÑÐ¸Ñ…Ð¾Ð»Ð¾Ð³Ð¸Ñ #Ð¡Ð°Ð¼Ð¾Ð¿Ð¾Ð¼Ð¾Ñ‰ÑŒ #ÐœÐ¾Ñ‚Ð¸Ð²Ð°Ñ†Ð¸Ñ #Ð¡Ð°Ð¼Ð¾Ñ€Ð°Ð·Ð²Ð¸Ñ‚Ð¸Ðµ #Ð­Ð¼Ð¾Ñ†Ð¸Ð¾Ð½Ð°Ð»ÑŒÐ½Ñ‹Ð¹Ð˜Ð½Ñ‚ÐµÐ»Ð»ÐµÐºÑ‚ #Ð¡Ð°Ð¼Ð¾Ð¾Ñ†ÐµÐ½ÐºÐ° #ÐŸÑ€Ð¾Ð´ÑƒÐºÑ‚Ð¸Ð²Ð½Ð¾ÑÑ‚ÑŒ #Shorts"
    )
    description = "\n\n".join(desc_parts)
    
    tags = [
        'ÐŸÑÐ¸Ñ…Ð¾Ð»Ð¾Ð³Ð¸Ñ', 'Ð¡Ð°Ð¼Ð¾Ð¿Ð¾Ð¼Ð¾Ñ‰ÑŒ', 'ÐœÐ¾Ñ‚Ð¸Ð²Ð°Ñ†Ð¸Ñ', 'Ð¡Ð°Ð¼Ð¾Ñ€Ð°Ð·Ð²Ð¸Ñ‚Ð¸Ðµ',
        'Ð­Ð¼Ð¾Ñ†Ð¸Ð¾Ð½Ð°Ð»ÑŒÐ½Ñ‹Ð¹ Ð˜Ð½Ñ‚ÐµÐ»Ð»ÐµÐºÑ‚', 'Ð¡Ð°Ð¼Ð¾Ð¾Ñ†ÐµÐ½ÐºÐ°', 'Ð”Ð»Ñ Ð’Ð·Ñ€Ð¾ÑÐ»Ñ‹Ñ…', 'ÐŸÐ¾Ð·Ð¸Ñ‚Ð¸Ð²Ð½Ð°Ñ ÐŸÑÐ¸Ñ…Ð¾Ð»Ð¾Ð³Ð¸Ñ', 'ÐŸÑ€Ð¾Ð´ÑƒÐºÑ‚Ð¸Ð²Ð½Ð¾ÑÑ‚ÑŒ',
        'Shorts', 'ÐÐ½Ð¸Ð¼Ð°Ñ†Ð¸Ñ', 'Ð ÑƒÑÑÐºÐ¸Ðµ Ð¡ÐºÐ°Ð·ÐºÐ¸', 'ÐŸÐ¾Ð·Ð½Ð°Ð²Ð°Ñ‚ÐµÐ»ÑŒÐ½Ð¾Ðµ'
    ]
    
    # Upload
    try:
        upload_to_youtube(
            video_file=video_file,
            title=title,
            description=description,
            tags=tags,
            category_id='22'
        )
    except Exception as e:
        print(f"[youtube] âŒ Upload failed: {e}")
        raise

if __name__ == '__main__':
    main()
