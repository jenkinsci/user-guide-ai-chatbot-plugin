import pytest
from data.collection.reddit_threads.models import Section, Author, Comment, ThreadDetails
from data.collection.reddit_threads.reddit_threads_utils import (
    get_subreddit_page_url, 
    parse_reddit_datetime,
    extract_integer, 
    build_thread_tree,
    build_thread_trees,
    export_threads_to_json
)
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import Optional, List
import json

@pytest.mark.parametrize("subreddit, section, expected", [
    # 1. Default section (Hot) → no trailing slash, no section in path
    ("python", Section.Hot, "https://old.reddit.com/r/python"),
 
    # 2. New section → section value appended with trailing slash
    ("python", Section.New, "https://old.reddit.com/r/python/new/"),
 
    # 3. Rising section
    ("MachineLearning", Section.Rising, "https://old.reddit.com/r/MachineLearning/rising/"),
 
    # 4. Controversial section
    ("worldnews", Section.Controversial, "https://old.reddit.com/r/worldnews/controversial/"),
 
    # 5. Top section
    ("programming", Section.Top, "https://old.reddit.com/r/programming/top/"),
])
def test_get_subreddit_page_url(subreddit, section, expected):
    assert get_subreddit_page_url(subreddit, section) == expected
 
 
def test_get_subreddit_page_url_default_section():
    """Calling without section argument defaults to Hot."""
    assert get_subreddit_page_url("python") == "https://old.reddit.com/r/python"


def make_time_tag(datetime_attr: str | None):
    if datetime_attr is None:
        return BeautifulSoup("<time>no attr</time>", "lxml").find("time")
    return BeautifulSoup(f'<time datetime="{datetime_attr}">label</time>', "lxml").find("time")
 
 
 
@pytest.mark.parametrize("text, expected", [
    # 1. Standard "N points" format
    ("14 points", 14),
 
    # 2. Number with thousands comma separator
    ("1,234 votes", 1234),
 
    # 3. Negative number
    ("-42 points", -42),
 
    # 4. Empty string → 0
    ("", 0),
 
    # 5. No digits at all → 0
    ("no numbers here", 0),
])
def test_extract_integer(text, expected):
    assert extract_integer(text) == expected
 
 
 
