import pytest
from bs4 import BeautifulSoup, Tag
from data.collection.plugin_docs.plugin_docs_utils import get_jenkins_version_req_and_release_date, get_version


def make_tag(html: str) -> Tag | None:
    return BeautifulSoup(html, "lxml").body
 
 
@pytest.mark.parametrize("html, expected", [
    # 1. Standard h5 with label and version → version extracted
    ("<aside><h5>Version 1.2.3</h5></aside>", "1.2.3"),
 
    # 2. Different version number
    ("<aside><h5>Version 42.0.0</h5></aside>", "42.0.0"),
 
    # 3. No h5 element → returns None
    ("<aside><h6>Version 1.0.0</h6></aside>", None),
 
    # 4. Empty sidebar → returns None
    ("<aside></aside>", None),
 
    # 5. h5 present but nested inside another tag → still found
    ("<aside><div><h5>Version 3.1.4</h5></div></aside>", "3.1.4"),
])
def test_get_version(html, expected):
    sidebar = make_tag(html)

    if sidebar: 
        result = get_version(sidebar)
        assert result == expected


@pytest.mark.parametrize("html, expected_jenkins_ver, expected_datetime", [
    # 1. Both time and jenkins version present
    (
        """<aside>
            <div><time datetime="2024-06-15">June 15, 2024</time></div>
            <div>Requires Jenkins 2.387.3</div>
        </aside>""",
        "2.387.3", "2024-06-15",
    ),
    # 2. No time element → datetime is None, jenkins version still extracted
    (
        """<aside>
            <div><span>No date here</span></div>
            <div>Requires Jenkins 2.100.0</div>
        </aside>""",
        "2.100.0", None,
    ),
    # 3. Different jenkins version format
    (
        """<aside>
            <div><time datetime="2023-01-01">Jan 1, 2023</time></div>
            <div>Requires Jenkins 2.000.1</div>
        </aside>""",
        "2.000.1", "2023-01-01",
    ),
    # 4. datetime attribute with full ISO timestamp
    (
        """<aside>
            <div><time datetime="2024-06-15T10:30:00Z">June 15, 2024</time></div>
            <div>Requires Jenkins 2.440.0</div>
        </aside>""",
        "2.440.0", "2024-06-15T10:30:00Z",
    ),
    # 5. Jenkins version with extra whitespace in text
    (
        """<aside>
            <div><time datetime="2024-03-10">Mar 10, 2024</time></div>
            <div>  Requires Jenkins 2.375.0  </div>
        </aside>""",
        "2.375.0", "2024-03-10",
    ),
])
def test_get_jenkins_version_req_and_release_date(
    html, expected_jenkins_ver, expected_datetime
):
    sidebar = make_tag(html)

    if sidebar: 
        jenkins_ver, dt = get_jenkins_version_req_and_release_date(sidebar)
        assert jenkins_ver == expected_jenkins_ver
        assert dt == expected_datetime
      