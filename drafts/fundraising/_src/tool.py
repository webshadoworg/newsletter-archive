#!/usr/bin/env python3
"""The fundraising email tool: read the wording, edit it, preview and copy each version, check the links.

    python3 drafts/fundraising/_src/tool.py          then open http://127.0.0.1:8822/

It runs on this machine only. Saving in the page writes to _src/<name>.src.html and rebuilds
every version, exactly as editing the file and running build.py would.
"""
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import build
import emailtext

PORT = 8822
REPO = build.SRC.parents[2]
OUT_URL = "/" + build.OUT.relative_to(REPO).as_posix() + "/"
MERGE = re.compile(r"\{\{|\*\||\*%7C", re.I)
LINK = re.compile(r'<(a|v:roundrect)\b[^>]*?href="([^"]*)"[^>]*>(.*?)</\1>', re.S)


def src_path(name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise ValueError("bad email name")
    path = build.SRC / f"{name}.src.html"
    if not path.exists():
        raise ValueError(f"no such email: {name}")
    return path


def links_of(built, v, tracked_hosts):
    rows = []
    for kind, href, inner in LINK.findall(built):
        url = html.unescape(href)
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        img = re.search(r'<img[^>]*alt="([^"]*)"', inner)
        label = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        label = re.sub(r"\s+", " ", label) or (f"Image: {html.unescape(img.group(1))}" if img else "(no text)")
        flags = []
        merge = bool(MERGE.search(url))
        if "utm_source" in query:
            for key, want in (("utm_source", v["utm_source"]), ("utm_medium", "email"), ("utm_content", v["utm"])):
                if query.get(key) != want:
                    flags.append(f"{key} is {query.get(key) or 'missing'}, expected {want}")
        elif parts.netloc in tracked_hosts and not merge:
            flags.append("no tracking tags, unlike the other links to this site")
        rows.append({"label": label, "outlook": kind != "a", "url": url,
                     "show": (parts.netloc + parts.path).rstrip("/") or url, "merge": merge, "flags": flags,
                     "utm_source": query.get("utm_source", ""), "utm_content": query.get("utm_content", "")})
    return rows


def describe(name):
    path = src_path(name)
    text = path.read_text(encoding="utf-8")
    settings, body = build.parse(path)
    header_len = len(text) - len(body)
    title = build.TITLE.search(body)
    versions = []
    for platform in build.PLATFORMS:
        if not settings.get(f"{platform}.out"):
            continue
        v = build.resolve(settings, platform)
        built = build.render(path, body, v)
        out_path = build.OUT / v["out"]
        v["html"] = built
        v["url"] = OUT_URL + v["out"]
        v["stale"] = not out_path.exists() or out_path.read_text(encoding="utf-8") != built
        v["footer_text"] = [b.get("html") for b in emailtext.extract("<body>" + v.pop("footer_html")) if b.get("html")]
        versions.append(v)
    for v in versions:
        hosts = {urlsplit(html.unescape(h)).netloc for _, h, _ in LINK.findall(v["html"]) if "utm_source=" in h}
        v["links"] = links_of(v["html"], v, hosts)
    blocks = emailtext.extract(text)
    return {
        "name": name,
        "rev": hashlib.sha1(text.encode()).hexdigest(),
        "source": f"drafts/fundraising/_src/{path.name}",
        "subject": html.unescape(title.group(1)) if title else "",
        "preheader": html.unescape(settings.get("preheader", "")),
        "utm": settings.get("utm", ""),
        "versions": versions,
        "blocks": [{"i": i, "kind": b["kind"], "html": b.get("html", ""), "locked": b["locked"],
                    "alt": b.get("alt"), "src": b.get("src"), "href": b.get("href")} for i, b in enumerate(blocks)],
        "_header_len": header_len,
    }


def set_setting(text, key, value):
    """Rewrite one 'key: value' line of the settings block (add it if missing, drop it if value is empty)."""
    m = build.HEADER.match(text)
    lines = m.group(1).split("\n")
    kept = [l for l in lines if l.partition(":")[0].strip() != key]
    if value:
        at = next((i for i, l in enumerate(lines) if l.partition(":")[0].strip() == key), len(kept))
        kept.insert(min(at, len(kept)), f"{key}: {value}")
    return "<!--@email\n" + "\n".join(kept) + "\n-->\n" + text[m.end():]


def change(name, payload):
    path = src_path(name)
    text = path.read_text(encoding="utf-8")
    if payload.get("rev") != hashlib.sha1(text.encode()).hexdigest():
        raise ValueError("The source file changed since this page loaded. Reload and try again.")
    action = payload.get("action")
    blocks = emailtext.extract(text)
    if action in ("edit", "delete", "add"):
        index = payload.get("index")
        if not isinstance(index, int) or not 0 <= index < len(blocks):
            raise ValueError("no such paragraph")
        if action == "edit":
            text = emailtext.edit_block(text, blocks, index, payload.get("html", ""))
        elif action == "delete":
            text = emailtext.delete_block(text, blocks, index)
        else:
            text = emailtext.add_after(text, blocks, index, payload.get("html", ""))
    elif action == "settings":
        values = payload.get("values", {})
        one_line = lambda s: re.sub(r"\s+", " ", s).strip()
        if "subject" in values:
            subject = emailtext.encode(one_line(values["subject"]))
            text = build.TITLE.sub(lambda _: f"<title>{subject}</title>", text, count=1)
        if "preheader" in values:
            text = set_setting(text, "preheader", emailtext.encode(one_line(values["preheader"])))
        if "utm" in values:
            utm = one_line(values["utm"])
            if not re.fullmatch(r"[A-Za-z0-9._-]+", utm):
                raise ValueError("utm_content can only use letters, numbers, dots, dashes and underscores.")
            text = set_setting(text, "utm", utm)
        for platform in build.PLATFORMS:
            key = f"{platform}.greeting"
            if key in values:   # greetings hold merge tags, so they are stored exactly as typed
                text = set_setting(text, key, one_line(values[key]))
    else:
        raise ValueError("unknown action")
    path.write_text(text, encoding="utf-8")
    build.build_email(path)
    return describe(name)


def check_url(url):
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.startswith("utm_") and not MERGE.search(v)]   # don't count the check as an email click
    clean = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
    request = urllib.request.Request(clean, headers={"User-Agent": "Mozilla/5.0 (link check)"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return {"ok": True, "status": response.status}
    except urllib.error.HTTPError as e:
        return {"ok": e.code in (401, 403, 405, 429), "status": e.code}   # blocked robots, not a dead link
    except Exception as e:
        return {"ok": False, "status": str(getattr(e, "reason", e))[:80]}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, data, status=200):
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if not k.startswith("_")}
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        try:
            if path == "/":
                body = (build.SRC / "tool.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif path == "/api/emails":
                self.send_json(sorted(p.name[:-len(".src.html")] for p in build.SRC.glob("*.src.html")))
            elif path.startswith("/api/email/"):
                self.send_json(describe(path.rsplit("/", 1)[1]))
            else:
                super().do_GET()
        except (ValueError, SystemExit) as e:
            self.send_json({"error": str(e)}, 400)

    def do_POST(self):
        origin = self.headers.get("Origin") or ""
        if urlsplit(origin).netloc not in (f"127.0.0.1:{PORT}", f"localhost:{PORT}"):
            return self.send_json({"error": "This tool only takes changes from its own page."}, 403)
        path = urlsplit(self.path).path
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            if path.startswith("/api/email/"):
                self.send_json(change(path.rsplit("/", 1)[1], payload))
            elif path == "/api/check":
                urls = [u for u in dict.fromkeys(payload.get("urls", [])) if u.startswith(("http://", "https://"))][:60]
                with ThreadPoolExecutor(8) as pool:
                    self.send_json(dict(zip(urls, pool.map(check_url, urls))))
            else:
                self.send_json({"error": "not found"}, 404)
        except (ValueError, SystemExit) as e:
            self.send_json({"error": str(e)}, 400)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(REPO)))
    print(f"Fundraising email tool: http://127.0.0.1:{PORT}/   (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
