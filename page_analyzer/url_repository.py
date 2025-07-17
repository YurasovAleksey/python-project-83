from datetime import datetime
from urllib.parse import urlparse

import psycopg2
import requests
from bs4 import BeautifulSoup
from psycopg2.extras import NamedTupleCursor
from validators import url as validate_url


class UrlRepository:
    def __init__(self, connection):
        self.connection = connection

    def add_url(self, raw_url):
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            try:
                parsed_url = self._normalize_url(raw_url)
                if not self._is_valid_url(parsed_url):
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

                try:
                    response = requests.get(url.name, timeout=5)
                    response.raise_for_status()
                    status_code = response.status_code
                    soup = BeautifulSoup(response.text, "html.parser")

                    h1 = soup.find("h1")
                    h1_content = h1.get_text().strip() if h1 else ""

                    title = soup.find("title")
                    title_content = title.get_text().strip() if title else ""

                    description = soup.find(
                        "meta", attrs={"name": "description"}
                    )
                    description_content = (
                        description["content"].strip() if description else ""
                    )

                except requests.exceptions.RequestException:
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
                        status_code,
                        h1_content[:255] if h1_content else None,
                        title_content[:255] if title_content else None,
                        description_content[:255]
                        if description_content
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

    def _normalize_url(self, raw_url):
        parsed = urlparse(raw_url)
        if not parsed.scheme:
            return f"https://{raw_url}"
        return f"{parsed.scheme}://{parsed.netloc}"

    def _is_valid_url(self, url):
        return validate_url(url) and len(url) <= 255 and url.count(".") > 0
