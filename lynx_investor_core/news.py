"""News aggregation (Yahoo Finance + Google News RSS).

Each agent passes ``sector_keyword`` so Google News returns relevant results —
e.g. ``"mining stock"`` for the basic-materials agent, ``"energy stock"`` for
the energy agent.
"""

from __future__ import annotations

from typing import Optional

import feedparser
import requests
import yfinance as yf

from lynx_investor_core.models import NewsArticle
from lynx_investor_core.storage import get_news_dir, save_json, save_text


def fetch_news_yfinance(ticker: str) -> list[NewsArticle]:
    try:
        t = yf.Ticker(ticker)
    except Exception:
        return []
    articles: list[NewsArticle] = []
    try:
        news_items = t.news or []
    except Exception:
        news_items = []
    for item in news_items:
        content = item.get("content", item) if isinstance(item, dict) else item
        if isinstance(content, dict):
            title = content.get("title", "")
            url = content.get("canonicalUrl", {})
            if isinstance(url, dict):
                url = url.get("url", "")
            elif not isinstance(url, str):
                url = content.get("link", "")
            pub = content.get("pubDate") or content.get("providerPublishTime", "")
            source = content.get("provider", {})
            if isinstance(source, dict):
                source = source.get("displayName", "")
            summary = content.get("summary", "")
        else:
            continue
        articles.append(NewsArticle(title=title, url=url if isinstance(url, str) else "",
                                    published=str(pub), source=source if isinstance(source, str) else "",
                                    summary=summary))
    return articles


def fetch_news_rss(company_name: str, ticker: str, sector_keyword: str = "stock") -> list[NewsArticle]:
    query = f"{company_name} {ticker} {sector_keyword}"
    feed_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en&gl=US&ceid=US:en"
    articles: list[NewsArticle] = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:20]:
            articles.append(NewsArticle(
                title=entry.get("title", ""), url=entry.get("link", ""),
                published=entry.get("published", ""),
                source=entry.get("source", {}).get("title", "") if isinstance(entry.get("source"), dict) else "",
                summary=entry.get("summary", ""),
            ))
    except Exception:
        pass
    return articles


def fetch_all_news(
    ticker: str,
    company_name: Optional[str] = None,
    sector_keyword: str = "stock",
) -> list[NewsArticle]:
    articles: list[NewsArticle] = []
    articles.extend(fetch_news_yfinance(ticker))
    name = company_name or ticker
    rss_news = fetch_news_rss(name, ticker, sector_keyword=sector_keyword)
    existing_titles = {a.title.lower().strip() for a in articles}
    for art in rss_news:
        if art.title.lower().strip() not in existing_titles:
            articles.append(art)
            existing_titles.add(art.title.lower().strip())
    ndir = get_news_dir(ticker)
    save_json(ndir / "news_index.json", [
        {"title": a.title, "url": a.url, "published": a.published, "source": a.source, "summary": a.summary}
        for a in articles
    ])
    return articles


def download_article(ticker: str, article: NewsArticle, user_agent: str = "Mozilla/5.0") -> Optional[str]:
    if not article.url:
        return None
    # Block SSRF / scheme abuse via RSS-sourced URLs before making the request.
    from .urlsafe import is_safe_url
    if not is_safe_url(article.url):
        return None
    ndir = get_news_dir(ticker)
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in article.title)[:60].strip()
    path = ndir / f"{safe_title}.txt"
    try:
        resp = requests.get(article.url, timeout=15, headers={"User-Agent": user_agent}, allow_redirects=False)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)[:50000]
        save_text(path, f"Title: {article.title}\nURL: {article.url}\nPublished: {article.published}\nSource: {article.source}\n\n{text}")
        article.local_path = str(path)
        return str(path)
    except Exception:
        return None
