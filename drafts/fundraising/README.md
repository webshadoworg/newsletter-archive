# Fundraising emails

A fundraising email usually goes out through more than one system. The wording is the same; a few
technical details differ. So each email is written once, in `_src/`, and a script builds a version
for each system. This applies to fundraising emails only, not to the rest of `drafts/`.

## What differs between the versions

| | Mailchimp | GYE mailer |
|---|---|---|
| Preheader | the `*\|MC_PREVIEW_TEXT\|*` tag; you type the sentence into Mailchimp's preview field | the sentence itself, inside the hidden div in the HTML |
| Greeting | a Mailchimp merge tag, e.g. `*\|IF:GREET\|*Dear *\|GREET\|*,*\|ELSE:\|*Dear Friend of GYE,*\|END:IF\|*` | plain text, e.g. `Dear Member,` |
| Footer | our Unsubscribe pill (not a duplicate of Mailchimp's link), then our own footer: "To donate by check" with `*\|LIST:ADDRESSLINE\|*` (one plain line that takes our styling; `*\|HTML:LIST_ADDRESS_HTML\|*` prints its own unstyled block with an "Add us to your address book" link), copyright, update preferences / `*\|UNSUB\|*`. Because the address and unsubscribe are Mailchimp's own tags, Mailchimp does not append its footer bar and the blank lines that come with it. A typed-out address does not count | the members footer: address, Manage Your Preferences (`{{preferenceUrl}}`), Unsubscribe from this list (`{{leaveCurrentSeriesOrListUrl}}`) |
| `utm_source` | `mc` | `members` |
| `utm_content` | the same in both, e.g. `erev-yk-teshuva` | |
| "Prefer to mail a check?" line | left out; the footer has the address | in the body |

## Changing the text

1. Edit `_src/<name>.src.html`. This is the only file you edit.
2. Run `python3 drafts/fundraising/_src/build.py` from the repo root.

That rewrites every version. Do not edit the built files (`<name>.html`, `<name>-members.html`);
the next build overwrites them. The tool below does both steps for you.

`python3 drafts/fundraising/_src/build.py --check` writes nothing and fails if a built file is
out of date or was edited by hand.

## The tool

`python3 drafts/fundraising/_src/tool.py`, then open <http://127.0.0.1:8822/>. Pick an email at the
top. It runs on this machine only.

- **Text.** The wording on one page: subject, preheader, both greetings, every paragraph and button,
  both footers. Click a paragraph to change it, add one below it, or delete it. Bold and links are
  kept. Saving writes to `_src/<name>.src.html` and rebuilds every version, the same as editing the
  file and running `build.py`. A paragraph with special formatting (the Hebrew sign-off, for
  example) is marked and can only be changed in the source file. Changing a button's label also
  changes the copy of it that Outlook uses.
- **Preview.** Either version, at desktop or phone width.
- **Copy.** One click copies a version's full HTML, the subject, the preheader (for Mailchimp's
  preview text field), or the plain text.
- **Links.** Every link in a version with its `utm_source` and `utm_content`. It flags a link whose
  tags differ from what that version should have, or that has none when other links to the same
  site do. "Check that the links load" opens each one without its tracking tags, so the check is
  not counted as a click from the email.
- **Settings.** Subject, preheader, the two greetings and `utm_content`.
- **Mailchimp.** "Create a Mailchimp draft" puts the Mailchimp version into Mailchimp as a draft
  campaign named after the email, with the subject and the preview text filled in. It never sends
  or schedules. Pressing it again updates the same draft (HTML, subject, preview text) and leaves
  the From line and the recipients as set in Mailchimp. The draft's id is kept in the source as
  `mailchimp.campaign_id`; if that campaign was already sent, the next push starts a new draft. A
  new draft is addressed to the whole audience, with the From line of the last campaign sent, so
  choose the segment in Mailchimp before sending. Images load from their web address
  (`gyenewsletters.netlify.app/images/...`), so a new image has to be committed, pushed and deployed
  first: the tab lists every image, says which are not on the web yet and why, and will not push
  until they all are. The API key is read at run time from
  `../gye-crm/.env` (`MAILCHIMP_API_KEY`, `MAILCHIMP_AUDIENCE_ID`). It is never stored in this
  repo, which is published.

