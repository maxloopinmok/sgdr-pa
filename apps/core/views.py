from django.http import HttpResponse
from django.shortcuts import render


# Blogger JSON-P feed URL used by the client-side renderer in
# templates/commentary.html. Kept on the server only so the template
# can pull it via context — no server-side fetch happens here. This
# avoids PA's outbound-traffic restrictions (free tier requires the
# proxy at proxy.server:3128 for any Python-driven outbound HTTP).
COMMENTARY_FEED_JSONP_URL = (
    "https://somethingusefulforinvestors.blogspot.com/feeds/posts/default"
    "?alt=json-in-script&max-results=1&callback=sgdrRenderLatestPost"
)
COMMENTARY_BLOG_URL = "https://somethingusefulforinvestors.blogspot.com/"


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
    """Render the page shell; the latest post is fetched client-side.

    The browser pulls Blogger's JSON-P feed directly from Google. This
    avoids two problems with server-side scraping on PA:
      1. PA's free tier requires outbound traffic via proxy.server:3128
         (urllib doesn't use it by default), and even then only a curated
         whitelist of hosts is reachable.
      2. Server-side caching would lag behind freshly-published posts.
    """
    return render(request, "commentary.html", {
        "feed_jsonp_url": COMMENTARY_FEED_JSONP_URL,
        "blog_url": COMMENTARY_BLOG_URL,
    })
