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
            return f"https://{raw_url}"

        netloc = parsed.netloc
        path = parsed.path.replace("//", "/") if parsed.path else ""

        return f"{parsed.scheme}://{netloc}{path}"

    @staticmethod
    def is_valid(url):
        try:
            result = validate_url(url)
            if isinstance(result, bool):
                return result
            return False
        except ValidationError:
            return False
