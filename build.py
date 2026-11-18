#!/usr/bin/env python3
"""Static site builder for «ТатуНаХоду — справочник по тату».
Usage: python3 build.py [--out dist] [--include-drafts]
Reads articles/*.md (YAML-ish front matter), images/<slug>/*, writes static site to dist/.
"""
import re, os, sys, json, shutil, html, datetime, markdown
from zoneinfo import ZoneInfo
TODAY = datetime.datetime.now(ZoneInfo("Europe/Moscow")).date()

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = os.environ.get("SITE_URL", "https://ivansiskov996-oss.github.io/tattoo-spravochnik")
BASE = "/" + SITE_URL.split("://", 1)[1].split("/", 1)[1].strip("/") if SITE_URL.count("/") > 2 else ""
BASE = BASE.rstrip("/")
SITE_NAME = "ТатуНаХоду — справочник по тату"
SITE_DESC = "Практичные ответы о татуировках от московской тату-студии «ТатуНаХоду»: заживление, уход, боль, подготовка к сеансу."
BOOK_URL = "https://t.me/tatunahody"
CHANNEL_URL = "https://t.me/tattoo_na_hodu"
ORG = {"@type": "Organization", "name": "ТатуНаХоду", "url": SITE_URL + "/",
       "sameAs": [BOOK_URL, CHANNEL_URL],
       "address": {"@type": "PostalAddress", "streetAddress": "Нижегородская ул., 5", "addressLocality": "Москва", "addressCountry": "RU"}}

args = sys.argv[1:]
OUT = os.path.join(ROOT, args[args.index("--out") + 1]) if "--out" in args else os.path.join(ROOT, "dist")
INCLUDE_DRAFTS = "--include-drafts" in args

def parse(path):
    s = open(path, encoding="utf-8").read()
    fm, body = re.match(r"---\n(.*?)\n---\n(.*)", s, re.S).groups()
    meta = {}
    for key in ("title", "description", "slug", "date"):
        m = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', fm, re.M)
        meta[key] = m.group(1) if m else ""
    meta["draft"] = bool(re.search(r"^draft:\s*true", fm, re.M))
    meta["keywords"] = re.findall(r"^\s+-\s+(.+)$", fm, re.M)
    meta["body"] = body
    return meta

def faq_pairs(body):
    m = re.search(r"## Частые вопросы\n(.*?)(?=\n---|\n## )", body, re.S)
    if not m: return []
    pairs = re.findall(r"### (.+?)\n\n(.+?)(?=\n### |\Z)", m.group(1).strip() + "\n", re.S)
    clean = lambda t: re.sub(r"[*_`]|\[([^\]]+)\]\([^)]+\)", lambda x: x.group(1) or "", t).strip()
    return [(q.strip(), clean(a)) for q, a in pairs]

def render_body(a):
    body = re.sub(r"<!--.*?-->", "", a["body"], flags=re.S)
    body = re.sub(r"\A\s*# .+\n", "", body, count=1)  # H1 rendered by template
    h = markdown.markdown(body, extensions=["tables", "toc"])
    # images: rewrite paths, add lazy loading, wrap img+caption in <figure>
    def fig(mo):
        alt, src, cap = mo.group(1), mo.group(2), mo.group(3)
        src = src.replace("../images/", f"{BASE}/images/")
        return f'<figure><img src="{src}" alt="{alt}" loading="lazy" decoding="async"><figcaption>{cap.strip()}</figcaption></figure>'
    h = re.sub(r'<p><img alt="([^"]*)" src="([^"]+)" ?/?>\s*(.*?)</p>', fig, h, flags=re.S)
    h = h.replace('<a href="http', '<a rel="noopener" target="_blank" href="http')
    # CTA section
    h = re.sub(r'<h2 id="[^"]*">Записаться в ТатуНаХоду</h2>(.*?)(?=<h2|$)', lambda m: f'<section class="cta-box"><h2>Записаться в ТатуНаХоду</h2>{m.group(1)}</section>', h, flags=re.S)
    h = re.sub(r'(<h2 id="[^"]*">Источники изображений</h2>.*)$', r'<section class="credits">\1</section>', h, flags=re.S)
    return h

