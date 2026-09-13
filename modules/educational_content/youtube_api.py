import os
import requests

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# YOUTUBE API SETTINGS
# ============================================================

YOUTUBE_API_KEY = os.getenv(
    "YOUTUBE_API_KEY"
)

YOUTUBE_SEARCH_URL = (
    "https://www.googleapis.com/youtube/v3/search"
)


# ============================================================
# SEARCH EDUCATIONAL VIDEOS
# ============================================================

def search_educational_videos(
    query,
    max_results=6
):

    if not YOUTUBE_API_KEY:

        raise ValueError(
            "YOUTUBE_API_KEY is missing. "
            "Add it to your .env file."
        )

    if not query or not query.strip():

        raise ValueError(
            "Please enter a subject or topic."
        )

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoCategoryId": "27",
        "maxResults": max_results,
        "relevanceLanguage": "en",
        "regionCode": "IN",
        "safeSearch": "moderate",
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(
        YOUTUBE_SEARCH_URL,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    videos = []

    for item in data.get(
        "items",
        []
    ):

        video_id = item.get(
            "id",
            {}
        ).get(
            "videoId"
        )

        snippet = item.get(
            "snippet",
            {}
        )

        if not video_id:
            continue

        videos.append(
            {
                "video_id": video_id,

                "title": snippet.get(
                    "title",
                    "Untitled"
                ),

                "description": snippet.get(
                    "description",
                    ""
                ),

                "channel_title": snippet.get(
                    "channelTitle",
                    "Unknown Channel"
                ),

                "published_at": snippet.get(
                    "publishedAt",
                    ""
                ),

                "thumbnail_url": (
                    snippet
                    .get("thumbnails", {})
                    .get("medium", {})
                    .get("url", "")
                ),

                "url": (
                    "https://www.youtube.com/watch?v="
                    + video_id
                )
            }
        )

    return videos


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    results = search_educational_videos(
        "Python programming",
        3
    )

    for video in results:

        print(
            video["title"]
        )

        print(
            video["url"]
        )

        print("-" * 50)