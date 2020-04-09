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
    def __init__(self, question, answer, source):
        self.question = question
        self.answer = answer
        self.source = source

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

# %%


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
                    row[QUESTION_COL], row[ANSWER_COL], row[AUDIO_FILE_OUT_COL]
                ),
                axis=1,
            )

            rounds[round_name] = questions.tolist()

    return rounds


def generate_latex(rounds: Rounds):
    preamble = r"""
\documentclass[11pt]{beamer}
\usepackage{graphicx}
\usepackage{media9}

\usetheme[hideothersubsections]{Hannover}
\usecolortheme{dolphin}
\setbeamercovered{invisible}
\setbeamertemplate{navigation symbols}{\insertslidenavigationsymbol}
\setbeamertemplate{page number in head/foot}{}
\setbeamertemplate{blocks}[rounded][shadow=false]
\setbeamerfont{section in sidebar}{size=\fontsize{5}{4}\selectfont}
% \setbeamerfont{subsection in sidebar}{size=\fontsize{4}{3}\selectfont}
% \setbeamerfont{subsubsection in sidebar}{size=\fontsize{4}{2}\selectfont}

\AtBeginSection[]{}
\AtBeginSection[]{
  \begin{frame}
    \vfill
    \centering
    \begin{beamercolorbox}[sep=8pt,center,shadow=true,rounded=true]{title}
    \usebeamerfont{title}\insertsectionhead\par%
    \end{beamercolorbox}
    \vfill
  \end{frame}
}

\AtBeginSubsection[]{
  \begin{frame}
    \vfill
    \centering
    \begin{beamercolorbox}[sep=8pt,center,shadow=true,rounded=true]{title}
    \usebeamerfont{title}\insertsectionhead\par%
    \usebeamerfont{subtitle}\insertsubsectionhead\par%
    \end{beamercolorbox}
    \vfill
  \end{frame}
}
\begin{document}

\title{Welcome to Quarantine Trivia!}
\date{}

\begin{frame}
  \titlepage{}
\end{frame}

    """

    latex_items = [preamble]

    def add_line(line):
        latex_items.append(line)

    round_section_template_str = r"""
\section{{{round_name}}}
    """

    question_template_str = r"""
\subsection*{{Q{question_number}}}
\begin{{frame}}[t]{{{question_title}}}
\vspace{{2em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\begin{{center}}
{media_block}
\end{{center}}
\end{{frame}}
    """

    answer_template_str = r"""
\begin{{frame}}[t]{{{question_title}}}
\vspace{{2em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\pause{{}}
\begin{{block}}{{Answer}}
{answer}
\end{{block}}
\end{{frame}}
    """

    # Rearrange to put bonus last (dicts remember insertion order)
    new_rounds = {}
    for k, v in rounds.items():
        if k.startswith("Bonus"):
            _bonus_k, _bonus_v = k, v
            continue
        new_rounds[k] = v
    new_rounds[_bonus_k] = _bonus_v

    for ri, (round_name, trivia_items) in enumerate(rounds.items()):
        round_frame_str = round_section_template_str.format(round_name=round_name)
        add_line(round_frame_str)

        # latex_items.append(r"\subsection{Questions}")
        for i, trivia_item in enumerate(trivia_items):
            if not pd.isna(trivia_item.source):
                media_block = r"""
\includemedia[%
    width=0.4\linewidth,
    height=0.3\linewidth,
    attachfiles,
    passcontext,
    addresource="{source}",
    flashvars={{source="{source}"}}
]{{}}{{VPlayer9.swf}}
""".format(
                    source=trivia_item.source.relative_to("LaTeX")
                )
            else:
                media_block = f"Media goes here"

            question_frame_str = question_template_str.format(
                question_number=ri * N_PER_ROUND + i + 1,
                question_title=f"{round_name}, Question {i+1}",
                question=trivia_item.question,
                source=trivia_item.source,
                media_block=media_block,
            )

            add_line(question_frame_str)

        add_line(r"\subsection{Answers}")
        for i, trivia_item in enumerate(trivia_items):
            answer_frame_str = answer_template_str.format(
                question_title=f"{round_name}, Answer {i+1}",
                question=trivia_item.question,
                answer=trivia_item.answer,
            )

            latex_items.append(answer_frame_str)

    latex_items.append(
        r"""
\section*{\ }
\subsection*{\ }
\begingroup{}
\setbeamertemplate{headline}{}
\begin{frame}
\vfill{}
\centering{}
\begin{beamercolorbox}[sep=8pt,center,shadow=true,rounded=true]{title}
\usebeamerfont{title}Thanks for playing!\par%
\end{beamercolorbox}
\vfill{}
\end{frame}
\endgroup{}
% \begingroup{}
% \setbeamertemplate{headline}{}
% \section*{Thanks for playing!}
% \subsection*{\ }
% \endgroup{}

\end{document}
"""
    )

    latex_str = "\n".join(latex_items)

    with open("LaTeX/trivia.tex", "w") as f:
        f.write(latex_str)

    return latex_str


generate_latex(get_rounds(df))

# rounds = get_rounds(get_data())
# generate_latex(rounds)


# %%
