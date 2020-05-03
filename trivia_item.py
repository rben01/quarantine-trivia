# %%
import re
from typing import List, Tuple

import pandas as pd

from latex_templates import _ABCTemplateGroup, BeamerFrame, LatexTemplates


class TextDimInfo:
    MAX_CHARS_PER_LINE = 50
    WRAP_WIDTH = 19

    def __init__(self, text: str):
        self.text = text

    def approx_dims(self) -> Tuple[float, float, float, float]:
        text = re.sub(r"\\\w+{{(.*)}}", r"\1", self.text)
        lines = [line.strip() for line in text.splitlines()]

        width = 0
        height = 0
        wrapped_height = 0
        for line in lines:
            line_width = min(len(line), self.MAX_CHARS_PER_LINE)
            width = max(width, line_width)

            line_height = (len(line) - 1) // self.MAX_CHARS_PER_LINE + 1
            height += line_height

            wrapped_line_height = (len(line) - 1) // self.WRAP_WIDTH + 1
            wrapped_height += wrapped_line_height

        return width, height, self.WRAP_WIDTH, wrapped_height


class TriviaItem:
    TEMPLATE_HANDLERS: List[_ABCTemplateGroup] = [
        LatexTemplates.Special.Bonus_NYC,
        LatexTemplates.Special.Bonus_CellinoBarnes,
        LatexTemplates.Generic,
    ]

    def __init__(
        self,
        *,
        q,
        a,
        round_name,
        section,
        topic,
        number,
        q_image_file,
        a_image_file,
        image_loc,
    ):
        self.question = q
        self.answer = a
        self.round_name = round_name
        self.section = section
        self.topic = topic
        self.number = number
        self.q_image_file = None if pd.isna(q_image_file) else q_image_file
        self.a_image_file = None if pd.isna(a_image_file) else a_image_file

        self.image_in_q = not (pd.isna(q_image_file) and pd.isna(image_loc))

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
                f"iq={self.image_in_q}",
            ]
        )
        return f"T({contents})"

    def matches(self, template_type: "_ABCTemplateGroup") -> bool:
        if template_type is LatexTemplates.Special.Bonus_NYC:
            return self.section == "Bonus" and self.topic == "New York City"

        if template_type is LatexTemplates.Special.Bonus_CellinoBarnes:
            return (
                self.section == "Bonus"
                and self.topic == "What are they saying about me?"
            )

        return template_type is LatexTemplates.Generic

    def get_q_and_a_frames(self) -> Tuple[BeamerFrame, BeamerFrame]:
        def get_question() -> BeamerFrame:
            for c in self.TEMPLATE_HANDLERS:
                if self.matches(c):
                    return c.Q.get_frame_for(self)

            raise ValueError

        def get_answer() -> BeamerFrame:
            for c in self.TEMPLATE_HANDLERS:
                if self.matches(c):
                    return c.A.get_frame_for(self)

            raise ValueError

        return (get_question(), get_answer())

    def get_approx_qanda_dims(
        self,
    ) -> Tuple[Tuple[float, float, float, float], Tuple[float, float, float, float]]:
        return tuple(
            TextDimInfo(text).approx_dims() for text in [self.question, self.answer]
        )
