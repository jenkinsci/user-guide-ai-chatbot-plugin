import pytest
from bs4 import BeautifulSoup
from data.collection.jenkins_docs.jenkins_docs_utils import extract_page_content_container, is_valid_url, normalize_url


@pytest.mark.parametrize("url, expected", [
    # 1. Plain URL without trailing slash → slash added
    ("https://docs.example.com/guide", "https://docs.example.com/guide/"),
 
    # 2. URL already ending with slash → unchanged
    ("https://docs.example.com/guide/", "https://docs.example.com/guide/"),
 
    # 3. URL pointing to an .html page → unchanged (no slash added)
    ("https://docs.example.com/page.html", "https://docs.example.com/page.html"),
 
    # 4. URL with .html in a query param → treated as containing '.html', unchanged
    ("https://docs.example.com/redirect?to=page.html", "https://docs.example.com/redirect?to=page.html"),
 
    # 5. Root URL without trailing slash → slash added
    ("https://docs.example.com", "https://docs.example.com/"),
])
def test_normalize_url(url, expected):
    assert normalize_url(url) == expected
 

@pytest.mark.parametrize("url, base_url, expected", [
    # 1. Valid internal HTTPS URL
    ("https://docs.example.com/guide/", "docs.example.com", True),
 
    # 2. Valid internal HTTP URL
    ("http://docs.example.com/intro/", "docs.example.com", True),
 
    # 3. Anchor fragment URL → invalid (contains #)
    ("https://docs.example.com/guide/#section", "docs.example.com", False),
 
    # 4. External URL not containing base_url → invalid
    ("https://external-site.com/page/", "docs.example.com", False),
 
    # 5. No scheme (relative URL) → invalid
    ("/guide/page/", "docs.example.com", False),
])
def test_is_valid_url(url, base_url, expected):
    assert is_valid_url(url, base_url) == expected


@pytest.mark.parametrize("html, expected_content, expected_class", [
    # 1. Developer docs layout → col-8 returned
    (
        '<div class="col-8"><p>Dev content</p></div>',
        "Dev content",
        "col-8",
    ),
    # 2. Non-developer docs layout → col-lg-9 returned
    (
        '<div class="col-lg-9"><p>User content</p></div>',
        "User content",
        "col-lg-9",
    ),
    # 3. Fallback → container returned when neither col-8 nor col-lg-9 exist
    (
        '<div class="container"><p>Fallback content</p></div>',
        "Fallback content",
        "container",
    ),
    # 4. col-8 takes priority over col-lg-9 when both are present
    (
        '<div class="col-8"><p>Primary</p></div><div class="col-lg-9"><p>Secondary</p></div>',
        "Primary",
        "col-8",
    ),
    # 5. No matching div → returns empty string
    (
        '<div class="col-12"><p>Irrelevant</p></div>',
        "",
        None,
    ),
])
def test_extract_page_content_container(html, expected_content, expected_class):
    soup = BeautifulSoup(html, "lxml")
    result = extract_page_content_container(soup)
 
    if expected_class is None:
        assert result == ""
    else:
        assert isinstance(result, str)
        assert expected_content in result
        assert expected_class in result