- **Share.** The public link to each version on the Netlify site
  (`https://gyenewsletters.netlify.app/drafts/fundraising/<file>`), with a Copy link button. It
  compares the live page with what is built here and says whether the link is up to date, shows an
  older version, or is not on the site yet, and why (not committed, not pushed, still deploying).
  A link shows what was last pushed, so push before sharing. Anyone with the link can open it.

## The source file

`_src/<name>.src.html` starts with a settings block, followed by the email's HTML:

```
<!--@email
preheader: For 38 years, on Yom Kippur I was asking Him to wipe out this sin...
utm: erev-yk-teshuva
mailchimp.out: erev-yk-teshuva.html
mailchimp.greeting: *|IF:GREET|*Dear *|GREET|*,*|ELSE:|*Dear Friend of GYE,*|END:IF|*
gyemailer.out: erev-yk-teshuva-members.html
gyemailer.greeting: Dear Member,
-->
```

A plain key (`utm`) applies to every version. A key with a platform in front (`gyemailer.greeting`)
applies to that version only. A version is built only if it has an `out` line, so an email that
goes out through one system lists one.

Optional settings:

- `utm_source: x` overrides the platform's `mc` / `members`.
- `mailchimp.footer: none` leaves the footer out of that version for this email.
- `mailchimp.footer: other.html` uses a different file from `_src/partials/`.

The HTML uses these slots where the versions differ:

| Slot | Filled with |
|---|---|
| `{{PREHEADER}}` | the Mailchimp tag, or the preheader sentence |
| `{{GREETING}}` | the `greeting` setting |
| `{{UTM_SOURCE}}` | `mc` or `members` |
| `{{EMAIL_TAG}}` | the reader's own email address: `*\|EMAIL\|*` for Mailchimp, `{{email}}` for GYE mailer |
| `{{UTM}}` | the `utm` setting |
| `{{FOOTER}}` | the platform's footer from `_src/partials/`. Goes alone on its own line, inside the last cell of the email |
| `<!--@only gyemailer-->` … `<!--@end-->` | not a slot: the lines between the two markers go into that version alone (`mailchimp` works the same way). The tool labels such a paragraph |
| `{{FOOTER_GAP}}` | bottom padding of that last cell: `0` when a footer follows, `40px` when none does |

## Starting a new email

Every email has its own layout, and the build does not care what it is. A source file is ordinary
email HTML with the settings block on top and the markers from the table above placed wherever
that layout needs them. The tool reads the wording out of whatever structure it finds.

1. Write the email as `_src/<new-name>.src.html`: settings block, then the HTML with the markers
   in place. Do not carry over a `mailchimp.campaign_id` line from another email; it points at
   that email's Mailchimp draft, and a push would overwrite it.
2. Run the build. Both versions are written and the email shows up in the tool.
3. Push any new image and wait for the deploy, then create the Mailchimp draft from the tool and
   copy the GYE mailer HTML from the Copy tab.
4. Commit again afterwards: the draft push adds a `mailchimp.campaign_id` line to the source.

To bring in an email that already exists as finished HTML: swap its preheader, greeting and link
tags for the markers, cut its footer and put `{{FOOTER}}` there, add the settings block, and check
that the rebuilt Mailchimp file matches the original apart from the footer.

Copy another email's source only when the new one really is its sibling (a resend, a variant).
Then change `utm` and both `out` lines first, or the build overwrites the older email's files.

## Shared pieces

- `_src/partials/footer-mailchimp.html` and `_src/partials/footer-gyemailer.html` are shared by every
  email. Change one, run the build, and every email picks it up.
- The platform defaults (preheader tag, footer file, `utm_source`) are the `PLATFORMS` table at the
  top of `_src/build.py`. A third system is one more row there, plus its footer file.

Emails written before this setup have no file in `_src/` and are still plain hand-edited HTML.
Convert one when it next needs a change.
