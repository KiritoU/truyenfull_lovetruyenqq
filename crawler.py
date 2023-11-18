import json
import logging
import re
import sys
from pathlib import Path
from time import sleep

import requests
from bs4 import BeautifulSoup
from icecream import ic
from slugify import slugify

from chapter import _chapter
from helper import helper
from lovetruyenqq import Lovetruyenqq
from settings import CONFIG
from story import _story

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


class Crawler:
    def __init__(self, database) -> None:
        self._lovetruyenqq = Lovetruyenqq(database=database)

    def crawl_chapter(
        self,
        story_title: int,
        story_id: int,
        story_slug: str,
        chapter_name: str,
        chapter_href: str,
    ) -> None:
        soup = helper.crawl_soup(chapter_href)

        chapter_content = _chapter.get_chapter_content(
            chapter_name=chapter_name, soup=soup
        )

        self._lovetruyenqq.get_or_insert_chapter(
            story_id=story_id,
            story_title=story_title,
            chapter_name=chapter_name,
            content=chapter_content,
        )
        logging.info(f"Inserted {chapter_name}")

    def crawl_written_story(self, href: str, labels: list[str]):
        soup = helper.crawl_soup(href)
        story_details = _story.get_story_details(href=href, soup=soup)
        story_details["labels"] = labels

        # with open("json/story.json", "w") as f:
        #     f.write(json.dumps(comic_details, indent=4, ensure_ascii=False))
        # sys.exit(0)

        story_id = self._lovetruyenqq.get_or_insert_comic(story_details)
        logging.info(f"Got (or inserted) comic: {story_id}")

        # with open("json/comic.json", "w") as f:
        #     f.write(json.dumps(comic_details, indent=4, ensure_ascii=False))

        if not story_id:
            logging.error(f"Cannot crawl comic with: {href}")
            return

        chapters = story_details.get("chapters", {})
        chapters_name = list(chapters.keys())
        inserted_chapters_slug = self._lovetruyenqq.get_backend_chapters_slug(story_id)

        for chapter_name in chapters_name:
            chapter_slug = _chapter.get_chapter_slug(chapter_name=chapter_name)
            if chapter_slug in inserted_chapters_slug:
                continue

            chapter_href = chapters.get(chapter_name)
            self.crawl_chapter(
                story_title=story_details.get("title"),
                story_id=story_id,
                story_slug=story_details.get("slug"),
                chapter_name=chapter_name,
                chapter_href=chapter_href,
            )

    def crawl_item(self, row: BeautifulSoup):
        try:
            col_xs_7 = row.find("div", class_="col-xs-7")
            a = col_xs_7.find("a")
            href = a.get("href")
            if not href:
                logging.error(f"Could not find href for row...")
                return
            label_titles = col_xs_7.find_all("span", class_="label-title")
            labels = []
            for label in label_titles:
                labels.extend(label.get("class", []))

            labels = list(set(labels))
            labels.remove("label-title")
            labels = [label.replace("label-", "") for label in labels]

            self.crawl_written_story(href=href, labels=labels)
        except Exception as e:
            print(e)
            logging.error(f"[-] Unknow error occurred while crawling row...")

    def crawl_page(self, page: int = 1):
        url = f"{CONFIG.TRUYENFULL_HOMEPAGE}/danh-sach/truyen-moi/trang-{page}/"
        soup = helper.crawl_soup(url)

        list_page = soup.find("div", {"id": "list-page"})
        if not list_page:
            return 0

        list_truyen = list_page.find("div", class_="list-truyen")
        if not list_truyen:
            return 0

        rows = list_truyen.find_all("div", class_="row")

        for row in rows:
            self.crawl_item(row=row)

        return 1

    def get_truyenfull_last_page(self):
        url = f"{CONFIG.TRUYENFULL_HOMEPAGE}/danh-sach/truyen-moi/trang-1/"
        soup = helper.crawl_soup(url)

        try:
            pagination = soup.find("ul", class_="pagination")
            lis = pagination.find_all("li")
            last_li = lis[-2]
            a = last_li.find("a")
            href = a.get("href")
            pattern = re.compile(r"/trang-(\d+)/")
            matches = pattern.search(href)
            page = matches.group(1)
            return int(page)
        except:
            return CONFIG.TRUYENFULL_LAST_PAGE

    def is_truyenfull_domain_work(self):
        for _ in range(5):
            try:
                response = helper.download_url(CONFIG.TRUYENFULL_HOMEPAGE)
                if response.status_code == 200:
                    return True

            except Exception as e:
                pass

            sleep(5)

        return False
