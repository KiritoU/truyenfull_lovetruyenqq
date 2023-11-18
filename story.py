import re

from bs4 import BeautifulSoup
from slugify import slugify

from helper import helper


class Story:
    def get_title(self, truyen: BeautifulSoup) -> str:
        title = truyen.find("h3", class_="title")
        if not title:
            return ""

        return title.text.strip()

    def get_cover_url(self, truyen: BeautifulSoup) -> str:
        try:
            books = truyen.find("div", class_="books")
            img = books.find("img")
            img_src = img.get("data-cfsrc", "")
            if not img_src:
                img_src = img.get("src", "")

            return img_src
        except:
            return ""

    def get_other_info(self, truyen: BeautifulSoup) -> dict:
        result = {}
        info = truyen.find("div", class_="info")
        if info:
            div_elements = info.find_all("div")
            for div in div_elements:
                h3 = div.find("h3")
                if not h3:
                    continue

                key = slugify(h3.text)
                value = div.text.replace(h3.text, "").strip()
                if value:
                    result[key] = value

        return result

    def get_description(self, truyen: BeautifulSoup) -> str:
        desc_text = truyen.find("div", class_="desc-text")
        if not desc_text:
            return ""

        pretty = desc_text.prettify()
        pretty = pretty.replace("<br>", "\n")

        desc_soup = BeautifulSoup(pretty, "html.parser")

        return desc_soup.get_text().strip("\n").strip()

    def get_chapter_last_page(self, truyen: BeautifulSoup) -> int:
        try:
            pagination = truyen.find("ul", class_="pagination")
            lis = pagination.find_all("li")
            last_li = lis[-2]
            a = last_li.find("a")
            href = a.get("href")
            pattern = re.compile(r"/trang-(\d+)/")
            matches = pattern.search(href)
            page = matches.group(1)
            return int(page)
        except:
            return 1

    def get_chapters_from_soup(self, soup: BeautifulSoup) -> dict:
        list_chapter = soup.find("div", {"id": "list-chapter"})
        if not list_chapter:
            return {}

        chapters_dict = {}
        ul_list_chapters = list_chapter.find_all("ul", class_="list-chapter")
        for ul in ul_list_chapters:
            li_elements = ul.find_all("li")
            for li in li_elements:
                a = li.find("a")
                if not a:
                    continue

                chapter_title = a.get("title", "").strip()
                if not chapter_title:
                    chapter_title = a.text.strip()

                href = a.get("href", "")
                if href:
                    chapters_dict[chapter_title] = href

        return chapters_dict

    def get_chapters_href(self, truyen: BeautifulSoup, story_href: str) -> dict:
        chapters_dict = self.get_chapters_from_soup(soup=truyen)

        chapter_last_page = self.get_chapter_last_page(truyen=truyen)
        for page in range(2, chapter_last_page + 1):
            page_href = story_href.strip("/") + f"/trang-{page}/#list-chapter"
            chapter_soup = helper.crawl_soup(url=page_href)
            chapters_dict = {
                **chapters_dict,
                **self.get_chapters_from_soup(soup=chapter_soup),
            }

        return chapters_dict

    def get_story_details(self, href: str, soup: BeautifulSoup) -> dict:
        truyen = soup.find("div", {"id": "truyen"})
        if not truyen:
            return {}

        title = self.get_title(truyen=truyen)
        slug = href.strip().strip("/").split("/")[-1]
        cover_url = self.get_cover_url(truyen=truyen)
        description = self.get_description(truyen=truyen)
        detail_list_info = self.get_other_info(truyen=truyen)

        chapters_dict = self.get_chapters_href(truyen=truyen, story_href=href)

        return {
            "title": title,
            "slug": slug,
            "cover_url": cover_url,
            "description": description,
            **detail_list_info,
            "chapters": chapters_dict,
        }


_story = Story()
