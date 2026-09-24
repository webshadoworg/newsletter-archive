#!/usr/bin/env python3
"""The email tool: read the wording, edit it, preview and copy each version, check the links.

    python3 drafts/fundraising/_src/tool.py          then open http://127.0.0.1:8822/

It runs on this machine only. For a fundraising email, saving in the page writes to
_src/<name>.src.html and rebuilds every version, exactly as editing the file and running build.py
would. It also opens the plain newsletter drafts in drafts/ (the ones that carry the GYE mailer's
unsubscribe tags); there it writes straight into drafts/<name>.html, and there is nothing to build.
"""
import base64
import hashlib
import html
import json
import re
import subprocess
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
CRM_ENV = REPO.parent / "gye-crm" / ".env"   # the Mailchimp key lives there, never in this (public) repo
SITE_HOST = "gyenewsletters.netlify.app"   # this repo, as published by Netlify
IMG = re.compile(r'<img\b[^>]*?\bsrc="([^"]*)"', re.I)
LINK = re.compile(r'<(a|v:roundrect)\b[^>]*?href="([^"]*)"[^>]*>(.*?)</\1>', re.S)
DRAFTS = REPO / "drafts"   # plain newsletter drafts: one hand-written HTML file each, sent through the GYE mailer
MAILER_TAG = re.compile(r"\{\{(?:preferenceUrl|unsubscribeFromAll|leaveCurrentSeriesOrListUrl)\}\}")
# the hidden preheader div at the top of the body; "spacer" is the invisible padding some drafts put there
PREHEADER_DIV = re.compile(r"(<div\b[^>]*display:\s*none[^>]*>)(.*?)(</div>)", re.S | re.I)
SPACER = re.compile(r"&#847;|&zwnj;|&nbsp;|[\u034f\u200c\u00a0]")


