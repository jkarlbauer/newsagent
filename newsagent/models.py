from dataclasses import dataclass, field
import numpy as np


@dataclass
class Article:
    title: str
    content: str
    url: str = ""
    topic: str = ""
    summary: str = ""
    embedding: np.ndarray = field(default=None, repr=False)
