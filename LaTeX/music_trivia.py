# %%
import subprocess
from pathlib import Path

import pandas as pd

songs_metadata_dir = Path("Song meta")
music_dir = Path("Audio/Trimmed")


def get_data() -> pd.DataFrame:
    dfs = []
    for csv in songs_metadata_dir.glob("*.csv"):
        df = pd.read_csv(csv, delimiter=";")
        df["section"] = csv.stem
        df["file"] = csv.stem
        dfs.append(df)
    return pd.concat(dfs, axis=0)


# :sectlinks:


def generate_asciidoc(df):
    preamble = """
= Music trivia
:toc2:
:toclevels: 5
:toc-title: Welcome to Quarantine Music Trivia!

[subs=""]
++++++++++++
<style>
html, body { height: 100%; }
.fullheight { overflow-y:auto; height:100vh; }​
a { color:blue; }
a:visited { color:blue; }
a:active { color:blue; }
a[tabindex]:focus { color:blue; outline:none; }
</style>
++++++++++++

== Welcome
    """

    doc_parts = []

    def add_line(s, empty_after=0):
        doc_parts.append(s)
        for _ in range(empty_after):
            doc_parts.append("")

    add_line(preamble, empty_after=1)

    sections = df["section"].unique()

    i = 0
    for section_idx, section in enumerate(sections):
        section_idx += 1
        add_line(f"[[s{section_idx}]]")
        add_line(f"== Section {section}", empty_after=1)

        this_section_df = df[df["section"] == section]
        this_section_df: pd.DataFrame
        for q_idx, q in enumerate(this_section_df.iterrows()):
            i += 1
            q_idx += 1
            if q_idx % 10 == 1:
                add_line(f"=== Questions {q_idx}-{q_idx+9}", empty_after=1)

            question_id = f"{section_idx}_{q_idx}"
            song_info = q[1]
            # Question section
            add_line(f"[[s{section_idx}q{q_idx}]]")
            add_line(f"==== Question {i}", empty_after=1)
            add_line(f"===== Question", empty_after=1)
            add_line(f"audio::{song_info['file']}[Song]", empty_after=1)
            add_line(f"===== Answer", empty_after=1)
            add_line(
                f"""
[subs=""]
+++++++++++++++++
<button onclick="toggle_hidden_{question_id}()">Toggle answer</button>
+++++++++++++++++""",
                empty_after=1,
            )
            add_line(f"[[answer_{question_id}]]")
            add_line(song_info["title"], empty_after=1)
            add_line(
                f"""
[subs=""]
+++++++++++++++
<script>
var z = document.getElementById("answer_{question_id}");
z.style.display = "none"
function toggle_hidden_{question_id}() {{
  var x = document.getElementById("answer_{question_id}");
  if (x.style.display === "none") {{
    x.style.display = "block";
  }} else {{
    x.style.display = "none";
  }}
}}
</script>
+++++++++++++++""",
                empty_after=1,
            )
            add_line(f'[role="fullheight"]')
            if section_idx == 1 and q_idx == 1:
                add_line(f"<<s{section_idx}q{q_idx+1}, next q>>")
            elif section_idx == len(sections) and q_idx == len(this_section_df):
                add_line(f"<<s{section_idx}q{q_idx-1}, prev q>>")
            else:
                add_line(
                    f"<<s{section_idx}q{q_idx-1}, prev q>>"
                    f" <<s{section_idx}q{q_idx+1}, next q>>"
                )

            add_line("")

    return "\n".join(doc_parts)


class TriviaItem:
    def __init__(self, question, answer, file_path):
        self.question = question
        self.answer = answer
        self.file_path = file_path


def generate_latex(rounds):
    preamble = r"""
\documentclass[11pt]{beamer}
\usepackage{graphicx}
\usepackage{media9}

\usetheme[hideothersubsections]{Hannover}
\usecolortheme{dolphin}
\setbeamercovered{invisible}
\setbeamertemplate{navigation symbols}{\insertslidenavigationsymbol}
\setbeamertemplate{page number in head/foot}{}
\setbeamertemplate{blocks}[rounded][shadow=false]
% \setbeamerfont{section in sidebar}{size=\fontsize{4}{3}\selectfont}
% \setbeamerfont{subsection in sidebar}{size=\fontsize{4}{3}\selectfont}
% \setbeamerfont{subsubsection in sidebar}{size=\fontsize{4}{2}\selectfont}

\AtBeginSection[]{}
\AtBeginSection[]{
  \begin{frame}
    \vfill
    \centering
    \begin{beamercolorbox}[sep=8pt,center,shadow=true,rounded=true]{title}
    \usebeamerfont{title}\insertsectionhead\par%
    \end{beamercolorbox}
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

\title{Welcome to Quarantine Trivia!}
\date{}

\begin{frame}
  \titlepage{}
\end{frame}

    """

    latex_items = []

    def add_line(line):
        latex_items.append(line)

    add_line(preamble)

    song_type_section_template_str = r"""
\section{{{song_type_section}}}
    """

    subsection_template_str = r"""
\subsection{{{subsection_name}}}
"""

    question_template_str = r"""
\subsubsection*{{Q{question_number}}}
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


def create_doc():
    df = get_data()
    text = generate_asciidoc(df)
    with open("trivia_.asciidoc", "w") as f:
        f.write(text)

    subprocess.run(["asciidoc", "-b", "html5", "trivia_.asciidoc"])


create_doc()
