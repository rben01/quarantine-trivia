from __future__ import annotations
from typing import TYPE_CHECKING

from typing import Mapping, NewType

if TYPE_CHECKING:
    from trivia_item import TriviaItem

LatexTemplate = NewType("LatexTemplate", str)
BeamerFrame = NewType("BeamerFrame", str)


class _MatchableQuestionSlide:
    SECTION = None
    TOPIC = None


class _GenericTemplateGroup:
    class __ABCTemplateSubgroup:
        @classmethod
        def template_for(cls, ti: TriviaItem) -> LatexTemplate:
            raise NotImplementedError

        @classmethod
        def kwargs_for(cls, ti: "TriviaItem") -> Mapping:
            raise NotImplementedError

        @classmethod
        def get_frame_for(cls, ti: "TriviaItem") -> BeamerFrame:
            return cls.template_for(ti).format(**cls.kwargs_for(ti))

    class Q(__ABCTemplateSubgroup):
        @classmethod
        def template_for(cls, ti: TriviaItem) -> LatexTemplate:
            if ti.q_image_file is None:
                return cls.QUESTION_SANS_IMAGE
            else:
                return cls.QUESTION_WITH_IMAGE

        @classmethod
        def kwargs_for(cls, ti: TriviaItem) -> Mapping:
            kwargs = {
                "question": ti.question,
                "question_number": ti.number,
                "q_image_file": ti.q_image_file,
                "a_image_file": ti.a_image_file,
            }

            if ti.section == "Bonus":
                kwargs["question_title"] = f"{ti.round_name} --- {ti.topic}"
            else:
                kwargs[
                    "question_title"
                ] = f"{ti.round_name} --- {ti.topic} --- \\mbox{{Question {ti.number}}}"

            return kwargs

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

    class A(__ABCTemplateSubgroup):
        @classmethod
        def template_for(cls, ti: TriviaItem) -> LatexTemplate:
            if ti.q_image_file is None and ti.a_image_file is None:
                return cls.ANSWER_SANS_IMAGE
            elif ti.q_image_file is not None and ti.a_image_file is None:
                return cls.ANSWER_WITH_QUESTION_WITH_IMAGE
            elif ti.q_image_file is None and ti.a_image_file is not None:
                return cls.ANSWER_WITH_IMAGE
            elif ti.q_image_file is not None and ti.a_image_file is not None:
                return cls.ANSWER_WITH_IMAGE_AND_QUESTION_WITH_IMAGE
            else:
                raise ValueError(f"Logic error for {ti}")

        @classmethod
        def kwargs_for(cls, ti: TriviaItem) -> Mapping:
            kwargs = {
                "question": ti.question,
                "answer": ti.answer,
                "q_image_file": ti.q_image_file,
                "a_image_file": ti.a_image_file,
            }

            if ti.section == "Bonus":
                kwargs["question_title"] = f"{ti.round_name} --- {ti.topic}"
            else:
                kwargs[
                    "question_title"
                ] = f"{ti.round_name} --- {ti.topic} --- \\mbox{{Answer {ti.number}}}"

            if r"\begin{enumerate}" in ti.answer:
                kwargs["maybe_s"] = "s"
            else:
                kwargs["maybe_s"] = ""

            if ti.q_image_file is None and ti.a_image_file is not None:
                (
                    (q_w, q_h, q_w_wr, q_h_wr),
                    (a_w, a_h, a_w_wr, a_h_wr),
                ) = ti.get_approx_qanda_dims()
                kwargs["image_height"] = 0.58 - 0.04 * (q_h - 1)

            return kwargs

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

    class Special_Q(Q):
        @classmethod
        def template_for(cls, ti: TriviaItem) -> LatexTemplate:
            try:
                return cls.TEMPLATE
            except AttributeError:
                raise NotImplementedError(f"type {cls} has no default template")

    class Special_A(A):
        @classmethod
        def template_for(cls, ti: TriviaItem) -> LatexTemplate:
            try:
                return cls.TEMPLATE
            except AttributeError:
                raise NotImplementedError(f"type {cls} has no default template")