CSS = """
:root{--red:#b4232b;--ink:#141414;--muted:#666;--bg:#f6f3ee}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;padding-bottom:72px}
a{color:var(--red)}
header.top{background:var(--ink);color:#fff}
header.top .in{max-width:820px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;gap:12px}
header.top a.logo{color:#fff;text-decoration:none;font-weight:800;letter-spacing:.02em}
header.top a.logo span{color:#ff5a63}
header.top a.btn{white-space:nowrap}
.btn{display:inline-block;background:var(--red);color:#fff!important;text-decoration:none;font-weight:700;padding:10px 18px;border-radius:10px}
.btn.ghost{background:transparent;border:2px solid currentColor;color:inherit!important}
main{max-width:820px;margin:0 auto;background:#fff;padding:28px 22px 40px}
@media(min-width:760px){main{padding:44px 56px 56px;margin-top:24px;border-radius:14px;box-shadow:0 2px 24px rgba(0,0,0,.05)}}
h1{font-size:clamp(28px,5vw,38px);line-height:1.18;margin:.1em 0 .4em}
h2{font-size:24px;line-height:1.3;margin:1.8em 0 .5em}
h3{font-size:19px;margin:1.4em 0 .3em}
.crumbs{font-size:14px;color:var(--muted)}
.crumbs a{color:var(--muted)}
.meta{font-size:14px;color:var(--muted);margin-bottom:20px}
blockquote{margin:1.2em 0;padding:12px 18px;background:#fff6e5;border-left:4px solid #f0a500;color:#5a4400;font-size:15px}
blockquote p{margin:0}
.table{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:15px;margin:1em 0}
th{background:var(--ink);color:#fff;text-align:left;padding:9px 10px}
td{padding:8px 10px;border-bottom:1px solid #e8e8e8;vertical-align:top}
tr:nth-child(even) td{background:#faf8f5}
figure{margin:1.6em 0}
figure img{display:block;max-width:100%;max-height:640px;height:auto;margin:0 auto;border-radius:12px}
figcaption{font-size:13.5px;color:var(--muted);line-height:1.45;margin-top:8px}
figcaption em{color:#333;font-style:normal;font-weight:600}
figcaption a{color:var(--muted)}
.cta-box{background:var(--ink);color:#eee;border-radius:16px;padding:22px 24px;margin:2em 0}
.cta-box h2{color:#fff;margin-top:0}
.cta-box a{color:#fff}
.cta-box p:first-of-type+p a,.cta-box a[href*="tatunahody"]{display:inline-block;background:var(--red);color:#fff;text-decoration:none;font-weight:700;padding:12px 22px;border-radius:10px}
.credits{font-size:13px;color:var(--muted);border-top:1px solid #eee;margin-top:2em}
.credits h2{font-size:17px}
.sticky{position:fixed;left:0;right:0;bottom:0;background:rgba(20,20,20,.96);color:#fff;z-index:10;backdrop-filter:blur(6px)}
.sticky .in{max-width:820px;margin:0 auto;padding:10px 16px;display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:14.5px}
.sticky .txt{line-height:1.3}
.sticky .acts{display:flex;gap:8px;flex-shrink:0}
.sticky .btn{padding:9px 14px}
.sticky .btn.ghost{color:#fff!important;border-width:1px}
@media(max-width:520px){.sticky .txt{display:none}.sticky .acts{width:100%}.sticky .btn{flex:1;text-align:center}}
.list{list-style:none;padding:0;margin:0}
.list li{border-bottom:1px solid #eee;padding:18px 0}
.list a.t{font-size:21px;font-weight:700;text-decoration:none;color:var(--ink)}
.list a.t:hover{color:var(--red)}
.list p{margin:.3em 0 0;color:#444}
.list .thumb{display:block;width:100%;max-height:280px;object-fit:cover;border-radius:12px;margin-bottom:12px}
footer{max-width:820px;margin:0 auto;padding:24px 20px;font-size:13.5px;color:var(--muted)}
footer a{color:var(--muted)}
"""

