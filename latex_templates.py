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
    NUMBER = None


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
\vspace{{-0.5em}}
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
\vspace{{-0.5em}}
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
\vspace{{-0.5em}}
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
\vspace{{-0.5em}}
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
\vspace{{-0.5em}}
\begin{{columns}}[T,totalwidth=\linewidth]
\begin{{column}}{{0.38\linewidth}}
\begin{{block}}{{Question}}
{question}
\end{{block}}
\end{{column}}
\begin{{column}}{{0.6\linewidth}}
\begin{{center}}
\includegraphics[max width=0.95\textwidth,max height=0.35\textheight]{{{q_image_file}}}
\end{{center}}
\end{{column}}
\end{{columns}}

\visible<2->{{
    \begin{{columns}}[T,totalwidth=\linewidth]
    \begin{{column}}{{0.38\linewidth}}
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
    \end{{column}}
    \begin{{column}}{{0.6\linewidth}}
    \begin{{center}}
    \includegraphics[max width=0.95\textwidth,
        max height=0.34\textheight]{{{a_image_file}}}
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
\vspace{{-0.5em}}
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
\vspace{{-0.5em}}
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
\usepackage{xcolor}
\usepackage{ifthen}
\usepackage{fontspec}
\usepackage{textcomp}
%\usepackage[T5,T1]{fontenc}
\usepackage{caption}

\usepackage{verse}
\newcommand{\attrib}[1]{%
\nopagebreak{\raggedleft\footnotesize #1\par}}
\renewcommand{\poemtitlefont}{\normalfont\large\itshape\centering}

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

\AtBeginSection[]{
  \begin{frame}
    \vfill
    \centering
    \begin{beamercolorbox}[sep=8pt,center,shadow=true,rounded=true]{title}
    \usebeamerfont{title}\insertsectionhead\par%
    \ifthenelse{\equal{\thisSectionName}{Bonus}}{}{
        \usebeamerfont{subtitle}\thisSectionName\par%
    }
    \end{beamercolorbox}
    \begin{center}
    \ifthenelse{\equal{\thisSectionName}{Colleges and Universities}}{
        \includegraphics[max height = 0.3\textheight]{Images/belushicollege.jpg}
    }{}

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

\title{{{TITLE_}}
\date{}

\begin{frame}
\titlepage{}
\begin{center}
\includegraphics[max width=0.9\textwidth,
    max height=0.4\textheight]{Images/triviatitleframelogo.png}
\end{center}
\end{frame}

\begingroup{}
\begin{frame}{}
Since this is Game 10, we'd like to look back over a few of the more ``interesting''
questions from the last nine games.
\end{frame}
\begin{frame}{}
First, we failed to distinguish between beignets and zeppole.

\begin{figure}
\captionsetup{labelformat=empty}
\centering
\begin{minipage}{.5\textwidth}
  \centering
  \includegraphics[height=.4\textheight]{Images/beignets.jpg}
  \captionof{figure}{Beignets (maybe?)}
\end{minipage}%
\begin{minipage}{.5\textwidth}
  \centering
  \includegraphics[height=.4\textheight]{Images/zeppole.jpg}
  \captionof{figure}{Zeppole (could be?)}
\end{minipage}
\end{figure}
\end{frame}
\begin{frame}{}
\medskip{}
Then, we introduced you to the poetry of Emily Dickson:
\pause{}
\vspace*{0.5in}
\settowidth{\versewidth}{Because I could not stop for meth}
\begin{verse}[\versewidth]
Because I could not stop for meth --- \\
I had it delivered --- \ldots{}
\end{verse}
\attrib{Emily Dickson}
\end{frame}
\begin{frame}{}
\medskip{}
We took a political stance on the meaning of the word ``Ireland''.
\begin{center}
\includegraphics[max width=0.9\textwidth,max height=0.5\textheight
]{Images/ireland.png}
\end{center}
\end{frame}
\begin{frame}{}
\medskip{}
And finally, we displayed cuneiform backwards, which we know confused everyone.
\end{frame}
\begin{frame}
So for all of these mistakes, we wish to say \ldots{}
\pause{}
\begin{center}
\includegraphics[max width=0.9\textwidth,max height=0.5\textheight
    ]{Images/cuneiform.png}
\end{center}

\end{frame}
\endgroup{}

\begin{frame}{}
\medskip{}
So now let's see what's in store for this week \ldots{}
\end{frame}


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
        class Ships_4(_GenericTemplateGroup, _MatchableQuestionSlide):
            SECTION = "Famous Ships and Boats"
            NUMBER = 6

            class A(_GenericTemplateGroup.Special_A):
                TEMPLATE = LatexTemplate(
                    r"""
\begin{{frame}}[t]{{{question_title}}}
\vspace{{-0.5em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}

\visible<2->{{
    \begin{{columns}}[T,totalwidth=\linewidth]
    \begin{{column}}{{0.65\linewidth}}
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
    \end{{column}}
    \begin{{column}}{{0.3\linewidth}}
    \begin{{center}}
    \includegraphics[max width=0.95\textwidth,
        max height={image_height:.5f}\textheight]{{{a_image_file}}}
    \end{{center}}
    \end{{column}}
    \end{{columns}}
}}
\end{{frame}}                """
                )

        class Colonial_9(_GenericTemplateGroup, _MatchableQuestionSlide):
            SECTION = "Colonial America"
            NUMBER = 9

            class A(_GenericTemplateGroup.Special_A):
                TEMPLATE = LatexTemplate(
                    r"""
\begin{{frame}}[t]{{{question_title}}}
\vspace{{-0.5em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}

\visible<2->{{
    \begin{{columns}}[T,totalwidth=\linewidth]
    \begin{{column}}{{0.65\linewidth}}
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
    \end{{column}}
    \begin{{column}}{{0.3\linewidth}}
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

        class Wonders_10(_GenericTemplateGroup, _MatchableQuestionSlide):
            SECTION = "Wonders of Engineering"
            NUMBER = 10

            class A(_GenericTemplateGroup.Special_A):
                TEMPLATE = LatexTemplate(
                    r"""
\begin{{frame}}[t]{{{question_title}}}
\vspace{{-0.5em}}
\begin{{block}}{{Question}}
{question}
\end{{block}}

\visible<2->{{
    \begin{{columns}}[T,totalwidth=\linewidth]
    \begin{{column}}{{0.65\linewidth}}
    \begin{{block}}{{Answer{maybe_s}}}
    {answer}
    \end{{block}}
    \end{{column}}
    \begin{{column}}{{0.3\linewidth}}
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
