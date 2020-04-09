# %%
import subprocess
from urllib.parse import quote_plus

import pandas as pd


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


fetch_all()
