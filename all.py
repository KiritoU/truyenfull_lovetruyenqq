import sys
from time import sleep

from icecream import ic

from _db import Database
from crawler import Crawler
from settings import CONFIG
from telegram_noti import send_direct_message


def main():
    database_for_crawl_all = Database()
    print(f"Using database: {database_for_crawl_all} for crawl_all.py file...")
    _crawler = Crawler(database=database_for_crawl_all)

    try:
        is_netttruyen_domain_work = _crawler.is_truyenfull_domain_work()
        if not is_netttruyen_domain_work:
            send_direct_message(msg="Truyenfull domain might be changed!!!")
            sys.exit(1)

        last_page = _crawler.get_truyenfull_last_page()
        ic(last_page)

        for i in range(last_page, 1, -1):
            _crawler.crawl_page(page=i)
            sleep(CONFIG.WAIT_BETWEEN_ALL)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    while True:
        main()
        sleep(CONFIG.WAIT_BETWEEN_LATEST)
