import sys
from time import sleep

from icecream import ic

from _db import Database
from crawler import Crawler
from settings import CONFIG
from telegram_noti import send_direct_message


def main():
    database_for_update = Database()
    print(f"Using database: {database_for_update} for update.py file...")
    _crawler = Crawler(database=database_for_update)

    try:
        is_netttruyen_domain_work = _crawler.is_truyenfull_domain_work()
        if not is_netttruyen_domain_work:
            send_direct_message(msg="Truyenfull domain might be changed!!!")
            sys.exit(1)
        _crawler.crawl_page(page=1)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    while True:
        main()
        sleep(CONFIG.WAIT_BETWEEN_LATEST)
