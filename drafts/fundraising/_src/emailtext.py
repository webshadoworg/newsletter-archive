"""Read the wording out of an email's HTML, and write wording changes back into it.

Used by tool.py. extract() boils the HTML down to paragraphs, buttons and image notes, and remembers
where each one sits in the source so that an edit replaces only that paragraph's own characters.
"""
import html
import re
from html.entities import codepoint2name
from html.parser import HTMLParser

BLOCKS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li"}
BREAKERS = {"table", "tr", "td", "div", "body", "center"}
INLINE = {"b": "b", "strong": "b", "i": "i", "em": "i", "u": "u"}
VOID = {"img", "br", "meta", "link", "hr", "input"}
KEEP_NAMED = {"rsquo", "lsquo", "rdquo", "ldquo", "nbsp", "amp", "lt", "gt", "quot", "mdash", "ndash", "hellip"}


class Extractor(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.text = text
        self.line_starts = [0] + [m.end() for m in re.finditer("\n", text)]
        self.blocks = []
        self.cur = None
        self.anchor = None
        self.hidden = []
        self.in_body = False
        self.only = None   # platform named by an open <!--@only x--> marker

    def handle_comment(self, data):
        marker = re.fullmatch(r"@(?:only ([a-z]+)|end)", data.strip())
        if marker:
            self.flush()
            self.only = marker.group(1)

    def at(self):
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def open(self, kind=None, start_tag=None):
        self.cur = {"kind": kind, "parts": [], "anchors": [], "locked": False, "linked": False, "only": self.only,
                    "unlinked": False, "start_tag": start_tag}
        if start_tag:
            self.cur["outer_start"] = self.at()
            self.cur["inner_start"] = self.at() + len(start_tag)

    def flush(self, inner_end=None, outer_end=None):
        cur, self.cur = self.cur, None
        if not cur:
            return
        inner = re.sub(r"\s+", " ", "".join(cur["parts"])).strip()
        plain = re.sub(r"<[^>]+>", "", inner).replace("\xa0", "").strip()
        if not plain or plain == "{{FOOTER}}":
            return
        if cur["kind"]:
            cur["inner_end"], cur["outer_end"] = inner_end, outer_end
            if inner_end is None:
                cur["locked"] = True
        elif cur["linked"] and not cur["unlinked"] and len(cur["anchors"]) == 1 and cur["anchors"][0].get("inner_end"):
            cur["kind"] = "button"
            cur["inner_start"], cur["inner_end"] = cur["anchors"][0]["inner_start"], cur["anchors"][0]["inner_end"]
        else:
            cur["kind"], cur["locked"] = "p", True
        if html.unescape(plain) == "{{GREETING}}":
            cur["kind"], cur["locked"] = "greeting", True
        cur["html"] = inner
        self.blocks.append(cur)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "body":
            self.in_body = True
            return
        if not self.in_body:
            return
        if self.hidden:
            if tag not in VOID:
                self.hidden.append(tag)
            return
        if "display:none" in (attrs.get("style") or "").replace(" ", "") and tag not in VOID:
            self.hidden.append(tag)
            return
        if tag in BLOCKS:
            self.flush()
            self.open("h" if tag[0] == "h" else tag, self.get_starttag_text())
        elif tag in BREAKERS:
            self.flush()
        elif tag == "img":
            note = {"kind": "image", "alt": attrs.get("alt") or "", "src": attrs.get("src") or "",
                    "href": self.anchor["href"] if self.anchor else "", "locked": True}
            if self.cur and self.cur["kind"]:
                self.cur["locked"] = True
            else:
                self.flush()
                self.blocks.append(note)
        else:
            if not self.cur:
                self.open()
            if tag == "a":
                raw = self.get_starttag_text()
                self.anchor = {"tag": raw, "href": attrs.get("href") or "", "inner_start": self.at() + len(raw)}
                self.cur["anchors"].append(self.anchor)
                self.cur["parts"].append(
                    f'<a data-i="{len(self.cur["anchors"]) - 1}" href="{html.escape(self.anchor["href"])}">')
            elif tag == "br":
                self.cur["parts"].append("<br>")
            elif tag in INLINE:
                self.cur["parts"].append(f"<{INLINE[tag]}>")
            else:
                self.cur["locked"] = True   # span, font, sup...: not safe to rewrite from the page

    def handle_endtag(self, tag):
        if not self.in_body:
            return
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag in BLOCKS:
            end = self.at()
            self.flush(end, self.text.index(">", end) + 1)
        elif tag in BREAKERS:
            self.flush()
        elif tag == "a":
            if self.anchor:
                self.anchor["inner_end"] = self.at()
                self.anchor = None
            if self.cur:
                self.cur["parts"].append("</a>")
        elif tag in INLINE and self.cur:
            self.cur["parts"].append(f"</{INLINE[tag]}>")

    def handle_data(self, data):
        if not self.in_body or self.hidden:
            return
        if not data.strip() and not self.cur:
            return
        if not self.cur:
            self.open()
        if data.strip():
            self.cur["linked" if self.anchor else "unlinked"] = True
        self.cur["parts"].append(html.escape(data, quote=False))


def extract(text):
    parser = Extractor(text)
    parser.feed(text)
    parser.close()
    parser.flush()
    return parser.blocks


def encode(text):
    """Plain text -> the ASCII-with-entities style the emails are written in."""
    out = []
    for ch in text:
        code = ord(ch)
        if ch in "&<>\"":
            out.append(html.escape(ch))
        elif code < 128:
            out.append(ch)
        elif codepoint2name.get(code) in KEEP_NAMED:
            out.append(f"&{codepoint2name[code]};")
        else:
            out.append(f"&#{code};")
    return "".join(out)


class Rebuilder(HTMLParser):
    """The page's simplified HTML (b, i, u, a, br) -> email HTML, reusing the paragraph's original <a ...> tags."""

    def __init__(self, anchors, link_tags):
        super().__init__(convert_charrefs=True)
        self.anchors, self.link_tags = anchors, link_tags
        self.out, self.stack = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "br":
            self.out.append("<br>")
        elif tag in ("b", "i", "u"):
            self.out.append(f"<{tag}>")
            self.stack.append(tag)
        elif tag == "a":
            index = attrs.get("data-i")
            if index is not None and index.isdigit() and int(index) < len(self.anchors):
                self.out.append(self.anchors[int(index)]["tag"])
            else:
                self.out.append(self.new_link(attrs.get("href") or ""))
            self.stack.append("a")

    def new_link(self, href):
        if not self.link_tags:
            raise ValueError("This email has no text link to copy the link style from; add the link in the source file.")
        bare = href.split("?")[0].rstrip("/")
        for tag in self.link_tags:   # same destination as an existing link: reuse it, tracking tags and all
            m = re.search(r'href="([^"]*)"', tag)
            if m and html.unescape(m.group(1)).split("?")[0].rstrip("/") == bare:
                return tag
        return re.sub(r'href="[^"]*"', lambda _: f'href="{html.escape(href)}"', self.link_tags[0], count=1)

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack:
                top = self.stack.pop()
                self.out.append(f"</{top}>")
                if top == tag:
                    break

    def handle_data(self, data):
        self.out.append(encode(data))

    def result(self):
        self.close()
        while self.stack:
            self.out.append(f"</{self.stack.pop()}>")
        return "".join(self.out).strip()


def link_tags(blocks):
    return [a["tag"] for b in blocks if b["kind"] in ("p", "li") for a in b.get("anchors", [])]


def to_source(simplified, block, blocks):
    builder = Rebuilder(block.get("anchors", []), link_tags(blocks))
    builder.feed(simplified)
    inner = builder.result()
    if not re.sub(r"<[^>]+>|&nbsp;|\s", "", inner):
        raise ValueError("The paragraph is empty. Use Delete to remove it.")
    return inner


def plain(simplified):
    return html.unescape(re.sub(r"<[^>]+>", "", simplified.replace("<br>", "\n"))).strip()


def edit_block(text, blocks, index, simplified):
    block = blocks[index]
    if block["locked"]:
        raise ValueError("This part can only be changed in the source file.")
    if block["kind"] == "button":
        label = plain(simplified)
        if not label:
            raise ValueError("The button needs a label.")
        edits = [(block["inner_start"], block["inner_end"], encode(label))]
        # Outlook draws the button from a separate copy of the label; keep the two the same
        tag_start = block["anchors"][0]["inner_start"] - len(block["anchors"][0]["tag"])
        window = text[max(0, tag_start - 3000):tag_start]
        copies = list(re.finditer(r"(<center[^>]*>)(.*?)(</center>)", window, re.S))
        if copies and plain(copies[-1].group(2)) == plain(block["html"]):
            base = max(0, tag_start - 3000)
            edits.append((base + copies[-1].start(2), base + copies[-1].end(2), encode(label)))
    else:
        edits = [(block["inner_start"], block["inner_end"], to_source(simplified, block, blocks))]
    for start, end, new in sorted(edits, reverse=True):
        text = text[:start] + new + text[end:]
    return text


def line_bounds(text, start, end):
    """Widen start..end to whole lines when nothing else shares those lines."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    line_end = len(text) if line_end == -1 else line_end + 1
    if not text[line_start:start].strip() and not text[end:line_end].strip():
        return line_start, line_end
    return start, end


def delete_block(text, blocks, index):
    block = blocks[index]
    if block["locked"] or block["kind"] not in ("p", "li", "h"):
        raise ValueError("This part can only be removed in the source file.")
    start, end = line_bounds(text, block["outer_start"], block["outer_end"])
    return text[:start] + text[end:]


def add_after(text, blocks, index, simplified):
    block = blocks[index]
    if block["locked"] or block["kind"] != "p":
        raise ValueError("A paragraph can only be added below an ordinary paragraph.")
    indent = text[text.rfind("\n", 0, block["outer_start"]) + 1:block["outer_start"]]
    indent = indent if not indent.strip() else ""
    new = f'\n{indent}{block["start_tag"]}{to_source(simplified, {"anchors": []}, blocks)}</p>'
    return text[:block["outer_end"]] + new + text[block["outer_end"]:]
