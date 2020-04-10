# %%
import base64  # noqa F401
import json
import multiprocessing as mp
import re
import subprocess
import uuid
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from IPython.display import display  # noqa F401

SONGS_METADATA_DIR = Path("Song meta")
AUDIO_DIR = Path("Audio")

ORIGINALS_DIR = AUDIO_DIR / "Originals"
TRIMMED_DIR = AUDIO_DIR / "Trimmed"
for d in [ORIGINALS_DIR, TRIMMED_DIR]:
    d.mkdir(exist_ok=True)

TITLE_COL = "title"
ARTIST_COL = "artist"
ALBUM_COL = "album"
SECTION_COL = "section"
AUDIO_FILE_IN_COL = "audio_in"
START_TIME_COL = "start"
END_TIME_COL = "end"
QUESTION_COL = "question"
ANSWER_COL = "answer"
ROW_ID_COL = "row_id"

N_PER_ROUND = 10

Rounds = List[Tuple[str, List["TriviaItem"]]]


class TriviaItem:
    def __init__(self, *, q, a, source, section, number=None, round_name, metadata):
        self.question = q
        self.answer = a
        self.source = source
        self.section = section
        self.number = number
        self.round_name = round_name
        self.metadata = metadata

    def __str__(self):
        return (
            f"Q:{self.question}; A:{self.answer}; R:{self.round_name}; N:{self.number}"
        )

    def __repr__(self):
        return str(self)


def get_audio_out_filepath(in_file) -> Path:
    if pd.isna(in_file):
        return None

    in_file = Path(in_file)
    new_name = re.sub(r"[^A-Za-z0-9.]+", "-", in_file.name)
    return (TRIMMED_DIR / new_name).with_suffix(".mp4")


def consolidate_metadata() -> pd.DataFrame:
    dfs = []
    for f in (
        f for extn in ["csv", "tsv"] for f in SONGS_METADATA_DIR.glob(f"*.{extn}")
    ):
        f: Path
        try:
            if f.suffix == ".csv":
                df = pd.read_csv(f, delimiter=";")
                if len(df.columns) < 3:
                    df = pd.read_csv(f, delimiter=",")
            elif f.suffix == ".tsv":
                df = pd.read_csv(f, delimiter="\t")
            else:
                raise ValueError
        except pd.errors.ParserError:
            print(f)
            raise

        df[ROW_ID_COL] = df.apply(lambda row: uuid.uuid4().hex[:6], axis=1)
        df[SECTION_COL] = f.stem

        dfs.append(df)

    df = pd.concat(dfs, axis=0)
    df = df[[ROW_ID_COL, TITLE_COL, ARTIST_COL, ALBUM_COL, SECTION_COL]]

    df.to_csv("songs_meta_pre.csv", index=False)
    return df


def read_df() -> pd.DataFrame:
    df = pd.read_csv(
        "./Songs_meta_filled_output/Sheet 2-Table 1.csv",
        dtype={
            ROW_ID_COL: str,
            TITLE_COL: str,
            ARTIST_COL: str,
            ALBUM_COL: str,
            SECTION_COL: str,
            START_TIME_COL: float,
            END_TIME_COL: float,
            QUESTION_COL: str,
            ANSWER_COL: str,
        },
    )

    df[SECTION_COL] = df[SECTION_COL].map({"Movie": "Movies"}).fillna(df[SECTION_COL])
    df = df[(df[QUESTION_COL].notna()) & (df[QUESTION_COL] != "")]

    df.to_csv("songs_meta_filled.csv", index=False)
    return df


def trim_audio_one_arg(kwargs_dict):
    kwargs_dict.setdefault("verbose", True)
    # keys must match kwargs of `trim_audio`
    kwargs_dict = {
        "in_file": kwargs_dict[AUDIO_FILE_IN_COL],
        "start": kwargs_dict[START_TIME_COL],
        "end": kwargs_dict[END_TIME_COL],
        "verbose": kwargs_dict["verbose"],
    }
    return trim_audio(**kwargs_dict)


