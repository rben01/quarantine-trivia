# %%
import json  # noqa F401
import re
from pathlib import Path
from typing import List, Mapping

import numpy as np
from IPython.display import display  # noqa F401

np.random.seed(12763)

N_ROUNDS = 2
N_QUESTIONS_PER_ROUND = 2
N_QUESTIONS_TOTAL = N_ROUNDS * N_QUESTIONS_PER_ROUND


class TriviaItem:
    QUESTION_RE = re.compile(r"^\s*\d+\.\s*(.*?)\s*$")
    ANSWER_RE = re.compile(r"^\s*-\s*(.*?)\s*$")

    @staticmethod
    def clean_str(string: str) -> str:
        string = string[0].upper() + string[1:]
        string = re.sub(r"""(^|\W)['"](.*?)['"](\W|$)""", r"\1``\2''\3", string)
        string = re.sub(r"([&%$#_\{\}])", r"\\\1", string)
        string = re.sub(r"\?$", r"\@?", string)
        return string

    def __init__(self, question, answer):
        question = self.clean_str(question)
        answer = self.clean_str(answer)

        self.question = question
        self.answer = answer

    @classmethod
    def from_lines(cls, question_line, answer_line):
        question = cls.QUESTION_RE.match(question_line).group(1)
        answer = cls.ANSWER_RE.match(answer_line).group(1)
        return cls(question, answer)

    def __repr__(self):
        return f"{self.__class__}(question={self.question}, answer={self.answer})"

    def __str__(self):
        return f"Q: {self.question}; A: {self.answer}"

    def to_dict(self) -> Mapping:
        return {"question": self.question, "answer": self.answer}


def parse_questions(filename) -> List[TriviaItem]:
    trivia_items = []
    with open(filename) as f:
        while True:
            try:
                question_line = next(f)
            except StopIteration:
                break
            else:
                answer_line = next(f)
                trivia_items.append(TriviaItem.from_lines(question_line, answer_line))

    return trivia_items


def get_trivia_items() -> Mapping[str, List[TriviaItem]]:
    trivia_items = {}
    for filename in ["questions.txt", "bonus_questions.txt"]:
        trivia_items[Path(filename).stem] = parse_questions(filename)

    return trivia_items


def get_rounds() -> Mapping[str, List[TriviaItem]]:
    rounds = {}
    trivia_items = get_trivia_items()
    selected_questions = np.random.choice(
        trivia_items["questions"], size=N_QUESTIONS_TOTAL, replace=False
    )

    for i in range(N_ROUNDS):
        round_name = f"Round {i+1}"
        rounds[round_name] = list(
            selected_questions[
                i * N_QUESTIONS_PER_ROUND : (i + 1) * N_QUESTIONS_PER_ROUND
            ]
        )

    rounds["Bonus Round"] = trivia_items["bonus_questions"]

    return rounds


# Best themes: Montepellier, EastLansing, Antibes, Bergen# CambridgeUS
# Best color themes: rose, orchid, lily, dolphin, seahorse
def make_latex() -> str:
    rounds = get_rounds()
    latex_items = [
        r"""\documentclass[11pt]{beamer}
\usepackage{mathtools, enumerate, graphicx, cancel}

\usetheme{CambridgeUS}
\usecolortheme{dolphin}
\setbeamercovered{invisible}
\setbeamertemplate{navigation symbols}{\insertslidenavigationsymbol}
\setbeamertemplate{page number in head/foot}{}
\setbeamertemplate{blocks}[rounded][shadow=false]

\AtBeginSection[]{}

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
    ]

    round_section_template_str = r"""
\section{{{round_name}}}
    """

    question_template_str = r"""
\begin{{frame}}[t]{{{question_title}}}
\vspace{{2em}}
\begin{{block}}{{Question}}
{question}
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
        latex_items.append(round_frame_str)

        latex_items.append(r"\subsection{Questions}")
        for i, trivia_item in enumerate(trivia_items):
            question = trivia_item.question
            question_frame_str = question_template_str.format(
                question_title=f"{round_name}, Question {i+1}", question=question,
            )

            latex_items.append(question_frame_str)

        latex_items.append(r"\subsection{Answers}")
        for i, trivia_item in enumerate(trivia_items):
            question = trivia_item.question
            answer = trivia_item.answer
            answer_frame_str = answer_template_str.format(
                question_title=f"{round_name}, Answer {i+1}",
                question=question,
                answer=answer,
            )

            latex_items.append(answer_frame_str)
    latex_items.append(
        r"""
\begingroup{}
\setbeamertemplate{headline}{}
\section{Thanks for playing!}
\subsection{\ }
\endgroup{}

\end{document}
"""
    )

    latex_str = "\n".join(latex_items)

    with open("LaTeX/trivia.tex", "w") as f:
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

    make_latex()


# %%