def check_name(name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise ValueError("bad email name")


def src_path(name):
    """The source file of a fundraising email. A plain draft has none."""
    check_name(name)
    path = build.SRC / f"{name}.src.html"
    if not path.exists():
        if (DRAFTS / f"{name}.html").is_file():
            raise ValueError(f"{name} is a plain newsletter draft, not a fundraising email. It has no source file "
                             "and no Mailchimp version.")
        raise ValueError(f"no such email: {name}")
    return path


def plain_path(name):
    """A plain draft's file, or None when the name is a fundraising email (which comes first)."""
    check_name(name)
    if (build.SRC / f"{name}.src.html").exists():
        return None
    path = DRAFTS / f"{name}.html"
    if not path.is_file():
        raise ValueError(f"no such email: {name}")
    return path


def is_plain_draft(path):
    """A file in drafts/ counts as an email when it carries the GYE mailer's footer tags. The rest of the
    folder (option pages, reviews, banner tests) is left out."""
    try:
        return bool(MAILER_TAG.search(path.read_text(encoding="utf-8")))
    except (UnicodeDecodeError, OSError):
        return False


def list_emails():
    fundraising = sorted(p.name[:-len(".src.html")] for p in build.SRC.glob("*.src.html"))
    # newest first, by the last commit that touched the file (a fresh checkout gives every file the same mtime)
    committed, when = {}, None
    for line in git("log", "--format=%ct", "--name-only", "--", "drafts/*.html").splitlines():
        if line.isdigit():
            when = int(line)
        elif line and line not in committed:
            committed[line] = when
    drafts = sorted((p for p in DRAFTS.glob("*.html") if is_plain_draft(p)),
                    key=lambda p: committed.get(p.relative_to(REPO).as_posix()) or p.stat().st_mtime, reverse=True)
    drafts = [p.name[:-len(".html")] for p in drafts]
    return [{"name": n, "group": "Fundraising"} for n in fundraising] + \
           [{"name": n, "group": "Newsletters"} for n in drafts if n not in fundraising]


def preheader_of(text):
    """The text of the hidden preheader div, if the draft has one. (found, text)"""
    body = text.find("<body")
    m = PREHEADER_DIV.search(text, body if body >= 0 else 0)
    if not m:
        return False, ""
    inner = html.unescape(SPACER.sub(" ", re.sub(r"<[^>]+>", "", m.group(2))))
    return True, re.sub(r"\s+", " ", inner).strip()


def set_preheader(text, value):
    """Write the preheader sentence into the hidden div, adding the div under <body> when there is none."""
    body = text.find("<body")
    m = PREHEADER_DIV.search(text, body if body >= 0 else 0)
    if m:
        return text[:m.start(2)] + value + text[m.end(2):]
    if not value:
        return text
    tag = re.compile(r"<body\b[^>]*>", re.I).search(text)
    if not tag:
        raise ValueError("The file has no <body> tag to put the preheader under.")
    div = ('<div style="display:none;font-size:1px;color:#ffffff;line-height:1px;max-height:0;max-width:0;'
           f'opacity:0;overflow:hidden;">{value}</div>')
    return text[:tag.end()] + "\n" + div + text[tag.end():]


def common(values):
    """The value most links agree on, else an empty string."""
    values = [v for v in values if v]
    return max(set(values), key=values.count) if values else ""


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
    if path := plain_path(name):
        return describe_plain(name, path)
    path = src_path(name)
    text = path.read_text(encoding="utf-8")
    settings, body = build.parse(path)
    title = build.TITLE.search(body)
    versions = []
    for platform in build.PLATFORMS:
        v = build.resolve(settings, platform)
        if not v["out"] and platform != "constantcontact":
            continue
        built = build.render(path, body, v)
        v["html"] = built
        if v["out"]:   # a version written to a file; Constant Contact is usually rendered here only
            out_path = build.OUT / v["out"]
            v["rel"] = out_path.relative_to(REPO).as_posix()
            v["url"] = OUT_URL + v["out"]
            v["stale"] = not out_path.exists() or out_path.read_text(encoding="utf-8") != built
        else:
            v["url"] = None
            v["stale"] = False
        v["footer_text"] = [b.get("html") for b in emailtext.extract("<body>" + v.pop("footer_html")) if b.get("html")]
        versions.append(v)
    for v in versions:
        hosts = {urlsplit(html.unescape(h)).netloc for _, h, _ in LINK.findall(v["html"]) if "utm_source=" in h}
        v["links"] = links_of(v["html"], v, hosts)
    blocks = emailtext.extract(text)
    return {
        "name": name,
        "plain": False,
        "rev": hashlib.sha1(text.encode()).hexdigest(),
        "source": f"drafts/fundraising/_src/{path.name}",
        "subject": html.unescape(title.group(1)) if title else "",
        "preheader": html.unescape(settings.get("preheader", "")),
        "utm": settings.get("utm", ""),
        "versions": versions,
        "blocks": block_rows(blocks),
    }


def block_rows(blocks):
    return [{"i": i, "kind": b["kind"], "html": b.get("html", ""), "locked": b["locked"],
             "alt": b.get("alt"), "src": b.get("src"), "href": b.get("href"), "only": b.get("only")} for i, b in enumerate(blocks)]


def describe_plain(name, path):
    """A plain draft: one version, the file itself, with nothing rendered or built."""
    text = path.read_text(encoding="utf-8")
    title = build.TITLE.search(text)
    rel = path.relative_to(REPO).as_posix()
    tagged = [dict(parse_qsl(urlsplit(html.unescape(h)).query)) for _, h, _ in LINK.findall(text) if "utm_source=" in h]
    v = {"platform": "gyemailer", "out": path.name, "rel": rel, "url": "/" + rel, "html": text, "stale": False,
         "greeting": "", "footer_file": None, "footer_text": [],
         # the tags most links carry; the Links tab then points out the odd one out
         "utm_source": common(q.get("utm_source") for q in tagged), "utm": common(q.get("utm_content") for q in tagged)}
    hosts = {urlsplit(html.unescape(h)).netloc for _, h, _ in LINK.findall(text) if "utm_source=" in h}
    v["links"] = links_of(text, v, hosts)
    has_preheader, preheader = preheader_of(text)
    return {
        "name": name,
        "plain": True,
        "rev": hashlib.sha1(text.encode()).hexdigest(),
        "source": rel,
        "subject": html.unescape(title.group(1)) if title else "",
        "preheader": preheader,
        "preheader_div": has_preheader,
        "utm": v["utm"],
        "versions": [v],
        "blocks": block_rows(emailtext.extract(text)),
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
    plain = plain_path(name)
    path = plain or src_path(name)
    text = path.read_text(encoding="utf-8")
    if payload.get("rev") != hashlib.sha1(text.encode()).hexdigest():
        raise ValueError("The source file changed since this page loaded. Reload and try again.")
    action = payload.get("action")
    blocks = emailtext.extract(text)
    one_line = lambda s: re.sub(r"\s+", " ", s).strip()
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
    elif action == "settings" and plain:
        values = payload.get("values", {})
        if "subject" in values:
            subject = emailtext.encode(one_line(values["subject"]))
            text = build.TITLE.sub(lambda _: f"<title>{subject}</title>", text, count=1)
        if "preheader" in values:
            text = set_preheader(text, emailtext.encode(one_line(values["preheader"])))
    elif action == "settings":
        values = payload.get("values", {})
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
    if not plain:
        build.build_email(path)
    return describe(name)


def mailchimp_env():
    if not CRM_ENV.exists():
        raise ValueError(f"Mailchimp key not found: {CRM_ENV} does not exist.")
    values = {}
    for line in CRM_ENV.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.strip().removeprefix("export ").partition("=")
        if sep and key.strip() in ("MAILCHIMP_API_KEY", "MAILCHIMP_AUDIENCE_ID"):
            values[key.strip()] = value.strip().strip("'\"")
    if len(values) < 2 or "-" not in values.get("MAILCHIMP_API_KEY", ""):
        raise ValueError(f"MAILCHIMP_API_KEY and MAILCHIMP_AUDIENCE_ID are not both set in {CRM_ENV}.")
    return values["MAILCHIMP_API_KEY"], values["MAILCHIMP_AUDIENCE_ID"]


def mailchimp(method, path, body=None, missing_ok=False):
    key, _ = mailchimp_env()
    request = urllib.request.Request(
        f"https://{key.rsplit('-', 1)[1]}.api.mailchimp.com/3.0{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Basic " + base64.b64encode(f"tool:{key}".encode()).decode(),
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as e:
        if e.code == 404 and missing_ok:
            return None
        try:
            problem = json.loads(e.read())
            detail = problem.get("detail", "") + " " + "; ".join(
                f"{x.get('field')}: {x.get('message')}" for x in problem.get("errors", []))
        except ValueError:
            detail = ""
        raise ValueError(f"Mailchimp said no ({e.code}). {detail.strip()}")
    except urllib.error.URLError as e:
        raise ValueError(f"Could not reach Mailchimp: {e.reason}")


def mailchimp_edit_url(campaign):
    key, _ = mailchimp_env()
    return f"https://{key.rsplit('-', 1)[1]}.admin.mailchimp.com/campaigns/edit?id={campaign['web_id']}"


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True).stdout.strip()


def image_report(built):
    """Every image in the email, and whether it is reachable on the web yet.

    Mailchimp (and every reader) loads images from their web address, so an image that lives in this
    repo has to be committed and pushed, and deployed by Netlify, before a draft can show it.
    """
    urls = list(dict.fromkeys(html.unescape(u) for u in IMG.findall(built)))
    with ThreadPoolExecutor(8) as pool:
        loads = list(pool.map(check_url, urls))
    report = []
    for url, load in zip(urls, loads):
        live = load["ok"] and load["status"] == 200
        why = ""
        parts = urlsplit(url)
        if not live and parts.netloc == SITE_HOST:
            rel = parts.path.lstrip("/")
            if not (REPO / rel).is_file():
                why = f"There is no {rel} in this repo."
            elif git("status", "--porcelain", "--", rel):
                why = "The file is in this folder but not committed. Commit and push it first."
            elif git("log", "--oneline", "origin/main..HEAD", "--", rel):
                why = "The file is committed but not pushed. Push it first."
            else:
                why = "The file is pushed. Netlify may still be deploying; try again in a minute."
        elif not live:
            why = f"It did not load ({load['status']})."
        report.append({"url": url, "live": live, "why": why})
    return report


def share_status(name):
    """The public address of each built version on the Netlify site, and whether that page is current."""
    rows = []
    for v in describe(name)["versions"]:
        if not v["out"]:   # not written to a file, so not on the site
            continue
        rel = v["rel"]
        url = f"https://{SITE_HOST}/{rel}"
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (share check)", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(request, timeout=15) as response:
                live = response.read().decode("utf-8", "replace")
            state = "current" if live == v["html"] else "old"
        except urllib.error.HTTPError as e:
            state = "missing" if e.code == 404 else "error"
        except Exception:
            state = "error"
        why = ""
        if state in ("old", "missing"):
            if v["stale"]:
                why = "The built file is out of date. Save a change in the tool or run build.py, then commit and push."
            elif git("status", "--porcelain", "--", rel):
                why = "Your latest changes are not committed. Commit and push them."
            elif git("log", "--oneline", "origin/main..HEAD", "--", rel):
                why = "Your latest changes are committed but not pushed. Push them."
            else:
                why = "Everything is pushed. Netlify may still be deploying; check again in a minute."
        elif state == "error":
            why = "The site could not be reached."
        rows.append({"platform": v["platform"], "out": v["out"], "url": url, "state": state, "why": why})
    return rows


PLACEHOLDER = re.compile(r"\[[^\]\n]{1,24}\]|\bX hours?\b|\bX ?%")


def placeholders(name):
    """Unfilled blanks such as [X] hours or [65%] in the subject, the preheader or the wording."""
    email = describe(name)
    version = email["versions"][0]["html"]
    visible = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<!--.*?-->", " ", version[version.find("<body"):], flags=re.S)))
    found = PLACEHOLDER.findall(" ".join([email["subject"], email["preheader"], visible]))
    return list(dict.fromkeys(found))


def mailchimp_version(name):
    version = next((v for v in describe(name)["versions"] if v["platform"] == "mailchimp"), None)
    if not version:
        raise ValueError("This email has no Mailchimp version (no mailchimp.out line in its settings).")
    return version


def mailchimp_from(audience_id):
    """The From line for a new draft: whatever the last sent campaign used, else the audience default."""
    sent = mailchimp("GET", f"/campaigns?status=sent&list_id={audience_id}&sort_field=send_time&sort_dir=DESC&count=1"
                            "&fields=campaigns.settings.from_name,campaigns.settings.reply_to")["campaigns"]
    if sent and sent[0]["settings"].get("from_name"):
        return sent[0]["settings"]["from_name"], sent[0]["settings"]["reply_to"], "same as the last campaign sent"
    defaults = mailchimp("GET", f"/lists/{audience_id}?fields=campaign_defaults").get("campaign_defaults", {})
    return defaults.get("from_name", ""), defaults.get("from_email", ""), "the audience default"


def mailchimp_status(name):
    """What the Mailchimp tab shows before anything is pushed. Reads only."""
    _, audience_id = mailchimp_env()
    audience = mailchimp("GET", f"/lists/{audience_id}?fields=name,stats.member_count")
    from_name, from_email, from_why = mailchimp_from(audience_id)
    settings, _ = build.parse(src_path(name))
    draft = None
    if settings.get("mailchimp.campaign_id"):
        found = mailchimp("GET", f"/campaigns/{settings['mailchimp.campaign_id']}?fields=id,web_id,status,settings.title",
                          missing_ok=True)
        if found:
            draft = {"status": found["status"], "title": found["settings"].get("title", ""),
                     "url": mailchimp_edit_url(found)}
    return {"audience": audience["name"], "members": audience["stats"]["member_count"],
            "images": image_report(mailchimp_version(name)["html"]), "placeholders": placeholders(name),
            "from_name": from_name, "from_email": from_email, "from_why": from_why, "draft": draft}


def mailchimp_push(name, rev):
    """Create this email's Mailchimp draft, or update the draft made last time. Never sends anything."""
    path = src_path(name)
    text = path.read_text(encoding="utf-8")
    if rev != hashlib.sha1(text.encode()).hexdigest():
        raise ValueError("The source file changed since this page loaded. Reload and try again.")
    email = describe(name)
    version = mailchimp_version(name)
    blanks = placeholders(name)
    if blanks:
        raise ValueError("Not pushed to Mailchimp: the email still has blanks to fill in: " + ", ".join(blanks))
    missing = [i for i in image_report(version["html"]) if not i["live"]]
    if missing:
        raise ValueError("Not pushed to Mailchimp: " + " ".join(f"{i['url']} is not on the web yet. {i['why']}" for i in missing))
    _, audience_id = mailchimp_env()
    settings, _ = build.parse(path)
    wording = {"subject_line": email["subject"], "preview_text": email["preheader"], "title": name}

    campaign, note = None, "created"
    if settings.get("mailchimp.campaign_id"):
        campaign = mailchimp("GET", f"/campaigns/{settings['mailchimp.campaign_id']}?fields=id,web_id,status",
                             missing_ok=True)
        if campaign and campaign["status"] != "save":   # sent or scheduled: leave it alone, start a new draft
            campaign, note = None, "created (the earlier campaign was already sent or scheduled, so it was left alone)"
    if campaign:
        mailchimp("PATCH", f"/campaigns/{campaign['id']}", {"settings": wording})   # keeps the From and audience set in Mailchimp
        note = "updated"
    else:
        from_name, from_email, _ = mailchimp_from(audience_id)
        campaign = mailchimp("POST", "/campaigns", {
            "type": "regular", "recipients": {"list_id": audience_id},
            "settings": {**wording, "from_name": from_name, "reply_to": from_email}})
    mailchimp("PUT", f"/campaigns/{campaign['id']}/content", {"html": version["html"]})

    if settings.get("mailchimp.campaign_id") != campaign["id"]:   # remember the draft so the next push updates it
        path.write_text(set_setting(text, "mailchimp.campaign_id", campaign["id"]), encoding="utf-8")
    return {"note": note, "url": mailchimp_edit_url(campaign), "email": describe(name)}


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
                self.send_json(list_emails())
            elif path.startswith("/api/share/"):
                self.send_json(share_status(path.rsplit("/", 1)[1]))
            elif path.startswith("/api/mailchimp/"):
                self.send_json(mailchimp_status(path.rsplit("/", 1)[1]))
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
            if path.startswith("/api/mailchimp/"):
                self.send_json(mailchimp_push(path.rsplit("/", 1)[1], payload.get("rev")))
            elif path.startswith("/api/email/"):
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
    print(f"Email tool: http://127.0.0.1:{PORT}/   (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
