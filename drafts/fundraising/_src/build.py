#!/usr/bin/env python3
"""Build the per-platform versions of the fundraising emails.

Each _src/<name>.src.html is the one file you edit. It starts with a settings block:

    <!--@email
    preheader: the preview sentence (HTML entities allowed)
    utm: erev-yk-teshuva
    mailchimp.out: erev-yk-teshuva.html
    mailchimp.greeting: *|IF:GREET|*Dear *|GREET|*,*|ELSE:|*Dear Friend of GYE,*|END:IF|*
    gyemailer.out: erev-yk-teshuva-members.html
    gyemailer.greeting: Dear Member,
    -->

A plain key is shared by every version; "<platform>.key" overrides it for one platform.
Only platforms that have an "out" line are written to a file. The third platform, constantcontact,
normally has none: the tool builds it on the fly for its Copy tab, with "Dear Supporter," as the
greeting, the preheader sentence in the HTML, utm_source=cc and no footer (Constant Contact adds
its own). Add "constantcontact.out: <name>-cc.html" to write it out too. The body uses these slots:

    {{PREHEADER}}   Mailchimp: its *|MC_PREVIEW_TEXT|* tag. GYE mailer: the sentence itself.
    {{GREETING}}    the "greeting" setting
    {{UTM}}         the "utm" setting (utm_content)
    {{EMAIL_TAG}}   the reader's own email address, as each system writes it: *|EMAIL|* / {{email}}
    {{UTM_SOURCE}}  Mailchimp: mc. GYE mailer: members. A "utm_source" setting overrides it.
    {{FOOTER}}      alone on its own line; replaced by the platform's footer partial:
                    Mailchimp gets the Unsubscribe pill (it sits above the footer Mailchimp
                    appends), GYE mailer gets the members footer. "<platform>.footer: none"
                    drops it for one email; "<platform>.footer: other.html" swaps the partial
    <!--@only gyemailer-->   lines up to the next <!--@end--> go into that version alone
    {{FOOTER_GAP}}  bottom padding of the cell above the footer: 0 with a footer, 40px without

To read and change the wording in the browser, run tool.py (see ../README.md).

Usage:
    python3 build.py            build every email
    python3 build.py NAME ...   build only _src/NAME.src.html
    python3 build.py --check    write nothing; exit 1 if any built file is stale or hand-edited
"""
import html
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
OUT = SRC.parent
PARTIALS = SRC / "partials"

PLATFORMS = {
    "mailchimp": {"preheader": "*|MC_PREVIEW_TEXT|*", "footer": "footer-mailchimp.html", "utm_source": "mc",
                  "email_tag": "*|EMAIL|*", "greeting": None},
    "gyemailer": {"preheader": None, "footer": "footer-gyemailer.html", "utm_source": "members",
                  "email_tag": "{{email}}", "greeting": None},
    # Constant Contact: no out file unless the email asks for one; the tool renders it for the Copy tab.
    # Constant Contact appends its own footer (address, unsubscribe), so ours is left out, and it has
    # no merge tag for the reader's address, so the wording says "this one".
    "constantcontact": {"preheader": None, "footer": None, "utm_source": "cc",
                        "email_tag": "this one", "greeting": "Dear Supporter,"},
}

HEADER = re.compile(r"\A<!--@email\n(.*?)\n-->\n", re.S)
SLOT = re.compile(r"\{\{([A-Z_]+)\}\}")
ONLY = re.compile(r"<!--@(?:only ([a-z]+)|end)-->")
TITLE = re.compile(r"<title>(.*?)</title>", re.S)


def parse(src_path):
    text = src_path.read_text(encoding="utf-8")
    m = HEADER.match(text)
    if not m:
        sys.exit(f"{src_path.name}: missing the <!--@email ... --> settings block at the top")
    settings = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            sys.exit(f"{src_path.name}: bad settings line: {line!r}")
        settings[key.strip()] = value.strip()
    return settings, text[m.end():]


def resolve(settings, platform):
    """The values one platform's version is built with."""
    def get(key):
        return settings.get(f"{platform}.{key}", settings.get(key))

    footer_file = get("footer") or PLATFORMS[platform]["footer"]
    if footer_file == "none":
        footer_file = None
    return {
        "platform": platform,
        "out": settings.get(f"{platform}.out"),
        "preheader": PLATFORMS[platform]["preheader"] or get("preheader"),
        "preheader_is_tag": bool(PLATFORMS[platform]["preheader"]),
        "greeting": get("greeting") or PLATFORMS[platform]["greeting"],
        "utm": get("utm"),
        "utm_source": get("utm_source") or PLATFORMS[platform]["utm_source"],
        "email_tag": PLATFORMS[platform]["email_tag"],
        "footer_file": footer_file,
        "footer_html": (PARTIALS / footer_file).read_text(encoding="utf-8").rstrip("\n") if footer_file else "",
    }


def render(src_path, body, v):
    footer = v["footer_html"]
    slots = {
        "PREHEADER": v["preheader"],
        "GREETING": v["greeting"],
        "UTM": v["utm"],
        "UTM_SOURCE": v["utm_source"],
        "EMAIL_TAG": v["email_tag"],
        "FOOTER": footer,
        "FOOTER_GAP": "0" if footer else "40px",
    }

    def fill(m):
        name = m.group(1)
        if slots.get(name) is None:
            sys.exit(f"{src_path.name} [{v['platform']}]: no value for {{{{{name}}}}}")
        return slots[name]

    lines, only = [], None
    for line in body.split("\n"):
        marker = ONLY.fullmatch(line.strip())
        if marker:   # <!--@only gyemailer--> ... <!--@end-->: lines kept in that version alone
            only = marker.group(1)
            if only and only not in PLATFORMS:
                sys.exit(f"{src_path.name}: unknown platform in {line.strip()}")
            continue
        if only and only != v["platform"]:
            continue
        if line.strip() == "{{FOOTER}}" and not footer:
            continue
        lines.append(SLOT.sub(fill, line))
    return "\n".join(lines)


def build_email(src_path, check=False):
    """Build every version of one email. Returns [(out_name, platform, changed)]."""
    settings, body = parse(src_path)
    results = []
    for v in (resolve(settings, p) for p in PLATFORMS if settings.get(f"{p}.out")):
        out_path = OUT / v["out"]
        result = render(src_path, body, v)
        current = out_path.read_text(encoding="utf-8") if out_path.exists() else None
        if not check:
            out_path.write_text(result, encoding="utf-8")
        results.append((v["out"], v["platform"], current != result))
    return settings, results


def main(argv):
    check = "--check" in argv
    names = [a for a in argv if not a.startswith("-")]
    sources = [SRC / f"{n}.src.html" for n in names] or sorted(SRC.glob("*.src.html"))
    stale = []
    for src_path in sources:
        settings, results = build_email(src_path, check)
        for out_name, platform, changed in results:
            if check:
                if changed:
                    stale.append(out_name)
                continue
            print(f"{'wrote    ' if changed else 'unchanged'}  {out_name}  [{platform}]")
        if not check and "mailchimp.out" in settings:
            print(f"           Mailchimp preview text: {html.unescape(settings.get('preheader', ''))}")
    if stale:
        print("Out of date, or edited by hand instead of in _src/:")
        for name in stale:
            print(f"  {name}")
        print("Run: python3 drafts/fundraising/_src/build.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
