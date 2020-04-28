# %%
import json  # noqa F401
import re  # noqa F401
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from IPython.display import display  # noqa F401

from trivia_item import LatexTemplates, TriviaItem

np.random.seed(126)

TEST = False

N_QUESTIONS_PER_ROUND = 10

Q_COL = "Question"
A_COL = "Answer"
SECTION_COL = "Section"
TOPIC_COL = "Topic"
Q_IMAGE_COL = "Question Image"
A_IMAGE_COL = "Answer Image"
IMAGE_LOC_COL = "Answer image in question"
SECTION_ORDER_COL = "Sort_"
INDEX_COL = "Index_"

LATEX_DIR: Path = Path("docs/LaTeX")
LATEX_DIR.mkdir(exist_ok=True, parents=True)


def get_trivia_items() -> List[TriviaItem]:
    df = pd.read_csv("./week 5 general trivia.csv")
    df = df[df[Q_COL].notna()]

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
            .str.replace(r"[lfthA-Z]\}\?$", r"}\,?", regex=True)
            .str.replace("-.-", "--", regex=False)
            .str.replace("-.-.-", "---", regex=False)
            .str.replace(r"([A-Z])\?", r"\1\@?", regex=True)
            .str.replace(r"oz. ", r"oz.\ ", regex=False)
            .str.replace("0.5 ", "½ ", regex=False)
            .str.replace(r"(\d*)\.5 ", r"\1½ ", regex=True)
            .str.replace("St. ", r"St.\ ", regex=False)
            .str.replace("pl. ", r"pl.\ ", regex=False)
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

    topic_order = [
        "Plants and Animals II",
        "TV",
        "Cocktails",
        "Superheroes",
        "New York",
        "Geography",
        "Logos",
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
                        image_loc=row[IMAGE_LOC_COL],
                    )
                )

                q_num += 1

    return trivia_items


get_trivia_items()
# %%
# Best themes: Montepellier, EastLansing, Antibes, Bergen# CambridgeUS, Hannover
# Best color themes: rose, orchid, lily, dolphin, seahorse
def make_latex(trivia_items: List[TriviaItem], include_images: bool = True) -> str:

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
                template_str = LatexTemplates.QUESTION_SANS_IMAGE
            else:
                template_str = LatexTemplates.QUESTION_WITH_IMAGE
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
                template_str = LatexTemplates.ANSWER_SANS_IMAGE
            elif (
                trivia_item.q_image_file is not None
                and trivia_item.a_image_file is None
            ):
                template_str = LatexTemplates.ANSWER_WITH_QUESTION_WITH_IMAGE
                answer_kwargs["image_file"] = trivia_item.q_image_file
            elif trivia_item.topic == "New York" and trivia_item.section == "Bonus":
                template_str = LatexTemplates.Special.Bonus_NYC.A
                answer_kwargs["image_file"] = trivia_item.a_image_file
            elif (
                trivia_item.q_image_file is None
                and trivia_item.a_image_file is not None
            ):
                (
                    (q_w, q_h, q_w_wr, q_h_wr),
                    (a_w, a_h, a_w_wr, a_h_wr),
                ) = trivia_item.get_approx_qanda_dims()
                if trivia_item.image_in_q:
                    template_str = LatexTemplates.ANSWER_WITH_IMAGE_MOVED_TO_QUESTION
                else:
                    template_str = LatexTemplates.ANSWER_WITH_IMAGE
                    answer_kwargs["image_height"] = 0.58 - 0.04 * (q_h - 1)

                answer_kwargs["image_file"] = trivia_item.a_image_file
            elif (
                trivia_item.q_image_file is not None
                and trivia_item.a_image_file is not None
            ):
                template_str = LatexTemplates.ANSWER_WITH_IMAGE_AND_QUESTION_WITH_IMAGE
                answer_kwargs["q_image_file"] = trivia_item.q_image_file
                answer_kwargs["a_image_file"] = trivia_item.a_image_file
            else:
                raise ValueError(f"Logic error for {trivia_item}")

            latex_items.append(template_str.format(**answer_kwargs))

    latex_items.append(LatexTemplates.PREAMBLE)

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
