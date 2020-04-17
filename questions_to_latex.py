# %%
from pathlib import Path
import json  # noqa F401
import re  # noqa F401
from typing import List

import numpy as np
import pandas as pd
from IPython.display import display  # noqa F401

np.random.seed(126)

TEST = False

N_QUESTIONS_PER_ROUND = 10

Q_COL = "Question"
A_COL = "Answer"
IS_MOVIE_COL = "Answer is movie"
IMAGE_COL = "Image"

LATEX_DIR: Path = Path("docs/LaTeX")
LATEX_DIR.mkdir(exist_ok=True, parents=True)


class TriviaItem:
    def __init__(self, *, q, a, round_name, number, image_file):
        self.question = q
        self.answer = a
        self.round_name = round_name
        self.number = number
        self.image_file = image_file

    def __repr__(self):
        contents = ", ".join(
            [
                f"q={self.question}",
                f"a={self.answer}",
                f"r={self.round_name}",
                f"f={self.image_file}",
            ]
        )
        return f"T({contents})"


def get_trivia_items() -> List[TriviaItem]:
    df = pd.read_csv("./questions_final.csv")
    df[IS_MOVIE_COL] = df[IS_MOVIE_COL].astype(bool)

    for c in [Q_COL, A_COL]:
        # df[c] = df[c].str.replace(r'\emph{(?P=film[^{}]*?)}', r'__\g<film}__')
        df[c] = (
            df[c]
            .str.replace(r'"([^"]*?)"', r"\g<1>", regex=True)
            .str.replace("“", "``", regex=False)
            .str.replace("”", "''", regex=False)
            .str.replace("‘", "`", regex=False)
            .str.replace("’", "'", regex=False)
            .str.replace("&", r"\&", regex=False)
            .str.replace(r"\}\?$", r"}\,?", regex=True)
        )

    df.loc[df[IS_MOVIE_COL], A_COL] = r"\emph{" + df.loc[df[IS_MOVIE_COL], A_COL] + r"}"

    regular_df, bonus_df = df.iloc[:-10, :], df.iloc[-10:, :]
    regular_df: pd.DataFrame
    bonus_df: pd.DataFrame

    q_num = 1
    round_i = 1
    trivia_items: List[TriviaItem] = []
    for df in [regular_df, bonus_df]:
        if TEST:
            df = df.iloc[:12, :]

        n_qs = len(df)
        n_subsections = (n_qs - 1) // N_QUESTIONS_PER_ROUND + 1
        for i in range(n_subsections):
            start_idx = i * N_QUESTIONS_PER_ROUND
            end_idx = start_idx + N_QUESTIONS_PER_ROUND

            this_round_df: pd.DataFrame = df.iloc[start_idx:end_idx, :]

            if df is not bonus_df:
                round_basename = f"Round {round_i}"
            else:
                round_basename = "Bonus Round"

            round_i += 1
            round_name = round_basename

            for _, row in this_round_df.iterrows():
                if pd.isna(row[IMAGE_COL]):
                    image_file = None
                else:
                    image_file_path: Path = Path(row[IMAGE_COL])
                    image_file = (
                        "{"
                        + str(Path("Images") / image_file_path.stem)
                        + "}"
                        + image_file_path.suffix
                    )

                trivia_items.append(
                    TriviaItem(
                        q=row[Q_COL],
                        a=row[A_COL],
                        round_name=round_name,
                        number=q_num,
                        image_file=image_file,
                    )
                )

                q_num += 1

    return trivia_items


get_trivia_items()

# %%

