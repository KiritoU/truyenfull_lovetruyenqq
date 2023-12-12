import json
import logging
import re
import sys
from pathlib import Path
from time import sleep
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from icecream import ic
from slugify import slugify
from websocket import create_connection

from chapter import _chapter
from helper import helper
from lovetruyenqq import Lovetruyenqq
from settings import CONFIG
from story import _story

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


from_source = urlparse(CONFIG.TRUYENFULL_HOMEPAGE).netloc
ws = create_connection(f"ws://{CONFIG.WS_NETLOC}/ws/source/{from_source}/")


def get_slug_index(slug: str, file_path: str) -> int:
    with open(file_path, "r") as f:
        stories = [story.strip("\n") for story in f.readlines()]
    if slug not in stories:
        stories.append(slug)
        with open(file_path, "a") as f:
            print(slug, file=f)

    story_id = stories.index(slug) + 1
    return story_id


def send_ws(data: dict):
    send_data = {"message": data}
    ws.send(json.dumps(send_data))


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

        if not chapter_content:
            return

        if CONFIG.DEBUG:
            chapter_post_slug = _chapter.get_chapter_slug(
                chapter_name=chapter_name, story_title=story_title
            )
            chapter_post_id = get_slug_index(
                slug=chapter_post_slug, file_path="test/chapters.txt"
            )
        else:
            chapter_post_id = self._lovetruyenqq.get_or_insert_chapter(
                story_id=story_id,
                story_title=story_title,
                chapter_name=chapter_name,
                content=chapter_content,
            )

        send_ws(
            data={
                "message": f"{story_title} => {chapter_name}",
                "crawled_chapter": {
                    "post_id": story_id,
                    "story_title": story_title,
                    "chapter_name": chapter_name,
                    "chapter_href": chapter_href,
                    "chapter_post_id": chapter_post_id,
                },
            }
        )

        logging.info(f"Inserted {chapter_name}")

    def crawl_written_story(self, href: str, labels: list[str]):
        soup = helper.crawl_soup(href)
        story_details = _story.get_story_details(href=href, soup=soup)
        story_details["labels"] = labels

        # with open("json/story.json", "w") as f:
        #     f.write(json.dumps(comic_details, indent=4, ensure_ascii=False))
        # sys.exit(0)

        if CONFIG.DEBUG:
            story_id = get_slug_index(
                slug=story_details.get("slug"), file_path="test/stories.txt"
            )
        else:
            story_id = self._lovetruyenqq.get_or_insert_comic(story_details)
        logging.info(f"Got (or inserted) comic: {story_id}")

        if not story_id:
            logging.error(f"Cannot crawl comic with: {href}")
            return

        story_details["href"] = href
        story_details["post_id"] = story_id

        # with open("json/comic.json", "w") as f:
        #     f.write(json.dumps(story_details, indent=4, ensure_ascii=False))

        send_ws(
            data={
                "message": f"Crawling {href}",
                "story_details": story_details,
            }
        )

        chapters = story_details.get("chapters", {})
        chapters_name = list(chapters.keys())
        if CONFIG.DEBUG:
            inserted_chapters_slug = []
        else:
            inserted_chapters_slug = self._lovetruyenqq.get_backend_chapters_slug(
                story_id
            )

        for chapter_name in chapters_name:
            chapter_slug = _chapter.get_chapter_slug(
                chapter_name=chapter_name, story_title=story_details.get("title", "")
            )
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
        if "label-title" in labels:
            labels.remove("label-title")
        labels = [label.replace("label-", "") for label in labels]

        self.crawl_written_story(href=href, labels=labels)
        # try:
        # except Exception as e:
        #     print(e)
        #     logging.error(f"[-] Unknow error occurred while crawling row...")

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
