# %%
import base64  # noqa F401
import re
import subprocess
import uuid
from pathlib import Path
from typing import List, Mapping, Tuple

import numpy as np
import pandas as pd
from IPython.display import display  # noqa F401

SONGS_METADATA_DIR = Path("Song meta")
AUDIO_DIR = Path("Audio")

ORIGINALS_DIR = AUDIO_DIR / "Originals"
TRIMMED_DIR = AUDIO_DIR / "Trimmed"
for d in [ORIGINALS_DIR, TRIMMED_DIR]:
    d.mkdir(exist_ok=True)

TITLE_COL = "title"
ARTIST_COL = "artist"
ALBUM_COL = "album"
SECTION_COL = "section"
AUDIO_FILE_IN_COL = "audio_in"
DURATION_COL = "duration"
QUESTION_COL = "question"
ANSWER_COL = "answer"
ROW_ID_COL = "row_id"

N_PER_ROUND = 10

Rounds = List[Tuple[str, List["TriviaItem"]]]


class TriviaItem:
    def __init__(self, question, answer, source, section, number, round_name):
        self.question = question
        self.answer = answer
        self.source = source
        self.section = section
        self.number = number
        self.round_name = round_name

    def __str__(self):
        return (
            f"Q:{self.question}; A:{self.answer}; R:{self.round_name}; N:{self.number}"
        )

    def __repr__(self):
        return str(self)


def get_out_filepath(in_file) -> Path:
    if pd.isna(in_file):
        return None

    in_file = Path(in_file)
    new_name = re.sub(r"[^A-Za-z0-9.]+", "-", in_file.name)
    return (TRIMMED_DIR / new_name).with_suffix(".mp4")


def trim_audio(in_file: str, duration: float, verbose=False):

    if pd.isna(in_file):
        return

    in_file = ORIGINALS_DIR / in_file
    if in_file.suffix not in [".webm", ".m4a", "mp3"]:
        print(in_file)
        raise ValueError

    out_path = get_out_filepath(in_file)

    if pd.isna(duration):
        duration = 5

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(in_file),
        "-i",
        "LaTeX/question_mark.jpg",
        "-ss",
        "0",
        "-t",
        str(duration),
        "-af",
        "silenceremove=start_periods=1:start_duration=1:start_threshold=-70dB:detection=peak,aformat=dblp",  # noqa E501
        "-filter:a",
        "loudnorm",
        "-acodec",
        "aac",
        "-vcodec",
        "libx264",
        "-tune",
        "stillimage",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        str(out_path),
    ]
    if verbose:
        print(" ".join(f"'{arg}'" for arg in cmd))

    subprocess.check_call(cmd)

    if verbose:
        print(f"Did {in_file.name}")


def consolidate_metadata() -> pd.DataFrame:
    dfs = []
    for f in (
        f for extn in ["csv", "tsv"] for f in SONGS_METADATA_DIR.glob(f"*.{extn}")
    ):
        f: Path
        try:
            if f.suffix == ".csv":
                df = pd.read_csv(f, delimiter=";")
                if len(df.columns) < 3:
                    df = pd.read_csv(f, delimiter=",")
            elif f.suffix == ".tsv":
                df = pd.read_csv(f, delimiter="\t")
            else:
                raise ValueError
        except pd.errors.ParserError:
            print(f)
            raise

        df[ROW_ID_COL] = df.apply(lambda row: uuid.uuid4().hex[:6], axis=1)
        df[SECTION_COL] = f.stem

        dfs.append(df)

    df = pd.concat(dfs, axis=0)
    df = df[[ROW_ID_COL, TITLE_COL, ARTIST_COL, ALBUM_COL, SECTION_COL]]

    df.to_csv("songs_meta_pre.csv", index=False)
    return df


