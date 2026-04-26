from dataclasses import dataclass, field
import numpy as np


@dataclass
class Article:
    title: str
    content: str
    url: str = ""
    topic: str = ""
    summary: str = ""
    score: float = field(default=None, repr=False)
    embedding: np.ndarray = field(default=None, repr=False)
