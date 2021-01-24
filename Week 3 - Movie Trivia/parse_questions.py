# %%
import re

import pandas as pd


def read_qs_into_list():
    with open("./questions.txt") as f:
        lines = f.read().splitlines()

    questions_answers = []

    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^\d+\. +Question: +(.*)$", line)
        if match:
            question = match.group(1)
            i += 1
            while len(lines[i].strip()) == 0:
                i += 1
            answer_line = lines[i]
            answer = re.match(r"^Answer: (.*)$", answer_line).group(1)

            questions_answers.append((question, answer))

        i += 1

    return questions_answers


def save_qs_as_csv():
    qandas = read_qs_into_list()
    df = pd.DataFrame(qandas, columns=["Question", "Answer"])
    df.to_csv("questions.csv", index=False)


save_qs_as_csv()
