from __future__ import annotations
from typing import TYPE_CHECKING

from typing import Mapping, NewType

if TYPE_CHECKING:
    from trivia_item import TriviaItem

LatexTemplate = NewType("LatexTemplate", str)
BeamerFrame = NewType("BeamerFrame", str)


class ABCTemplateGroup:
    class _ABCTemplateSubgroup:
        @classmethod
        def get_common_kwargs(cls, ti: "TriviaItem") -> Mapping:
            raise NotImplementedError

        @classmethod
        def get_frame_for(cls, ti: "TriviaItem") -> BeamerFrame:
            raise NotImplementedError

    class Q(_ABCTemplateSubgroup):
        @classmethod
        def get_common_kwargs(cls, ti: TriviaItem) -> Mapping:
            kwargs = {
                "question": ti.question,
                "question_number": ti.number,
                "q_image_file": ti.q_image_file,
                "a_image_file": ti.a_image_file,
            }

            if ti.section == "Bonus":
                kwargs["question_title"] = f"{ti.round_name}: {ti.topic}"
            else:
                kwargs["question_title"] = f"{ti.topic}, Question {ti.number}"

            return kwargs

        @classmethod
        def get_frame_for(cls, ti: TriviaItem) -> BeamerFrame:
            kwargs = cls.get_common_kwargs(ti)

            if ti.q_image_file is None:
                template_str = cls.QUESTION_SANS_IMAGE
            else:
                template_str = cls.QUESTION_WITH_IMAGE

            return template_str.format(**kwargs)

        QUESTION_SANS_IMAGE = LatexTemplate(
            r"""
\subsection*{{Q{question_number}}}
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{frame}}
            """
        )

        QUESTION_WITH_IMAGE = LatexTemplate(
            r"""
\subsection*{{Q{question_number}}}
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.32\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.65\linewidth}}
\begin{{center}}
\includegraphics[max width=0.95\textwidth,max height=0.7\textheight]{{{q_image_file}}}
\end{{center}}
\end{{column}}
\end{{columns}}
\end{{frame}}
            """
        )

    class A(_ABCTemplateSubgroup):
        @classmethod
        def get_common_kwargs(cls, ti: TriviaItem) -> Mapping:
            kwargs = {
                "question": ti.question,
                "answer": ti.answer,
                "q_image_file": ti.q_image_file,
                "a_image_file": ti.a_image_file,
            }

            if ti.section == "Bonus":
                kwargs["question_title"] = f"{ti.round_name}: {ti.topic}"
            else:
                kwargs["question_title"] = f"{ti.topic}, Answer {ti.number}"

            if r"\begin{enumerate}" in ti.answer:
                kwargs["maybe_s"] = "s"
            else:
                kwargs["maybe_s"] = ""

            return kwargs

        @classmethod
        def get_frame_for(cls, ti: TriviaItem) -> BeamerFrame:
            kwargs = cls.get_common_kwargs(ti)

            template_str: LatexTemplate
            if ti.q_image_file is None and ti.a_image_file is None:
                template_str = cls.ANSWER_SANS_IMAGE
            elif ti.q_image_file is not None and ti.a_image_file is None:
                template_str = cls.ANSWER_WITH_QUESTION_WITH_IMAGE
            elif ti.q_image_file is None and ti.a_image_file is not None:
                if ti.image_in_q:
                    template_str = cls.ANSWER_WITH_IMAGE_MOVED_TO_QUESTION
                else:
                    (
                        (q_w, q_h, q_w_wr, q_h_wr),
                        (a_w, a_h, a_w_wr, a_h_wr),
                    ) = ti.get_approx_qanda_dims()
                    template_str = cls.ANSWER_WITH_IMAGE
                    kwargs["image_height"] = 0.58 - 0.04 * (q_h - 1)

            elif ti.q_image_file is not None and ti.a_image_file is not None:
                template_str = cls.ANSWER_WITH_IMAGE_AND_QUESTION_WITH_IMAGE
            else:
                raise ValueError(f"Logic error for {ti}")

            return template_str.format(**kwargs)

        ANSWER_SANS_IMAGE = LatexTemplate(
            r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
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
        )

        ANSWER_WITH_QUESTION_WITH_IMAGE = LatexTemplate(
            r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.32\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\visible<2->{{
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
}}
\end{{column}}
\begin{{column}}{{0.65\linewidth}}
\begin{{center}}
\includegraphics[max width=0.95\textwidth,max height=0.7\textheight]{{{q_image_file}}}
\end{{center}}
\end{{column}}
\end{{columns}}
\end{{frame}}
                """
        )

        ANSWER_WITH_IMAGE_AND_QUESTION_WITH_IMAGE = LatexTemplate(
            r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.32\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.65\linewidth}}
\begin{{center}}
\includegraphics[max width=0.95\textwidth,max height=0.35\textheight]{{{q_image_file}}}
\end{{center}}
\end{{column}}
\end{{columns}}

\visible<2->{{
    \begin{{columns}}[T,totalwidth=\linewidth]
    \begin{{column}}{{0.32\linewidth}}
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
    \end{{column}}
    \begin{{column}}{{0.65\linewidth}}
    \begin{{center}}
    \includegraphics[max width=0.95\textwidth,
        max height=0.38\textheight]{{{a_image_file}}}
    \end{{center}}
    \end{{column}}
    \end{{columns}}
}}
\end{{frame}}
                """
        )

        ANSWER_WITH_IMAGE_MOVED_TO_QUESTION = LatexTemplate(
            r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.32\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\visible<2->{{
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
}}
\end{{column}}
\begin{{column}}{{0.65\linewidth}}
\visible<2->{{
    \begin{{center}}
    \includegraphics[max width=0.9\textwidth,
        max height=0.7\textheight]{{{a_image_file}}}
    \end{{center}}
}}
\end{{column}}
\end{{columns}}
\end{{frame}}
                """
        )

        ANSWER_WITH_IMAGE = LatexTemplate(
            r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}

\visible<2->{{
    \begin{{columns}}[T,totalwidth=\linewidth]
    \begin{{column}}{{0.32\linewidth}}
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
    \end{{column}}
    \begin{{column}}{{0.65\linewidth}}
    \begin{{center}}
    \includegraphics[max width=0.95\textwidth,
        max height={image_height:.5f}\textheight]{{{a_image_file}}}
    \end{{center}}
    \end{{column}}
    \end{{columns}}
}}
\end{{frame}}
                """
        )


