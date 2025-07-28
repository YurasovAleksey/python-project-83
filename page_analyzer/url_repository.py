from datetime import datetime

import psycopg2
from psycopg2.extras import NamedTupleCursor

from .parser import HtmlParser
from .url_normalizer import UrlNormalizer


class UrlRepository:
    def __init__(self, connection):
        self.connection = connection

    def add_url(self, raw_url):
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            try:
                parsed_url = UrlNormalizer.normalize(raw_url)
                if not UrlNormalizer.is_valid(parsed_url):
                    return False, None, "Некорректный URL"

                cursor.execute(
                    "SELECT id FROM urls WHERE name = %s", (parsed_url,)
                )
                existing = cursor.fetchone()
                if existing:
                    return False, existing.id, "Страница уже существует"

                cursor.execute(
                    """
                    INSERT INTO urls (name, created_at)
                    VALUES (%s, %s) RETURNING id
                    """,
                    (parsed_url, datetime.now()),
                )
                url_id = cursor.fetchone().id
                self.connection.commit()
                return True, url_id, "Страница успешно добавлена"

            except psycopg2.Error as e:
                self.connection.rollback()
                return False, None, f"Ошибка базы данных: {str(e)}"

    def find_by_id(self, url_id):
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
            return cursor.fetchone()

    def get_all_urls(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    urls.id,
                    urls.name,
                    urls.created_at,
                    MAX(url_checks.created_at) as last_check_date,
                    MAX(url_checks.status_code) as last_check_status
                FROM urls
                LEFT JOIN url_checks ON urls.id = url_checks.url_id
                GROUP BY urls.id
                ORDER BY urls.created_at DESC
            """)
            return cursor.fetchall()

    def add_check(self, url_id):
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            try:
                cursor.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
                url = cursor.fetchone()
                if not url:
                    return False, None, "URL не найден"

                parsed_data = HtmlParser.parse(url.name)
                if not parsed_data:
                    return False, None, "Произошла ошибка при проверке"

                cursor.execute(
                    """INSERT INTO url_checks (
                        url_id,
                        status_code,
                        h1,
                        title,
                        description,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                    (
                        url_id,
                        parsed_data["status_code"],
                        parsed_data["h1"][:255] if parsed_data["h1"] else None,
                        parsed_data["title"][:255]
                        if parsed_data["title"]
                        else None,
                        parsed_data["description"][:255]
                        if parsed_data["description"]
                        else None,
                        datetime.now(),
                    ),
                )
                check_id = cursor.fetchone().id
                self.connection.commit()
                return True, check_id, "Проверка успешно добавлена"
            except psycopg2.Error as e:
                self.connection.rollback()
                return False, None, f"Ошибка при добавлении проверки: {str(e)}"

    def get_checks_url(self, url_id):
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    url_id,
                    status_code,
                    h1,
                    title,
                    description,
                    created_at,
                    ROW_NUMBER() OVER
                    (PARTITION BY url_id ORDER BY created_at)
                    as local_id
                FROM url_checks
                WHERE url_id = %s
                ORDER BY created_at DESC
            """,
                (url_id,),
            )
            return cursor.fetchall()