def read_df() -> pd.DataFrame:
    df = pd.read_csv(
        "songs_meta_pre.csv",
        dtype={
            TITLE_COL: str,
            ARTIST_COL: str,
            ALBUM_COL: str,
            SECTION_COL: str,
            ROW_ID_COL: str,
        },
    )
    audio_files = [
        f.name for f in sorted(ORIGINALS_DIR.iterdir(), key=lambda f: f.stat().st_mtime)
    ]
    display(len(audio_files))
    display(len(df))
    df[AUDIO_FILE_IN_COL] = audio_files

    df[DURATION_COL] = np.where(df[AUDIO_FILE_IN_COL].isna(), None, 3)
    df[QUESTION_COL] = "Q" + df[ROW_ID_COL]
    df[ANSWER_COL] = "A" + df[ROW_ID_COL]

    df.to_csv("songs_meta_filled.csv", index=False)
    return df


def trim_songs(df: pd.DataFrame):
    for row in df.iterrows():
        row = row[1]
        trim_audio(row[AUDIO_FILE_IN_COL], duration=row[DURATION_COL], verbose=True)


consolidate_metadata()
df = read_df()
trim_songs(df)

# %%


def get_rounds(df) -> Rounds:
    sections = df[SECTION_COL].unique()
    rounds = {}

    for s_idx, section in enumerate(sections):
        section_df = df[df[SECTION_COL] == section]
        section_df: pd.DataFrame

        n_qs = len(section_df)
        q_num = 1

        n_subsections = n_qs // N_PER_ROUND

        for i in range(n_subsections):
            start_idx = i * N_PER_ROUND
            end_idx = start_idx + N_PER_ROUND
            if n_qs > N_PER_ROUND:
                round_name = f"{section.title()} (Q{start_idx+1}--{end_idx})"
            else:
                round_name = f"{section.title()}"

            questions = []
            for row in section_df.iloc[start_idx:end_idx, :].iterrows():
                row = row[1]
                questions.append(
                    TriviaItem(
                        row[QUESTION_COL],
                        row[ANSWER_COL],
                        row[AUDIO_FILE_OUT_COL],
                        row[SECTION_COL],
                        q_num,
                        round_name,
                    )
                )

                q_num += 1

            rounds[round_name] = questions

    # Rearrange to put bonus last (dicts remember insertion order)
    new_rounds = {}
    for k, v in rounds.items():
        if k.startswith("Bonus"):
            _bonus_k, _bonus_v = k, v
            continue
        new_rounds[k] = v
    new_rounds[_bonus_k] = _bonus_v
    rounds = new_rounds

    return list(rounds.items())


get_rounds(df)
# %%


def make_anchor(trivia_item: TriviaItem) -> str:
    pp_round_name = re.sub(r"[^A-Za-z0-9]+", "-", trivia_item.round_name)
    anchor = f"s-{pp_round_name}-q-{trivia_item.number}"
    anchor = re.sub(r"-+", "-", anchor)
    return anchor


