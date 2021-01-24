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

QUESTIONS_CSV_FILE = "week 13 general trivia.csv"
TITLE = "Welcome to Quarantine Trivia XIII -- Holiday Edition!"

Q_COL = "Question"
A_COL = "Answer"
SECTION_COL = "Section"
TOPIC_COL = "Topic"
Q_IMAGE_COL = "Question Image"
A_IMAGE_COL = "Answer Image"
SECTION_ORDER_COL = "Sort_Section_"
TOPIC_ORDER_COL = "Sort_Topic_"
INDEX_COL = "Index_"

LATEX_DIR: Path = Path("docs/LaTeX")
LATEX_DIR.mkdir(exist_ok=True, parents=True)

SECTION_ORDER = [
    "Board Games",
    "Companies That Are No More",
    "Famous Foreign-Language Literary Works",
    "Newspapers and Magazines",
    "One of the things this city is famous for is\\ldots",
    "Winter Sports",
    "Cartoons and the Funny Pages",
    "Specialized Words II",
    "Other Things that Happened in 2020",
    "Movies From Their Stills",
]

if SECTION_ORDER[-1] != "Bonus":
    SECTION_ORDER.append("Bonus")


# %%


def get_trivia_items() -> List[TriviaItem]:
    df = pd.read_csv(QUESTIONS_CSV_FILE)
    df = df[df[Q_COL].notna()]

    for c in [Q_COL, A_COL]:
        # df[c] = df[c].str.replace(r'\emph{(?P=film[^{}]*?)}', r'__\g<film}__')
        df[c] = (
            df[c]
            .str.replace(r'(\S)"', r"\1”", regex=True)
            .str.replace(r'"(\S)', r"“\1", regex=True)
            .str.replace(r'"([^"]*?)"', r"``\1''", regex=True)
            .str.replace("’”", r"’\,”", regex=False)
            .str.replace("”’", r"”\,’", regex=False)
            .str.replace("“", "``", regex=False)
            .str.replace("”", "''", regex=False)
            .str.replace("‘", "`", regex=False)
            .str.replace("’", "'", regex=False)
            .str.replace("_", r"\textunderscore{}", regex=False)
            .str.replace("&", r"\&", regex=False)
            .str.replace("%", r"\%", regex=False)
            .str.replace("#", r"\#", regex=False)
            .str.replace(r"([lfthA-Z])\}\?$", r"\1}\,?", regex=True)
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
            .str.replace("vs. ", r"vs.\ ", regex=False)
            # .str.replace(r"([A-Z]+)\.", r"\1.\@", regex=True)
            .str.replace(
                r"(?!<\\)_+",
                lambda match: " ".join(
                    [r"\textunderscore{}" * 5] * len(match.group(0))
                ),
            )
            .str.replace(r"(\d+)([a-z]{2,})", r"\1\\textsuperscript{\2}")
        )
        if c == A_COL:
            df[c] = (
                df[c]
                .str.replace("/", " / ", regex=False)
                .str.replace(r"\s+/\s+", " / ", regex=True)
            )

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
        df[SECTION_ORDER_COL] = df[SECTION_COL].map(SECTION_ORDER.index)
        df[TOPIC_ORDER_COL] = df[TOPIC_COL].map(SECTION_ORDER.index)

        df.sort_values([SECTION_ORDER_COL, TOPIC_ORDER_COL, INDEX_COL], inplace=True)

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

        n_subsections = (
            1 if section == "Bonus" else (n_qs - 1) // N_QUESTIONS_PER_ROUND + 1
        )
        for i in range(n_subsections):
            start_idx = i * N_QUESTIONS_PER_ROUND
            end_idx = None if section == "Bonus" else start_idx + N_QUESTIONS_PER_ROUND

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
        r"{{CATEGORIES_}",
        "\n".join(
            f"\\item {topic if topic != 'Bonus' else 'Bonus Round'}"
            for topic in SECTION_ORDER
        ),
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
