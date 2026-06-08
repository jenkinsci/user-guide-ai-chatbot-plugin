from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


@dataclass
class SearchFilters:
    """Stores filters for searching topics"""
    category_slug: str
    subcategory_slug: str | None
    tag_slug: str | None


class TopicSummary(BaseModel):
    """Stores basic information of a topic fetched from the category/tag lists."""
    id: int
    title: str
    slug: str
    reply_count: int
    created_at: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopicSummary":
        # Extracts specific keys safely with default fallbacks
        return cls(
            id=data.get("id", 0),
            title=data.get("title", "Unknown Title"),
            slug=data.get("slug", ""),
            reply_count=data.get("reply_count", 0),
            created_at=data.get("created_at", "")
        )


class TopicCollection(BaseModel):
    """Container for the entire list of topics fetched across all pages."""
    topics: List[TopicSummary] = field(default_factory=list)
    
    def add_topic(self, topic_data: Dict[str, Any]) -> None:
        """Parses a raw API dictionary and adds it to the collection."""
        new_topic = TopicSummary.from_dict(topic_data)
        self.topics.append(new_topic)
        
    def get_total_count(self) -> int:
        return len(self.topics)


class Post(BaseModel):
    """Stores details of an individual message, supporting tree-like structures."""
    id: int
    post_number: int
    username: str
    content: str
    is_solution: bool
    reply_to_post_number: Optional[int]
    created_at: str
    reactions: list[dict]
    url: str
    
    # Recursive field to hold child posts (replies to this specific post)
    replies: List["Post"] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Post":
        return cls(
            id=data.get("id", 0),
            post_number=data.get("post_number", 0),
            username=data.get("username", "Unknown"),
            content=data.get("cooked", ""),
            created_at=data.get("created_at", ""),
            is_solution=data.get("accepted_answer", False),
            reply_to_post_number=data.get("reply_to_post_number"),
            reactions=data.get("reactions", []),
            url=data.get("post_url", "")
        )


class SolutionPost(BaseModel):
    """
    Data model representing a solution post in Discourse.
    Validates and stores the JSON payload structure.
    """
    id: int
    username: str
    created_at: str
    content: str
    topic_id: int
    url: str
    reactions: list[dict]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SolutionPost":
        return cls(
            id=data.get("id", 0),
            username=data.get("username", "Unknown"),
            content=data.get("cooked", ""),
            topic_id=data.get("topic_id", ""),
            url=data.get("url", ""),
            created_at=data.get("created_at", ""),
            reactions=data.get("reactions", [])
        )


class TopicDetails(BaseModel):
    """Stores the topic details. 'posts' will contain only root-level posts."""
    topic_id: int
    title: str
    posts: List[Post] = field(default_factory=list)
    solutions: List[SolutionPost] = field(default_factory=list)
