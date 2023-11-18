from bs4 import BeautifulSoup
from slugify import slugify


class Chapter:
    def get_chapter_slug(self, chapter_name: str, story_title: str) -> str:
        return slugify(f"{story_title}-{chapter_name}")

    def get_chapter_content(self, chapter_name: str, soup: BeautifulSoup) -> dict:
        chapter_c = soup.find("div", {"id": "chapter-c"})
        if not chapter_c:
            return ""

        pretty = chapter_c.prettify()
        pretty = pretty.replace("<br>", "\n")

        chapter_c_soup = BeautifulSoup(pretty, "html.parser")

        return chapter_c_soup.get_text().strip("\n").strip()


_chapter = Chapter()
