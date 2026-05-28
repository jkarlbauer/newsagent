import colorsys
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
import plotly.graph_objects as go
from plotly.subplots import make_subplots

N_CLUSTERS = 5

CLUSTER_PALETTE = [
    (60/360,  0.90),
    (0/360,   0.90),
    (120/360, 0.65),
    (240/360, 0.90),
    (270/360, 0.80),
    (25/360,  0.55),
    (180/360, 0.75),
    (0/360,   0.00),
]


def _rgb(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"


def _reductions(embeddings: np.ndarray) -> dict:
    n = len(embeddings)
    result = {"PCA": PCA(n_components=2).fit_transform(embeddings)}
    if n >= 6:
        result["t-SNE"] = TSNE(
            n_components=2, perplexity=min(30, n - 1), random_state=42
        ).fit_transform(embeddings)
    try:
        import umap
        result["UMAP"] = umap.UMAP(n_components=2, random_state=42).fit_transform(embeddings)
    except ImportError:
        pass
    return result


def _color_schemes(articles: list, cluster_labels: np.ndarray,
                   proximity: np.ndarray, score_norm: np.ndarray) -> list:
    topics = list(dict.fromkeys(a["topic"] for a in articles))

    def cluster_color(i):
        h, s = CLUSTER_PALETTE[int(cluster_labels[i]) % len(CLUSTER_PALETTE)]
        return _rgb(h, 0.50, s)

    def topic_color(i):
        idx = topics.index(articles[i]["topic"]) if articles[i]["topic"] in topics else 0
        h, s = CLUSTER_PALETTE[idx % len(CLUSTER_PALETTE)]
        return _rgb(h, 0.50, s)

    def proximity_color(i):
        return _rgb(210/360, 0.18 + float(proximity[i]) * 0.58, 0.85)

    def score_color(i):
        return _rgb(150/360, 0.20 + float(score_norm[i]) * 0.50, 0.80)

    def selected_color(i):
        return _rgb(120/360, 0.45, 0.70) if articles[i].get("selected") else _rgb(0, 0.70, 0.0)

    return [
        ("Clusters",   cluster_color),
        ("Topic",      topic_color),
        ("Selected",   selected_color),
        ("Score",      score_color),
        ("Proximity",  proximity_color),
    ]


def generate_plot(articles: list, title: str = "") -> str:
    n = len(articles)
    if n < 3:
        return "<p>Not enough articles to generate a plot.</p>"

    embeddings = np.array([a["embedding"] for a in articles])

    mid_dim = min(50, embeddings.shape[1], n - 1)
    pca_mid = PCA(n_components=mid_dim).fit_transform(embeddings)
    k = min(N_CLUSTERS, n)
    cluster_labels = KMeans(n_clusters=k, random_state=42, n_init="auto").fit_predict(pca_mid)

    centroid = embeddings.mean(axis=0)
    dists = np.linalg.norm(embeddings - centroid, axis=1)
    proximity = 1.0 - (dists - dists.min()) / (dists.max() - dists.min() or 1.0)

    scores = np.array([a["score"] for a in articles], dtype=float)
    score_norm = (scores - scores.min()) / (scores.max() - scores.min() or 1.0)

    reductions = _reductions(embeddings)
    color_schemes = _color_schemes(articles, cluster_labels, proximity, score_norm)

    methods = list(reductions.keys())
    n_rows, n_cols = len(color_schemes), len(methods)

    subplot_titles = [
        f"{scheme} — {method}"
        for scheme, _ in color_schemes
        for method in methods
    ]

    fig = make_subplots(rows=n_rows, cols=n_cols,
                        subplot_titles=subplot_titles,
                        vertical_spacing=0.06)

    hover = [
        f"<b>{a['title'][:80]}</b><br>"
        f"Topic: {a['topic']} | Cluster: {cluster_labels[i]}<br>"
        f"Score: {a['score']} | Coverage: {round(a['coverage'] * 100)}%<br>"
        f"Selected: {'yes' if a.get('selected') else 'no'}"
        for i, a in enumerate(articles)
    ]

    for row, (_, color_fn) in enumerate(color_schemes, 1):
        colors = [color_fn(i) for i in range(n)]
        for col, (method, coords) in enumerate(reductions.items(), 1):
            fig.add_trace(
                go.Scatter(
                    x=coords[:, 0], y=coords[:, 1],
                    mode="markers",
                    marker=dict(size=7, color=colors),
                    text=hover,
                    hovertemplate="%{text}<extra></extra>",
                    showlegend=False,
                ),
                row=row, col=col,
            )

    fig.update_layout(
        title=title,
        height=280 * n_rows + 100,
        hoverlabel=dict(bgcolor="white", font_size=13),
    )

    return fig.to_html(full_html=True)
