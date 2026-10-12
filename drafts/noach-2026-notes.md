# Noach 2026 (issue 97) - review notes

Draft: `drafts/noach-2026.html` (local only, not committed or pushed). Preview: `/workspace/noach-preview/index.html`.
Built from `bereishis-2026.html` (issue 96) skeleton, header and footer unchanged. Builder: `/workspace/noach-build/build.py`
(guards: raw U+05F3/U+05F4, em dash, banned phrases, British spellings; all pass).

## BLOCKER: D and E source text is not available to me

The full supplied text of D (Chayim #986, 1,057 words) and E (Chayim #994, 607 words) is **not** in this repo.
`noach-ideas.html` (identical to the live copy) only quotes fragments, and says the verbatim copies live in
`noach-2026/sources/` and `marriage-silver/sources/`, which are not in this clone. Also searched: the rest of the
box, Mendy's Gmail and Drive, the bot inbox. Nothing found. `noach-review-article2.html` is Rafael's Hebrew section 3 (G), not D or E.

So I wrote nothing in either member's or Chayim's voice. Both sections are built (headings, attributions, card, byline)
with red **[PLACEHOLDER: ...]** paragraphs that say in words what gets pasted, with the verified fragments as anchors.
Once the text arrives: paste, cut D to about 540, apply typo fixes only, rerun the build.

## Word counts

| Section | Words | Note |
|---|---|---|
| Opening letter (excl. "Dear Friends," and sign-off) | 65 | target 50-75 |
| Dvar Torah body | 486 | follows the Hebrew original (Mendy); title 3 words |
| TOC blurbs | 15 / 16 / 18 | fragments, no terminal periods |
| Wisdom from the Forum | 12 of ours (attribution lines) + placeholders | target ~540. Planned split: OP ~150, @theboywholived ~70, @mechazaik/@chosemyshem ~130, @BenHashemBH ~100, @noilad ~70 |
| HAVE A QUESTION? card | 57 | verbatim from Yom Kippur issue (Bereishis had no forum section, so no card to copy from it) |
| Marriage | byline 7 + placeholder | supplied draft is 607 |

## Flags needing your ruling (pick one; my recommendation marked *)

1. **Dvar Torah title.** (a)* "The Bad Teiva" (straight from התיבה הרעה) (b) "The Teiva That Only Looks Like Noach's"
2. **Rafael's CTA.** His phone-workshop notice and Israeli contact details are gone. (a)* no CTA. The piece ends on צא מן התבה, as the Hebrew does (b) add an English GYE CTA (mentor or chizuk-partner link). Who writes it?
3. **Copy-editing member posts under their own handles (OPEN, 3rd+ issue).** (a)* spelling, typos and capitalization only, never wording (b) fully verbatim (c) light trims allowed
4. **@chosemyshem quote inside a quote.** Set as "@mechazaik replied, quoting @chosemyshem:". (a)* keep that chain (b) fold it into @mechazaik's paraphrase (c) drop it
5. **"harav hagaon @chosemyshem shlita."** (a)* start the excerpt after the honorific (that's a cut, not a rewrite) (b) print it as his words
6. **Forum h2 / TOC.** (a)* thread title, "“I Need Some Help”" (short, one line) (b) use the member's actual question sentence from the OP once it's pasted, with the TOC updated to match word for word
7. **Explicitness (OPEN: sdny on Sukkos, yaakov on Bereishis).** (a)* recheck by eye after pasting D and E and bracket anything found (b) leave as supplied
8. **E: Berachos 17a scope.** The gemara is about wives waiting for husbands coming back from the beis medrash. The draft applies it to a husband 20 minutes late from a meeting. (a)* Chayim adds one line placing it as an extension (b) run as drafted (c) Chayim reframes the proof
9. **E: "It must be because it is genuinely difficult."** That's an inference. The gemara never says it. (a)* Chayim adds two words marking it as inference (b) back it with לפום צערא אגרא (Avos 5:23) (c) leave it
10. **E: which shiur.** Only a speaker page (torahanytime.com/speakers/816). (a)* Chayim names the shiur; byline stays "Based on the shiurim of R' Yitzchok Silver" (my wording) (b) run with the speaker-level byline only
11. **E: husband or couple (open since Re'eh).** (a)* husband for Part 1 as written, and settle the series direction now (b) couple, so Chayim revises
12. **E: wives read this.** "she is normal", "this is not your wife being difficult or irrational", the ambulance paragraph. (a)* get a second read before send (b) run it
13. **E: house banned constructions in supplied copy**, "Not better or worse. Differently." and "the whole marriage changes." Flagged only. Copy untouched. (a)* leave them (b) ask Chayim
14. **Subject line** (below). (a)* option 1

## Resolved (Mendy, Oct 13)

- The dvar Torah is now a close English adaptation of Rafael's Hebrew section 1, in his order and not reshaped to problem-first. Length follows the original.
- Shaarei Kedusha 1:2 and Rambam, Yesodei HaTorah 4:1 stay as cited. The Hebrew edition is a trusted source, so its citations aren't flagged.
- "Many gedolei Yisrael in recent generations called the beis medrash a teivas Noach" stays as in the Hebrew, unattributed.
- Pun: תיבה / טביעה (and the נוח / Noach play) became "In reality, it isn't a teiva at all. It's a sinking ship." That's the one bold run.
- @theboywholived appearing two issues in a row is fine, since the content is different.
- Only Rafael's phone-workshop announcement was dropped.

## Build decisions (mine, for info)

- Member story section left out because none is in the Noach materials. Bereishis had two member pieces (Day 121 and Member Story). Neither carries over.
- Dvar Torah fill is `#f1ebee` (Yom Kippur precedent) instead of Bereishis's `#fbf7e8`. Otherwise it would sit right next to the forum section's required `#fbf7e8`.
- Handles are unlinked because the thread URL and board are unknown. The "Join the conversation in the ... thread" line is left out for the same reason.
- No preheader div because the template has none. Set the preheader in the ESP. `<title>` = subject option 1.
- Hebrew צא מן התבה goes in `<span dir="rtl">` with the Hebrew font stack, with nikud and no taamim, checked against Sefaria (Bereishis 8:16, 6:14).
- Issue number: neither file prints an issue number. The only "96" in either one is Outlook's `<o:PixelsPerInch>96</o:PixelsPerInch>` DPI setting, which stays at 96 (changing it would break Outlook scaling).
- Body text is left-aligned. Justified isn't confirmed for the English send.

## Subject and preheader

1. * It is filtering my own brain
2. The bad teiva
3. The filter is on. Now what?

Preheader: A filter stops the screen. This week: what to do when the fight moves into your head, and why hiding it only looks safe.

## Uncertain / unchecked

- Re-run check: the `campaigns/` archive isn't in this clone, so I'm relying on the ideas page (A, D and E: zero hits in 151 issues). The archive has no Noach 5786 campaign (Oct 2025 gap).
- The card markup copies the Yom Kippur version (mailto link at 16px inside 15px text). Shoftim's has 15px. Wording is identical.