def trim_audio(in_file: str, start: float, end: float, verbose=False):

    if pd.isna(in_file):
        return

    in_file = ORIGINALS_DIR / in_file
    if in_file.suffix not in [".webm", ".m4a", "mp3"]:
        print(in_file)
        raise ValueError

    out_path = get_audio_out_filepath(in_file)

    loudnorm_cmd = [
        "ffmpeg",
        "-i",
        str(in_file),
        "-af",
        # Target loudness values (i=target loudness; lra=loudness range; tp=true peak)
        # These (approximately) show up as "outputs" in the json
        # "Inputs" are fed back into loudnorm in second pass to produce these outputs
        "loudnorm=I=-6:LRA=10:tp=-1:print_format=json",
        "-f",
        "null",
        "-",
    ]
    sed_cmd = ["sed", "-E", "-e", r"1,/^\[Parsed_loudnorm/d"]
    loudnorm_ps = subprocess.Popen(
        loudnorm_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    loudnorm_json_str = subprocess.check_output(
        sed_cmd, stdin=loudnorm_ps.stdout, text=True
    )
    loudnorm_ps.communicate()
    loudnorm_dict = json.loads(loudnorm_json_str)

    ln_input_i = loudnorm_dict["input_i"]
    ln_input_lra = loudnorm_dict["input_lra"]
    ln_input_tp = loudnorm_dict["input_tp"]
    ln_input_thresh = loudnorm_dict["input_thresh"]

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        "question_mark.jpg",
        "-i",
        str(in_file),
        "-ss",
        str(start),
        "-to",
        str(end),
        # "-af",
        # "silenceremove=start_periods=1:start_duration=1:start_threshold=-70dB:detection=peak,aformat=dblp",  # noqa E501
        "-af",
        ":".join(
            [
                "loudnorm=linear=true",
                f"measured_I={ln_input_i}",
                f"measured_LRA={ln_input_lra}",
                f"measured_tp={ln_input_tp}",
                f"measured_thresh={ln_input_thresh}",
            ]
        ),
        # f"loudnorm=linear=true:measured_I={ln_input_i}:measured_LRA={ln_input_lra}:measured_tp={ln_input_tp}:measured_thresh={ln_input_thresh}",  # noqa E501
        # "-vf",
        # "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-acodec",
        "aac",
        "-vcodec",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-tune",
        "stillimage",
        "-movflags",
        "+faststart",
        str(out_path),
    ]

    if verbose:
        print(" ".join(f"'{arg}'" for arg in cmd))

    subprocess.check_call(cmd)
    return in_file


def trim_songs(df: pd.DataFrame):
    # Don't redo needless work - whenever we encode something, save the options used to
    # encode it, and only reencode if the options have changed since last time
    PREV_ARGS_FILE = "previous_ffmpeg.json"
    try:
        with open(PREV_ARGS_FILE) as f:
            saved_args = json.load(f)
    except FileNotFoundError:
        saved_args = {}

    # saved_args looks like {filename: trim_audio_one_arg kwargs_dict}

    args = []
    for _, row in df.iterrows():
        source_file = row[AUDIO_FILE_IN_COL]
        arg = row[[AUDIO_FILE_IN_COL, START_TIME_COL, END_TIME_COL]].to_dict()

        if arg != saved_args.get(source_file):
            args.append(arg)
            saved_args[source_file] = arg

    if not args:
        return

    args = [{**arg, "verbose": True} for arg in args]

    with mp.Pool(4) as pool:
        for i, item in enumerate(pool.imap(trim_audio_one_arg, args, chunksize=5)):
            print(i, "Did", item)

    # Save the list of files and encode args (without verbose) for next time
    # We do this *after* processing so that if we abort early we don't end up writing
    # anything (which would give the appearance that we'd done work we hadn't)
    with open(PREV_ARGS_FILE, "w") as f:
        json.dump(saved_args, f, indent=2)


# consolidate_metadata()
df = read_df()
trim_songs(df)