@pytest.mark.parametrize("datetime_attr, expected", [
    # 1. Valid ISO datetime (naive)
    ("2024-06-15T10:30:00", datetime(2024, 6, 15, 10, 30, 0)),
 
    # 2. Valid ISO datetime with UTC timezone offset
    ("2024-01-01T00:00:00+00:00", datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
 
    # 3. No datetime attribute on the tag → None
    (None, None),
 
    # 4. Malformed datetime string → None
    ("not-a-datetime", None),
 
    # 5. Date only, no time component — valid ISO format
    ("2024-06-15", datetime(2024, 6, 15)),
])
def test_parse_reddit_datetime(datetime_attr, expected):
    tag = make_time_tag(datetime_attr)
    result = parse_reddit_datetime(tag)
    assert result == expected
 
 
def test_parse_reddit_datetime_none_element():
    """Passing None directly (no tag at all) → returns None."""
    assert parse_reddit_datetime(None) is None


AUTHOR = Author(username="user1", id="u_001")
 

def make_comment(cid: str, parent_id: Optional[str] = None, content: str = "text") -> Comment:
    return Comment(
        id=cid,
        author=AUTHOR,
        content=content,
        points=1,
        create_date=None,
        parent_id=parent_id,
    )
 

def make_thread(tid: str, comments: List[Comment], title: str = "Thread") -> ThreadDetails:
    return ThreadDetails(
        id=tid, title=title, content="OP", author=AUTHOR,
        subreddit="python", comments=comments,
        comments_qty=len(comments), points=10,
        create_date=datetime(2024, 1, 1),
    )
 
 
def flatten(comments: list) -> dict:
    """Return a flat {id: comment} lookup from a tree of comment dicts."""
    result = {}
    for c in comments:
        result[c['id']] = c
        result.update(flatten(c.get('replies', [])))
    return result
 
 
@pytest.mark.parametrize("comments, expected_root_count, expected_replies", [
    # 1. All top-level comments (parent_id = t3_) → flat tree
    (
        [make_comment("t1_c1", "t3_abc"), make_comment("t1_c2", "t3_abc")],
        2,
        {"t1_c1": 0, "t1_c2": 0},
    ),
    # 2. One reply nested under a top-level comment
    (
        [make_comment("t1_c1", "t3_abc"), make_comment("t1_c2", "t1_c1")],
        1,
        {"t1_c1": 1, "t1_c2": 0},
    ),
    # 3. Deep chain: t1_c1 → t1_c2 → t1_c3
    (
        [make_comment("t1_c1", "t3_abc"), make_comment("t1_c2", "t1_c1"), make_comment("t1_c3", "t1_c2")],
        1,
        {"t1_c1": 1, "t1_c2": 1, "t1_c3": 0},
    ),
    # 4. Reply whose parent is missing → fallback to root
    (
        [make_comment("t1_c2", "t1_missing")],
        1,
        {"t1_c2": 0},
    ),
    # 5. No comments at all → empty tree, thread fields preserved
    (
        [],
        0,
        {},
    ),
])
def test_build_thread_tree(comments, expected_root_count, expected_replies):
    thread = make_thread("t3_abc",comments)
    result = build_thread_tree(thread)
 
    assert len(result['comments']) == expected_root_count
 
    all_comments = flatten(result['comments'])
    for cid, expected_reply_count in expected_replies.items():
        assert cid in all_comments
        assert len(all_comments[cid]['replies']) == expected_reply_count
 
 
def test_build_thread_tree_returns_dict():
    """build_thread_tree must return a dict (serialized via asdict), not a ThreadDetails."""
    result = build_thread_tree(make_thread("t3_abc", []))
    assert isinstance(result, dict)
 
 
def test_build_thread_tree_preserves_thread_fields():
    """Non-comment fields (title, subreddit, points…) must be preserved in the output."""
    thread = make_thread("t3_abc", [], "Test Thread")
    result = build_thread_tree(thread)
    assert result['title'] == "Test Thread"
    assert result['subreddit'] == "python"
    assert result['points'] == 10
 
 
def test_build_thread_tree_every_comment_has_replies_key():
    """Every comment dict in the result must have a 'replies' key."""
    comments = [make_comment("t1_c1", "t3_abc"), make_comment("t1_c2", "t1_c1")]
    result = build_thread_tree(make_thread("t3_abc", comments))
 
    def check(comments_list):
        for c in comments_list:
            assert 'replies' in c
            check(c['replies'])
 
    check(result['comments'])


@pytest.mark.parametrize("threads, expected_length, expected_root_counts", [
    # 1. Single thread, no comments → length 1, empty comment tree
    (
        [make_thread("t3_abc", [])],
        1, [0],
    ),
    # 2. Multiple threads → length matches, each processed independently
    (
        [make_thread("t3_abc", [make_comment("t1_c1", "t3_abc")]),
         make_thread("t3_abc", [make_comment("t1_c2", "t3_abc"), make_comment("t1_c3", "t3_abc")])],
        2, [1, 2],
    ),
    # 3. Thread with nested reply → root count is 1, reply nested inside
    (
        [make_thread("t3_abc", [make_comment("t1_c1", "t3_t1"), make_comment("t1_c2", "t1_c1")])],
        1, [1],
    ),
    # 4. Empty list → length 0, threads array empty
    (
        [], 0, [],
    ),
    # 5. Two threads with the same structure → both processed correctly
    (
        [make_thread("t3_abc", [make_comment("t1_c1", "t3_t1")]),
         make_thread("t3_abc", [make_comment("t1_c2", "t3_t2")])],
        2, [1, 1],
    ),
])
def test_build_thread_trees(threads, expected_length, expected_root_counts):
    result = build_thread_trees(threads)
 
    assert result['length'] == expected_length
    assert len(result['threads']) == expected_length
 
    for thread_dict, expected_roots in zip(result['threads'], expected_root_counts):
        assert len(thread_dict['comments']) == expected_roots
 
 
def test_build_thread_trees_returns_dict_with_required_keys():
    """Result must always contain 'threads' and 'length' keys."""
    result = build_thread_trees([])
    assert 'threads' in result
    assert 'length' in result
 
 
 
@pytest.mark.parametrize("threads, expected_length, expected_titles", [
    # 1. Single thread → file written, length and title correct
    (
        [make_thread("t3_abc", [], title="First")],
        1, ["First"],
    ),
    # 2. Multiple threads → all titles preserved in order
    (
        [make_thread("t3_abc", [], title="Alpha"), make_thread("t3_abc", [], title="Beta")],
        2, ["Alpha", "Beta"],
    ),
    # 3. Empty list → file written with length 0
    (
        [], 0, [],
    ),
    # 4. Thread with datetime create_date → serialized to ISO string without error
    (
        [make_thread("t3_abc", [], title="Dated")],
        1, ["Dated"],
    ),
    # 5. Thread with nested comments → full tree written to file
    (
        [make_thread("t3_abc", [make_comment("t1_c1", "t3_abc"), make_comment("t1_c2", "t1_c1")], title="Nested")],
        1, ["Nested"],
    ),
])
def test_export_threads_to_json(tmp_path, threads, expected_length, expected_titles):
    file_path = str(tmp_path / "output.json")
    export_threads_to_json(threads, file_path)
 
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
 
    assert data['length'] == expected_length
    assert len(data['threads']) == expected_length
    assert [t['title'] for t in data['threads']] == expected_titles
