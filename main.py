__version__ = "1.0.5"
__author__ = "Cha @github.com/invzfnc"

import concurrent.futures

from typing import TypedDict
from time import sleep
from random import uniform
from sys import exit

from spotapi import Public
from innertube import InnerTube
from yt_dlp import YoutubeDL

DOWNLOAD_PATH = "./downloads/"
AUDIO_FORMAT = "m4a"
CONCURRENT_LIMIT = 3

client = None


class PlaylistInfo(TypedDict):
    title: str
    artist: str
    length: int


def get_playlist_info(playlist_id: str) -> list[PlaylistInfo]:
    """Extracts data from Spotify and return them in format
       `[{"title": title, "artist": artist, "length": length}]`."""

    result: list[PlaylistInfo] = []

    try:
        items = next(Public.playlist_info(playlist_id))["items"]
    except KeyError:
        return result

    for item in items:
        item = item["itemV2"]["data"]

        assert item["__typename"] in ("Track", "LocalTrack",
                                      "RestrictedContent", "NotFound")
        # RestrictedContent and NotFound:
        # Hidden entries, not actual songs in playlist

        song: PlaylistInfo

        if item["__typename"] == "Track":
            song = {
                "title": item["name"],
                "artist": item["artists"]["items"][0]["profile"]["name"],
                "length": int(item["trackDuration"]["totalMilliseconds"])
            }
        elif item["__typename"] == "LocalTrack":
            song = {
                "title": item["name"],
                "artist": item["artistName"],
                "length": int(item["localTrackDuration"]["totalMilliseconds"])
            }
        else:
            continue

        result.append(song)

    return result


def convert_to_milliseconds(text: str) -> int:
    """Converts `"%M:%S"` timestamp from YTMusic to milliseconds."""
    try:
        minutes, seconds = text.split(":")
    except ValueError:  # text is not duration
        return 0

    return (int(minutes) * 60 + int(seconds)) * 1000


def get_song_url(song_info: PlaylistInfo) -> tuple[str, str]:
    """Simulates searching from the YTMusic web and returns url to the
    closest match."""

    global client
    if client is None:
        client = InnerTube("WEB_REMIX", "1.20250203.01.00")
    data = client.search(f"{song_info['title']} {song_info['artist']}")

    # handle "did you mean" case
    if "itemSectionRenderer" in data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]:  # noqa: E501
        del data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]  # noqa: E501

    # get first song result info, will succeed unless case is too extreme
    try:
        first_song_id = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["overlay"]["musicItemThumbnailOverlayRenderer"]["content"]["musicPlayButtonRenderer"]["playNavigationEndpoint"]["watchEndpoint"]["videoId"]  # noqa: E501
        first_song_title = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"]  # noqa: E501
        first_song_length = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][-1]["text"]  # noqa: E501
        first_song_diff = abs(convert_to_milliseconds(first_song_length) - song_info["length"])  # noqa: E501
    except (KeyError, IndexError):
        first_song_length = 0

    # get top result info, fails if it's neither Song nor Video
    try:
        top_result_id = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"]  # noqa: E501
        top_result_title = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["title"]["runs"][0]["text"]  # noqa: E501
        top_result_length = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["subtitle"]["runs"][-1]["text"]  # noqa: E501
        top_result_diff = abs(convert_to_milliseconds(top_result_length) - song_info["length"])  # noqa: E501
    except (KeyError, IndexError):
        top_result_length = 0

    url_part = "https://music.youtube.com/watch?v="

    if first_song_length and top_result_length:
        if top_result_diff < first_song_diff:
            return url_part + top_result_id, top_result_title
        else:
            return url_part + first_song_id, first_song_title
    elif top_result_length:
        return url_part + top_result_id, top_result_title
    elif first_song_length:
        return url_part + first_song_id, first_song_title
    else:
        return ("", "")


def get_song_urls(playlist_info: list[PlaylistInfo],
                  concurrent_limit: int) -> list[str]:
    """Repeatedly calls `get_song_url` on given playlist info.
    Returns list of results."""

    def process_song_entry(song_info: PlaylistInfo):
        """Helper function for concurrency in `get_song_urls`.
        Reports and prints status to user,
        returns matched url."""

        print(f"Getting url for {song_info['title']}")
        url, title = get_song_url(song_info)

        if url:
            print(f"Matched {title} ({url})")
        else:
            print(f"Failed matching for {song_info['title']}")

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
            # required for future use (feature coming s∞n)
            urls.extend(executor.map(process_song_entry, batch))
        print()

    return urls


def download_from_urls(urls: list[str], output_dir: str,
                       audio_format: str) -> None:
    """Downloads list of songs with yt-dlp"""

    if not output_dir.endswith("/"):
        output_dir += "/"

    # options generated from https://github.com/yt-dlp/yt-dlp/blob/master/devscripts/cli_to_api.py  # noqa: E501
    options = {'extract_flat': 'discard_in_playlist',
               'final_ext': 'm4a',
               'format': 'bestaudio/best',
               'fragment_retries': 10,
               'ignoreerrors': 'only_download',
               'outtmpl': {'default': f'{output_dir}%(title)s.%(ext)s',
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

    # downloads stream with highest bitrate
    with YoutubeDL(options) as ydl:
        ydl.download(urls)


def main(playlist_id: str, output_dir: str = DOWNLOAD_PATH,
         audio_format: str = AUDIO_FORMAT,
         concurrent_limit: int = CONCURRENT_LIMIT) -> None:
    playlist_info = get_playlist_info(playlist_id)

    if not playlist_info:
        print("Invalid playlist URL. Aborting operation.")
        exit(0)

    download_urls = get_song_urls(playlist_info, concurrent_limit)
    download_from_urls(download_urls, output_dir, audio_format)


if __name__ == "__main__":
    url = "https://open.spotify.com/playlist/22hvxfJq0KwpgulLhDGslq?si=621f90e597784a75"  # noqa: E501
    main(url)
