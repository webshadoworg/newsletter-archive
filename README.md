# GYE newsletters

Every email GYE sends to its lists, as finished HTML: the English weekly, the Hebrew
weekly gilyon (רק חזק ואמץ), fundraising emails, and one-off announcements. Netlify publishes
the whole repo as-is at <https://gyenewsletters.netlify.app/>, so any file here has a public
link at the same path. Emails load their images from that site.

## The editing tool

One local web page edits every email in this repo:

```
cd ~/projects/gye/gye-newsletters
python3 drafts/fundraising/_src/tool.py
```

Then open <http://127.0.0.1:8822/>. It lives under `drafts/fundraising/_src/` because it was
written for fundraising emails first, but the picker at the top lists the weekly newsletters
too, under **Newsletters**, newest file first. Pick one to:

- **Text** – click any paragraph to change, add or delete it. For a newsletter the edit writes
  straight into `drafts/<name>.html`; there is no build step.
- **Settings** – subject line and preheader.
- **Preview** – desktop or phone width.
- **Copy** – the full HTML to paste into the GYE mailer, the subject, the preheader, plain text.
- **Links** – every link with its utm tags, flagging the odd one out.
- **Share** – the public Netlify link, and whether the live copy matches what is here.
- **Mailchimp** – fundraising emails only: creates or updates a Mailchimp draft.

Full reference, including the fundraising source/build system: `drafts/fundraising/README.md`.

## Where things are

| What | Where |
|---|---|
| English weekly issues | `drafts/<parsha>-2026.html`, e.g. `drafts/sukkos-2026.html`, `drafts/bereishis-2026.html` |
| Hebrew weekly gilyon | `drafts/<parsha>-5787.html`, print PDF in `pdf/`, public archive at `archive/`, internal issue list `archive/nihul-*.html` |
| Hebrew issue calendar | `drafts/luach-gilyonot.html` and `files/issue-calendar.docx` (110 issues, status per issue, idea bank link) |
| Reader star ratings for the gilyon | `feedback/` (thank-you page, Apps Script, setup guide; ratings land in a Google Sheet) |
| Fundraising emails | `drafts/fundraising/` – sources in `_src/`, built per platform, see its README |
| Review and option pages | `drafts/*-review-*.html`, `*-options.html`, `*-ideas.html`, `*-candidates.html`, `*-slot.html` – working pages for deciding what goes into an issue; not emails |
| Writing rules for the English weekly | `drafts/writing-rules-aug27.html` |
| Images | `images/` – push before referencing from an email, since emails load them from the live site |
| Heavy media | moved off Netlify; `_redirects` points old URLs at GitHub releases / the `media-archive` branch |

## How a weekly issue is made

There is no generator. Each English issue is a copy of the previous one's skeleton
(header, intro letter with a bulleted table of contents, dvar Torah, member story, marriage
series, footer) with the slots filled in a Claude session, then refined in the tool. The
candidate, idea and slot pages above are that session's working notes, kept so decisions stay
checkable. The template originally came from Stripo exports; the samples and the earlier
issues (May–July 2026) are in `../stripo`, with the format rules in that folder's Claude memory.

The Hebrew gilyon follows its own RTL template and the issue calendar, and gets a PDF for print.

## Deploying

Push to `main`. Netlify deploys the repo root (`netlify.toml`). Check the Share tab in the tool
to confirm the live copy is current before sending a link or an email that references it.
