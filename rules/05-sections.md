# 05 Sections

The shape of the weekly issue. **Last week's published newsletter is the ground truth.** Open its
builder before making any style decision; it has almost certainly already answered the question.

Current template: `serve/index.html`. Reusable generator: copy `shoftim-2026/`.

## Headings: the house pattern

Where a section has a fixed series name plus a subject that changes weekly, **the changing subject
gets the 24px h2 and the series name becomes a small uppercase label above it.** Never the reverse;
the series name in big type swallows the real subject.

- **Eyebrow label:** `<p>` at `font-size:12px;font-weight:700;letter-spacing:1.6px;color:#624b78`,
  typed literally uppercase. Do not rely on `text-transform`; Outlook ignores it.
- **Never an eyebrow label for a handle.** That makes a subhead, and these sections take no subheads.

## Wisdom from the Forum

1. Fill `#fbf7e8`. Eyebrow label `WISDOM FROM THE FORUM`.
2. The question is the h2: 23px, italic, inside `<strong>`, **in curly quotes**, with a `<br/>` at
   the natural break so it sets as two balanced lines. Never bare, never one long line.
3. A member is named in a **plain body line** at his own capitalisation: `@memberhandle asked:`,
   `@anothermember replied:`. Where the column is prose, the handle runs inline in the sentence.
4. **Prose only. No standalone bold subheadings** between paragraphs.
5. Close with the standing `HAVE A QUESTION?` inset card, word for word, `chaim@guardyoureyes.org`.
   It is furniture, not new copy. If it is missing, it was dropped by mistake.

## The two quote devices, which are not interchangeable

- **White inset card** (`#ffffff`, `border-radius:12px`, `border-left:3px solid #624b78`,
  `border-collapse:separate`, 15px `#4a4a4a`, own eyebrow label) = **an editorial CTA or aside**. The
  newsletter speaking to the reader. Never a device for quoting a member.
- **Purple-rule quote** (`border-left:3px solid #624b78`, 16px, no fill) = **a member's own words**.

Getting these backwards on Haazinu left the column with no card for its CTA and the CTA vanished.

## Dvar Torah

- **A catchy, descriptive title that says what the piece is about.** Not a verse reference.
- **Never repeat the section heading as a bold line inside the body.** The h2 is the title; the body
  opens on content.
- **No subheads.** Prose only.
- **Open cold, inside the story.** No setup paragraph before the parsha arrives. Mendy, rewriting
  Chayei Sarah 2026 by hand: his first sentence is "Avraham comes to Chevron to buy a burial plot
  for Sarah." Mine spent two paragraphs on the idea first. The idea arrives out of the story.
- **Mekoros in the first third, application in the rest.** Sources up front read as the thing being
  applied. Sources in the middle, wrapped in my framing, read as evidence for my argument.
- **An abstract word owes the reader a test he can run.** If the piece names a trap, give him the
  question that tells him whether he is in it: *"Will this change what I do tonight or tomorrow?
  If it will, you're planning. If it won't, you're philosophizing."*
- **Close on the mekor, short.** Four words in bold beats a paragraph of reassurance. The
  wind-down paragraph is the one that always gets cut.
- **About 300 words.** Chayei Sarah 2026 ran 299 after he cut 424.

## Marriage column

Label `10 REALLY DUMB MISTAKES &middot; #9`, h2 the mistake name, byline below reduced to
`By Rabbi Benzion Shafier (TheShmuz.com)`. The number and name come out of the byline because the
heading carries them. It is the section readers keep; one reader archived the whole run.

## Opening letter and TOC

- One short paragraph, 50 to 75 words. Does not enumerate the articles.
- **TOC blurbs are fragments with no terminal period.** All four match.
- **The TOC's Forum question matches the section heading verbatim**, including Title Case.
- **When the dvar Torah is swapped, rewrite the opening letter's framing**, not just the clause
  naming it, and reread the whole sentence afterward.

## Subject line

Pick the line that gets the open, from **any** section. Never default to the dvar Torah.

## Review pages

A review page shows an inbox preview: from name, bold subject, grey preheader.
**Options are added, never replaced.** "Try a version where X" is a new lettered option on the
existing comparison page; "it should be X" rebuilds in place. Label each option in its own box with
its own big heading, never a stacked pair under one caption.
