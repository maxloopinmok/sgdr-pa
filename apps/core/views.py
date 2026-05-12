import logging
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


# Atom feed for Max's Blogger. Atom (not RSS) so we get the full entry
# content, not just a summary.
COMMENTARY_FEED_URL = (
    "https://somethingusefulforinvestors.blogspot.com/feeds/posts/default"
)
COMMENTARY_BLOG_URL = "https://somethingusefulforinvestors.blogspot.com/"
COMMENTARY_CACHE_KEY = "stocks_commentary_latest_v1"
COMMENTARY_CACHE_TTL_SECONDS = 15 * 60  # 15 min


def landing(request):
    return render(request, "landing.html")


def about(request):
    return render(request, "about.html")


def disclaimer(request):
    return render(request, "legal/disclaimer.html")


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")


def robots_txt(request):
    return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")


def commentary(request):
    """Render the latest post from Max's Blogger as an embedded page.

    Cached for ~15 min so we don't hammer Blogger on every page load.
    On feed-fetch failure (Blogger down, network blip), shows a friendly
    fallback that links out to the live blog.
    """
    post = cache.get(COMMENTARY_CACHE_KEY)
    if post is None:
        try:
            post = _fetch_latest_blogger_post(COMMENTARY_FEED_URL)
        except Exception:
            logger.exception("commentary: failed to fetch %s",
                             COMMENTARY_FEED_URL)
            post = None
        if post:
            cache.set(COMMENTARY_CACHE_KEY, post, COMMENTARY_CACHE_TTL_SECONDS)

    return render(request, "commentary.html", {
        "post": post,
        "blog_url": COMMENTARY_BLOG_URL,
    })


def _fetch_latest_blogger_post(feed_url: str) -> dict | None:
    """Return a dict for the most-recent Atom entry, or ``None`` if missing.

    Keys: ``title``, ``link``, ``content_html`` (raw HTML — trusted, since
    it's the site owner's own blog), ``published`` (a date object or None).
    """
    req = urllib.request.Request(
        feed_url,
        headers={
            "User-Agent": "sgdr-commentary/1.0 (+https://dividendsandreports.pythonanywhere.com/)",
            "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("commentary: feed fetch failed: %s", exc)
        return None

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        logger.exception("commentary: feed XML parse failed")
        return None

    entry = root.find("atom:entry", ns)
    if entry is None:
        return None

    title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
    content_el = entry.find("atom:content", ns)
    content_html = (content_el.text or "") if content_el is not None else ""

    link = ""
    for link_el in entry.findall("atom:link", ns):
        if link_el.get("rel") == "alternate" and link_el.get("type", "").startswith("text/html"):
            link = link_el.get("href", "")
            break

    published_raw = entry.findtext("atom:published", default="",
                                   namespaces=ns) or ""
    published_dt = None
    if published_raw:
        try:
            # Atom: "2026-05-11T12:34:56.000+08:00". fromisoformat handles
            # this directly from 3.11+.
            published_dt = datetime.fromisoformat(published_raw)
        except ValueError:
            published_dt = None

    return {
        "title": title,
        "link": link,
        "content_html": content_html,
        "published": published_dt,
    }
