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
SECTION_COL = "Section"
TOPIC_COL = "Topic"
Q_IMAGE_COL = "Question Image"
A_IMAGE_COL = "Answer Image"
SECTION_ORDER_COL = "Sort_"
INDEX_COL = "Index_"

LATEX_DIR: Path = Path("docs/LaTeX")
LATEX_DIR.mkdir(exist_ok=True, parents=True)


class TriviaItem:
    def __init__(
        self, *, q, a, round_name, section, topic, number, q_image_file, a_image_file
    ):
        self.question = q
        self.answer = a
        self.round_name = round_name
        self.section = section
        self.topic = topic
        self.number = number
        self.q_image_file = q_image_file
        self.a_image_file = a_image_file

    def __repr__(self):
        contents = ", ".join(
            [
                f"q={self.question}",
                f"a={self.answer}",
                f"r={self.round_name}",
                f"s={self.section}",
                f"t={self.topic}",
                f"qi={self.q_image_file}",
                f"ai={self.a_image_file}",
            ]
        )
        return f"T({contents})"


def get_trivia_items() -> List[TriviaItem]:
    df = pd.read_csv("./general trivia questions.csv")

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
            .str.replace("-.-", "---", regex=False)
        )

    topic_remapper = {
        "Plays and playwrights": "Plays and Playwrights",
        "Plants and animals": "Plants and Animals",
        "Famous American Women": "Women in American History",
        "Anthony Fauci": "Dr.\\ Anthony Fauci",
        "Paintings": "Famous Paintings",
        "World landmarks": "World Landmarks",
    }

    section_remapper = {
        **topic_remapper,
        "Canada": "Canada --- Our Friendly Neighbor to the North",
        "Anthony Fauci": (
            "Dr.\\ Anthony S.\\ " + "Fauci: Great New Yorker and Great Italian-American"
        ),
    }

    df[SECTION_COL] = df[SECTION_COL].map(section_remapper).fillna(df[SECTION_COL])

    df[TOPIC_COL] = df[TOPIC_COL].map(topic_remapper).fillna(df[TOPIC_COL])

    df[INDEX_COL] = list(range(len(df)))

    regular_df = df[df[SECTION_COL] != "Bonus"].copy()
    bonus_df = df[df[SECTION_COL] == "Bonus"].copy()
    regular_df: pd.DataFrame
    bonus_df: pd.DataFrame

    topic_order = [
        "Sports",
        "Plays and Playwrights",
        "Women in American History",
        "Science",
        "Plants and Animals",
        "Presidents",
        "Dr.\\ Anthony Fauci",
        "Famous Paintings",
        "Canada",
        "World Landmarks",
    ]

    for df in [regular_df, bonus_df]:
        df[SECTION_ORDER_COL] = df[TOPIC_COL].map(topic_order.index)
        df.sort_values([SECTION_ORDER_COL, INDEX_COL], inplace=True)

    df = pd.concat([regular_df, bonus_df], axis=0)
    if TEST:
        df = pd.concat([df.iloc[:23], bonus_df])

    g = df.groupby(SECTION_COL, sort=False)
    round_i = 1
    trivia_items: List[TriviaItem] = []
    for section, group in g:
        is_bonus = section == "Bonus"

        q_num = 1
        n_qs = len(group)
        n_subsections = (n_qs - 1) // N_QUESTIONS_PER_ROUND + 1
        for i in range(n_subsections):
            start_idx = i * N_QUESTIONS_PER_ROUND
            end_idx = start_idx + N_QUESTIONS_PER_ROUND

            this_round_df: pd.DataFrame = group.iloc[start_idx:end_idx, :]

            if is_bonus:
                round_name = "Bonus Round"
            else:
                round_name = f"Round {round_i}"

            round_i += 1

            for _, row in this_round_df.iterrows():
                image_files = {}
                for attr_name, col in [
                    ("q_image_file", Q_IMAGE_COL),
                    ("a_image_file", A_IMAGE_COL),
                ]:
                    if pd.isna(row[col]):
                        image_files[attr_name] = None
                    else:
                        img_path: Path = Path(row[col])
                        image_files[attr_name] = "".join(
                            [
                                "{",
                                str(Path("Images") / img_path.stem),
                                "}",
                                img_path.suffix,
                            ]
                        )

                trivia_items.append(
                    TriviaItem(
                        q=row[Q_COL],
                        a=row[A_COL],
                        round_name=round_name,
                        section=row[SECTION_COL],
                        topic=row[TOPIC_COL],
                        number=q_num,
                        **image_files,
                    )
                )

                q_num += 1

    return trivia_items


