from typing import TypedDict, List, Dict, Optional, Any, Set
import concurrent.futures
from threading import Lock
import time
import os
import platform
from pathlib import Path

from yt_dlp import YoutubeDL

from ytmusic_utils import SongData

# Global variables
FFMPEG_PATH = None  # Will store custom FFmpeg path if provided
DOWNLOAD_PATH = "./downloads/"  # Default download path

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


def download_from_urls(urls: List[SongData], progress_callback: Optional[callable] = None, concurrent_downloads: int = 3, ffmpeg_path: Optional[str] = None, download_path: Optional[str] = None) -> DownloadStats:
    """Downloads list of songs with yt-dlp with concurrent downloads support
    
    Args:
        urls: List of song data dictionaries to download
        progress_callback: Optional callback function for progress updates
        concurrent_downloads: Number of concurrent downloads (default: 3)
        ffmpeg_path: Optional path to FFmpeg executable
        download_path: Optional path to download directory
    
    Returns:
        Download statistics dictionary
    """
    
    import concurrent.futures
    import time
    from collections import defaultdict
    import os
    import platform
    from pathlib import Path
    
    # Check for empty URL list
    if not urls:
        empty_stats: DownloadStats = {
            "start_time": time.time(),
            "total_bytes": 0,
            "downloaded_bytes": 0,
            "current_speed": 0,
            "successful": [],
            "failed": [],
            "in_progress": set(),
            "completed": 0
        }
        if progress_callback:
            progress_callback("No songs to download", 100, empty_stats)
        return empty_stats
    
    # Set global download path if provided
    global DOWNLOAD_PATH
    if download_path:
        DOWNLOAD_PATH = download_path
        # Ensure download path ends with separator
        if not DOWNLOAD_PATH.endswith(os.sep):
            DOWNLOAD_PATH = DOWNLOAD_PATH + os.sep
        # Create directory if it doesn't exist
        Path(DOWNLOAD_PATH).mkdir(exist_ok=True, parents=True)
        if progress_callback:
            progress_callback(
                f"Using download path: {DOWNLOAD_PATH}", 
                5,
                None
            )
    
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
    ffmpeg_path_local = None
    
    # First check if a custom path was provided via parameter
    if ffmpeg_path and os.path.isfile(ffmpeg_path):
        ffmpeg_found = True
        ffmpeg_path_local = ffmpeg_path
        if progress_callback:
            progress_callback(
                f"Using custom FFmpeg path: {ffmpeg_path}", 
                10,
                download_stats
            )
    # Then check global variable as fallback
    elif FFMPEG_PATH and os.path.isfile(FFMPEG_PATH):
        ffmpeg_found = True
        ffmpeg_path_local = FFMPEG_PATH
        if progress_callback:
            progress_callback(
                f"Using custom FFmpeg path: {FFMPEG_PATH}", 
                10,
                download_stats
            )
    else:
        try:
            import subprocess
            import shutil
            
            # First check if ffmpeg is in PATH
            ffmpeg_in_path = shutil.which("ffmpeg")
            if ffmpeg_in_path:
                ffmpeg_found = True
                ffmpeg_path_local = ffmpeg_in_path
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
                        # Add the directory where the script is located
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe"),
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg", "bin", "ffmpeg.exe"),
                    ]
                    
                    for path in common_paths:
                        if os.path.isfile(path):
                            ffmpeg_found = True
                            ffmpeg_path_local = path
                            # Set the global path for future use
                            FFMPEG_PATH = path
                            break
                            
                    # Last resort: try the where command
                    if not ffmpeg_found:
                        try:
                            result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True)
                            if "ffmpeg" in result.stdout.lower():
                                ffmpeg_path_local = result.stdout.strip().split('\n')[0]
                                ffmpeg_found = os.path.isfile(ffmpeg_path_local)
                                if ffmpeg_found:
                                    FFMPEG_PATH = ffmpeg_path_local
                        except Exception:
                            pass
                else:  # Linux/Mac
                    try:
                        result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
                        if result.stdout.strip():
                            ffmpeg_path_local = result.stdout.strip()
                            ffmpeg_found = os.path.isfile(ffmpeg_path_local)
                            if ffmpeg_found:
                                FFMPEG_PATH = ffmpeg_path_local
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error checking for FFmpeg: {str(e)}")
            ffmpeg_found = False
            
    if not ffmpeg_found and progress_callback:
        progress_callback(
            "Warning: FFmpeg not found - audio conversion will be skipped. Please install FFmpeg for best quality or place ffmpeg.exe in the application directory.", 
            10,
            download_stats
        )
    elif ffmpeg_found and progress_callback:
        progress_callback(
            f"FFmpeg detected at: {ffmpeg_path_local} - audio conversion enabled for high quality output.", 
            10,
            download_stats
        )
        
    # If FFmpeg was found, add it to the PATH environment variable temporarily
    if ffmpeg_found and ffmpeg_path_local:
        ffmpeg_dir = os.path.dirname(ffmpeg_path_local)
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    
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
                        with stats_lock:
                            if self.current_title in download_stats["in_progress"]:
                                download_stats["in_progress"].remove(self.current_title)
                            download_stats["failed"].append(self.song_info)
                            download_stats["completed"] += 1
                            self.error_reported = True
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
                "no_warnings": False,  # Show warnings
                "retries": 10,
                "writethumbnail": True,
                "noplaylist": True,
                "extractor_args": {"youtubetab": {"approximate_date": "0"}}
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
                    },
                    {
                        "key": "EmbedThumbnail",
                        "already_have_thumbnail": False
                    }
                ]
            
            if progress_callback:
                options["progress_hooks"] = [ProgressHook(progress_callback, song_data, idx, total)]
            
            url = song_data["url"]
            
            with YoutubeDL(options) as ydl:
                ydl.download([url])
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
