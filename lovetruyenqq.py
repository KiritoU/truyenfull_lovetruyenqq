import logging
import os
import time
from datetime import datetime

import pytz
from phpserialize import serialize
from PIL import Image
from slugify import slugify

from _db import Database
from chapter import _chapter
from helper import helper
from settings import CONFIG

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)

vn_timezone = pytz.timezone("Asia/Ho_Chi_Minh")


class Lovetruyenqq:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get_backend_chapters_slug(self, story_id: int) -> list:
        chapters = self.database.select_all_from(
            table=f"posts",
            condition=f'post_parent={story_id} AND post_type="chap"',
        )

        chapters_slug = [chapter[11] for chapter in chapters]
        return chapters_slug

    def insert_postmeta(self, postmeta_data: list, table: str = "postmeta"):
        self.database.insert_into(table=table, data=postmeta_data, is_bulk=True)

    def get_timeupdate(self) -> str:
        # TODO: later
        timeupdate = datetime.now(vn_timezone).strftime("%Y/%m/%d %H:%M:%S")

        return timeupdate

    def get_comic_timeupdate(self) -> str:
        # TODO
        return int(time.time())

    def download_and_save_thumb(self, story_slug: str, cover_url: str):
        try:
            # Download the cover image
            image_name = story_slug + ".png"
            thumb_save_path, is_not_saved = helper.save_image(
                image_url=cover_url, image_name=image_name, is_thumb=True
            )

            # return thumb_save_path.replace(CONFIG.IMAGE_SAVE_PATH, CONFIG.CUSTOM_CDN)
            return f"covers/{image_name}", thumb_save_path
        except Exception:
            return CONFIG.DEFAULT_THUMB, thumb_save_path

    def get_wp_attachment_metadata(
        self, saved_thumb_url: str, thumb_save_path: str
    ) -> str:
        if not thumb_save_path:
            return ""

        image = Image.open(thumb_save_path)
        width, height = image.size
        size_in_bytes = os.path.getsize(thumb_save_path)

        _wp_attachment_metadata_dict = {
            "width": width,
            "height": height,
            "file": saved_thumb_url,
            "filesize": size_in_bytes,
            "image_meta": {
                "aperture": "0",
                "credit": "",
                "camera": "",
                "caption": "",
                "created_timestamp": "0",
                "copyright": "",
                "focal_length": "0",
                "iso": "0",
                "shutter_speed": "0",
                "title": "",
                "orientation": "0",
                "keywords": {},
            },
        }
        _wp_attachment_metadata = serialize(_wp_attachment_metadata_dict).decode(
            "utf-8"
        )
        return _wp_attachment_metadata

    def insert_thumb(self, story_slug: str, cover_url: str) -> int:
        if not cover_url:
            return 0

        saved_thumb_url, thumb_save_path = self.download_and_save_thumb(
            story_slug=story_slug, cover_url=cover_url
        )

        thumb_name = saved_thumb_url.split("/")[-1]

        timeupdate = self.get_timeupdate()
        thumb_post_data = (
            0,
            timeupdate,
            timeupdate,
            "",
            thumb_name,
            "",
            "inherit",
            "open",
            "closed",
            "",
            slugify(thumb_name),
            "",
            "",
            timeupdate,
            timeupdate,
            "",
            0,
            "",
            0,
            "attachment",
            "image/png",
            0,
        )

        thumb_id = self.database.insert_into(table="posts", data=thumb_post_data)

        postmeta_data = [
            (thumb_id, "_wp_attached_file", saved_thumb_url),
            # (
            #     thumb_id,
            #     "_wp_attachment_metadata",
            #     self.get_wp_attachment_metadata(
            #         saved_thumb_url=saved_thumb_url, thumb_save_path=thumb_save_path
            #     ),
            # ),
        ]

        self.insert_postmeta(postmeta_data)
        # self.database.insert_into(
        #     table="postmeta",
        #     data=(thumb_id, "_wp_attached_file", saved_thumb_url),
        # )

        # self.database.insert_into(
        #     table="postmeta",
        #     data=(thumb_id, "_wp_attached_file", saved_thumb_url),
        # )

        return thumb_id

    def insert_terms(
        self,
        post_id: int,
        terms: str,
        taxonomy: str,
        is_title: str = False,
        term_slug: str = "",
    ):
        try:
            terms = (
                [term.strip() for term in terms.split(",")] if not is_title else [terms]
            )
        except Exception as e:
            logging.error(f"[-] Error in insert terms: {terms}")
            return

        term_ids = []
        for term in terms:
            term_insert_slug = slugify(term_slug) if term_slug else slugify(term)
            cols = "tt.term_taxonomy_id, tt.term_id"
            table = (
                f"{CONFIG.TABLE_PREFIX}term_taxonomy tt, {CONFIG.TABLE_PREFIX}terms t"
            )
            condition = f't.slug = "{term_insert_slug}" AND tt.term_id=t.term_id AND tt.taxonomy="{taxonomy}"'

            query = f"SELECT {cols} FROM {table} WHERE {condition}"

            be_term = self.database.select_with(query=query)
            if not be_term:
                term_id = self.database.insert_into(
                    table="terms",
                    data=(term, term_insert_slug, 0),
                )
                term_taxonomy_count = 1 if taxonomy == "seasons" else 0
                term_taxonomy_id = self.database.insert_into(
                    table="term_taxonomy",
                    data=(term_id, taxonomy, "", 0, term_taxonomy_count),
                )
                term_ids = [term_taxonomy_id, True]
            else:
                term_taxonomy_id = be_term[0][0]
                term_id = be_term[0][1]
                term_ids = [term_taxonomy_id, False]

            try:
                self.database.insert_into(
                    table="term_relationships",
                    data=(post_id, term_taxonomy_id, 0),
                )
            except:
                pass

        return term_ids

    def insert_comic(self, story_data: dict):
        thumb_id = self.insert_thumb(
            story_data.get("slug", ""), story_data.get("cover_url")
        )
        timeupdate = self.get_timeupdate()
        data = (
            0,
            timeupdate,
            timeupdate,
            story_data.get("description", ""),
            story_data["title"],
            "",
            "publish",
            "open",
            "closed",
            "",
            story_data.get("slug", ""),
            "",
            "",
            timeupdate,
            timeupdate,
            "",
            0,
            "",
            0,
            "post",
            "",
            0,
        )

        try:
            story_id = self.database.insert_into(table=f"posts", data=data)
        except Exception as e:
            helper.error_log(
                msg=f"Failed to insert comic\n{e}", filename="helper.comic_id.log"
            )
            return 0

        postmeta_data = [
            # (comic_id, "_latest_update", f"{self.get_comic_timeupdate()}"),
            (story_id, "_thumbnail_id", thumb_id),
            (
                story_id,
                "tw_status",
                story_data.get("trang-thai", "Đang ra"),
            ),
            # (story_id, "_wp_manga_alternative", story_data.get("ten-khac", "")),
            # (story_id, "manga_adult_content", ""),
            # (story_id, "manga_title_badges", "no"),
            # (story_id, "_wp_manga_chapter_type", "text"),
        ]

        self.insert_postmeta(postmeta_data)

        self.insert_terms(
            post_id=story_id,
            terms=story_data.get("tac-gia", ""),
            taxonomy="tac-gia",
        )
        self.insert_terms(
            post_id=story_id,
            terms=story_data.get("the-loai", ""),
            taxonomy="category",
        )

        # TODO: insert label - tien_to

        return story_id

    def get_or_insert_comic(self, comic_details: dict) -> int:
        condition = f"""post_name = '{comic_details["slug"]}'"""
        be_post = self.database.select_all_from(table=f"posts", condition=condition)
        if not be_post:
            return self.insert_comic(story_data=comic_details)
        else:
            return be_post[0][0]

    def insert_chapter(
        self,
        story_id: int,
        story_title: str,
        chapter_name: str,
        content: str,
    ):
        chapter_post_slug = _chapter.get_chapter_slug(
            chapter_name=chapter_name, story_title=story_title
        )
        timeupdate = self.get_timeupdate()
        data = (
            0,
            timeupdate,
            timeupdate,
            content,
            chapter_name,
            "",
            "publish",
            "open",
            "closed",
            "",
            chapter_post_slug,
            "",
            "",
            timeupdate,
            timeupdate,
            "",
            story_id,
            "",
            0,
            "chap",
            "",
            0,
        )

        try:
            return self.database.insert_into(table=f"posts", data=data)
        except Exception as e:
            helper.error_log(
                msg=f"Failed to insert comic\n{e}",
                filename="madara.insert_chapter_content_to_posts.log",
            )
            return 0

    def get_or_insert_chapter(
        self,
        story_id: int,
        story_title: str,
        chapter_name: str,
        content: str,
    ):
        chapter_post_slug = _chapter.get_chapter_slug(
            chapter_name=chapter_name, story_title=story_title
        )
        condition = f"""post_name='{chapter_post_slug}' AND post_type='chap'"""
        be_post = self.database.select_all_from(table=f"posts", condition=condition)
        if not be_post:
            return self.insert_chapter(
                story_id=story_id,
                story_title=story_title,
                chapter_name=chapter_name,
                content=content,
            )
        else:
            return be_post[0][0]
