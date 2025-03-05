__version__ = "1.0.1"
__author__ = "Cha @github.com/invzfnc"

from typing import TypedDict
from time import sleep
from random import uniform

from spotapi import Public
from innertube import InnerTube
from yt_dlp import YoutubeDL

DOWNLOAD_PATH = "./downloads/"
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

        # sanity check: only two cases found
        assert item["__typename"] in ("Track", "LocalTrack")

        song: PlaylistInfo

        if item["__typename"] == "Track":
            song = {
                "title": item["name"],
                "artist": item["artists"]["items"][0]["profile"]["name"],
                "length": int(item["trackDuration"]["totalMilliseconds"])
            }
        else:
            song = {
                "title": item["name"],
                "artist": item["artistName"],
                "length": int(item["localTrackDuration"]["totalMilliseconds"])
            }

        result.append(song)

    return result


def convert_to_milliseconds(text: str) -> int:
    """Converts `"%M:%S"` timestamp from YTMusic to milliseconds."""
    try:
        minutes, seconds = text.split(":")
    except ValueError:  # text is not duration: result's neither song nor video
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

    top_result_length = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["subtitle"]["runs"][-1]["text"]  # noqa: E501
    first_song_length = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][-1]["text"]  # noqa: E501

    top_result_diff = abs(convert_to_milliseconds(top_result_length) - song_info["length"])  # noqa: E501
    first_song_diff = abs(convert_to_milliseconds(first_song_length) - song_info["length"])  # noqa: E501

    if top_result_diff < first_song_diff:
        # get top result url
        video_id = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"]  # noqa: E501
        video_title = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["title"]["runs"][0]["text"]  # noqa: E501
    else:
        # get first song result url
        video_id = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["overlay"]["musicItemThumbnailOverlayRenderer"]["content"]["musicPlayButtonRenderer"]["playNavigationEndpoint"]["watchEndpoint"]["videoId"]  # noqa: E501
        video_title = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"]  # noqa: E501

    url = "https://music.youtube.com/watch?v=" + video_id

    return url, video_title


def get_song_urls(playlist_info: list[PlaylistInfo]) -> list[str]:
    """Repeatedly calls get_song_url on given playlist info. Returns
    list of results."""
    urls = []

    for song_info in playlist_info:
        print(f"Getting url for {song_info['title']}")

        try:
            url, title = get_song_url(song_info)
        except (KeyError, IndexError):
            print(f"Fail in matching {song_info['title']}")

        urls.append(url)
        print(f"Matched {title} ({url})")

        sleep(uniform(1, 3))

    return urls


def download_from_urls(urls: list[str], output_dir: str) -> None:
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
                                   'preferredcodec': 'm4a',
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

    # downloads stream with highest bitrate, then save them in m4a format
    with YoutubeDL(options) as ydl:
        ydl.download(urls)


def main(playlist_id: str, output_dir: str = DOWNLOAD_PATH) -> None:
    playlist_info = get_playlist_info(playlist_id)

    if not playlist_info:
        print("Invalid playlist URL. Aborting operation.")

    download_urls = get_song_urls(playlist_info)
    download_from_urls(download_urls, output_dir)


if __name__ == "__main__":
    url = "https://open.spotify.com/playlist/2LE8ZObOZOqjsGrR6QFXwu?si=9b4a5deb005148e1"  # noqa: E501
    # main(url)  # test
