# %%
import json  # noqa F401
import re  # noqa F401
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from IPython.display import display  # noqa F401

from trivia_item import TriviaItem
from latex_templates import BeamerFrame, LatexTemplates

np.random.seed(126)

TEST = False
DRAFT = False

N_QUESTIONS_PER_ROUND = 10

QUESTIONS_CSV_FILE = "week 7 general trivia.csv"
TITLE = "Welcome to Quarantine Trivia VII!"

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

TOPIC_ORDER = [
    "Album by Album Art",
    "France",
    "Airport Codes",
    "Big Dates in History",
    "Gangsters in Fact and Fiction",
    "Holidays and Observances",
    "All the Cool Kids are Texting about South Dakota",
    "Pastries",
    "Explorers",
    "Products and Companies By Their Slogans",
]


def sms_thread_to_latex(thread_str: str) -> str:
    if not thread_str.strip().startswith("!"):
        return thread_str

    # Find all instances of: ! followed by a letter followed by any number of
    # characters up until the next instance of ! followed by a letter
    thread_str = re.sub(
        r"\*+",
        lambda match: " ".join([r"\textunderscore{}" * 6] * len(match.group(0))),
        thread_str,
    )
    messages = re.findall(r"!(\w(?:.(?!!\w))*)", thread_str)
    latex_strs = []

    for i, message in enumerate(messages):
        message = message.strip()
        latex_format_str = r"""
{maybe_hfill}\begin{{minipage}}{{0.9\textwidth}}
\begin{{mdframed}}[
    roundcorner=7pt,
    backgroundcolor={bg_color},
    linecolor={bg_color},
    fontcolor={text_color},
    ignorelastdescenders]
\begin{{flushleft}}
{{\small{{}}\fontfamily{{qhv}}\selectfont{{}}
{message}
}}
\end{{flushleft}}
\end{{mdframed}}
\end{{minipage}}"""

        if i % 2 == 1:
            maybe_hfill = r"\hfill{}"
            bg_color = "blue!80!white"
            text_color = "white"
        else:
            maybe_hfill = r""
            bg_color = "black!5"
            text_color = "black"

        latex_str = latex_format_str.format(
            maybe_hfill=maybe_hfill,
            bg_color=bg_color,
            text_color=text_color,
            message=message,
        )

        latex_strs.append(latex_str)

    return "\n".join(latex_strs)


sms_thread_to_latex(
    """!I just got admitted to the flagship university
    of our state system! But I don't know where it's located.
!It's like a miracle you ever got in - it's in **.
"""
)
# sms_thread_to_latex("akjhdakjsdh")
# %%


