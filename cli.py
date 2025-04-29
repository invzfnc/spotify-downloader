__version__ = "1.0.6"
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
       "-c", "--max-concurrent",
       default=CONCURRENT_LIMIT,
       type=int,
       help=f"number of songs to process simultaneously (default: {CONCURRENT_LIMIT})"  # noqa: E501
    )

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
        print("--max-concurrent should be integer larger than 1")
        sys.exit(1)

    print(f"Starting download from {args.playlist_url} to {args.output_dir}")

    try:
        main(args.playlist_url, args.output_dir,
             args.audio_format, args.max_concurrent)

        print("Download completed.")
        sys.exit(0)

    except KeyboardInterrupt:
        print("Program terminated by user.")
        sys.exit(0)

    except Exception:
        print(traceback.format_exc())
        print("If you'd like to report this issue, please include the message above when opening issues on GitHub. For detailed instructions, see CONTRIBUTING.md")  # noqa: E501
        sys.exit(1)