class LatexTemplates:

    PREAMBLE = BeamerFrame(
        r"""
\documentclass[11pt,draft]{beamer}
\usepackage{graphicx}
\usepackage[export]{adjustbox}
\usepackage{ifthen}
\usepackage{xeCJK}
\usepackage[T1]{fontenc}
\usepackage{xfrac}

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
    \begin{center}
    Please mute yourselves!
    \end{center}

    \ifthenelse{\equal{\secname}{Bonus Rakjshdound} \AND{\equal{\subsecname}{Answers}}}{
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
    \ifthenelse{\equal{\subsecname}{Answers}} {
        \begin{center}
        Unmute yourselves!
        \end{center}
    }
    \vfill
  \end{frame}
}
\begin{document}

\title{Welcome to Quarantine General Trivia II!\vspace{-0.5in}}
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
    )

    POST_SCRIPT = BeamerFrame(
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

    ROUND_SECTION = LatexTemplate(
        r"""
\def\thisSectionName{{{section}}}
\section{{{round_name}}}
        """
    )

    class Generic(ABCTemplateGroup):
        pass

    class Special:
        class Bonus_NYC(ABCTemplateGroup):
            class A(ABCTemplateGroup.A):
                @classmethod
                def get_frame_for(cls, ti: TriviaItem) -> BeamerFrame:
                    kwargs = cls.get_common_kwargs(ti)

                    return cls.TEMPLATE.format(**kwargs)

                TEMPLATE = LatexTemplate(
                    r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}

\visible<2->{{
    \begin{{columns}}[T,totalwidth=\linewidth]
    \begin{{column}}{{0.5\linewidth}}
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
    \end{{column}}
    \begin{{column}}{{0.45\linewidth}}
    \begin{{center}}
    \includegraphics[max width=0.95\textwidth,
        max height=0.7\textheight]{{{a_image_file}}}
    \end{{center}}
    \end{{column}}
    \end{{columns}}
}}
\end{{frame}}
                    """
                )

        class Bonus_Logos(ABCTemplateGroup):
            class Q(ABCTemplateGroup.Q):
                @classmethod
                def get_frame_for(cls, ti: TriviaItem) -> BeamerFrame:
                    kwargs = cls.get_common_kwargs(ti)

                    return cls.TEMPLATE.format(**kwargs)

                TEMPLATE = LatexTemplate(
                    r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.47\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.47\linewidth}}
\includegraphics[max width=0.95\textwidth,
        max height=0.35\textheight]{{{q_image_file}}}
\end{{column}}
\end{{columns}}
\end{{frame}}
                    """
                )

            class A(ABCTemplateGroup.A):
                @classmethod
                def get_frame_for(cls, ti: TriviaItem) -> BeamerFrame:
                    kwargs = cls.get_common_kwargs(ti)

                    return cls.TEMPLATE.format(**kwargs)

                TEMPLATE = LatexTemplate(
                    r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.47\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.47\linewidth}}
\includegraphics[max width=0.95\textwidth,
        max height=0.35\textheight]{{{q_image_file}}}
\end{{column}}
\end{{columns}}
\vspace{{1em}}
\pause{{}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.47\linewidth}}
\begin{{block}}{{Answer}}
{answer}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.47\linewidth}}
\includegraphics[max width=0.95\textwidth,
        max height=0.35\textheight]{{{a_image_file}}}
\end{{column}}
\end{{columns}}
\end{{frame}}
                    """
                )

        class Bonus_CellinoBarnes(ABCTemplateGroup):
            class A(ABCTemplateGroup.A):
                @classmethod
                def get_frame_for(cls, ti: TriviaItem) -> BeamerFrame:
                    kwargs = cls.get_common_kwargs(ti)

                    return cls.TEMPLATE.format(**kwargs)

                TEMPLATE = LatexTemplate(
                    r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.47\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.47\linewidth}}
\includegraphics[max width=0.95\textwidth,
        max height=0.35\textheight]{{{q_image_file}}}
\end{{column}}
\end{{columns}}
\vspace{{1em}}
\pause{{}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.47\linewidth}}
\begin{{block}}{{Answer}}
{answer}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.47\linewidth}}
\includegraphics[max width=0.95\textwidth,
        max height=0.4\textheight]{{{a_image_file}}}
\end{{column}}
\end{{columns}}
\end{{frame}}
                """
                )