# %%


def get_trivia_items(df: pd.DataFrame) -> List[TriviaItem]:
    df = df.sample(frac=1, replace=False, random_state=13892)
    sections = df[SECTION_COL].unique()
    trivia_items = []

    round_order = {
        section: index
        for index, section in enumerate(
            ["General", "Movies", "Broadway", "One Hit Wonders", "New York", "Bonus"]
        )
    }

    for section in sections:
        section_df = df[df[SECTION_COL] == section]

        n_qs = len(section_df)

        n_subsections = ((n_qs - 1) // N_PER_ROUND) + 1

        for i in range(n_subsections):
            start_idx = i * N_PER_ROUND
            end_idx = start_idx + N_PER_ROUND
            if n_qs > N_PER_ROUND:
                round_name = f"{section.title()} (Q{start_idx+1}--{end_idx})"
            else:
                round_name = f"{section.title()}"

            for _, row in section_df.iloc[start_idx:end_idx, :].iterrows():
                trivia_items.append(
                    TriviaItem(
                        q=row[QUESTION_COL],
                        a=row[ANSWER_COL],
                        source=get_audio_out_filepath(row[AUDIO_FILE_IN_COL]),
                        section=row[SECTION_COL],
                        round_name=round_name,
                        metadata=row[[TITLE_COL, ARTIST_COL, ALBUM_COL]],
                    )
                )

    trivia_items.sort(key=lambda ti: round_order[ti.section])
    for i, ti in enumerate(trivia_items, start=1):
        ti.number = i

    return trivia_items


get_trivia_items(df)


def make_anchor(trivia_item: TriviaItem) -> str:
    pp_round_name = re.sub(r"[^A-Za-z0-9]+", "-", trivia_item.round_name)
    anchor = f"s-{pp_round_name}-q-{trivia_item.number}"
    anchor = re.sub(r"-+", "-", anchor)
    return anchor


def _get_adjacent_trivia_item_text(
    adj_item: TriviaItem, *, prev: bool, include_round: bool, has_link_after: bool
):

    anchor = make_anchor(adj_item)

    if prev:
        direction_text = "Previous"
    else:
        direction_text = "Next"

    if include_round:
        dest_text = f"round: {adj_item.round_name}"
    else:
        dest_text = f"question: Q{adj_item.number}"

    desc_text = f"{direction_text} {dest_text}"

    if has_link_after:
        line_breaker = " +\n +"
    else:
        line_breaker = ""

    return f"<<{anchor}, {desc_text}>> {line_breaker}"


def get_prev_trivia_item_link_text(ti_index: int, trivia_items: List[TriviaItem]):
    if ti_index == 0:
        return None

    this_item = trivia_items[ti_index]
    adj_item = trivia_items[ti_index - 1]
    include_round = adj_item.round_name != this_item.round_name
    return _get_adjacent_trivia_item_text(
        adj_item, prev=True, include_round=include_round, has_link_after=True,
    )


def get_next_trivia_item_link_text(ti_index: int, trivia_items: List[TriviaItem]):
    if ti_index == len(trivia_items) - 1:
        return None

    this_item = trivia_items[ti_index]
    adj_item = trivia_items[ti_index + 1]
    include_round = adj_item.round_name != this_item.round_name
    return _get_adjacent_trivia_item_text(
        adj_item, prev=False, include_round=include_round, has_link_after=False
    )


def generate_asciidoc(trivia_items: List[TriviaItem]):
    preamble = """
= Music trivia
:nofooter:
:toc2:
:toclevels: 2
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
#footer { visibility:hidden; }
</style>
++++++++++++

== Welcome

[big]#Welcome to Week 2 of quarantine trivia: *music*!#
    """

    doc_parts = []

    def add_line(s, empty_after=0):
        s = str(s)
        doc_parts.append(s)
        for _ in range(empty_after):
            doc_parts.append("")

    add_line(preamble, empty_after=1)
    add_line('[role="fullheight"]')
    add_line(f"<<{make_anchor(trivia_items[0])},Begin>>", empty_after=2)

    last_round_name = None
    round_index = 0
    for ti_index, trivia_item in enumerate(trivia_items):

        round_name = trivia_item.round_name
        if round_name != last_round_name:
            add_line(f"[[s{round_index}]]")
            add_line(f"== {round_name}", empty_after=1)

            last_round_name = round_name
            round_index += 1

        question_id = f"q{ti_index}"

        this_anchor = make_anchor(trivia_item)
        print(this_anchor)

        add_line(f"[[{this_anchor}]]")
        add_line(f"=== Q{trivia_item.number}", empty_after=1)
        add_line(f"[big]#{round_name}: Question {trivia_item.number}#", empty_after=1)
        add_line(f"==== Question", empty_after=1)
        add_line(trivia_item.question, empty_after=1)

        if not pd.isna(trivia_item.source):
            _should_embed = False
            if _should_embed:
                with open(trivia_item.source, "rb") as f:
                    b64_enc_vid = base64.b64encode(f.read()).decode("ascii")
                src = f"data:video/mp4;base64,{b64_enc_vid}"
            else:
                src = trivia_item.source

            media_block = f"""

[pass]
+++++++++++
<video
loading="lazy"
controls
width="300
poster="question_mark.jpg"
preload="auto"
playsinline
>
<source src={src} type="video/mp4" />
</video>
+++++++++++
"""
            # media_block = f"video::{src}[width=300]"

        else:
            media_block = f"Media goes here"

        add_line(media_block, empty_after=1)

        add_line(f"==== Answer", empty_after=1)
        add_line(
            f"""
[pass]
+++++++++++++++++
<button id="button_{question_id}" onclick="toggle_hidden_{question_id}()">
Show answer
</button>
+++++++++++++++++""",
            empty_after=1,
        )
        add_line(f"[[answer_{question_id}]]")
        add_line(f"{trivia_item.answer} +")
        add_line(" / ".join(trivia_item.metadata), empty_after=1)
        add_line(
            f"""
[pass]
+++++++++++++++
<script>
var z = document.getElementById("answer_{question_id}");
z.style.display = "none"
function toggle_hidden_{question_id}() {{
var x = document.getElementById("answer_{question_id}");
var b = document.getElementById("button_{question_id}");
if (x.style.display === "none") {{
x.style.display = "block";
b.innerHTML = "Hide answer";
}} else {{
x.style.display = "none";
b.innerHTML = "Show answer";
}}
}}
</script>
+++++++++++++++""",
            empty_after=1,
        )

        if (
            ti_index < len(trivia_items) - 1
            and trivia_item.round_name != trivia_items[ti_index + 1].round_name
        ):
            add_line("[big]*End of round*", empty_after=1)

        add_line('[role="fullheight"]')
        prev_link_text = get_prev_trivia_item_link_text(ti_index, trivia_items)
        if prev_link_text is not None:
            add_line(prev_link_text)

        if ti_index < len(trivia_items) - 1:
            # Add next/prev buttons
            next_link_text = get_next_trivia_item_link_text(ti_index, trivia_items)

            if next_link_text is not None:
                add_line(next_link_text)
        else:
            add_line("<<thanks_for_playing, Conclusion>>")

        add_line("")

    add_line("[[thanks_for_playing]]")
    add_line("[float]")
    add_line("= Thanks for playing!", empty_after=1)
    add_line('[role="fullheight"]')
    add_line("[big]#See you soon!#")

    return "\n".join(doc_parts)


def write_asciidoc(df=None):
    if df is None:
        df = consolidate_metadata(trim=True)

    trivia_items = get_trivia_items(df)
    with open("trivia.asciidoc", "w") as f:
        f.write(generate_asciidoc(trivia_items))

    return subprocess.check_output(
        ["asciidoc", "-b", "html5", "trivia.asciidoc"],
        stderr=subprocess.STDOUT,
        text=True,
    )


write_asciidoc(df)


# %%
