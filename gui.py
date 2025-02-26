import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
from main import get_playlist_info, get_song_urls, download_from_urls, DOWNLOAD_PATH as MAIN_DOWNLOAD_PATH
import re
from pathlib import Path
import sys
import os
import time

class ModernSpotifyDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Set the appearance mode and color theme
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title("Spotify Downloader")
        self.configure(fg_color=("#FAFAFA", "#1A1A1A"))
        
        # Window size and position
        window_width = 700
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.minsize(600, 600)
        
        # Initialize download path
        self.download_path = os.path.abspath("./downloads")
        Path(self.download_path).mkdir(exist_ok=True)
        
        # Initialize FFmpeg path
        self.ffmpeg_path = None
        
        # Track playlist and download stats
        self.total_songs = 0
        self.current_song_index = 0
        self.concurrent_downloads = 3
        self.concurrent_searches = 3
        self.download_stats = None
        self.failed_songs = []
        self.start_time = None
        self.download_threads = []
        self.running = True
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=30, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Header section
        self.header_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=("gray95", "gray15"),
            corner_radius=15,
            height=70
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.header_frame.grid_propagate(False)
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Title and subtitle
        title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_container.place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_label = ctk.CTkLabel(
            title_container,
            text="Spotify Downloader",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=("gray15", "gray90")
        )
        self.title_label.grid(row=0, column=0)
        
        self.subtitle_label = ctk.CTkLabel(
            title_container,
            text="Download your playlists in high quality",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray45", "gray70")
        )
        self.subtitle_label.grid(row=1, column=0, pady=(2, 0))
        
        # Input section
        self.input_section = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent"
        )
        self.input_section.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        self.input_section.grid_columnconfigure(0, weight=1)
        
        # URL input frame
        self.url_frame = ctk.CTkFrame(
            self.input_section,
            fg_color=("gray90", "gray17"),
            corner_radius=15
        )
        self.url_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.url_frame.grid_columnconfigure(1, weight=1)
        
        self.url_prefix = ctk.CTkLabel(
            self.url_frame,
            text="",
            font=ctk.CTkFont(size=18),
            width=20
        )
        self.url_prefix.grid(row=0, column=0, padx=(15, 5), pady=12)
        
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            placeholder_text="Paste your Spotify playlist URL here",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=38,
            border_width=0,
            fg_color="transparent"
        )
        self.url_entry.grid(row=0, column=1, padx=(5, 15), sticky="ew")
        
        # Download location frame
        self.location_frame = ctk.CTkFrame(
            self.input_section,
            fg_color=("gray90", "gray17"),
            corner_radius=15
        )
        self.location_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.location_frame.grid_columnconfigure(1, weight=1)
        
        self.folder_icon = ctk.CTkLabel(
            self.location_frame,
            text="",
            font=ctk.CTkFont(size=18),
            width=20
        )
        self.folder_icon.grid(row=0, column=0, padx=(15, 5), pady=12)
        
        self.location_entry = ctk.CTkEntry(
            self.location_frame,
            placeholder_text="Download location (default: ./downloads)",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=38,
            border_width=0,
            fg_color="transparent"
        )
        self.location_entry.grid(row=0, column=1, padx=(5, 5), sticky="ew")
        self.location_entry.insert(0, self.download_path)
        
        self.browse_button = ctk.CTkButton(
            self.location_frame,
            text="Browse",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=70,
            height=30,
            corner_radius=8,
            command=self.browse_location
        )
        self.browse_button.grid(row=0, column=2, padx=(5, 15))
        
        # FFmpeg path frame
        self.ffmpeg_frame = ctk.CTkFrame(
            self.input_section,
            fg_color=("gray90", "gray17"),
            corner_radius=15
        )
        self.ffmpeg_frame.grid(row=2, column=0, sticky="ew")
        self.ffmpeg_frame.grid_columnconfigure(1, weight=1)
        
        self.ffmpeg_icon = ctk.CTkLabel(
            self.ffmpeg_frame,
            text="🎬",
            font=ctk.CTkFont(size=18),
            width=20
        )
        self.ffmpeg_icon.grid(row=0, column=0, padx=(15, 5), pady=12)
        
        self.ffmpeg_entry = ctk.CTkEntry(
            self.ffmpeg_frame,
            placeholder_text="FFmpeg path (optional, auto-detected if installed)",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=38,
            border_width=0,
            fg_color="transparent"
        )
        self.ffmpeg_entry.grid(row=0, column=1, padx=(5, 5), sticky="ew")
        
        self.ffmpeg_browse_button = ctk.CTkButton(
            self.ffmpeg_frame,
            text="Browse",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=70,
            height=30,
            corner_radius=8,
            command=self.browse_ffmpeg
        )
        self.ffmpeg_browse_button.grid(row=0, column=2, padx=(5, 15))
        
        # Download button
        self.download_button = ctk.CTkButton(
            self.main_container,
            text="Download Playlist ",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=40,
            corner_radius=12,
            command=self.start_download,
            fg_color=("#3B82F6", "#2563EB"),
            hover_color=("#2563EB", "#1D4ED8")
        )
        self.download_button.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        
        # Status section
        self.status_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=("gray95", "gray15"),
            corner_radius=15,
            height=160
        )
        self.status_frame.grid(row=3, column=0, sticky="ew")
        self.status_frame.grid_propagate(False)
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        status_content = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        status_content.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95)
        status_content.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            status_content,
            text=" Ready to download",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 4))
        
        self.detail_label = ctk.CTkLabel(
            status_content,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray45", "gray70"),
            anchor="w"
        )
        self.detail_label.grid(row=1, column=0, sticky="w", pady=(0, 6))
        
        self.speed_label = ctk.CTkLabel(
            status_content,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray45", "gray70"),
            anchor="w"
        )
        self.speed_label.grid(row=2, column=0, sticky="w", pady=(0, 6))
        
        self.progress_bar_label = ctk.CTkLabel(
            status_content,
            text="Current File:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("gray45", "gray70"),
            anchor="w"
        )
        self.progress_bar_label.grid(row=3, column=0, sticky="w", pady=(0, 4))
        
        self.progress_bar = ctk.CTkProgressBar(
            status_content,
            height=6,
            corner_radius=3,
            fg_color=("gray85", "gray25"),
            progress_color=("#3B82F6", "#2563EB"),
            border_width=0
        )
        self.progress_bar.grid(row=4, column=0, sticky="ew")
        self.progress_bar.set(0)
        
        # Create a frame for overall progress and ETA
        self.overall_progress_frame = ctk.CTkFrame(
            status_content,
            fg_color="transparent"
        )
        self.overall_progress_frame.grid(row=5, column=0, sticky="ew", pady=(8, 4))
        self.overall_progress_frame.grid_columnconfigure(0, weight=1)
        
        self.overall_progress_label = ctk.CTkLabel(
            self.overall_progress_frame,
            text="Overall Progress:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("gray45", "gray70"),
            anchor="w"
        )
        self.overall_progress_label.grid(row=0, column=0, sticky="w")
        
        self.eta_label = ctk.CTkLabel(
            self.overall_progress_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("gray45", "gray70"),
            anchor="e"
        )
        self.eta_label.grid(row=0, column=1, sticky="e")
        
        self.overall_progress_bar = ctk.CTkProgressBar(
            status_content,
            height=6,
            corner_radius=3,
            fg_color=("gray85", "gray25"),
            progress_color=("#4ADE80", "#22C55E"),
            border_width=0
        )
        self.overall_progress_bar.grid(row=6, column=0, sticky="ew")
        self.overall_progress_bar.set(0)
        
        self.downloads_label = ctk.CTkLabel(
            status_content,
            text=f" {os.path.abspath('./downloads')}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray45", "gray70"),
            anchor="w"
        )
        self.downloads_label.grid(row=7, column=0, sticky="w", pady=(8, 0))
        
        Path("./downloads").mkdir(exist_ok=True)
        
    def choose_folder(self):
        """Legacy method, redirects to browse_location"""
        self.browse_location()
    
    def extract_playlist_id(self, url):
        pattern = r'playlist/([a-zA-Z0-9]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else url
    
    def update_progress(self, value, status, detail="", stats=None):
        """Update the progress display with current download status.
        This method is thread-safe."""
        if not self.running:
            return
            
        # Use after() to ensure UI updates happen on the main thread
        self.after(0, lambda: self._update_progress_internal(value, status, detail, stats))
    
    def _update_progress_internal(self, value, status, detail="", stats=None):
        """Internal method to update the UI elements. Called by update_progress."""
        if not self.running:
            return
            
        try:
            self.progress_bar.set(value / 100)
            icon = "" if value < 100 else ""
            self.status_label.configure(text=f"{icon} {status}")
            self.detail_label.configure(text=detail)
            
            if stats:
                self.download_stats = stats
                
                if "completed" in stats and stats.get("completed", 0) > 0 and self.total_songs > 0:
                    # Calculate overall progress
                    overall_progress = min(stats["completed"] / self.total_songs, 1.0)
                    self.overall_progress_bar.set(overall_progress)
                    
                    # Calculate and display ETA based on overall progress
                    if self.start_time and overall_progress > 0:
                        elapsed = time.time() - self.start_time
                        eta_seconds = (elapsed / overall_progress) - elapsed
                        if eta_seconds > 0:
                            eta_min = int(eta_seconds // 60)
                            eta_sec = int(eta_seconds % 60)
                            eta_text = f"ETA: {eta_min}m {eta_sec}s"
                            self.eta_label.configure(text=eta_text)
                
                # Update speed display
                speed_mbps = stats.get("current_speed", 0) / (1024 * 1024) * 8
                if speed_mbps > 0:
                    self.speed_label.configure(text=f"Download Speed: {speed_mbps:.2f} Mbps")
                
                if "failed" in stats and stats["failed"]:
                    self.failed_songs = stats["failed"]
            
            self.update_idletasks()
        except Exception as e:
            print(f"Error updating UI: {str(e)}")
    
    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a playlist URL")
            return
        
        # Update download path from entry field
        if hasattr(self, 'location_entry'):
            path = self.location_entry.get().strip()
            if path:
                self.download_path = path
                Path(path).mkdir(exist_ok=True)
        
        self.download_button.configure(
            state="disabled",
            text="Downloading... ",
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray35")
        )
        
        # Record start time for ETA calculation
        self.start_time = time.time()
        
        # Create and start the download thread
        download_thread = threading.Thread(target=self.download_playlist, args=(url,), daemon=True)
        self.download_threads.append(download_thread)
        download_thread.start()
    
    def download_playlist(self, url):
        try:
            global MAIN_DOWNLOAD_PATH
            original_path = MAIN_DOWNLOAD_PATH
            
            if not self.download_path.endswith(os.sep):
                self.download_path += os.sep
                
            MAIN_DOWNLOAD_PATH = self.download_path
            
            import main
            main.DOWNLOAD_PATH = self.download_path
            
            # Set FFmpeg path if provided
            if hasattr(self, 'ffmpeg_entry') and self.ffmpeg_entry.get().strip():
                ffmpeg_path = self.ffmpeg_entry.get().strip()
                if os.path.isfile(ffmpeg_path):
                    main.FFMPEG_PATH = ffmpeg_path
                    print(f"Using custom FFmpeg path: {ffmpeg_path}")
            
            playlist_id = self.extract_playlist_id(url)
            
            self.update_progress(0, "Fetching playlist information...")
            playlist_info = get_playlist_info(playlist_id)
            
            if not playlist_info:
                raise Exception("Could not fetch playlist information")
            
            self.total_songs = len(playlist_info)
            self.update_progress(10, f"Found {self.total_songs} songs in playlist")
            
            self.update_progress(20, "Finding songs on YouTube Music...")
            song_urls = get_song_urls(playlist_info, 
                                    lambda detail, progress, stats=None: self.update_progress(progress, "Finding songs...", detail, stats),
                                    self.concurrent_searches)
            
            if not song_urls:
                raise Exception("No songs found in playlist")
            
            self.update_progress(40, f"Downloading {len(song_urls)} songs...")
            download_stats = download_from_urls(song_urls,
                             lambda detail, progress, stats: self.update_progress(progress, "Downloading songs...", detail, stats),
                             self.concurrent_downloads)
            
            failed_message = ""
            if download_stats and download_stats.get("failed"):
                failed_songs = download_stats.get("failed", [])
                if failed_songs:
                    failed_message = "\n\nThe following songs could not be downloaded:"
                    for i, song in enumerate(failed_songs, 1):
                        title = song.get("original_title", song.get("title", "Unknown"))
                        artist = song.get("artist", "Unknown Artist")
                        failed_message += f"\n{i}. {title} by {artist}"
            
            success_count = len(download_stats.get("successful", [])) if download_stats else 0
            failed_count = len(download_stats.get("failed", [])) if download_stats else 0
            
            self.update_progress(100, "Download complete!", 
                              f"Downloaded {success_count} of {self.total_songs} songs to {self.download_path}")
            
            completion_message = f"Playlist downloaded successfully to {self.download_path}!\n\n" + \
                              f"Successfully downloaded: {success_count} songs\n" + \
                              f"Failed to download: {failed_count} songs"
            
            if failed_message:
                completion_message += failed_message
                
            messagebox.showinfo("Download Complete", completion_message)
            
        except Exception as e:
            self.update_progress(0, "Error occurred", str(e))
            messagebox.showerror("Error", str(e))
        
        finally:
            MAIN_DOWNLOAD_PATH = original_path
            import main
            main.DOWNLOAD_PATH = original_path
            
            self.download_button.configure(
                state="normal",
                text="Download Playlist ",
                fg_color=("#3B82F6", "#2563EB"),
                hover_color=("#2563EB", "#1D4ED8")
            )
            self.update_progress(0, " Ready to download")
            
    def on_closing(self):
        """Handle window close event to properly terminate all threads"""
        print("Closing application...")
        self.running = False
        
        # Reset UI elements to prevent errors during shutdown
        try:
            self.download_button.configure(
                state="normal",
                text="Download Playlist ",
                fg_color=("#3B82F6", "#2563EB"),
                hover_color=("#2563EB", "#1D4ED8")
            )
        except Exception:
            pass
        
        # Wait for all download threads to finish with a timeout
        for thread in self.download_threads:
            if thread.is_alive():
                thread.join(0.1)  # Short timeout to avoid blocking
        
        # Ensure all resources are freed
        try:
            self.quit()
        except Exception:
            pass
            
        # Force termination
        self.destroy()
        
        # Exit application with force
        import os
        os._exit(0)  # More forceful exit than sys.exit()

    def browse_location(self):
        path = filedialog.askdirectory(
            title="Choose Download Location",
            initialdir=self.download_path
        )
        if path:
            self.download_path = path
            self.location_entry.delete(0, 'end')
            self.location_entry.insert(0, path)
            # Update the downloads label in the status section
            if hasattr(self, 'downloads_label'):
                self.downloads_label.configure(text=f" {path}")
            Path(path).mkdir(exist_ok=True)

    def browse_ffmpeg(self):
        path = filedialog.askopenfilename(
            title="Choose FFmpeg Executable",
            filetypes=[("Executable files", "*.exe")]
        )
        if path:
            self.ffmpeg_path = path
            self.ffmpeg_entry.delete(0, 'end')
            self.ffmpeg_entry.insert(0, path)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = ModernSpotifyDownloader()
    app.mainloop()
