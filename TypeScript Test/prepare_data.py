import json
import re
from pathlib import Path

import pandas as pd


def col_renamer(s: str) -> str:
    return re.sub(r"\W+", "", re.sub(r"\s+", "_", s.lower()))


if __name__ == "__main__":
    df: pd.DataFrame = pd.read_csv(
        "./week 15 general trivia.csv", dtype=str, keep_default_na=False
    )
    df = df.drop(
        columns=[c for c in df.columns if c.lower().startswith("unnamed")]
    ).rename(columns=col_renamer)
    # print(df)
    # print(df.columns)

    json_data = df.to_dict("records")
    json_str = json.dumps(json_data, indent=2, allow_nan=False)

    with Path("data.ts").open("w") as f:
        _ = f.write('import { TriviaItem } from "./types"\n')
        _ = f.write(f"export const data: TriviaItem[] = {json_str};")