# Best themes: Montepellier, EastLansing, Antibes, Bergen# CambridgeUS, Hannover
# Best color themes: rose, orchid, lily, dolphin, seahorse
def make_latex(trivia_items: List[TriviaItem], include_images: bool = True) -> str:
    preamble = r"""\documentclass[11pt]{beamer}
\usepackage{graphicx}
\usepackage[export]{adjustbox}
\usepackage[space,multidot]{grffile}

\usetheme[hideothersubsections]{Hannover}
\usecolortheme{dolphin}
\setbeamercovered{invisible}
\setbeamertemplate{navigation symbols}{\insertslidenavigationsymbol}
\setbeamertemplate{page number in head/foot}{}
\setbeamertemplate{blocks}[rounded][shadow=false]
% \setbeamerfont{section in sidebar}{size=\fontsize{4}{3}\selectfont}
% \setbeamerfont{subsection in sidebar}{size=\fontsize{4}{3}\selectfont}
% \setbeamerfont{subsubsection in sidebar}{size=\fontsize{4}{2}\selectfont}

\usepackage{microtype}
\DisableLigatures[f]{encoding = *, family = *}

% \usefonttheme{professionalfonts} % using non standard fonts for beamer
\usepackage[utf8]{inputenc}
\usefonttheme{serif} % default family is serif
\usepackage{XCharter}
% stix2
% XCharter
% (sans) [defaultsans]{cantarell}

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

\title{Welcome to Quarantine Movie Trivia!}
\date{}

\begin{frame}
\titlepage{}
\end{frame}

\begingroup{}
\begin{frame}
\vfill{}
\begin{beamercolorbox}[sep=8pt,center,shadow=true,rounded=true]{title}
\usebeamerfont{title}Good luck everyone! And have fun!
\end{beamercolorbox}
\vfill{}
\end{frame}
\endgroup{}
    """

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
\end{{frame}}
    """

    answer_sans_image_template_str = r"""
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

    answer_with_image_template_str = r"""
\begin{{frame}}[t]{{{question_title}}}
\vspace{{2em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\pause{{}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.35\linewidth}}
\begin{{block}}{{Answer}}
{answer}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.6\linewidth}}
\begin{{center}}
\includegraphics[max width=0.9\textwidth,max height=0.4\textheight]{{{image_file}}}
\end{{center}}
\end{{column}}
\end{{columns}}
\end{{frame}}
    """

    latex_items = []

    def append_qs_and_as(trivia_items: List[TriviaItem]):

        for trivia_item in trivia_items:
            round_name = trivia_item.round_name
            number = trivia_item.number

            latex_items.append(
                question_template_str.format(
                    question_title=f"{round_name}, Question {number}",
                    question=trivia_item.question,
                    question_number=number,
                )
            )

        latex_items.append(r"\subsection{Answers}")
        for trivia_item in trivia_items:
            round_name = trivia_item.round_name
            number = trivia_item.number

            if pd.isna(trivia_item.image_file) or not include_images:
                latex_items.append(
                    answer_sans_image_template_str.format(
                        question_title=f"{round_name}, Answer {number}",
                        question=trivia_item.question,
                        answer=trivia_item.answer,
                    )
                )

            else:
                latex_items.append(
                    answer_with_image_template_str.format(
                        question_title=f"{round_name}, Answer {number}",
                        question=trivia_item.question,
                        answer=trivia_item.answer,
                        image_file=trivia_item.image_file,
                    )
                )

    latex_items.append(preamble)

    prev_round_name = None
    this_round_items: List[TriviaItem] = []

    for trivia_item in trivia_items:
        round_name = trivia_item.round_name

        if round_name != prev_round_name:
            if prev_round_name is not None:
                append_qs_and_as(this_round_items)

            latex_items.append(round_section_template_str.format(round_name=round_name))

            prev_round_name = round_name
            this_round_items: List[TriviaItem] = []

        this_round_items.append(trivia_item)

    append_qs_and_as(this_round_items)

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

    if include_images:
        outfile = "movie_trivia.tex"
    else:
        outfile = "movie_trivia_no_images.tex"
    with (LATEX_DIR / outfile).open("w") as f:
        f.write(latex_str)

    return latex_str


if __name__ == "__main__":
    # display(get_trivia_items())
    # rounds = get_rounds()
    # assert len(rounds) == N_ROUNDS + 1  # for bonus
    # for k, v in rounds.items():
    #     print(k, len(v))
    #     assert len(v) == N_QUESTIONS_PER_ROUND

    # with open("test.json", "w") as f:
    #   json.dump({k: [x.to_dict() for x in v] for k, v in rounds.items()}, f, indent=2)

    items = get_trivia_items()
    make_latex(items)
    make_latex(items, include_images=False)

# %%
