from datetime import datetime
from urllib.parse import urlparse

import psycopg2
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
                
                cursor.execute("SELECT id FROM urls WHERE name = %s", (parsed_url,))
                existing = cursor.fetchone()
                if existing:
                    return False, existing.id, "Страница уже существует"
                
                cursor.execute(
                    "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                    (parsed_url, datetime.now())
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
            cursor.execute("SELECT * FROM urls ORDER BY created_at DESC")
            return cursor.fetchall()

    def add_check(self, url_id):
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            try:
                cursor.execute(
                    """INSERT INTO url_checks (url_id, created_at)
                    VALUES (%s, %s) RETURNING id""",
                    (url_id, datetime.now())
                )
                check_id = cursor.fetchone().id
                self.connection.commit()
                return True, check_id, "Проверка успешно добавлена"
            except psycopg2.Error as e:
                self.connection.rollback()
                return False, None, f"Ошибка при добавлении проверки: {str(e)}"
    
    def get_checks_url(self, url_id):
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute("""
                SELECT
                    id,
                    url_id,
                    status_code,
                    created_at,
                    ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY created_at) as local_id
                FROM url_checks
                WHERE url_id = %s
                ORDER BY created_at DESC
            """, (url_id,))
            return cursor.fetchall()

    def _normalize_url(self, raw_url):
        parsed = urlparse(raw_url)
        if not parsed.scheme:
            return f"https://{raw_url}"
        return f"{parsed.scheme}://{parsed.netloc}"

    def _is_valid_url(self, url):
        return (validate_url(url) and 
                len(url) <= 255 and 
                url.count('.') > 0)