get_trivia_items()

# %%
# Best themes: Montepellier, EastLansing, Antibes, Bergen# CambridgeUS, Hannover
# Best color themes: rose, orchid, lily, dolphin, seahorse
def make_latex(trivia_items: List[TriviaItem], include_images: bool = True) -> str:
    preamble = r"""
\documentclass[11pt]{beamer}
\usepackage{graphicx}
\usepackage[export]{adjustbox}
\usepackage[space,multidot]{grffile}
\usepackage{ifthen}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}

\usetheme[hideothersubsections]{Goettingen}
\usecolortheme{seahorse}
\setbeamercovered{invisible}
\setbeamertemplate{navigation symbols}{\insertslidenavigationsymbol}
\setbeamertemplate{page number in head/foot}{}
\setbeamertemplate{blocks}[rounded][shadow=false]
% \setbeamerfont{section in sidebar}{size=\fontsize{4}{3}\selectfont}
% \setbeamerfont{subsection in sidebar}{size=\fontsize{4}{3}\selectfont}
% \setbeamerfont{subsubsection in sidebar}{size=\fontsize{4}{2}\selectfont}

\usepackage{microtype}
% \DisableLigatures[f]{encoding = *, family = *}

% \usefonttheme{professionalfonts} % using non standard fonts for beamer
\usepackage[utf8]{inputenc}
\usefonttheme{serif} % default family is serif
\usepackage{XCharter}
% stix2
% XCharter
% (sans) [defaultsans]{cantarell}

\AtBeginSection[]{
  \begin{frame}
    \vfill
    \centering
    \begin{beamercolorbox}[sep=8pt,center,shadow=true,rounded=true]{title}
    \usebeamerfont{title}\insertsectionhead\par%
    \ifthenelse{\equal{\secname}{Bonus Round}}{}{
        \usebeamerfont{subtitle}\thisSectionName\par%
    }
    \end{beamercolorbox}

    \ifthenelse{\equal{\secname}{Bonus Round} \AND{\equal{\subsecname}{Answers}}}{
        Get ready for some \emph{devilishly} hard questions!

        \includegraphics[width=0.5\textwidth]{Images/devil.jpg}
    }
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

\title{Welcome to Quarantine General Trivia!\vspace{-0.5in}}
\date{}

\begin{frame}
\titlepage{}
\end{frame}

\begin{frame}
In order to keep Ellen from hearing us put together the questions, we used advanced
technology\ldots
\vspace{1em}
\pause{}
\begin{center}
\includegraphics[max width=0.9\textwidth,max height=0.8\textheight]{Images/cone.jpg}
\end{center}
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
\def\thisSectionName{{{section}}}
\section{{{round_name}}}
    """

    question_sans_image_template_str = r"""
\subsection*{{Q{question_number}}}
\begin{{frame}}[t]{{{question_title}}}
\vspace{{0.5em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{frame}}
    """

    question_with_image_template_str = r"""
\subsection*{{Q{question_number}}}
\begin{{frame}}[t]{{{question_title}}}
\vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.25\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.7\linewidth}}
\begin{{center}}
\includegraphics[max width=0.9\textwidth,max height=0.6\textheight]{{{image_file}}}
\end{{center}}
\end{{column}}
\end{{columns}}
\end{{frame}}
    """

    answer_sans_image_template_str = r"""
\begin{{frame}}[t]{{{question_title}}}
\vspace{{0.5em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\visible<2->{{
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
}}
\end{{frame}}
    """

    answer_with_question_with_image_template_str = r"""
\begin{{frame}}[t]{{{question_title}}}
\vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.35\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\visible<2->{{
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
}}
\end{{column}}
\begin{{column}}{{0.6\linewidth}}
\begin{{center}}
\includegraphics[max width=0.9\textwidth,max height=0.6\textheight]{{{image_file}}}
\end{{center}}
\end{{column}}
\end{{columns}}
\end{{frame}}
    """

    answer_with_image_template_str = r"""
\begin{{frame}}[t]{{{question_title}}}
\vspace{{0.5em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\visible<2->{{
    \begin{{columns}}[T,totalwidth=\linewidth]
    \begin{{column}}{{0.35\linewidth}}
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
    \end{{column}}
    \begin{{column}}{{0.6\linewidth}}
    \begin{{center}}
    \includegraphics[max width=0.9\textwidth,max height=0.4\textheight]{{{image_file}}}
    \end{{center}}
    \end{{column}}
    \end{{columns}}
}}
\end{{frame}}
    """

    latex_items = []

    def append_qs_and_as(trivia_items: List[TriviaItem]):

        for trivia_item in trivia_items:
            round_name = trivia_item.round_name
            number = trivia_item.number

            question_kwargs = {
                "question": trivia_item.question,
                "question_number": number,
            }

            if trivia_item.section == "Bonus":
                question_kwargs["question_title"] = f"{round_name}: {trivia_item.topic}"
            else:
                question_kwargs["question_title"] = f"{round_name}, Question {number}"

            if trivia_item.q_image_file is None:
                template_str = question_sans_image_template_str
            else:
                template_str = question_with_image_template_str
                question_kwargs["image_file"] = trivia_item.q_image_file

            latex_items.append(template_str.format(**question_kwargs))

        latex_items.append(r"\subsection{Answers}")
        for trivia_item in trivia_items:
            round_name = trivia_item.round_name
            number = trivia_item.number

            answer_kwargs = {
                "question": trivia_item.question,
                "answer": trivia_item.answer,
            }

            if trivia_item.section == "Bonus":
                answer_kwargs["question_title"] = f"{round_name}: {trivia_item.topic}"
            else:
                answer_kwargs["question_title"] = f"{round_name}, Answer {number}"

            if r"\begin{enumerate}" in trivia_item.answer:
                answer_kwargs["maybe_s"] = "s"
            else:
                answer_kwargs["maybe_s"] = ""

            if (not include_images) or (
                trivia_item.q_image_file is None and trivia_item.a_image_file is None
            ):
                template_str = answer_sans_image_template_str
            elif (
                trivia_item.a_image_file is not None
                and trivia_item.a_image_file != trivia_item.q_image_file
            ):
                template_str = answer_with_image_template_str
                answer_kwargs["image_file"] = trivia_item.a_image_file
            elif trivia_item.q_image_file is not None:
                template_str = answer_with_question_with_image_template_str
                answer_kwargs["image_file"] = trivia_item.q_image_file

            latex_items.append(template_str.format(**answer_kwargs))

    latex_items.append(preamble)

    prev_round_name = None
    this_round_items: List[TriviaItem] = []

    for trivia_item in trivia_items:
        round_name = trivia_item.round_name

        if round_name != prev_round_name:
            if prev_round_name is not None:
                append_qs_and_as(this_round_items)

            latex_items.append(
                round_section_template_str.format(
                    round_name=f"{round_name}", section=trivia_item.section
                )
            )

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
        outfile = "general_trivia.tex"
    else:
        outfile = "no_img_general_trivia.tex"
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
    # make_latex(items, include_images=False)

# %%
