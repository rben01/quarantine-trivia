# %%
import subprocess
import uuid
from pathlib import Path
from typing import List, Mapping

import pandas as pd
from IPython.display import display  # noqa F401

songs_metadata_dir = Path("Song meta")
music_dir = Path("Audio/Trimmed")

TITLE = "title"
ARTIST = "artist"
ALBUM = "album"
SECTION = "section"
AUDIO_FILE = "audio"
QUESTION = "question"
ANSWER = "answer"

N_PER_ROUND = 10


class TriviaItem:
    def __init__(self, question, answer, filepath):
        self.question = question
        self.answer = answer
        self.filepath = filepath

    def __str__(self):
        return f"Q:{self.question}; A:{self.answer}; P:{self.filepath}"

    def __repr__(self):
        return str(self)


def get_data() -> pd.DataFrame:
    dfs = []
    for f in (
        f for extn in ["csv", "tsv"] for f in songs_metadata_dir.glob(f"*.{extn}")
    ):
        f: Path
        try:
            if f.suffix == ".csv":
                df = pd.read_csv(f, delimiter=";")
            elif f.suffix == ".tsv":
                df = pd.read_csv(f, delimiter="\t")
            else:
                raise ValueError
        except pd.errors.ParserError:
            print(f)
            raise

        df["random_id"] = df.apply(lambda row: uuid.uuid4().hex[:5], axis=1)
        df[SECTION] = f.stem

        df[AUDIO_FILE] = f.stem + "_" + df["random_id"]
        df[QUESTION] = "Q_" + df["random_id"]
        df[ANSWER] = "A_" + df["random_id"]

        dfs.append(df)

    df = pd.concat(dfs, axis=0)
    df = df[[TITLE, ARTIST, ALBUM, SECTION, AUDIO_FILE, QUESTION, ANSWER]]

    return df


display(get_data())


def get_rounds(df) -> Mapping[str, List[TriviaItem]]:
    sections = df[SECTION].unique()
    rounds = {}

    for s_idx, section in enumerate(sections):
        section_df = df[df[SECTION] == section]
        section_df: pd.DataFrame

        n_qs = len(section_df)

        n_subsections = n_qs // N_PER_ROUND
        for i in range(n_subsections):
            start_idx = i * N_PER_ROUND
            end_idx = start_idx + N_PER_ROUND
            round_name = f"{section.title()} (Q{start_idx+1}-Q{end_idx})"
            questions = section_df.iloc[start_idx:end_idx, :].apply(
                lambda row: TriviaItem(row[QUESTION], row[ANSWER], row[AUDIO_FILE]),
                axis=1,
            )

            rounds[round_name] = questions.tolist()

    return rounds


get_rounds(get_data())
# %%


def generate_latex(rounds):
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
% \setbeamerfont{section in sidebar}{size=\fontsize{4}{3}\selectfont}
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
\begin{{center}}
\includemedia[%
    width=0.4\linewidth,
    height=0.3\linewidth,
    addresource={source},
    flashvars={{source={source}}}
  ]{}{VPlayer9.swf}
\end{{center}}
\end{{block}}
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

    for round_name, trivia_items in rounds.items():
        round_frame_str = round_section_template_str.format(round_name=round_name)
        add_line(round_frame_str)

        # latex_items.append(r"\subsection{Questions}")
        for i, trivia_item in enumerate(trivia_items):
            question_frame_str = question_template_str.format(
                question_number=i + 1,
                question_title=f"{round_name}, Question {i+1}",
                question=trivia_item.question,
                source=trivia_item.source,
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


def create_doc():
    df = get_data()
    text = generate_asciidoc(df)
    with open("trivia_.asciidoc", "w") as f:
        f.write(text)

    subprocess.run(["asciidoc", "-b", "html5", "trivia_.asciidoc"])
