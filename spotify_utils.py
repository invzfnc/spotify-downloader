from typing import TypedDict, List

from spotapi import Public

class PlaylistInfo(TypedDict):
    """TypedDict for structured playlist information"""
    title: str
    artist: str
    length: int


def get_playlist_info(playlist_id: str) -> List[PlaylistInfo]:
    """Extracts data from Spotify and return them in format
       `[{"title": title, "artist": artist, "length": length}]`."""

    try:
        # Note: This is now handled in main.py's extract_playlist_id function
        items = next(Public.playlist_info(playlist_id))["items"]
        
        result = []
        
        for item in items:
            try:
                song = {}
                item = item["itemV2"]["data"]
                song["title"] = item["name"]
                song["artist"] = item["artists"]["items"][0]["profile"]["name"]
                song["length"] = int(item["trackDuration"]["totalMilliseconds"])
                result.append(song)
            except (KeyError, IndexError, TypeError) as e:
                print(f"Warning: Could not process song in playlist: {str(e)}")
                continue
        
        return result
    except Exception as e:
        print(f"Error fetching playlist: {str(e)}")
        return []
