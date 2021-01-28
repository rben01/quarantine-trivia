import re
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup, Tag


def fill_toc(path: Path):
    path = Path(path)
    soup = BeautifulSoup(path.read_text(), "html5lib")
    toc: Tag = soup.find(id="toc")
    dummy: Tag = toc.find(id="dummy2")
    tag: Tag
    for tag in dummy.parents:
        if tag.parent.parent == toc:
            tag.decompose()
            break

    toc_ul = toc.find("ul", {"class": "sectlevel1"})
    section_selector = (
        "#trivia-item-list .hdlist1 > span, #trivia-item-list .hdlist1 > a"
    )
    section_tags: List[Tag] = soup.select(section_selector)
    for tag in section_tags:
        tag_id = tag["id"]
        title = tag.a.decode_contents()
        # new_tag = BeautifulSoup(new_tag_html, "html.parser")
        li: Tag = soup.new_tag("li")
        toc_ul.append(li)

        a = soup.new_tag("a")
        a.append(BeautifulSoup(title, "html.parser"))
        a["href"] = f"#{tag_id}"
        li.append(a)

    path.write_text(str(soup))


if __name__ == "__main__":
    fill_toc("./index.html")
