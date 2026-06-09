import os, json, pytest
from typing import List
from data.collection.discourse_topics.models import (
    SearchFilters,
    Post,
    TopicDetails,
    SolutionPost,
)
from data.collection.discourse_topics.discourse_topics_utils import (
    build_discourse_endpoint,
    build_topic_tree,
    export_topics_to_json,
)

BASE = "https://discourse.example.com"


@pytest.mark.parametrize(
    "category_slug, subcategory_slug, tag_slug, expected",
    [
        # 1. No filters → global latest
        (None, None, None, f"{BASE}/latest.json"),
        # 2. Category only → category endpoint
        ("support", None, None, f"{BASE}/c/support.json"),
        # 3. Category + subcategory → nested category endpoint
        ("support", "billing", None, f"{BASE}/c/support/billing.json"),
        # 4. Tag only → global tag endpoint
        (None, None, "python", f"{BASE}/tag/python.json"),
        # 5. Tag + category, no subcategory → tag scoped to category
        ("support", None, "python", f"{BASE}/tags/c/support/python.json"),
        # 6. Tag + category + subcategory → fully scoped tag endpoint
        ("support", "billing", "python", f"{BASE}/tags/c/support/billing/python.json"),
        # 7. Tag + subcategory but no category → subcategory ignored, global tag used
        (None, "billing", "python", f"{BASE}/tag/python.json"),
    ],
)
def test_build_discourse_endpoint(category_slug, subcategory_slug, tag_slug, expected):
    filters = SearchFilters(
        category_slug=category_slug,
        subcategory_slug=subcategory_slug,
        tag_slug=tag_slug,
    )
    assert build_discourse_endpoint(BASE, filters) == expected


def test_base_url_trailing_slash_stripped():
    """Trailing slash on base_url must not produce double slashes in the result."""
    filters = SearchFilters(
        category_slug="support", subcategory_slug=None, tag_slug=None
    )
    result = build_discourse_endpoint("https://discourse.example.com/", filters)
    assert result == "https://discourse.example.com/c/support.json"
    assert "//" not in result.replace("https://", "")


def make_post(post_number: int, reply_to: int | None = None, **kwargs) -> dict:
    return {
        "id": post_number,
        "post_number": post_number,
        "username": kwargs.get("username", "user"),
        "cooked": kwargs.get("cooked", f"Content of post {post_number}"),
        "created_at": "2024-01-01T00:00:00Z",
        "accepted_answer": kwargs.get("accepted_answer", False),
        "reply_to_post_number": reply_to,
        "reactions": [],
        "post_url": f"/t/topic/1/{post_number}",
    }


def flatten(posts: List[Post]) -> List[Post]:
    """Recursively flatten a post tree into a list."""
    result = []
    for post in posts:
        result.append(post)
        result.extend(flatten(post.replies))
    return result


@pytest.mark.parametrize(
    "raw_posts, expected_root_count, expected_replies",
    [
        # 1. All top-level posts (no reply_to) → flat tree
        (
            [make_post(1), make_post(2), make_post(3)],
            3,
            {1: 0, 2: 0, 3: 0},
        ),
        # 2. One reply nested under post 1
        (
            [make_post(1), make_post(2, reply_to=1)],
            1,
            {1: 1, 2: 0},
        ),
        # 3. Deep chain: post 1 → post 2 → post 3
        (
            [make_post(1), make_post(2, reply_to=1), make_post(3, reply_to=2)],
            1,
            {1: 1, 2: 1, 3: 0},
        ),
        # 4. Reply whose parent is missing → falls back to root
        (
            [make_post(2, reply_to=99)],
            1,
            {2: 0},
        ),
        # 5. Multiple replies to the same parent
        (
            [make_post(1), make_post(2, reply_to=1), make_post(3, reply_to=1)],
            1,
            {1: 2, 2: 0, 3: 0},
        ),
    ],
)
def test_build_topic_tree(raw_posts, expected_root_count, expected_replies):
    result = build_topic_tree(raw_posts)

    assert len(result) == expected_root_count

    post_lookup = {p.post_number: p for p in flatten(result)}

    for post_number, expected_reply_count in expected_replies.items():
        assert post_number in post_lookup
        assert len(post_lookup[post_number].replies) == expected_reply_count


