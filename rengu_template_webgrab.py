import re
from uuid import uuid4
from datetime import date
from io import StringIO

from html2text import HTML2Text
from bs4 import BeautifulSoup
import requests

from rengu.template import RenguTemplate
from rengu.io.yaml import RenguOutputYaml

converter = HTML2Text()


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


_WEBSITES = {
    "https://www.poetryfoundation.org": _parse_poetryfoundation,
    "https://poets.org": _parse_poetsorg,
    "https://www.poets.org": _parse_poetsorg,
    "https://www.poemhunter.com": _parse_poemhunter,
    "https://www.loc.gov/programs/poetry-and-literature/poet-laureate/poet-laureate-projects/": _parse_loc_laureate,
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
                yaml_out = yaml_out + f"---\n__ERROR: No handler for {url}"
                break

            page = requests.get(url, headers=_HEADERS)
            soup = BeautifulSoup(page.content, "html5lib")

            data = method(soup) | {
                "ID": str(uuid4()),
                "Category": "fragment",
                "Format": "verse",
                "Source": {"URL": url, "Date": date.today().strftime("%Y%m%d")},
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
