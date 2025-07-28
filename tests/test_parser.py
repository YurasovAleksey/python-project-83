import pytest
from unittest.mock import patch, Mock
from requests.exceptions import RequestException
from page_analyzer.parser import HtmlParser


@pytest.fixture
def mock_response():
    html_content = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Test Header</h1>
        </body>
    </html>
    """
    response = Mock()
    response.text = html_content
    response.status_code = 200
    return response


def test_parse_success(mock_response):
    with patch('requests.get', return_value=mock_response) as mock_get:
        result = HtmlParser.parse("http://example.com")
        
        assert result == {
            "status_code": 200,
            "h1": "Test Header",
            "title": "Test Page",
            "description": "Test description"
        }
        mock_get.assert_called_once_with("http://example.com", timeout=5)


def test_parse_missing_elements():
    html_content = "<html><body></body></html>"
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.status_code = 200
    
    with patch('requests.get', return_value=mock_response):
        result = HtmlParser.parse("http://example.com")
        
        assert result == {
            "status_code": 200,
            "h1": "",
            "title": "",
            "description": ""
        }


def test_parse_request_exception():
    with patch('requests.get', side_effect=RequestException("Connection error")):
        result = HtmlParser.parse("http://example.com")
        assert result is None


def test_parse_invalid_status_code():
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = RequestException("404 error")
    
    with patch('requests.get', return_value=mock_response):
        result = HtmlParser.parse("http://example.com")
        assert result is None
