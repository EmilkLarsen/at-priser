"""Hagebau.at (EUR, Austria) — sitemap/category/?index=N pages embed
product URLs; product pages carry itemprop price + sku (same as bauhaus.dk)."""
import re
from common import get, sane_price, valid_ean, write_jsonl, scrape_urls

BASE = "https://www.hagebau.at"
OUT = "data/latest/hagebau_at.jsonl"


def fetch_url_list(limit=None):
    """Category sitemaps -> category pages -> product URLs from HTML."""
    idx = get(f"{BASE}/sitemap.xml")
    cat_pages = re.findall(r"<loc>([^<]+sitemap/category/\?index=\d+)</loc>", idx)
    urls = []
    seen = set()
    for cp in cat_pages[:8]:
        try:
            xml = get(cp)
        except Exception:
            continue
        cats = re.findall(r"<loc>(https://www\.hagebau\.at/[^<]+)</loc>", xml)
        for cat in cats[:5]:
            try:
                ch = get(cat)
            except Exception:
                continue
            us = re.findall(r'https://[^\s"<]+/p/\d+', ch)

            for u in us:
                if u not in seen:
                    seen.add(u)
                    urls.append(u)
            if limit and len(urls) >= limit:
                break
        if limit and len(urls) >= limit:
            break
    return urls[:limit] if limit else urls

def _old_fetch(limit=None):
    idx = get(f"{BASE}/sitemap.xml")
    cat_pages = re.findall(r"<loc>([^<]+sitemap/category/\?index=\d+)</loc>", idx)
    urls = []
    for cp in cat_pages:
        try:
            xml = get(cp)
        except Exception:
            continue
        us = re.findall(r"<loc>(https://www\.hagebau\.at/[^<]+/p/\d+)</loc>", xml)
        urls.extend(us)
        if limit and len(urls) >= limit:
            break
    return urls[:limit] if limit else urls


def handle(u, html):
    m = re.search(r'itemprop="price" content="([0-9.]+)"', html)
    if not m:
        return []
    p = sane_price(float(m.group(1)))
    if not p:
        return []
    sk = re.search(r'itemprop="sku" content="([^"]+)"', html)
    t = re.search(r"<title[^>]*>([^<]+)</title>", html)
    name = (t.group(1).split("|")[0].strip() if t else u.rsplit("/", 1)[-1])
    return [{
        "chain": "hagebau_at",
        "country": "at",
        "currency": "EUR",
        "sku": sk.group(1) if sk else None,
        "ean": None,
        "name": name,
        "url": u,
        "price": p,
        "in_stock": None,
        "image": None,
    }]


def scrape(limit=None):
    return scrape_urls(fetch_url_list(limit), handle)


if __name__ == "__main__":
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = scrape(lim)
    write_jsonl(OUT, rows)
    print("hagebau_at: %d products -> %s" % (len(rows), OUT))
