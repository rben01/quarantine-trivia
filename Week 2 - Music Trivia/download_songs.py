# %%
import subprocess
import time
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd

AUDIO_DIR = Path("Audio")

ORIGINALS_DIR = AUDIO_DIR / "Originals"


def fetch_all():
    df = pd.read_csv("songs_meta_pre.csv")
    df: pd.DataFrame

    for i, row in enumerate(df.iterrows()):

        row = row[1]
        search_string = " ".join([row["title"], row["artist"]])
        if len(search_string) < 20:
            search_string += " " + row["album"]

        search_string = quote_plus(search_string)
        url = f"https://www.youtube.com/results?search_query={search_string}"
        subprocess.check_call(
            [
                "osascript",
                "-e",
                'tell application "Keyboard Maestro Engine" '
                + 'to do script "CD02385B-8868-491E-B54F-D9714BA3459A" '
                + f'with parameter "{url}"',
            ]
        )
        print(i + 1, f"Got {url}")

    return df


def sort_songs():
    df = pd.read_csv("./songs_meta_filled_no_qs_as.csv")
    audio_files = df["audio_in"]
    for af in reversed(audio_files):
        af = Path(ORIGINALS_DIR / af)
        assert af.exists()
        af.touch(exist_ok=True)
        time.sleep(0.02)


sort_songs()
