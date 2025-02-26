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
- **Custom FFmpeg Path**: Specify a custom FFmpeg executable path if auto-detection fails

## Warning
This program uses YouTube Music as the source for music downloads, there is a chance of mismatching.

> This program is for **educational purposes only**. Users are responsible for complying with YouTube Music and Spotify's terms of service.

## Dependencies
Unlike most downloaders, this program does not require a Spotify Developers account. However, you should have these libraries installed: 

- [innertube](https://github.com/tombulled/innertube): For YouTube Music API access
- [SpotAPI](https://github.com/Aran404/SpotAPI): For Spotify playlist data extraction
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): For downloading high-quality audio
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter): For the modern GUI
- [FFmpeg](https://www.ffmpeg.org/): Required for audio conversion to m4a format

### Installation

1. Clone the repository:
```sh
git clone https://github.com/invzfnc/spotify-downloader.git
cd spotify-downloader
```

2. Create a virtual environment (recommended):
```sh
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

3. Install Python dependencies:
```sh
pip install -r requirements.txt
```

4. Verify installation:
```sh
# Check if all dependencies are installed correctly
python -c "import customtkinter, yt_dlp, requests; print('Dependencies successfully installed!')"
```

### Installing FFmpeg (Required for M4A conversion)

**Windows:**
1. Download FFmpeg from the [official website](https://ffmpeg.org/download.html) or use a pre-built Windows version from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
2. Extract the files to a folder (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your system PATH:
   - Right-click on "This PC" or "My Computer" > Properties > Advanced System Settings > Environment Variables
   - Edit the "Path" variable and add the path to the bin folder (e.g., `C:\ffmpeg\bin`)
   - Click OK to save changes
4. Restart any open command prompts or applications
5. Verify installation by opening a new command prompt and typing: `ffmpeg -version`

**Alternative Windows Installation (Simplified):**
1. Download the FFmpeg executable from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)
2. Extract the zip file
3. Copy `ffmpeg.exe` from the `bin` folder directly to the spotify-downloader folder
4. No PATH configuration needed - the application will find it automatically

**macOS:**
```sh
# Install using Homebrew
brew install ffmpeg

# Verify installation
ffmpeg -version
```

**Linux:**
```sh
# For Debian/Ubuntu
sudo apt update && sudo apt install ffmpeg

# For Fedora
sudo dnf install ffmpeg

# For Arch Linux
sudo pacman -S ffmpeg

# Verify installation
ffmpeg -version
```

> **Note:** If FFmpeg is not installed, the application will still download audio files but will skip the conversion to M4A format and leave them as webm files. The GUI now allows you to specify a custom FFmpeg path if automatic detection fails.

## Usage

### GUI Mode (Recommended)
```sh
python gui.py
```

This launches the graphical interface where you can:
1. Paste your Spotify playlist URL
2. Choose a download folder
3. Optionally specify a custom FFmpeg path if auto-detection fails
4. Click "Download Playlist" to start

### Command Line Mode
```sh
python -m cli <playlist_url>
```

You can also use additional command line options:
```sh
python -m cli --help
```

This will show all available options:
- `-o, --output-dir`: Specify output directory (default: ./downloads/)
- `-c, --concurrent-searches`: Number of concurrent song searches (default: 3)
- `-d, --concurrent-downloads`: Number of concurrent downloads (default: 3)

## Performance Tips
- For best performance, ensure you have a stable internet connection
- The application supports parallel downloads, which works best with a good connection
- FFmpeg is required for M4A conversion; without it, files will remain in webm format
- Higher quality downloads require more bandwidth and disk space
- Increasing concurrent searches and downloads can improve speed on faster connections

## Troubleshooting
- **FFmpeg Errors**: Install FFmpeg as described above
- **Download Issues**: Check your internet connection and try again
- **Application Not Closing**: The application now properly closes when the window is closed
- **Missing Songs**: Some songs might not be found on YouTube Music; try downloading the playlist again
- **Slow Downloads**: Reduce the number of concurrent downloads or check your internet connection
- **Audio Quality Issues**: Make sure FFmpeg is properly installed for high-quality m4a conversion

## Known Limitations
- Some region-restricted songs may not be found
- Very new releases might not be available on YouTube Music
- Song matching is based on title and artist, so there might be occasional mismatches

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Ensure your code passes flake8 linting
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License
This software is licensed under the [MIT License](https://github.com/invzfnc/spotify-downloader/blob/main/LICENSE)  [Cha](https://github.com/invzfnc)
