import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

import requests
from bs4 import BeautifulSoup
from slugify import slugify

from settings import CONFIG

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


class Helper:
    def get_header(self):
        header = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E150",  # noqa: E501
            "Accept-Encoding": "gzip, deflate",
            "Cache-Control": "max-age=0",
            "Accept-Language": "vi-VN",
            "Referer": f"{CONFIG.TRUYENFULL_HOMEPAGE}/",
        }
        return header

    def download_url(self, url):
        response = requests.get(url, headers=self.get_header())
        sleep(0.1)
        return response

    def crawl_soup(self, url) -> BeautifulSoup:
        logging.info(f"[+] Crawling {url}")

        html = self.download_url(url)
        soup = BeautifulSoup(html.content, "html.parser")

        return soup

    def error_log(self, msg, filename: str = "failed.txt"):
        Path("log").mkdir(parents=True, exist_ok=True)
        with open(f"log/{filename}", "a") as f:
            print(f"{msg}\n{'-' * 80}", file=f)

    def save_image(
        self,
        image_url: str,
        comic_seo: str = "",
        chap_seo: str = "",
        image_name: str = "0.jpg",
        is_thumb: bool = False,
        overwrite: bool = False,
    ) -> str:
        save_full_path = os.path.join(CONFIG.IMAGE_SAVE_PATH, comic_seo, chap_seo)

        Path(save_full_path).mkdir(parents=True, exist_ok=True)
        Path(CONFIG.THUMB_SAVE_PATH).mkdir(parents=True, exist_ok=True)

        save_image = os.path.join(save_full_path, image_name)
        if is_thumb:
            save_image = os.path.join(CONFIG.THUMB_SAVE_PATH, image_name)

        is_not_saved = not Path(save_image).is_file()

        if overwrite or is_not_saved:
            image = self.download_url(image_url)
            with open(save_image, "wb") as f:
                f.write(image.content)
            is_not_saved = True

        return [save_image, is_not_saved]


helper = Helper()
