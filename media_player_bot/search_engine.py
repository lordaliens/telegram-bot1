import os
import asyncio
import yt_dlp
import google.generativeai as genai
from config import GEMINI_API_KEY
from urllib.parse import urlparse

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Configure model to use appropriate generation config
    generation_config = {
        "temperature": 0.7,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)
else:
    model = None

async def extract_search_query(description: str) -> str:
    """Uses Gemini to extract a clean search query from a user description."""
    if not model:
        # Fallback if no Gemini key
        return description

    prompt = f"""
    You are an AI assistant that extracts search keywords from user descriptions for music or videos.
    The user might ask in Persian. Convert their request into a clean, short search query suitable for YouTube or Google.
    Do NOT include extra words like "find", "search", "video of".
    Just return the keywords.

    User Description: {description}
    Keywords:
    """
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        return description # Fallback to original text

def is_url(text: str) -> bool:
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

async def download_media(query: str, download_dir: str = "downloads") -> dict:
    """Downloads media using yt-dlp based on a query or URL."""
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    is_link = is_url(query)

    # If it's a description and not a URL, use Gemini to refine it, then use ytsearch
    search_query = query if is_link else f"ytsearch1:{await extract_search_query(query)}"

    ydl_opts = {
        'format': 'bestaudio/best', # Prefer audio for voice chat, but best overall
        'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
    }

    try:
        def extract_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=True)
                if 'entries' in info:
                    # It was a search, get first result
                    return info['entries'][0]
                return info

        info_dict = await asyncio.to_thread(extract_info)

        file_path = ydl_opts['outtmpl'].replace('%(title)s', info_dict['title']).replace('%(ext)s', info_dict['ext'])
        # Handle cases where title has special chars and yt-dlp sanitizes it
        # Safest is to list files in dir and find the newest, or just use info_dict['requested_downloads'][0]['filepath']
        if 'requested_downloads' in info_dict and len(info_dict['requested_downloads']) > 0:
            file_path = info_dict['requested_downloads'][0]['filepath']

        return {
            "title": info_dict.get('title', 'Unknown Title'),
            "duration": info_dict.get('duration', 0),
            "file_path": file_path,
            "url": info_dict.get('webpage_url', query)
        }
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return None
