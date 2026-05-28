def _escape_html(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def coverage_label(coverage: float) -> str:
    pct = coverage * 100
    if pct >= 10:
        return "High"
    if pct >= 5:
        return "Medium"
    return "Low"


def digest_header(articles: list) -> str:
    max_coverage = max(a.coverage for a in articles)
    pct = max_coverage * 100
    if pct >= 10:
        return "🔥 <b>High activity today</b> — major stories are trending across multiple sources."
    if pct >= 5:
        return "📰 <b>Moderate activity today</b> — some notable stories are picking up traction."
    return "🌤 <b>Quiet day today</b> — lighter coverage across your topics."


def format_article(article) -> str:
    title = _escape_html(article.title)
    summary = _escape_html(article.summary)
    return f"<b>{title}</b>\nCoverage: {coverage_label(article.coverage)} ({round(article.coverage * 100)}%)\n{summary}\n{article.url}"
