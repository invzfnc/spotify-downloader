import sys
import os
import argparse
from main import main

def cli_progress_callback(message, progress, stats=None):
    """Command-line progress callback for displaying download progress"""
    # Create a progress bar
    bar_length = 40
    filled_length = int(bar_length * progress / 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    # Format the progress message
    progress_str = f"[{bar}] {progress:.1f}%"
    
    # Add statistics if available
    stats_str = ""
    if stats:
        if "current_speed" in stats:
            speed_mbps = stats.get("current_speed", 0) / (1024 * 1024) * 8
            if speed_mbps > 0:
                stats_str += f" {speed_mbps:.2f} Mbps"
        
        if "completed" in stats and "failed" in stats:
            completed = len(stats.get("successful", []))
            failed = len(stats.get("failed", []))
            total = completed + failed + len(stats.get("in_progress", []))
            if total > 0:
                stats_str += f" | {completed}/{total} songs"
    
    # Print the progress line (overwriting the previous line)
    print(f"\r{progress_str} {message} {stats_str}", end="")
    
    # Print a new line when finished
    if progress >= 100:
        print()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Download songs from a Spotify playlist in high quality from YouTube Music.",
        epilog="For a better experience, try the GUI mode: python gui.py"
    )
    
    parser.add_argument(
        "playlist_url", 
        help="Spotify playlist URL or ID"
    )
    
    parser.add_argument(
        "-o", "--output-dir", 
        default="./downloads/",
        help="Output directory for downloaded songs (default: ./downloads/)"
    )
    
    parser.add_argument(
        "-c", "--concurrent-searches", 
        type=int, 
        default=3,
        help="Number of concurrent song searches (default: 3)"
    )
    
    parser.add_argument(
        "-d", "--concurrent-downloads", 
        type=int, 
        default=3,
        help="Number of concurrent downloads (default: 3)"
    )
    
    return parser.parse_args()

def main_cli():
    """Main CLI entry point"""
    args = parse_arguments()
    
    # Ensure the download directory exists and ends with a separator
    download_dir = os.path.abspath(args.output_dir)
    if not download_dir.endswith(os.sep):
        download_dir += os.sep
    
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Set the download path in the main module
    import main as main_module
    main_module.DOWNLOAD_PATH = download_dir
    
    print(f"Starting download from: {args.playlist_url}")
    print(f"Saving to: {download_dir}")
    print(f"Concurrent searches: {args.concurrent_searches}")
    print(f"Concurrent downloads: {args.concurrent_downloads}")
    print()
    
    try:
        # Run the main download function
        download_stats = main(
            args.playlist_url, 
            cli_progress_callback, 
            args.concurrent_searches, 
            args.concurrent_downloads
        )
        
        # Print summary
        success_count = len(download_stats.get("successful", []))
        failed_count = len(download_stats.get("failed", []))
        
        print("\nDownload Summary:")
        print(f"Successfully downloaded: {success_count} songs")
        print(f"Failed to download: {failed_count} songs")
        
        # Print failed songs if any
        if failed_count > 0:
            print("\nFailed songs:")
            for i, song in enumerate(download_stats.get("failed", []), 1):
                title = song.get("original_title", song.get("title", "Unknown"))
                artist = song.get("artist", "Unknown Artist")
                print(f"{i}. {title} by {artist}")
        
        return 0
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main_cli())
