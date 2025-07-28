import pytest
from page_analyzer.url_normalizer import UrlNormalizer


@pytest.mark.parametrize("input_url,expected", [
    ("example.com", "https://example.com"),
    ("http://example.com", "http://example.com"),
    ("https://example.com", "https://example.com"),
    ("ftp://example.com", "ftp://example.com"),
    ("//example.com", "https://example.com"),
])
def test_normalize(input_url, expected):
    assert UrlNormalizer.normalize(input_url) == expected


@pytest.mark.parametrize("url,expected", [
    ("https://example.com", True),
    ("http://example.com", True),
    ("https://sub.example.com/path?query=1", True),
    ("example.com", False),
    ("https://example", False),
    ("not-a-url", False),
    ("https://example.com/" + "a" * 255, True),
])
def test_is_valid(url, expected):
    assert UrlNormalizer.is_valid(url) == expected