def get_trivia_items() -> List[TriviaItem]:
    df = pd.read_csv(QUESTIONS_CSV_FILE)
    df = df[df[Q_COL].notna()]

    for c in [Q_COL, A_COL]:
        # df[c] = df[c].str.replace(r'\emph{(?P=film[^{}]*?)}', r'__\g<film}__')
        df[c] = (
            df[c]
            .str.replace(r'"([^"]*?)"', r"``\1''", regex=True)
            .str.replace("’”", r"’\,”", regex=False)
            .str.replace("”’", r"”\,’", regex=False)
            .str.replace("“", "``", regex=False)
            .str.replace("”", "''", regex=False)
            .str.replace("‘", "`", regex=False)
            .str.replace("’", "'", regex=False)
            .str.replace("_", r"\textunderscore{}", regex=False)
            .str.replace("$", r"\$", regex=False)
            .str.replace("&", r"\&", regex=False)
            .str.replace("%", r"\%", regex=False)
            .str.replace("#", r"\#", regex=False)
            .str.replace(r"[lfthA-Z]\}\?$", r"}\,?", regex=True)
            .str.replace("-.-.-", "---", regex=False)
            .str.replace("-.-", "--", regex=False)
            .str.replace("°", r"\textdegree{}", regex=False)
            .str.replace(r"([A-Z])\?", r"\1\@?", regex=True)
            .str.replace("0.5 ", "½ ", regex=False)
            .str.replace(r"(\d*)\.5 ", r"\1½ ", regex=True)
            .str.replace("½", r"\({}^1{\mskip -5mu⁄\mskip -3mu}_2\)", regex=False)
            .str.replace("oz. ", r"oz.\ ", regex=False)
            .str.replace("St. ", r"St.\ ", regex=False)
            .str.replace("Mr. ", r"Mr.\ ", regex=False)
            .str.replace("Ms. ", r"Ms.\ ", regex=False)
            .str.replace("Dr. ", r"Dr.\ ", regex=False)
            .str.replace("pl. ", r"pl.\ ", regex=False)
            .str.replace("Jr. ", r"Jr.\ ", regex=False)
            .str.replace("Mt. ", r"Mt.\ ", regex=False)
            .str.replace(r"([A-Z]+)\.", r"\1.\@", regex=True)
        )

        df[c] = df[c].map(sms_thread_to_latex)

    topic_remapper = {}

    section_remapper = {**topic_remapper}

    df[SECTION_COL] = df[SECTION_COL].map(section_remapper).fillna(df[SECTION_COL])

    df[TOPIC_COL] = df[TOPIC_COL].map(topic_remapper).fillna(df[TOPIC_COL])

    df[INDEX_COL] = list(range(len(df)))

    regular_df = df[df[SECTION_COL] != "Bonus"].copy()
    bonus_df = df[df[SECTION_COL] == "Bonus"].copy()
    regular_df: pd.DataFrame
    bonus_df: pd.DataFrame

    for df in [regular_df, bonus_df]:
        df[SECTION_ORDER_COL] = df[TOPIC_COL].map(TOPIC_ORDER.index)
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
# Best themes: Montepellier, EastLansing, Antibes, Bergen# CambridgeUS, Hannover
# Best color themes: rose, orchid, lily, dolphin, seahorse
def make_latex(trivia_items: List[TriviaItem], include_images: bool = True) -> str:

    latex_items: List[BeamerFrame] = []

    def append_qs_and_as(trivia_items: List[TriviaItem]):
        answer_frames: List[BeamerFrame] = []

        for trivia_item in trivia_items:
            qf, af = trivia_item.get_q_and_a_frames()

            latex_items.append(qf)
            answer_frames.append(af)

        latex_items.append(r"\subsection{Answers}")

        for af in answer_frames:
            latex_items.append(af)

    preamble = LatexTemplates.PREAMBLE
    if DRAFT:
        _draft_str = ",draft"
    else:
        _draft_str = ""
    preamble = preamble.replace(r"{{DRAFT_}", _draft_str)

    preamble = preamble.replace(r"{{TITLE_}", TITLE)
    preamble = preamble.replace(
        r"{{CATEGORIES_}", "\n".join(f"\\item {topic}" for topic in TOPIC_ORDER)
    )

    latex_items.append(preamble)

    prev_round_name = None
    this_round_items: List[TriviaItem] = []

    for trivia_item in trivia_items:
        round_name = trivia_item.round_name

        if round_name != prev_round_name:
            if prev_round_name is not None:
                append_qs_and_as(this_round_items)

            latex_items.append(
                LatexTemplates.ROUND_SECTION.format(
                    round_name=f"{round_name}", section=trivia_item.section
                )
            )

            prev_round_name = round_name
            this_round_items: List[TriviaItem] = []

        this_round_items.append(trivia_item)

    append_qs_and_as(this_round_items)

    latex_items.append(LatexTemplates.POST_SCRIPT)

    latex_str = "\n".join(map(str.strip, latex_items)).strip()

    if DRAFT:
        latex_str = (
            latex_str.replace(r"\pause{}", "")
            .replace(r"\pause", "")
            .replace(r"\visible<2->", r"\visible<1->")
        )

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
