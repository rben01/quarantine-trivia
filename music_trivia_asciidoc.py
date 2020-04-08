import pandas as pd

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