def test_build_topic_tree_empty_input():
    """Empty list → returns empty list without errors."""
    assert build_topic_tree([]) == []


def test_build_topic_tree_returns_post_instances():
    """Each root element must be a Post instance."""
    result = build_topic_tree([make_post(1), make_post(2)])
    assert all(isinstance(p, Post) for p in result)


def test_build_topic_tree_from_dict_field_mapping():
    """from_dict must correctly map raw API fields to Post attributes."""
    raw = {
        "id": 7,
        "post_number": 3,
        "username": "alice",
        "cooked": "<p>Hello</p>",
        "created_at": "2024-06-01T12:00:00Z",
        "accepted_answer": True,
        "reply_to_post_number": None,
        "reactions": [{"id": "heart", "count": 2}],
        "post_url": "/t/topic/1/3",
    }
    post = Post.from_dict(raw)
    assert post.id == 7
    assert post.post_number == 3
    assert post.username == "alice"
    assert post.content == "<p>Hello</p>"
    assert post.is_solution is True
    assert post.reactions == [{"id": "heart", "count": 2}]
    assert post.url == "/t/topic/1/3"


def make_topic(topic_id: int, title: str = "Test Topic") -> TopicDetails:
    return TopicDetails(
        topic_id=topic_id,
        title=title,
        posts=[],
        solutions=[],
    )


@pytest.mark.parametrize(
    "topics, expected_length, expected_titles",
    [
        # 1. Single topic → length 1, title preserved
        (
            [make_topic(1, "First Topic")],
            1,
            ["First Topic"],
        ),
        # 2. Multiple topics → length matches, all titles preserved
        (
            [
                make_topic(1, "Topic A"),
                make_topic(2, "Topic B"),
                make_topic(3, "Topic C"),
            ],
            3,
            ["Topic A", "Topic B", "Topic C"],
        ),
        # 3. Empty list → length 0, topics array is empty
        (
            [],
            0,
            [],
        ),
        # 4. Topic with unicode title → written correctly (ensure_ascii=False)
        (
            [make_topic(1, "Pythön & Rüst")],
            1,
            ["Pythön & Rüst"],
        ),
        # 5. Topic with posts and solutions → nested data preserved
        (
            [
                TopicDetails(
                    topic_id=99,
                    title="With Content",
                    posts=[
                        Post(
                            id=1,
                            post_number=1,
                            username="alice",
                            content="Hello",
                            is_solution=False,
                            reply_to_post_number=None,
                            created_at="2024-01-01",
                            reactions=[],
                            url="/t/1",
                        )
                    ],
                    solutions=[
                        SolutionPost(
                            id=1,
                            content="The answer",
                            reactions=[],
                            created_at="",
                            topic_id=1,
                            url="",
                            username="mario",
                        )
                    ],
                )
            ],
            1,
            ["With Content"],
        ),
    ],
)
def test_export_topics_to_json(tmp_path, topics, expected_length, expected_titles):
    file_path = str(tmp_path / "output.json")

    export_topics_to_json(topics, file_path)

    assert os.path.exists(file_path)

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["length"] == expected_length
    assert len(data["topics"]) == expected_length

    actual_titles = [t["title"] for t in data["topics"]]
    assert actual_titles == expected_titles


def test_export_topics_to_json_valid_json_structure(tmp_path):
    """Output file must be valid JSON with 'topics' and 'length' keys."""
    file_path = str(tmp_path / "output.json")
    export_topics_to_json([make_topic(1)], file_path)

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    assert "topics" in data
    assert "length" in data
