__version__ = "1.2.0"
__author__ = "Cha @github.com/invzfnc"

import concurrent.futures

from typing import TypedDict
from time import sleep
from random import uniform
from sys import exit
from itertools import chain

from spotapi import Public
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

DOWNLOAD_PATH = "./downloads/"
AUDIO_FORMAT = "m4a"
CONCURRENT_LIMIT = 3

client = None


class PlaylistInfo(TypedDict):
    title: str
    artist: str


def get_playlist_info(playlist_id: str) -> list[PlaylistInfo]:
    """Extracts data from Spotify and return them in format
       `[{"title": title, "artist": artist}]`."""

    result: list[PlaylistInfo] = []

    try:
        chunks = list(Public.playlist_info(playlist_id))
        items = list(chain.from_iterable([chunk["items"] for chunk in chunks]))
    except KeyError:
        return result

    for item in items:
        item = item["itemV2"]["data"]

        assert item["__typename"] in ("Track", "LocalTrack", "RestrictedContent", "NotFound", "Episode"), f"typename is {item['__typename']}"  # noqa: E501
        # RestrictedContent and NotFound:
        # Hidden entries, not actual songs in playlist

        song: PlaylistInfo

        if item["__typename"] == "Track":
            song = {
                "title": item["name"],
                "artist": item["artists"]["items"][0]["profile"]["name"],
            }
        elif item["__typename"] == "LocalTrack":
            song = {
                "title": item["name"],
                "artist": item["artistName"],
            }
        else:
            continue

        # remove duplicates
        if song in result:
            continue

        result.append(song)

    return result


def get_song_url(song_info: PlaylistInfo) -> tuple[str, str]:
    """Simulates searching from the YTMusic web and returns url to the
    closest match."""

    # setup client
    global client
    if client is None:
        client = YTMusic()
    data = client.search(f"{song_info['title']} {song_info['artist']}")

    url_part = "https://music.youtube.com/watch?v="

    # observe: will "did you mean" interrupt the flow?

    # ignore top results and match entries from Song category
    songs = [entry for entry in data if entry["resultType"] == "song"]
    matches = [song for song in songs if song_info["title"] in song["title"]]
    # in the most ideal cases the titles are exactly the same,
    # but sometimes ytmusic has longer titles containing translations for non english songs

    if matches:
        match = matches[0]
        return url_part + match["videoId"], match["title"]

    # if there is no Song result that exactly matches the given info, return top result
    top_result = data[0]
    return url_part + top_result["videoId"], top_result["title"]

    # no error handling for now, will add if have new observations
    # also removed the part where the original algorithm returns ("", "")
    # ideally in the worst case this function returns the top result
    # unless even the top result is absent, then we'll see what to do


def get_song_urls(playlist_info: list[PlaylistInfo],
                  concurrent_limit: int) -> list[str]:
    """Repeatedly calls `get_song_url` on given playlist info.
    Returns list of results."""

    def process_song_entry(song_info: PlaylistInfo):
        """Helper function for concurrency in `get_song_urls`.
        Reports and prints status to user,
        returns matched url."""

        print(f"[MATCHING] {song_info['title']}")
        url, title = get_song_url(song_info)

        if url:
            print(f"[FOUND] {title} ({url})")
        else:
            print(f"[NO MATCH] {song_info['title']}")

        sleep(uniform(1, 2.5))

        return url

    urls: list[str] = []

    # split playlist_info into batches of (let's say) three
    # spltting manually so program responds better to keyboard interruption
    # program will end on ctrl-c once the batch is finished
    batches = [playlist_info[i: i+concurrent_limit]
               for i in range(0, len(playlist_info), concurrent_limit)]

    for batch in batches:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # maintains order of urls with playlist entries
            urls.extend(executor.map(process_song_entry, batch))
        print()

    return urls


def download_from_urls(urls: list[str], output_dir: str,
                       audio_format: str, title_first: bool,
                       download_archive: str | None) -> None:
    """Downloads list of songs with yt-dlp"""

    if not output_dir.endswith("/"):
        output_dir += "/"

    if title_first:
        filename = f"{output_dir}%(title)s - %(creator)s.%(ext)s"
    else:
        filename = f"{output_dir}%(creator)s - %(title)s.%(ext)s"

    # options generated with https://github.com/yt-dlp/yt-dlp/blob/master/devscripts/cli_to_api.py  # noqa: E501
    options = {'concurrent_fragment_downloads': 3,
               'extract_flat': 'discard_in_playlist',
               'final_ext': 'm4a',
               'format': 'bestaudio/best',
               'fragment_retries': 10,
               'ignoreerrors': 'only_download',
               'outtmpl': {'default': filename,
                           'pl_thumbnail': ''},
               'postprocessor_args': {'ffmpeg': ['-c:v',
                                                 'mjpeg',
                                                 '-vf',
                                                 "crop='if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'"]},  # noqa: E501
               'postprocessors': [{'format': 'jpg',
                                   'key': 'FFmpegThumbnailsConvertor',
                                   'when': 'before_dl'},
                                  {'key': 'FFmpegExtractAudio',
                                   'nopostoverwrites': False,
                                   'preferredcodec': audio_format,
                                   'preferredquality': '5'},
                                  {'add_chapters': True,
                                   'add_infojson': 'if_exists',
                                   'add_metadata': True,
                                   'key': 'FFmpegMetadata'},
                                  {'already_have_thumbnail': False,
                                   'key': 'EmbedThumbnail'},
                                  {'key': 'FFmpegConcat',
                                   'only_multi_video': True,
                                   'when': 'playlist'}],
               'retries': 10,
               'writethumbnail': True}

    # place in download folder
    if download_archive:
        options["download_archive"] = f"{output_dir}{download_archive}"

    # downloads stream with highest bitrate
    with YoutubeDL(options) as ydl:
        ydl.download(urls)


def main(playlist_id: str,
         output_dir: str,
         audio_format: str,
         title_first: bool,
         concurrent_limit: int,
         download_archive: str | None) -> None:
    playlist_info = get_playlist_info(playlist_id)

    if not playlist_info:
        print("Invalid playlist URL. Aborting operation.")
        exit(1)

    download_urls = get_song_urls(playlist_info, concurrent_limit)
    download_from_urls(download_urls, output_dir, audio_format,
                       title_first, download_archive)


if __name__ == "__main__":
    url = "https://open.spotify.com/playlist/22hvxfJq0KwpgulLhDGslq"
    main(url, DOWNLOAD_PATH, AUDIO_FORMAT, False, CONCURRENT_LIMIT, ".archive")
