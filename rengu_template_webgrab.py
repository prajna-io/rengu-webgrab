import re
from uuid import uuid4
from datetime import datetime
from io import StringIO

from html2text import HTML2Text
from bs4 import BeautifulSoup
import requests

from rengu.template import RenguTemplate
from rengu.io.yaml import RenguOutputYaml

converter = HTML2Text()
converter.ignore_links = True


def _parse_poetrysociety(soup):

    title = soup.select(".entry-title")[0].get_text().strip()
    author = soup.select(".entry-header > h3 > a")[0].get_text().strip()
    body = converter.handle(
        str(soup.select(".entry-content")[0]).replace("\u00a0", "&nbsp;")
    ).rstrip()

    return {
        "Title": title,
        "By": author,
        "Body": body,
    }


def _parse_poemhunter(soup):

    title = soup.select(".phPageDetailsTitle")[0].get_text().strip()
    author = soup.select(".phpdAuthor > a")[0].get_text().strip()
    body = converter.handle(
        str(soup.select(".phContent")[0]).replace("\u00a0", "&nbsp;")
    ).rstrip()

    return {
        "Title": title,
        "By": author,
        "Body": body,
    }


def _parse_poetsorg(soup):

    title = soup.select(".poem__title")[0].get_text().strip()
    author = soup.select(".card-subtitle > a")[0].get_text().strip()
    body = converter.handle(
        str(soup.select(".poem__body")[0]).replace("\u00a0", "&nbsp;")
    ).rstrip()

    return {
        "Title": title,
        "By": author,
        "Body": body,
    }


def _parse_poetryfoundation(soup):

    title = soup.select(".c-feature-hd > h1")[0].get_text().strip()
    author = soup.select(".c-txt_attribution > a")[0].get_text().strip()
    body = (
        converter.handle(str(soup.select(".o-poem")[0]).replace("\u00a0", "&nbsp;"))
        .replace("\n\n", "\n")
        .rstrip()
    )

    return {
        "Title": title,
        "By": author,
        "Body": body,
    }


def _parse_loc_laureate(soup):

    title = re.sub(
        r"Poem \d{3}:",
        "",
        soup.select("[id=page-title] > .smaller-h1 > span")[1].get_text(),
    ).strip()
    author = soup.select(".info > h2")[0].get_text().strip()

    poem = soup.select(".poem > pre")
    if not poem:
        poem = soup.select(".poem > p")

    body = (
        converter.handle(str(poem[0]).replace("\u00a0", "&nbsp;"))
        .replace("\n\n", "\n")
        .replace("\n    ", "\n")
        .rstrip()
    )

    return {
        "Title": title,
        "By": author,
        "Body": body,
    }


def _parse_vianegativa(soup):

    title = soup.select(".entry-title")[0].get_text().strip()
    author = soup.select(".byline")[0].get_text().strip().replace("by ", "")

    content = soup.select(".wp-block-verse")
    if not content:
        content = soup.select(".entry-content")
    body = converter.handle(str(content[0])).replace("\n\n", "\n").rstrip()

    return {
        "Title": title,
        "By": author,
        "Body": body,
    }


def _parse_americanlife(soup):
    title = soup.select(".title-block__heading > .type-h1")[0].get_text().strip()
    author = (
        soup.select(".title-block__attribution > span > .type-highlight")[0]
        .get_text()
        .strip()
    )

    body = (
        converter.handle(str(soup.select(".poem")[0]).replace("\u00a0", "&nbsp;"))
        .replace("\n\n", "\n")
        .rstrip()
    )

    return {
        "Title": title,
        "By": author,
        "Body": body,
    }


def _parse_greatpoets(soup):

    try:
        author, title = soup.select(".asset-name")[0].get_text().split(",", 1)
    except ValueError:
        tagline = soup.select(".asset-name")[0].get_text()
        index_by = tagline.index(" by ")
        title = tagline[:index_by].strip()
        author = tagline[index_by + 4 :].strip()

    body = (
        converter.handle(str(soup.select(".asset-body")[0]).replace("\u00a0", "&nbsp;"))
        .replace("\n\n", "\n")
        .rstrip()
    )

    return {
        "Title": title,
        "By": author,
        "Body": body,
    }


def _parse_allpoetry(soup):

    title = soup.select(".title")[0].get_text()
    author = soup.select(".bio .media-body .u")[0].get_text()

    body = soup.select(".poem_body div")[1].get_text()

    return {
        "Title": title,
        "By": author,
        "Body": body,
    }


def _parse_poetry_chaikhana(soup):
    title = soup.select("#content p")[0].get_text()
    author = soup.select("#content big a")[0].get_text()

    body = converter.handle(str(soup.select("#content p big")[0]))

    return {
        "Title": title,
        "By": author,
        "Body": body,
    }


_WEBSITES = {
    "https://www.poetryfoundation.org": _parse_poetryfoundation,
    "https://poets.org": _parse_poetsorg,
    "https://www.poets.org": _parse_poetsorg,
    "https://www.poemhunter.com": _parse_poemhunter,
    "https://www.loc.gov/programs/poetry-and-literature/poet-laureate/poet-laureate-projects/": _parse_loc_laureate,
    "https://www.vianegativa.us": _parse_vianegativa,
    "https://www.americanlifeinpoetry.org": _parse_americanlife,
    "https://greatpoets.livejournal.com": _parse_greatpoets,
    "https://allpoetry.com": _parse_allpoetry,
    "https://poetry-chaikhana.com": _parse_poetry_chaikhana,
    "https://poems.poetrysociety.org.uk": _parse_poetrysociety,
}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/39.0.2171.95 Safari/537.36"
}


class RenguTemplateWebgrab(RenguTemplate):
    def list_templates(self):
        yield "webgrab"

    def load_template(self, template: str, *arguments) -> str:

        yaml_out = ""

        for url in arguments:

            method = None
            for w, m in _WEBSITES.items():
                if url.startswith(w):
                    method = m
                    break

            if not method:
                yaml_out = f"""---
Category: fragment
Source:
    URL: {url}
    Date: '{datetime.now():%Y%m%d}'
Format: verse
## ERROR: No handler for {url}
---
"""
                break

            page = requests.get(url, headers=_HEADERS)
            soup = BeautifulSoup(page.content, "html5lib")

            data = method(soup) | {
                "ID": str(uuid4()),
                "Category": "fragment",
                "Format": "verse",
                "Source": {"URL": url, "Date": f"{datetime.now():%Y%m%d}"},
            }

            yaml_stream = StringIO()
            RenguOutputYaml(arg="", fd=yaml_stream)(data)
            yaml_out = yaml_out + yaml_stream.getvalue()
            yaml_stream.close()

        return yaml_out


if __name__ == "__main__":

    import sys

    grab = RenguTemplateWebgrab(None)

    print(grab.load_template("webgrab", *sys.argv[1:]))
