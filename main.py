from typing import Optional
import os
import sys
import time

# Import from utility modules
from spotify_utils import get_playlist_info
from ytmusic_utils import get_song_urls
from downloader import download_from_urls, DownloadStats

# Global variables
DOWNLOAD_PATH = "./downloads/" # ends with "/"
client = None
FFMPEG_PATH = None  # Will store custom FFmpeg path if provided


def extract_playlist_id(playlist_url: str) -> str:
    """Extract playlist ID from a Spotify playlist URL
    
    Args:
        playlist_url: Full Spotify playlist URL or ID
        
    Returns:
        Extracted playlist ID
    """
    if "spotify.com/playlist/" in playlist_url:
        # Extract ID from URL
        playlist_id = playlist_url.split("playlist/")[1].split("?")[0]
        return playlist_id
    return playlist_url  # Already an ID


def main(playlist_id: str, progress_callback: Optional[callable] = None, concurrent_searches: int = 3, concurrent_downloads: int = 3, ffmpeg_path: Optional[str] = None, download_path: Optional[str] = None) -> DownloadStats:
    """Main function to handle the playlist download workflow
    
    Args:
        playlist_id: Spotify playlist ID or URL
        progress_callback: Optional callback function for progress updates
        concurrent_searches: Number of concurrent song searches (default: 3)
        concurrent_downloads: Number of concurrent downloads (default: 3)
        ffmpeg_path: Optional path to FFmpeg executable
        download_path: Optional path to download directory
    
    Returns:
        Download statistics dictionary
    """
    # Set custom FFmpeg path if provided
    global FFMPEG_PATH
    if ffmpeg_path and os.path.isfile(ffmpeg_path):
        FFMPEG_PATH = ffmpeg_path
        
    # Set custom download path if provided
    global DOWNLOAD_PATH
    if download_path:
        DOWNLOAD_PATH = download_path
        
    # Extract playlist ID if a full URL was provided
    playlist_id = extract_playlist_id(playlist_id)
    
    # Extract playlist info
    playlist_info = get_playlist_info(playlist_id)
    
    if not playlist_info:
        if progress_callback:
            progress_callback("No songs found in playlist or playlist not found", 100, {
                "start_time": time.time(),
                "total_bytes": 0,
                "downloaded_bytes": 0,
                "current_speed": 0,
                "successful": [],
                "failed": [],
                "in_progress": set(),
                "completed": 0
            })
        return {
            "start_time": time.time(),
            "total_bytes": 0,
            "downloaded_bytes": 0,
            "current_speed": 0,
            "successful": [],
            "failed": [],
            "in_progress": set(),
            "completed": 0
        }
    
    # Update progress
    if progress_callback:
        progress_callback(f"Found {len(playlist_info)} songs in playlist", 10)
    
    # Get YouTube Music URLs for each song
    download_urls = get_song_urls(playlist_info, progress_callback, 
                                concurrent_searches=concurrent_searches)
    
    # Update progress
    if progress_callback:
        progress_callback(f"Found {len(download_urls)} out of {len(playlist_info)} songs", 40)
    
    # Download songs from the URLs
    download_stats = download_from_urls(download_urls, progress_callback,
                                      concurrent_downloads=concurrent_downloads,
                                      ffmpeg_path=FFMPEG_PATH,
                                      download_path=DOWNLOAD_PATH)
    
    # Print final stats
    if progress_callback:
        progress_callback(
            f"Downloaded {len(download_stats['successful'])} songs, failed {len(download_stats['failed'])} songs",
            100,
            download_stats
        )
    
    return download_stats
    
if __name__ == "__main__":
    import sys

    def progress_callback(message: str, progress: float, stats: Optional[DownloadStats] = None):
        """Simple command-line progress callback for testing"""
        print(f"{progress:.1f}% - {message}")
    
    # For testing - use a test playlist
    if len(sys.argv) > 1:
        playlist_url = sys.argv[1]
    else:
        playlist_url = "https://open.spotify.com/playlist/2LE8ZObOZOqjsGrR6QFXwu?si=9b4a5deb005148e1"  # Test playlist
    
    main(playlist_url, progress_callback)
