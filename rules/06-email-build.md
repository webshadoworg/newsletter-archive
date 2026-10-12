# 06 Email build

Table-based email HTML with inline styles. **Never build a layout from scratch.** Pull last week's
file and use it as the exact template.

## Mobile, every email

- Card table `width="100%" style="width:100%;max-width:600px"` plus an `<!--[if mso]>` 600px wrapper
  for Outlook. Never a bare `width="600"`.
- `@media (max-width:620px)`: full-bleed card, side padding to ~18px, headline down ~20%.
- **Every media-query rule must also exist inline as the default.** Clients strip `<style>`.
- `img { display:block; width:100%; max-width:<Npx>; height:auto }` on every image.
- `<meta name="viewport" content="width=device-width, initial-scale=1">` plus `format-detection`,
  `color-scheme`, `-webkit-text-size-adjust:100%`.
- Verify at a real 390px viewport: `document.documentElement.scrollWidth` must equal `innerWidth`.

## Details that bite

- **Pill buttons need a `v:roundrect` VML fallback** for Outlook.
- `border-radius` needs `border-collapse:separate` on the wrapping table. `collapse` kills it.
- **No `&mdash;` in the HTML.** Convert to ` - ` as the last step before publishing.
- **No rationale in HTML comments.** It ships inside the email.
- **Justified body text** is confirmed for the Hebrew newsletter (Rafael, Aug 13 2026): inline
  `text-align:justify` on each `<p>`, not only in `<style>`. Headlines, caption and footer stay
  centred. **Not confirmed for the English newsletter**; ask before switching it.

## Palette

GYE brand: `#624b78` purple, `#1376c8` link blue, `#e9b308` gold, `#6fcac0` teal, cream fills
(`#fbf7e8`). Campaign accent `#741B47` is separate and deliberate. Real sends are in `files/`.

## Footer

Tokens: `{{preferenceUrl}}`, `{{unsubscribeFromAll}}`, `{{email}}`, `{{mailingCampaignId}}`,
`{{leaveCurrentSeriesOrListUrl}}`. **Mailchimp campaign emails carry no footer and no preheader div.**

## Images

Run `node hebrew-newsletter/process-image.mjs <in.png> <out.jpg> <displayWidthPx>` on every supplied
image. It targets 2x display width, resamples Lanczos3 in linear light, unsharp-masks, encodes JPEG
q96. There is no imagemagick or sharp in this container. If the source is under 2x it prints a NOTE;
ask for a bigger export rather than pretending it is fixed.

- **Ask for the design source.** Never measure a colour or font off a processed export.
- **Verify text at full resolution.** A downscaled screenshot hides tofu; crop the text 1:1.
- **Don't caption what the image already says.** Read the words set into supplied artwork before
  writing a heading under it.
- **A swap is a swap.** "Try this image instead" changes one thing; a gap it leaves is a question.

## Build guards worth copying into every new issue builder

- Fail on a raw U+05F3 / U+05F4 reaching the output ([07-hebrew.md](07-hebrew.md)).
- Fail on the banned AI-voice phrases (`build-shoftim.mjs`).
- The American spelling word list (`rosh-hashana-2026/arush-copy.mjs`).

**The build script's own checks are the only verification.** Fix a failing build before pushing.
A guard I wrote myself is a check, not a ruling anyone made; read why it was written before treating
it as one.

## Print

No empty space. A half-empty page reads as a mistake. Tighten gaps and even the fills, never the
type. Placeholders must survive a paste: mark a blank in words, because highlighting is lost and a
highlighted blank becomes a printable sentence in Google Docs.
