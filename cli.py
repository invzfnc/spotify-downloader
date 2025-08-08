__version__ = "1.1.0"
__author__ = "Cha @github.com/invzfnc"

import sys
import argparse
import traceback

from main import main
from main import DOWNLOAD_PATH, AUDIO_FORMAT, CONCURRENT_LIMIT


def parse_arguments() -> argparse.Namespace:
    """Parses command line arguments and returns them."""

    parser = argparse.ArgumentParser(
        description="Download songs from Spotify playlist"
    )

    parser.add_argument(
        "playlist_url",
        help="spotify playlist URL or ID"
    )

    parser.add_argument(
        "-o", "--output-dir",
        default=DOWNLOAD_PATH,
        help=f"output directory for downloading songs (default: {DOWNLOAD_PATH})"  # noqa: E501
    )

    parser.add_argument(
        "-f", "--audio-format",
        default=AUDIO_FORMAT,
        help=f"audio format for downloaded songs (default: {AUDIO_FORMAT})"
    )

    parser.add_argument(
        "--title-first",
        action="store_true",
        help='save as "<title> - <artist>.<ext>" instead of the default "<artist> - <title>.<ext>"'  # noqa: E501
    )

    parser.add_argument(
       "-c", "--max-concurrent",
       default=CONCURRENT_LIMIT,
       type=int,
       help=f"number of songs to search simultaneously (default: {CONCURRENT_LIMIT})"  # noqa: E501
    )

    parser.add_argument(
        "--download-archive",
        action="store",
        metavar="FILE",
        type=str,
        help="Passes --download-archive FILE to yt-dlp. \
              Download only videos not listed in the archive file. \
              Record the IDs of all downloaded videos in it.")

    parser.add_argument(
        "--version",
        action="version",
        version=f"{__version__}",
        help="show version number and exit"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    if args.max_concurrent <= 0:
        print("--max-concurrent should be an integer larger than 0")
        sys.exit(1)

    print(f"Starting download from {args.playlist_url} to {args.output_dir}")

    try:
        main(args.playlist_url, args.output_dir,
             args.audio_format, args.title_first,
             args.max_concurrent, args.download_archive)

        print("Download completed.")
        sys.exit(0)

    except KeyboardInterrupt:
        print("Program terminated by user.")
        sys.exit(0)

    except Exception:
        print(traceback.format_exc())
        print("If you'd like to report this issue, please include the message above when opening issues on GitHub.")  # noqa: E501
        sys.exit(1)
