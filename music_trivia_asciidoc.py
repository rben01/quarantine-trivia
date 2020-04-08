# %%
import re
import subprocess
import uuid
from pathlib import Path
from typing import List, Mapping

import numpy as np
import pandas as pd
from IPython.display import display  # noqa F401

SONGS_METADATA_DIR = Path("Song meta")
AUDIO_DIR = Path("LaTeX/Audio")

ORIGINALS_DIR = AUDIO_DIR / "Originals"
TRIMMED_DIR = AUDIO_DIR / "Trimmed"
for d in [ORIGINALS_DIR, TRIMMED_DIR]:
    d.mkdir(exist_ok=True)

TITLE_COL = "title"
ARTIST_COL = "artist"
ALBUM_COL = "album"
SECTION_COL = "section"
AUDIO_FILE_IN_COL = "audio_in"
AUDIO_FILE_OUT_COL = "audio_out"
DURATION_COL = "duration"
QUESTION_COL = "question"
ANSWER_COL = "answer"

N_PER_ROUND = 10

Rounds = Mapping[str, List["TriviaItem"]]


class TriviaItem:
    def __init__(self, question, answer, source, section):
        self.question = question
        self.answer = answer
        self.source = source
        self.section = section

    def __str__(self):
        return f"Q:{self.question}; A:{self.answer}; P:{self.source}"

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
        "-acodec",
        "mp3",
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


def get_data(trim=True) -> pd.DataFrame:
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

        df["random_id"] = df.apply(lambda row: uuid.uuid4().hex[:5], axis=1)
        df[SECTION_COL] = f.stem

        if "audio" in df.columns:
            df[AUDIO_FILE_IN_COL] = df["audio"]
        else:
            df[AUDIO_FILE_IN_COL] = None

        df[AUDIO_FILE_OUT_COL] = np.where(
            df[AUDIO_FILE_IN_COL].isna(),
            None,
            df[AUDIO_FILE_IN_COL].map(get_out_filepath),
        )

        df[DURATION_COL] = np.where(df[AUDIO_FILE_IN_COL].isna(), None, 3)
        df[QUESTION_COL] = "Q" + df["random_id"]
        df[ANSWER_COL] = "A" + df["random_id"]

        dfs.append(df)

    df = pd.concat(dfs, axis=0)
    df = df[
        [
            TITLE_COL,
            ARTIST_COL,
            ALBUM_COL,
            SECTION_COL,
            AUDIO_FILE_IN_COL,
            AUDIO_FILE_OUT_COL,
            DURATION_COL,
            QUESTION_COL,
            ANSWER_COL,
        ]
    ]

    if trim:
        for row in df.iterrows():
            row = row[1]
            trim_audio(row[AUDIO_FILE_IN_COL], duration=row[DURATION_COL], verbose=True)

    return df


df = get_data(trim=True)
display(df)


def get_rounds(df) -> Rounds:
    sections = df[SECTION_COL].unique()
    rounds = {}

    for s_idx, section in enumerate(sections):
        section_df = df[df[SECTION_COL] == section]
        section_df: pd.DataFrame

        n_qs = len(section_df)

        n_subsections = n_qs // N_PER_ROUND
        for i in range(n_subsections):
            start_idx = i * N_PER_ROUND
            end_idx = start_idx + N_PER_ROUND
            round_name = f"{section.title()} (Q{start_idx+1}--{end_idx})"
            questions = section_df.iloc[start_idx:end_idx, :].apply(
                lambda row: TriviaItem(
                    row[QUESTION_COL],
                    row[ANSWER_COL],
                    row[AUDIO_FILE_OUT_COL],
                    row[SECTION_COL],
                ),
                axis=1,
            )

            rounds[round_name] = questions.tolist()

    # Rearrange to put bonus last (dicts remember insertion order)
    new_rounds = {}
    for k, v in rounds.items():
        if k.startswith("Bonus"):
            _bonus_k, _bonus_v = k, v
            continue
        new_rounds[k] = v
    new_rounds[_bonus_k] = _bonus_v
    rounds = new_rounds

    return rounds


# %%


