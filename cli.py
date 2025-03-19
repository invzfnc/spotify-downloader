__version__ = "1.0.3"
__author__ = "Cha @github.com/invzfnc"

import sys
import argparse
import traceback

from main import main, DOWNLOAD_PATH


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
        "--version",
        action="version",
        version=f"{__version__}",
        help="show version number and exit"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    print(f"Starting download from {args.playlist_url} to {args.output_dir}")

    try:
        main(args.playlist_url, args.output_dir)

        print("Download completed.")
        sys.exit(0)

    except KeyboardInterrupt:
        print("Program terminated by user.")

    except Exception:
        print(traceback.format_exc())
        print("If you'd like to report this issue, please include the message above when opening issues on GitHub. For detailed instructions, see CONTRIBUTING.md")  # noqa: E501
        sys.exit(1)
