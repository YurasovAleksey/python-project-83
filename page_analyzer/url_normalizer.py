from urllib.parse import urlparse

from validators import ValidationError
from validators import url as validate_url


class UrlNormalizer:
    @staticmethod
    def normalize(raw_url):
        raw_url = raw_url.strip()

        if raw_url.startswith("//"):
            raw_url = "https:" + raw_url

        parsed = urlparse(raw_url)

        if not parsed.scheme:
            raw_url = f"https://{raw_url}"
            parsed = urlparse(raw_url)

        normalized = f"{parsed.scheme}://{parsed.netloc}"
        return normalized.rstrip('/')

    @staticmethod
    def is_valid(url):
        try:
            result = validate_url(url)
            if isinstance(result, bool):
                return result
            return False
        except ValidationError:
            return False