def generate_asciidoc(rounds: Rounds):
    preamble = """
= Music trivia
:toc2:
:toclevels: 5
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
        doc_parts.append(s)
        for _ in range(empty_after):
            doc_parts.append("")

    add_line(preamble, empty_after=1)

    for ri, (round_name, trivia_items) in enumerate(rounds.items()):
        trivia_item: TriviaItem

        ri += 1
        add_line(f"[[s{ri}]]")
        add_line(f"== {round_name}", empty_after=1)

        # latex_items.append(r"\subsection{Questions}")
        for qi, trivia_item in enumerate(trivia_items):
            qi += 1
            question_id = f"q{ri}_{qi}"

            add_line(f"[[s{ri}q{qi}]]")
            add_line(f"==== Question {qi}", empty_after=1)
            add_line(f"===== Question", empty_after=1)
            add_line(trivia_item.question)

            if not pd.isna(trivia_item.source):
                media_block = r"video::{trivia_item.source}[width=300]"
            else:
                media_block = f"Media goes here"

            add_line(media_block, empty_after=1)

            add_line(f"===== Answer", empty_after=1)
            add_line(
                f"""
[subs=""]
+++++++++++++++++
<button onclick="toggle_hidden_{qi}()">Toggle answer</button>
+++++++++++++++++""",
                empty_after=1,
            )
            add_line(f"[[answer_{question_id}]]")
            add_line(trivia_item.answer, empty_after=1)
            add_line(
                f"""
[subs=""]
+++++++++++++++
<script>
var z = document.getElementById("answer_{question_id}");
z.style.display = "none"
function toggle_hidden_{question_id}() {{
  var x = document.getElementById("answer_{question_id}");
  if (x.style.display === "none") {{
    x.style.display = "block";
  }} else {{
    x.style.display = "none";
  }}
}}
</script>
+++++++++++++++""",
                empty_after=1,
            )
            add_line(f'[role="fullheight"]')
            if ri == 1 and qi == 1:
                add_line(f"<<s{ri}q{qi+1}, next q>>")
            elif ri == len(rounds) and qi == len(trivia_items):
                add_line(f"<<s{ri}q{qi-1}, prev q>>")
            else:
                add_line(f"<<s{ri}q{qi-1}, prev q>>" f" <<s{ri}q{qi+1}, next q>>")

            add_line("")

            question_frame_str = question_template_str.format(
                question_number=ri * N_PER_ROUND + qi + 1,
                question_title=f"{round_name}, Question {qi+1}",
                question=trivia_item.question,
                source=trivia_item.source,
                media_block=media_block,
            )

            add_line(question_frame_str)

        add_line(r"\subsection{Answers}")
        for qi, trivia_item in enumerate(trivia_items):
            answer_frame_str = answer_template_str.format(
                question_title=f"{round_name}, Answer {qi+1}",
                question=trivia_item.question,
                answer=trivia_item.answer,
            )

            latex_items.append(answer_frame_str)

    sections = df["section"].unique()

    qi = 0
    for section_idx, section in enumerate(sections):
        section_idx += 1
        add_line(f"[[s{section_idx}]]")
        add_line(f"== Section {section}", empty_after=1)

        this_section_df = df[df["section"] == section]
        this_section_df: pd.DataFrame
        for q_idx, q in enumerate(this_section_df.iterrows()):
            qi += 1
            q_idx += 1
            if q_idx % 10 == 1:
                add_line(f"=== Questions {q_idx}-{q_idx+9}", empty_after=1)

            question_id = f"{section_idx}_{q_idx}"
            song_info = q[1]
            # Question section
            add_line(f"[[s{section_idx}q{q_idx}]]")
            add_line(f"==== Question {qi}", empty_after=1)
            add_line(f"===== Question", empty_after=1)
            add_line(f"audio::{song_info['file']}[Song]", empty_after=1)
            add_line(f"===== Answer", empty_after=1)
            add_line(
                f"""
[subs=""]
+++++++++++++++++
<button onclick="toggle_hidden_{question_id}()">Toggle answer</button>
+++++++++++++++++""",
                empty_after=1,
            )
            add_line(f"[[answer_{question_id}]]")
            add_line(song_info["title"], empty_after=1)
            add_line(
                f"""
[subs=""]
+++++++++++++++
<script>
var z = document.getElementById("answer_{question_id}");
z.style.display = "none"
function toggle_hidden_{question_id}() {{
  var x = document.getElementById("answer_{question_id}");
  if (x.style.display === "none") {{
    x.style.display = "block";
  }} else {{
    x.style.display = "none";
  }}
}}
</script>
+++++++++++++++""",
                empty_after=1,
            )
            add_line(f'[role="fullheight"]')
            if section_idx == 1 and q_idx == 1:
                add_line(f"<<s{section_idx}q{q_idx+1}, next q>>")
            elif section_idx == len(sections) and q_idx == len(this_section_df):
                add_line(f"<<s{section_idx}q{q_idx-1}, prev q>>")
            else:
                add_line(
                    f"<<s{section_idx}q{q_idx-1}, prev q>>"
                    f" <<s{section_idx}q{q_idx+1}, next q>>"
                )

            add_line("")

    return "\n".join(doc_parts)
