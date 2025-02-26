from typing import TypedDict, List, Tuple, Dict, Optional, Any, Set
import concurrent.futures
from threading import Lock

from spotapi import Public
from innertube import InnerTube
from yt_dlp import YoutubeDL

from time import sleep
from random import uniform
    
DOWNLOAD_PATH = "./downloads/" # ends with "/"
client = None


class PlaylistInfo(TypedDict):
    """TypedDict for structured playlist information"""
    title: str
    artist: str
    length: int


class SongData(TypedDict):
    """TypedDict for structured song data"""
    url: str
    title: str
    original_title: str
    artist: str


class DownloadStats(TypedDict):
    """TypedDict for structured download statistics"""
    start_time: float
    total_bytes: int
    downloaded_bytes: int
    current_speed: float
    successful: List[SongData]
    failed: List[SongData]
    in_progress: Set[str]
    completed: int


def get_playlist_info(playlist_id: str) -> List[PlaylistInfo]:
    """Extracts data from Spotify and return them in format
       `[{"title": title, "artist": artist, "length": length}]`."""

    items = next(Public.playlist_info(playlist_id))["items"]

    result = []
    
    for item in items:
        song = {}
        item = item["itemV2"]["data"]
        song["title"] = item["name"]
        song["artist"] = item["artists"]["items"][0]["profile"]["name"]
        song["length"] = int(item["trackDuration"]["totalMilliseconds"])
        result.append(song)

    return result

def convert_to_milliseconds(text: str) -> int:
    """Converts `"%M:%S"` timestamp from YTMusic to milliseconds."""
    minutes, seconds = text.split(":")
    return (int(minutes) * 60 + int(seconds)) * 1000
    
def get_song_url(song_info: PlaylistInfo, client: Optional[InnerTube] = None) -> Tuple[Optional[str], Optional[str]]:
    """Simulates searching from the YTMusic web and returns url to closest match."""

    if client is None:
        client = InnerTube("WEB_REMIX", "1.20250203.01.00")
    data = client.search(f"{song_info['title']} {song_info['artist']}")

    try:
        contents = data.get("contents", {}).get("tabbedSearchResultsRenderer", {}).get("tabs", [{}])[0].get("tabRenderer", {}).get("content", {}).get("sectionListRenderer", {}).get("contents", [])
        
        if not contents:
            raise ValueError("No search results found")
            
        # Find the first music item
        music_item = None
        video_id = None
        video_title = None
        
        for item in contents:
            # Check for musicCardShelfRenderer (top result)
            if "musicCardShelfRenderer" in item:
                renderer = item["musicCardShelfRenderer"]
                if "title" in renderer and "runs" in renderer["title"]:
                    run = renderer["title"]["runs"][0]
                    if "navigationEndpoint" in run and "watchEndpoint" in run["navigationEndpoint"]:
                        video_id = run["navigationEndpoint"]["watchEndpoint"]["videoId"]
                        video_title = run["text"]
                        break
                        
            # Check for musicShelfRenderer (list results)
            elif "musicShelfRenderer" in item:
                renderer = item["musicShelfRenderer"]
                if "contents" in renderer and len(renderer["contents"]) > 0:
                    first_item = renderer["contents"][0].get("musicResponsiveListItemRenderer", {})
                    for column in first_item.get("flexColumns", []):
                        col_renderer = column.get("musicResponsiveListItemFlexColumnRenderer", {})
                        if "navigationEndpoint" in str(col_renderer):  # Quick way to check if this column has the video info
                            for text in col_renderer.get("text", {}).get("runs", []):
                                if "navigationEndpoint" in text and "watchEndpoint" in text["navigationEndpoint"]:
                                    video_id = text["navigationEndpoint"]["watchEndpoint"]["videoId"]
                                    video_title = text["text"]
                                    break
                            if video_id:
                                break
                if video_id:
                    break

        if not video_id:
            raise ValueError("Could not find video ID in search results")

        url = f"https://music.youtube.com/watch?v={video_id}"
        return url, video_title

    except Exception as e:
        print(f"Error processing search results: {str(e)}")
        # Return a tuple to maintain compatibility
        return None, None

def get_song_urls(playlist_info: List[PlaylistInfo], progress_callback: Optional[callable] = None, concurrent_searches: int = 3) -> List[SongData]:
    """Searches for songs in playlist concurrently and returns list of results."""
    urls = []
    client = InnerTube("WEB_REMIX", "1.20250203.01.00")
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
        result = get_song_url(song_info, client)
        
        # Process results and update progress
        with progress_lock:
            completed_count += 1
            
            if result[0]:  # Only add if we got a valid URL
                urls.append({"url": result[0], "title": result[1], "original_title": song_info['title'], "artist": song_info['artist']})
                if progress_callback:
                    progress_callback(f"Found: {result[1]} ({index}/{total_songs})", 
                                     20 + (completed_count / total_songs) * 20)
            else:
                if progress_callback:
                    progress_callback(f"Skipped: Could not find {song_info['title']} ({index}/{total_songs})", 
                                     20 + (completed_count / total_songs) * 20)
        
        return result[0] is not None
    
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
                if progress_callback:
                    with progress_lock:
                        progress_callback(f"Error: {str(e)}", 20 + (completed_count / total_songs) * 20)
    
    return urls

