import requests
from bs4 import BeautifulSoup


class HtmlParser:
    @staticmethod
    def parse(url):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            h1 = soup.find("h1")
            h1_content = h1.get_text().strip() if h1 else ""

            title = soup.find("title")
            title_content = title.get_text().strip() if title else ""

            description = soup.find("meta", attrs={"name": "description"})
            description_content = (
                description["content"].strip() if description else ""
            )

            return {
                "status_code": response.status_code,
                "h1": h1_content,
                "title": title_content,
                "description": description_content,
            }
        except requests.exceptions.RequestException:
            return None
