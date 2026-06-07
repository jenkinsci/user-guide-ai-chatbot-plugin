from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import Enum

class Section(Enum):
    Hot = "hot"
    New = "new"
    Rising = "rising"
    Controversial = "controversial"
    Top = "top"

@dataclass
class ThreadPreview:
    id: str
    title: str

@dataclass
class Author:
    username: str
    id: Optional[str] = None  

@dataclass
class Comment:
    id: str
    author: Author
    content: str
    points: int
    create_date: Optional[datetime]
    parent_id: Optional[str] = None  

@dataclass
class ThreadDetails:
    id: str
    title: str
    content: str
    author: Author         
    subreddit: str         
    comments: List[Comment]
    comments_qty: int
    points: int
    create_date: Optional[datetime]