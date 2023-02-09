from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Podcast:
    _id: str
    title: str
    host: str
    year: int
    cast: list[str] = field(default_factory=list)
    series: list[str] = field(default_factory=list)
    last_watched: datetime = None
    rating: int = 0
    tags: list[str] = field(default_factory=list)
    description: str = None
    video_link: str = None

@dataclass
class User:
    _id: str
    email: str
    password: str
    Podcasts:list[str] = field(default_factory=list)