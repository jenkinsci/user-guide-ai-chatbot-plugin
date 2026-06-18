from urllib.parse import urlparse
from bs4 import BeautifulSoup


def normalize_url(url: str):
    """Normalize URL by adding trailing slash for non-HTML pages."""
    if ".html" not in url and not url.endswith("/"):
        url += "/"
    return url


def is_valid_url(url: str, base_url: str):
    """Check if the URL is a valid link to a new page, internal to the doc,
    or a redirect to another page
    """
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and base_url in url and "#" not in url


def extract_page_content_container(soup: BeautifulSoup):
    """Extract main content from the page.

    Developer docs use col-8, non-developer docs use col-lg-9.
    Falls back to container if neither is found.
    """
    content_div = (
        soup.find("div", class_="col-8")
        or soup.find("div", class_="col-lg-9")
        or soup.find("div", class_="container")
    )
    if content_div:
        return str(content_div)
    return ""
