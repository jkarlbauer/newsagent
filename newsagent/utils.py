import numpy as np


def centroid(articles):
    matrix = np.stack([a.embedding for a in articles])
    return matrix.mean(axis=0)


def cosine_distance(a, b):
    a = a / (np.linalg.norm(a) + 1e-9)
    b = b / (np.linalg.norm(b) + 1e-9)
    return 1 - float(a @ b)


def closest_to_center(articles, n=5):
    center = centroid(articles)
    return sorted(articles, key=lambda a: cosine_distance(a.embedding, center))[:n]
