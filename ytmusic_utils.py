from typing import TypedDict, List, Tuple, Dict, Optional, Any, Set
import concurrent.futures
from threading import Lock
from time import sleep
from random import uniform

from innertube import InnerTube

# Import PlaylistInfo from spotify_utils
from spotify_utils import PlaylistInfo


class SongData(TypedDict):
    """TypedDict for structured song data"""
    url: str
    title: str
    original_title: str
    artist: str
    match_quality: float


def convert_to_milliseconds(text: str) -> int:
    """Converts `"%M:%S"` timestamp from YTMusic to milliseconds."""
    try:
        minutes, seconds = text.split(":")
        return (int(minutes) * 60 + int(seconds)) * 1000
    except (ValueError, TypeError):
        # Handle invalid format gracefully
        print(f"Warning: Could not convert timestamp '{text}' to milliseconds")
        return 0


def get_song_url(song_info: PlaylistInfo, client: Optional[InnerTube] = None) -> Tuple[Optional[str], Optional[str]]:
    """Simulates searching from the YTMusic web and returns url to closest match based on song length."""
    if client is None:
        client = InnerTube("WEB_REMIX", "1.20250203.01.00")
    data = client.search(f"{song_info['title']} {song_info['artist']}")

    try:
        # Handle "did you mean" case
        if "itemSectionRenderer" in data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]:
            del data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]

        # Extract top result length and video info
        top_result_length = None
        top_result_video_id = None
        top_result_title = None
        try:
            top_result_length = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["subtitle"]["runs"][-1]["text"]
            top_result_video_id = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"]
            top_result_title = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["title"]["runs"][0]["text"]
        except (KeyError, IndexError):
            pass

        # Extract first song result length and video info
        first_song_length = None
        first_song_video_id = None
        first_song_title = None
        try:
            first_song_length = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][-1]["text"]
            first_song_video_id = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["overlay"]["musicItemThumbnailOverlayRenderer"]["content"]["musicPlayButtonRenderer"]["playNavigationEndpoint"]["watchEndpoint"]["videoId"]
            first_song_title = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"]
        except (KeyError, IndexError):
            pass

        # Compare song lengths to find the best match
        if top_result_length and first_song_length and top_result_video_id and first_song_video_id:
            top_result_diff = abs(convert_to_milliseconds(top_result_length) - song_info["length"])
            first_song_diff = abs(convert_to_milliseconds(first_song_length) - song_info["length"])

            if top_result_diff < first_song_diff:
                # Top result is a better match
                video_id = top_result_video_id
                video_title = top_result_title
            else:
                # First song is a better match
                video_id = first_song_video_id
                video_title = first_song_title
        elif top_result_video_id:
            # Only top result available
            video_id = top_result_video_id
            video_title = top_result_title
        elif first_song_video_id:
            # Only first song available
            video_id = first_song_video_id
            video_title = first_song_title
        else:
            raise ValueError("Could not find video ID in search results")

        url = f"https://music.youtube.com/watch?v={video_id}"
        return url, video_title

    except Exception as e:
        print(f"Error processing search results: {str(e)}")
        # Return a tuple to maintain compatibility
        return None, None


def get_song_url_improved(title: str, artist: str, length: int) -> Optional[SongData]:
    """Searches for a song on YouTube Music and returns the URL of the best match.

    Args:
        title: Song title
        artist: Artist name
        length: Song length in milliseconds

    Returns:
        Dictionary with song data or None if no match found
    """
    try:
        client = InnerTube("WEB_REMIX", "1.20250203.01.00")
        data = client.search(f"{title} {artist}")

        search_results = []
        try:
            # Extract top result length and video info
            top_result_length = None
            top_result_video_id = None
            top_result_title = None
            try:
                top_result_length = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["subtitle"]["runs"][-1]["text"]
                top_result_video_id = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"]
                top_result_title = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["title"]["runs"][0]["text"]
                search_results.append({
                    "duration": top_result_length,
                    "videoId": top_result_video_id,
                    "title": top_result_title
                })
            except (KeyError, IndexError):
                pass

            # Extract first song result length and video info
            first_song_length = None
            first_song_video_id = None
            first_song_title = None
            try:
                first_song_length = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][-1]["text"]
                first_song_video_id = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["overlay"]["musicItemThumbnailOverlayRenderer"]["content"]["musicPlayButtonRenderer"]["playNavigationEndpoint"]["watchEndpoint"]["videoId"]
                first_song_title = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"]
                search_results.append({
                    "duration": first_song_length,
                    "videoId": first_song_video_id,
                    "title": first_song_title
                })
            except (KeyError, IndexError):
                pass
        except Exception as e:
            print(f"Error processing search results: {str(e)}")
            return None

        if not search_results:
            print(f"No search results found for '{title}' by {artist}")
            return None

        # Find the best match by comparing duration
        best_match = None
        min_diff = float('inf')

        for result in search_results:
            try:
                result_length = convert_to_milliseconds(result.get("duration", "0:00"))
                diff = abs(result_length - length)

                # If this result is closer in length than our current best match
                if diff < min_diff:
                    min_diff = diff
                    best_match = result
            except Exception as e:
                print(f"Error processing search result: {str(e)}")
                continue

        if not best_match:
            print(f"No suitable match found for '{title}' by {artist}")
            return None

        # Calculate match quality (0-100%)
        match_quality = max(0, 100 - (min_diff / (length * 0.01)))

        # Create song data dictionary
        song_data = {
            "title": title,
            "artist": artist,
            "url": f"https://music.youtube.com/watch?v={best_match.get('videoId')}",
            "original_title": title,
            "match_quality": match_quality
        }

        return song_data
    except Exception as e:
        print(f"Error searching for '{title}' by {artist}: {str(e)}")
        return None


def get_song_urls(playlist_info: List[PlaylistInfo], progress_callback: Optional[callable] = None, concurrent_searches: int = 3) -> List[SongData]:
    """Searches for songs in playlist concurrently and returns list of results."""
    urls = []
    total_songs = len(playlist_info)

    # Mutex for thread-safe updates to the progress
    progress_lock = Lock()
    completed_count = 0

    def search_song(index: int, song_info: PlaylistInfo) -> bool:
        nonlocal completed_count

        # Update progress at start of search
        with progress_lock:
            if progress_callback:
                progress_callback(f"Finding: {song_info['title']} by {song_info['artist']} ({index}/{total_songs})", 
                                 20 + (completed_count / total_songs) * 20)

        # Small delay between API calls to avoid rate limiting (reduced from 1-3 seconds to 0.2-0.5 seconds)
        sleep(uniform(0.2, 0.5))

        # Perform the search
        result = get_song_url_improved(song_info['title'], song_info['artist'], song_info['length'])

        # Process results and update progress
        with progress_lock:
            completed_count += 1

            if result:  # Only add if we got a valid URL
                urls.append(result)

                if progress_callback:
                    progress_callback(f"Found: {result['title']} ({index}/{total_songs})", 
                                     20 + (completed_count / total_songs) * 20)
            else:
                if progress_callback:
                    progress_callback(f"Skipped: Could not find {song_info['title']} ({index}/{total_songs})", 
                                     20 + (completed_count / total_songs) * 20)

        return result is not None

    # Execute searches concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_searches) as executor:
        futures = {}

        # Submit all search tasks
        for index, song_info in enumerate(playlist_info, 1):
            future = executor.submit(search_song, index, song_info)
            futures[future] = index

        # Wait for all searches to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in search task: {str(e)}")

    return urls