def page(title, desc, canonical, body, og_image=None, og_type="website", jsonld=(), keywords=None):
    og_img = f'<meta property="og:image" content="{og_image}">\n<meta name="twitter:image" content="{og_image}">' if og_image else ""
    lds = "\n".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in jsonld)
    kw = f'<meta name="keywords" content="{html.escape(", ".join(keywords))}">' if keywords else ""
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{kw}
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:site_name" content="{html.escape(SITE_NAME)}">
<meta property="og:locale" content="ru_RU">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canonical}">
{og_img}
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="text/plain" title="llms.txt" href="{BASE}/llms.txt">
<style>{CSS}</style>
{lds}
</head>
<body>
<header class="top"><div class="in"><a class="logo" href="{BASE}/">Тату<span>На</span>Ходу · справочник</a><a class="btn" href="{BOOK_URL}" rel="noopener" target="_blank">Записаться</a></div></header>
<main>
{body}
</main>
<footer>© {TODAY.year} Тату-студия «ТатуНаХоду», Москва, Нижегородская ул., 5. Материалы справочника не являются медицинской консультацией. · <a href="{BOOK_URL}" rel="noopener" target="_blank">Записаться в Telegram</a> · <a href="{CHANNEL_URL}" rel="noopener" target="_blank">Наш канал</a></footer>
<div class="sticky"><div class="in"><div class="txt">Есть вопрос про тату или хотите записаться? Ответим в Telegram.</div><div class="acts"><a class="btn" href="{BOOK_URL}" rel="noopener" target="_blank">Записаться</a><a class="btn ghost" href="{CHANNEL_URL}" rel="noopener" target="_blank">Канал</a></div></div></div>
</body>
</html>
"""

def first_image(a):
    m = re.search(r"!\[[^\]]*\]\(\.\./images/([^)]+)\)", a["body"])
    return f"{SITE_URL}/images/{m.group(1)}" if m else None

def main():
    arts = [parse(os.path.join(ROOT, "articles", f)) for f in sorted(os.listdir(os.path.join(ROOT, "articles"))) if f.endswith(".md")]
    pub = [a for a in arts if INCLUDE_DRAFTS or not a["draft"]]
    pub.sort(key=lambda a: a["date"] or "9999", reverse=True)
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    for a in pub:
        url = f"{SITE_URL}/{a['slug']}/"
        img = first_image(a)
        body = render_body(a).replace("<table>", '<div class="table"><table>').replace("</table>", "</table></div>")
        date_h = datetime.date.fromisoformat(a["date"]).strftime("%d.%m.%Y") if a["date"] else ""
        content = f'<div class="crumbs"><a href="{BASE}/">Справочник</a> › {html.escape(a["title"])}</div>\n<h1>{html.escape(a["title"])}</h1>\n<div class="meta">Тату-студия «ТатуНаХоду» · {date_h}</div>\n{body}'
        article_ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["description"],
                      "inLanguage": "ru", "mainEntityOfPage": url, "datePublished": a["date"], "dateModified": a["date"],
                      "author": ORG, "publisher": {"@type": "Organization", "name": "ТатуНаХоду", "url": SITE_URL + "/"},
                      "keywords": ", ".join(a["keywords"])}
        if img: article_ld["image"] = [img]
        lds = [article_ld]
        fq = faq_pairs(a["body"])
        if fq:
            lds.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in fq]})
        lds.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Справочник", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": a["title"], "item": url}]})
        os.makedirs(os.path.join(OUT, a["slug"]))
        open(os.path.join(OUT, a["slug"], "index.html"), "w", encoding="utf-8").write(
            page(f'{a["title"]} | ТатуНаХоду', a["description"], url, content, img, "article", lds, a["keywords"]))
        src = os.path.join(ROOT, "images", a["slug"])
        if os.path.isdir(src): shutil.copytree(src, os.path.join(OUT, "images", a["slug"]))
        a["_url"], a["_img"] = url, img
    # home
    items = "\n".join(
        f'<li>{f"<a href=\"{BASE}/{a["slug"]}/\"><img class=\"thumb\" src=\"{a["_img"].replace(SITE_URL, BASE)}\" alt=\"{html.escape(a["title"])}\" loading=\"lazy\"></a>" if a["_img"] else ""}'
        f'<a class="t" href="{BASE}/{a["slug"]}/">{html.escape(a["title"])}</a><p>{html.escape(a["description"])}</p></li>' for a in pub)
    home = (f'<h1>Справочник по тату</h1><p>Честные и практичные ответы на частые вопросы о татуировках: как заживает тату, чем за ним ухаживать, больно ли и как подготовиться к сеансу. '
            f'Пишем на основе опыта студии «ТатуНаХоду» (Москва) и проверенных медицинских источников. Новые статьи выходят регулярно.</p>'
            f'<blockquote><p>Материалы справочника не являются медицинским советом. При признаках воспаления обращайтесь к врачу.</p></blockquote>'
            f'<h2>Статьи</h2><ul class="list">{items}</ul>')
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/", "inLanguage": "ru", "publisher": ORG}
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        page(SITE_NAME, SITE_DESC, SITE_URL + "/", home, pub[0]["_img"] if pub else None, "website", [site_ld]))
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(
        page("Страница не найдена | ТатуНаХоду", SITE_DESC, SITE_URL + "/", f'<h1>Страница не найдена</h1><p><a href="{BASE}/">Перейти в справочник</a></p>'))
    # sitemap
    today = TODAY.isoformat()
    urls = [(SITE_URL + "/", today)] + [(a["_url"], a["date"] or today) for a in pub]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n"
    open(os.path.join(OUT, "sitemap.xml"), "w").write(sm)
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    llms = [f"# {SITE_NAME}", "", f"> {SITE_DESC}", "",
            "Справочник ведёт тату-студия «ТатуНаХоду» (Москва, Нижегородская ул., 5). Статьи — практические ответы на частые вопросы о татуировках; это не медицинская консультация.",
            f"Запись и вопросы: {BOOK_URL} · Канал студии: {CHANNEL_URL}", "", "## Статьи", ""]
    llms += [f"- [{a['title']}]({a['_url']}): {a['description']}" for a in pub]
    open(os.path.join(OUT, "llms.txt"), "w", encoding="utf-8").write("\n".join(llms) + "\n")
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    print(f"Built {len(pub)} article(s) -> {OUT}")

if __name__ == "__main__":
    main()
