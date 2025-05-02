<div align="center">  
  <a href="https://github.com/invzfnc/spotify-downloader">
    <img src="https://raw.githubusercontent.com/invzfnc/spotify-downloader/main/assets/icon.ico" alt="Logo" width="80">
  </a>

  ### spotify-dl - Spotify Playlist Downloader

  Downloads Spotify playlists in high quality without logging in by searching for each track and downloading the best match from YouTube Music.

  <a href="https://github.com/invzfnc/spotify-downloader/releases"><img src="https://img.shields.io/github/v/release/invzfnc/spotify-downloader" alt="Latest release version"></a>
  <a href="https://github.com/invzfnc/spotify-downloader/releases"><img src="https://img.shields.io/github/downloads/invzfnc/spotify-downloader/total" alt="Total downloads"></a>
</div> 

## Features
- No premium subscription required
- No login required
- Lightweight
- Downloads in higher bitrate (around 256 kbps)
- With embed metadata (title, artist, album and album art, etc)

## Warning
This program uses YouTube Music as the source for music downloads, there is a chance of mismatching.

> This program is for **educational purposes only**. Users are responsible for complying with YouTube Music and Spotify's terms of service.

## Usage
This program requires **ffmpeg** to work. Install [ffmpeg](https://ffmpeg.org/download.html) and add the folder where `ffmpeg.exe` is located to PATH/system environment variables.

Unlike most downloader, this program **does not** require a Spotify Developers account.

### Using Binaries (Windows Only)
1. Download the latest binaries from the [release section](https://github.com/invzfnc/spotify-downloader/releases).
2. Extract the files and navigate to the extracted folder.
3. Open command prompt/terminal and run the program with your playlist URL.

   ```sh
   spotify-dl.exe playlist_url
   ```

**Available Options**
- To get help on available options:

  ```sh
  spotify-dl.exe --help
  ```

- To specify where to store downloaded files:

  ```sh
  spotify-dl.exe -o path playlist_url
  ```

- To change audio format (for example mp3):
  ```sh
  spotify-dl.exe -f mp3 playlist_url
  ```

- To save as `<title> - <artist>.<ext>` instead of the default `<artist> - <title>.<ext>`:
  ```sh
  spotify-dl.exe --title-first playlist_url
  ```

### Using Source Code
1. Clone the repository.

   ```sh
   git clone https://github.com/invzfnc/spotify-downloader.git
   cd spotify-downloader
   ```
   
2. Create and activate a virtual environment (Optional but recommended).

   ```sh
   python -m venv venv
   venv\Scripts\activate.bat  # Windows
   # or
   source venv/bin/activate   # Linux/macOS
   ```
   
3. Install required dependencies.

   ```sh
   python -m pip install -r requirements.txt
   ```
   
4. Run the program with your playlist URL.

   ```sh
   python -m cli playlist_url
   ```

**Available Options**
- To get help on available options:

  ```sh
  python -m cli --help
  ```

- To specify where to store dowloaded files:
  ```sh
  python -m cli -o path playlist_url
  ```

- To change audio format (for example mp3):
  ```sh
  python -m cli -f mp3 playlist_url
  ```

- To save as `<title> - <artist>.<ext>` instead of the default `<artist> - <title>.<ext>`:
  ```sh
  python -m cli --title-first playlist_url
  ```

## Issues
If you have encountered problems, please read the [guidelines](CONTRIBUTING.md#reporting-issuesasking-questions) for detailed instructions on how to open an issue.

## Contributing
Contributions are welcome! If you'd like to contribute, please read our [CONTRIBUTING.md](CONTRIBUTING.md) guide for details on how to get started.

## Credits
Icon designed by [exia098](https://www.artstation.com/exia098).

## License
This software is licensed under the [MIT License](https://github.com/invzfnc/spotify-downloader/blob/main/LICENSE) © [Cha](https://github.com/invzfnc)