def generate_asciidoc(rounds: Rounds):
    preamble = """
= Music trivia
:toc2:
:toclevels: 2
:toc-title: Welcome to Quarantine Music Trivia!

[subs=""]
++++++++++++
<style>
html, body { height: 100%; }
.fullheight { overflow-y:auto; height:100vh; }​
a { color:blue; }
a:visited { color:blue; }
a:active { color:blue; }
a[tabindex]:focus { color:blue; outline:none; }
</style>
++++++++++++

== Welcome
    """

    doc_parts = []

    def add_line(s, empty_after=0):
        s = str(s)
        doc_parts.append(s)
        for _ in range(empty_after):
            doc_parts.append("")

    add_line(preamble, empty_after=1)

    for ri, (round_name, trivia_items) in enumerate(rounds):
        trivia_items: List[TriviaItem]

        add_line(f"[[s{ri}]]")
        add_line(f"== {round_name}", empty_after=1)

        # latex_items.append(r"\subsection{Questions}")
        for qi, trivia_item in enumerate(trivia_items):
            trivia_item: TriviaItem

            question_id = f"q{ri}_{qi}"

            this_anchor = make_anchor(trivia_item)
            print(this_anchor)

            if not (ri == 0 and qi == 0):
                if qi == 0:
                    prev_trivia_item = rounds[ri - 1][1][-1]
                else:
                    prev_trivia_item = trivia_items[qi - 1]

                prev_anchor = make_anchor(prev_trivia_item)

            if not (ri == len(rounds) - 1 and qi == len(trivia_items) - 1):
                if qi == len(trivia_items) - 1:
                    next_trivia_item = rounds[ri + 1][1][0]
                else:
                    next_trivia_item = trivia_items[qi + 1]
                next_anchor = make_anchor(next_trivia_item)

            add_line(f"[[{this_anchor}]]")
            add_line(f"=== Q{trivia_item.number}", empty_after=1)
            add_line(
                f"[big]#{round_name}: Question {trivia_item.number}#", empty_after=1
            )
            add_line(f"==== Question", empty_after=1)
            add_line(trivia_item.question, empty_after=1)

            if not pd.isna(trivia_item.source):
                # with open(trivia_item.source, "rb") as f:
                #     b64_enc_vid = base64.b64encode(f.read()).decode("ascii")
                # src = f"data:video/mp4;base64,{b64_enc_vid}"
                src = trivia_item.source
                media_block = f"video::{src}[width=300]"
            else:
                media_block = f"Media goes here"

            add_line(media_block, empty_after=1)

            add_line(f"==== Answer", empty_after=1)
            add_line(
                f"""
[subs=""]
+++++++++++++++++
<button id="button_{question_id}" onclick="toggle_hidden_{question_id}()">
Show answer
</button>
+++++++++++++++++""",
                empty_after=1,
            )
            add_line(f"[[answer_{question_id}]]")
            add_line(trivia_item.answer)
            add_line(trivia_item.source, empty_after=1)
            add_line(
                f"""
[subs=""]
+++++++++++++++
<script>
var z = document.getElementById("answer_{question_id}");
z.style.display = "none"
function toggle_hidden_{question_id}() {{
  var x = document.getElementById("answer_{question_id}");
  var b = document.getElementById("button_{question_id}");
  if (x.style.display === "none") {{
    x.style.display = "block";
    b.innerHTML = "Hide answer";
  }} else {{
    x.style.display = "none";
    b.innerHTML = "Show answer";
  }}
}}
</script>
+++++++++++++++""",
                empty_after=1,
            )
            add_line(f'[role="fullheight"]')
            # Very first question
            if ri == 0 and qi == 0:
                add_line(
                    f"<<{next_anchor}, Next question -- "
                    + f"Q{next_trivia_item.number}>>"
                )
            # Very last question
            elif ri == len(rounds) - 1 and qi == len(trivia_items) - 1:
                add_line(
                    f"<<{prev_anchor}, Previous question -- "
                    + f"Q{prev_trivia_item.number}>>"
                )
            # First question in round >= 1
            elif qi == 0:
                add_line(
                    f"<<{prev_anchor}, Previous question -- "
                    + f"{prev_trivia_item.round_name}: Q{prev_trivia_item.number}>> +"
                )
                add_line(
                    f"<<{next_anchor}, Next question -- "
                    + f"Q{next_trivia_item.number}>>"
                )
            # Last question in round < last_round
            elif qi == len(trivia_items) - 1:
                add_line(
                    f"<<{prev_anchor}, Previous question -- "
                    + f"Q{prev_trivia_item.number}>> +"
                )
                add_line(
                    f"<<{next_anchor}, Next question -- "
                    + f"{next_trivia_item.round_name}: Q{next_trivia_item.number}>>"
                )
            # Middle questions
            else:
                add_line(
                    f"<<{prev_anchor}, Previous question -- "
                    + f"Q{prev_trivia_item.number}>> +"
                )
                add_line(
                    f"<<{next_anchor}, Next question -- "
                    + f"Q{next_trivia_item.number}>>"
                )

            add_line("")

    return "\n".join(doc_parts)


def write_asciidoc(df=None):
    if df is None:
        df = consolidate_metadata(trim=True)

    rounds = get_rounds(df)
    with open("trivia.asciidoc", "w") as f:
        f.write(generate_asciidoc(rounds))

    subprocess.check_call(["asciidoc", "-b", "html5", "trivia.asciidoc"])


write_asciidoc(df)