def download_from_urls(urls: List[SongData], progress_callback: Optional[callable] = None, concurrent_downloads: int = 3) -> DownloadStats:
    """Downloads list of songs with yt-dlp with concurrent downloads support"""
    
    import concurrent.futures
    import time
    from collections import defaultdict
    import os
    import platform
    from pathlib import Path
    
    # Track overall download stats
    download_stats: DownloadStats = {
        "start_time": time.time(),
        "total_bytes": 0,
        "downloaded_bytes": 0,
        "current_speed": 0,
        "successful": [],
        "failed": [],
        "in_progress": set(),
        "completed": 0
    }
    stats_lock = Lock()
    
    # Check if ffmpeg is available
    ffmpeg_found = False
    try:
        import subprocess
        import shutil
        
        # First check if ffmpeg is in PATH
        ffmpeg_in_path = shutil.which("ffmpeg") is not None
        
        if ffmpeg_in_path:
            ffmpeg_found = True
        else:
            # Secondary check using platform-specific commands
            if platform.system() == "Windows":
                # Try multiple common installation locations on Windows
                common_paths = [
                    os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "ffmpeg", "bin", "ffmpeg.exe"),
                    os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "ffmpeg", "bin", "ffmpeg.exe"),
                    os.path.join(os.environ.get("USERPROFILE", "C:\\Users\\User"), "ffmpeg", "bin", "ffmpeg.exe"),
                    # Add the current directory and its subdirectories
                    os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"),
                    os.path.join(os.getcwd(), "ffmpeg.exe"),
                ]
                
                for path in common_paths:
                    if os.path.isfile(path):
                        ffmpeg_found = True
                        break
                        
                # Last resort: try the where command
                if not ffmpeg_found:
                    result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True)
                    ffmpeg_found = "ffmpeg" in result.stdout.lower()
            else:  # Linux/Mac
                result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
                ffmpeg_found = bool(result.stdout.strip())
    except Exception as e:
        print(f"Error checking for FFmpeg: {str(e)}")
        ffmpeg_found = False
        
    if not ffmpeg_found and progress_callback:
        progress_callback(
            "Warning: FFmpeg not found - audio conversion will be skipped. Please install FFmpeg for best quality.", 
            10,
            download_stats
        )
    elif ffmpeg_found and progress_callback:
        progress_callback(
            "FFmpeg detected - audio conversion enabled for high quality output.", 
            10,
            download_stats
        )
    
    class ProgressHook:
        def __init__(self, callback: callable, song_info: SongData, current_idx: int, total_songs: int):
            self.callback = callback
            self.current_title = ""
            self.song_info = song_info
            self.current_idx = current_idx
            self.total_songs = total_songs
            self.last_downloaded_bytes = 0
            self.last_time = time.time()
            self.error_reported = False
            
        def __call__(self, d: Dict[str, Any]):
            with stats_lock:
                if d['status'] == 'downloading':
                    # Get title if not set
                    if self.current_title != d.get('info_dict', {}).get('title', ''):
                        self.current_title = d.get('info_dict', {}).get('title', '')
                        download_stats["in_progress"].add(self.current_title)
                    
                    # Calculate download speed
                    if "downloaded_bytes" in d and "total_bytes" in d:
                        # Update total bytes if we have that info
                        if d["total_bytes"] and self.current_title in download_stats["in_progress"]:
                            download_stats["total_bytes"] = max(download_stats["total_bytes"], d["total_bytes"])
                        
                        # Calculate current speed for this file
                        now = time.time()
                        time_diff = now - self.last_time
                        if time_diff >= 0.5:  # Update every half second
                            bytes_diff = d["downloaded_bytes"] - self.last_downloaded_bytes
                            current_speed = bytes_diff / time_diff if time_diff > 0 else 0
                            
                            # Update overall download stats
                            download_stats["downloaded_bytes"] += bytes_diff
                            download_stats["current_speed"] = current_speed
                            
                            # Reset for next calculation
                            self.last_downloaded_bytes = d["downloaded_bytes"]
                            self.last_time = now
                    
                    # Calculate progress percentage
                    progress = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100 if d.get('total_bytes') else 0
                    
                    # Calculate ETA
                    elapsed = time.time() - download_stats["start_time"]
                    completed_fraction = download_stats["completed"] / len(urls) if urls else 0
                    if completed_fraction > 0:
                        eta_seconds = (elapsed / completed_fraction) - elapsed
                        eta_str = f" - ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                    else:
                        eta_str = " - Calculating..."
                    
                    # Format speed in Mbps
                    speed_mbps = download_stats["current_speed"] / (1024 * 1024) * 8  # Convert bytes/s to Mbps
                    speed_str = f" - {speed_mbps:.2f} Mbps"
                    
                    if self.callback:
                        self.callback(
                            f"Downloading: {self.current_title} ({self.current_idx}/{self.total_songs}){speed_str}{eta_str}", 
                            min(40 + progress * 0.6, 100),
                            download_stats
                        )
                
                elif d['status'] == 'finished' and self.current_title:
                    # Remove from in_progress and add to successful
                    if self.current_title in download_stats["in_progress"]:
                        download_stats["in_progress"].remove(self.current_title)
                    download_stats["successful"].append(self.song_info)
                    
                    if self.callback:
                        download_stats["completed"] += 1
                        overall_progress = (download_stats["completed"] / len(urls)) * 100
                        
                        # Calculate ETA
                        elapsed = time.time() - download_stats["start_time"]
                        completed_fraction = download_stats["completed"] / len(urls) if urls else 0
                        if completed_fraction > 0:
                            eta_seconds = (elapsed / completed_fraction) - elapsed
                            eta_str = f" - ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                        else:
                            eta_str = " - Calculating..."
                            
                        self.callback(
                            f"Processing: {self.current_title} ({self.current_idx}/{self.total_songs}){eta_str}", 
                            min(40 + overall_progress * 0.6, 100),
                            download_stats
                        )
                        
                elif d['status'] == 'error':
                    # Track failed download and report only once
                    if not self.error_reported:
                        if self.current_title in download_stats["in_progress"]:
                            download_stats["in_progress"].remove(self.current_title)
                        download_stats["failed"].append(self.song_info)
                        download_stats["completed"] += 1
                        self.error_reported = True
                        
                        # Report the error (with detailed error message if available)
                        error_msg = d.get('error', 'Unknown error')
                        if self.callback:
                            self.callback(
                                f"Error: Could not download {self.song_info.get('title', 'Unknown')} - {error_msg}", 
                                min(40 + (download_stats["completed"] / len(urls) if urls else 0) * 60, 100),
                                download_stats
                            )
    
    def download_song(song_data: SongData, idx: int, total: int) -> bool:
        try:
            # Get the current download path from the global variable
            current_download_path = DOWNLOAD_PATH
            
            # options generated from https://github.com/yt-dlp/yt-dlp/blob/master/devscripts/cli_to_api.py
            options = {
                "extract_flat": "discard_in_playlist",
                "final_ext": "m4a" if ffmpeg_found else "webm",  # Use webm if FFmpeg not available
                "format": "bestaudio/best",
                "fragment_retries": 10,
                "ignoreerrors": "only_download",
                "outtmpl": {"default": f"{current_download_path}%(title)s.%(ext)s"},
                "postprocessors": [],  # Will be populated conditionally below
                "quiet": False,  # Make yt-dlp show output
                "no_warnings": False  # Show warnings
            }
            
            # Only add postprocessors if ffmpeg is available
            if ffmpeg_found:
                options["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "nopostoverwrites": False,
                        "preferredcodec": "m4a",
                        "preferredquality": "5"
                    },
                    {
                        "add_chapters": True,
                        "add_infojson": 'if_exists',
                        "add_metadata": True,
                        "key": "FFmpegMetadata"
                    }
                ]
            
            if progress_callback:
                options["progress_hooks"] = [ProgressHook(progress_callback, song_data, idx, total)]
            
            with YoutubeDL(options) as ydl:
                ydl.download([song_data["url"]])
            return True
        except Exception as e:
            print(f"Error downloading {song_data.get('title', 'Unknown')}: {str(e)}")
            with stats_lock:
                download_stats["failed"].append(song_data)
                download_stats["completed"] += 1
            if progress_callback:
                progress_callback(
                    f"Error: Could not download {song_data.get('title', 'Unknown')} ({idx}/{total})", 
                    min(40 + (download_stats["completed"] / len(urls) if urls else 0) * 60, 100),
                    download_stats
                )
            return False
    
    total_songs = len(urls)
    
    # Use ThreadPoolExecutor for concurrent downloads
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_downloads) as executor:
        futures = []
        for idx, song_data in enumerate(urls, 1):
            future = executor.submit(download_song, song_data, idx, total_songs)
            futures.append(future)
        
        # Wait for all downloads to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Unhandled exception: {str(e)}")
    
    # Return download stats for reporting
    return download_stats

def main(playlist_id: str, progress_callback: Optional[callable] = None, concurrent_searches: int = 3, concurrent_downloads: int = 3) -> DownloadStats:
    """Main function to handle the playlist download workflow
    
    Args:
        playlist_id: Spotify playlist ID or URL
        progress_callback: Optional callback function for progress updates
        concurrent_searches: Number of concurrent song searches (default: 3)
        concurrent_downloads: Number of concurrent downloads (default: 3)
    
    Returns:
        Download statistics dictionary
    """
    # Extract playlist info
    playlist_info = get_playlist_info(playlist_id)
    
    # Get YouTube Music URLs for each song
    download_urls = get_song_urls(playlist_info, progress_callback, 
                                concurrent_searches=concurrent_searches)
    
    # Download songs from the URLs
    download_stats = download_from_urls(download_urls, progress_callback,
                                      concurrent_downloads=concurrent_downloads)
    
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