class LatexTemplates:

    PREAMBLE = BeamerFrame(
        r"""
\documentclass[11pt{{DRAFT_}]{beamer}
\usepackage{graphicx}
\usepackage[export]{adjustbox}  % max width/height in includegraphics
\usepackage[framemethod=TikZ]{mdframed}
\usepackage[document]{ragged2e}
\usepackage{xcolor}
\usepackage{ifthen}
\usepackage{fontspec}
\usepackage{textcomp}
% \usepackage[T1]{fontenc}
\usepackage{caption}


\usetheme[hideothersubsections]{Goettingen}
\usecolortheme{seahorse}
%%% \usetheme{Montpellier}
%%% \usecolortheme{dolphin}
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
\usepackage{tgheros}
\usefonttheme{serif}
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
    \ifthenelse{\equal{\thisSectionName}{Bonus}}{}{
        \usebeamerfont{subtitle}\thisSectionName\par%
    }
    \ifthenelse{\equal{\thisSectionName}{France}}{
        \vspace{0.5em}
        \usebeamerfont{subtitle}
        {\small
        \begin{flushleft}
        ``When good Americans die, they go to Paris.''
        ---Oscar Wilde
        \end{flushleft}
        }
        \vspace{-1em}
    }{}
    \end{beamercolorbox}
    \begin{center}
    Please mute yourselves!
    \end{center}

    \ifthenelse{\equal{\thisSectionName}{Bonus}}
    {
        Get ready for some \emph{devilishly} hard questions!
        \vspace*{1em}
        \includegraphics[max width=0.5\textwidth,
            max height=0.4\textheight]{Images/devil.jpg}
    }{}

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

\title{{{TITLE_}\vspace{-0.5in}}
\date{}

\begin{frame}
\titlepage{}
\begin{center}
\includegraphics[max width=0.9\textwidth,
    max height=0.4\textheight]{Images/triviatitleframelogo.png}
\end{center}
\end{frame}

\begingroup{}
\begin{frame}[t]{}
Out of the 660 questions that we have posed so far, only three answers have been
 challenged. Nonetheless, we want to make sure that everyone who has a challenge has an
 opportunity to be heard, so we have retained a \mbox{Challenge Coordinator}.

\pause{}
\begin{center}
\begin{figure}[h]
\caption*{OUR CHALLENGE COORDINATOR}
\includegraphics[max width=0.9\textwidth,
     max height=0.35\textheight]{Images/challengecoordinator.jpg}
\end{figure}
\end{center}
Please feel free to contact the Coordinator with any challenges.
For fastest resolution of your challenge, be sure to provide him with your home address.
\end{frame}
\endgroup{}

\begingroup{}
\begin{frame}[t]{Categories}
This week, you'll be answering questions in the following categories:
\begin{enumerate}
{{CATEGORIES_}
\end{enumerate}
\end{frame}
\endgroup{}

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

    class Generic(_GenericTemplateGroup):
        pass

    class Special:
        class Bonus_WordOrigins(_GenericTemplateGroup, _MatchableQuestionSlide):
            SECTION = "Bonus"
            TOPIC = "Word Origins"

            class A(_GenericTemplateGroup.Special_A):
                TEMPLATE = LatexTemplate(
                    r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\pause{{}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.73\linewidth}}
\begin{{block}}{{Answer}}
{answer}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.23\linewidth}}
\includegraphics[max width=0.95\textwidth,
        max height=0.4\textheight]{{{a_image_file}}}
\end{{column}}
\end{{columns}}
\end{{frame}}
                """
                )

        class Bonus_Disney(_GenericTemplateGroup, _MatchableQuestionSlide):
            SECTION = "Bonus"
            TOPIC = "Disney"

            class A(_GenericTemplateGroup.Special_A):
                TEMPLATE = LatexTemplate(
                    r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.65\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.35\linewidth}}
\begin{{center}}
\includegraphics[max width=0.95\textwidth,max height=0.35\textheight]{{{q_image_file}}}
\end{{center}}
\end{{column}}
\end{{columns}}

\visible<2->{{
    \begin{{columns}}[T,totalwidth=\linewidth]
    \begin{{column}}{{0.65\linewidth}}
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
    \end{{column}}
    \begin{{column}}{{0.35\linewidth}}
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

        class Bonus_California(_GenericTemplateGroup, _MatchableQuestionSlide):
            SECTION = "Bonus"
            TOPIC = "California"

            class Q(_GenericTemplateGroup.Special_Q):
                TEMPLATE = LatexTemplate(
                    r"""
\subsection*{{Q{question_number}}}
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.7\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.25\linewidth}}
\begin{{center}}
\includegraphics[max width=0.95\textwidth,max height=0.7\textheight]{{{q_image_file}}}
\end{{center}}
\end{{column}}
\end{{columns}}
\end{{frame}}
            """
                )

            class A(_GenericTemplateGroup.Special_A):
                TEMPLATE = LatexTemplate(
                    r"""
\begin{{frame}}[t]{{{question_title}}}
% \vspace{{0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.7\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.25\linewidth}}
\begin{{center}}
\includegraphics[max width=0.95\textwidth,max height=0.7\textheight]{{{q_image_file}}}
\end{{center}}
\end{{column}}
\end{{columns}}
\visible<2->{{
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
}}
\end{{frame}}
                """
                )