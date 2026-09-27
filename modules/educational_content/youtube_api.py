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

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

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
    """
    Search YouTube for educational videos.

    Returns a list of video dictionaries containing:
    video ID, title, description, channel, publication date,
    thumbnail and YouTube URL.
    """

    # --------------------------------------------------------
    # Validate API key
    # --------------------------------------------------------

    if not YOUTUBE_API_KEY:
        raise ValueError(
            "YOUTUBE_API_KEY is missing. "
            "Add it to your .env file."
        )

    # --------------------------------------------------------
    # Validate search query
    # --------------------------------------------------------

    if query is None:
        raise ValueError(
            "Please enter a subject or topic."
        )

    if not isinstance(query, str):
        raise ValueError(
            "Search topic must be text."
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "Please enter a subject or topic."
        )

    # --------------------------------------------------------
    # Validate result count
    # --------------------------------------------------------

    if not isinstance(max_results, int):
        raise ValueError(
            "Maximum results must be a whole number."
        )

    if max_results <= 0:
        raise ValueError(
            "Maximum results must be greater than zero."
        )

    if max_results > 50:
        raise ValueError(
            "Maximum results cannot exceed 50."
        )

    # --------------------------------------------------------
    # API parameters
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Send API request
    # --------------------------------------------------------

    try:
        response = requests.get(
            YOUTUBE_SEARCH_URL,
            params=params,
            timeout=15
        )

    except requests.exceptions.Timeout as error:
        raise RuntimeError(
            "YouTube API request timed out. "
            "Please check your internet connection and try again."
        ) from error

    except requests.exceptions.ConnectionError as error:
        raise RuntimeError(
            "Unable to connect to YouTube. "
            "Please check your internet connection."
        ) from error

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Unable to contact YouTube API: {error}"
        ) from error

    # --------------------------------------------------------
    # Handle HTTP/API errors
    # --------------------------------------------------------

    if response.status_code != 200:

        try:
            error_data = response.json()

            api_error = (
                error_data
                .get("error", {})
                .get("errors", [])
            )

            if api_error:
                reason = api_error[0].get(
                    "reason",
                    ""
                )

                if reason == "quotaExceeded":
                    raise RuntimeError(
                        "YouTube API quota has been exceeded. "
                        "Please try again later."
                    )

                if reason in {
                    "keyInvalid",
                    "badRequest"
                }:
                    raise ValueError(
                        "The YouTube API key is invalid. "
                        "Please check your .env file."
                    )

            message = (
                error_data
                .get("error", {})
                .get("message")
            )

            if message:
                raise RuntimeError(
                    f"YouTube API error: {message}"
                )

        except ValueError:
            raise

        except RuntimeError:
            raise

        except Exception:
            pass

        raise RuntimeError(
            f"YouTube API request failed with status code "
            f"{response.status_code}."
        )

    # --------------------------------------------------------
    # Parse API response
    # --------------------------------------------------------

    try:
        data = response.json()

    except ValueError as error:
        raise RuntimeError(
            "YouTube returned an invalid response."
        ) from error

    # --------------------------------------------------------
    # Extract videos
    # --------------------------------------------------------

    videos = []

    for item in data.get("items", []):

        if not isinstance(item, dict):
            continue

        video_id = (
            item
            .get("id", {})
            .get("videoId")
        )

        snippet = item.get(
            "snippet",
            {}
        )

        if not video_id:
            continue

        if not isinstance(snippet, dict):
            snippet = {}

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

    # --------------------------------------------------------
    # Handle no results
    # --------------------------------------------------------

    if not videos:
        raise ValueError(
            f"No educational videos were found for "
            f"'{query}'. Please try a different topic."
        )

    return videos


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    try:

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

    except Exception as error:

        print(
            f"YouTube search failed: {error}"
        )