# Spotify Playlist Downloader

A modern, user-friendly application to download songs from your Spotify playlists in high quality from YouTube Music.

![Spotify Downloader](https://github.com/invzfnc/spotify-downloader/raw/main/screenshot.png)

## Features
- **No Premium Required**: Works with free Spotify accounts
- **No Login Required**: No authentication needed
- **Modern GUI**: Clean, responsive interface with light/dark mode support
- **High Quality Downloads**: Downloads in high bitrate (around 256 kbps)
- **Parallel Processing**:
  - Concurrent song searching (3 parallel searches) for faster playlist processing
  - Concurrent downloads (3 parallel downloads) for improved speed
- **Comprehensive Progress Tracking**:
  - Per-file and overall progress bars
  - Download speed display in Mbps
  - Estimated time to completion
  - Detailed success/failure reporting
- **Embedded Metadata**: Includes song title, artist, and more in audio files
- **Flexible Download Location**: Choose where to save your music

## Warning
This program uses YouTube Music as the source for music downloads, there is a chance of mismatching.

> This program is for **educational purposes only**. Users are responsible for complying with YouTube Music and Spotify's terms of service.

## Dependencies
Unlike most downloaders, this program does not require a Spotify Developers account. However, you should have these libraries installed: 

- [innertube](https://github.com/tombulled/innertube)
- [SpotAPI](https://github.com/Aran404/SpotAPI)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter)
- [FFmpeg](https://www.ffmpeg.org/) (Required for audio conversion to m4a format)

### Installation

1. Clone the repository:
```sh
git clone https://github.com/invzfnc/spotify-downloader.git
cd spotify-downloader
```

2. Install Python dependencies:
```sh
pip install -r requirements.txt
```

### Installing FFmpeg (Required for M4A conversion)

**Windows:**
1. Download FFmpeg from the [official website](https://ffmpeg.org/download.html) or use a pre-built Windows version from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
2. Extract the files to a folder (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your system PATH:
   - Right-click on "This PC" or "My Computer" > Properties > Advanced System Settings > Environment Variables
   - Edit the "Path" variable and add the path to the bin folder (e.g., `C:\ffmpeg\bin`)
4. Restart any open command prompts

**macOS:**
```sh
brew install ffmpeg
```

**Linux:**
```sh
sudo apt update && sudo apt install ffmpeg  # For Debian/Ubuntu
sudo dnf install ffmpeg                     # For Fedora
```

> **Note:** If FFmpeg is not installed, the application will still download audio files but will skip the conversion to M4A format and leave them as webm files.

## Usage

### GUI Mode (Recommended)
```sh
python gui.py
```

This launches the graphical interface where you can:
1. Paste your Spotify playlist URL
2. Choose a download folder
3. Click "Download Playlist" to start

### Command Line Mode
```sh
python -m cli <playlist_url>
```

## Performance Tips
- For best performance, ensure you have a stable internet connection
- The application supports parallel downloads, which works best with a good connection
- FFmpeg is required for M4A conversion; without it, files will remain in webm format
- Higher quality downloads require more bandwidth and disk space

## Troubleshooting
- **FFmpeg Errors**: Install FFmpeg as described above
- **Download Issues**: Check your internet connection and try again
- **Application Not Closing**: The application now properly closes when the window is closed

## License
This software is licensed under the [MIT License](https://github.com/invzfnc/spotify-downloader/blob/main/LICENSE) © [Cha](https://github.com/invzfnc)
