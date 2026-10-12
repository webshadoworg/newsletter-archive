# 07 Hebrew

## Hebrew inside an English email

- **Wrap in `<span dir="rtl">`** inside the LTR paragraph, so bidi does not drag the surrounding
  punctuation around. The issue builder's `H()` helper does this.
- Use a Hebrew font stack. The default body stack (`'open sans', 'helvetica neue', helvetica, arial`)
  contains no Hebrew.
- **Never a real geresh or gershayim.** Write `&rsquo;` for geresh and `&rdquo;` for gershayim.
  U+05F3 and U+05F4 are *punctuation*, so the font stack is consulted from the top for them and Open
  Sans has neither; the result is tofu, which most mail clients draw as nothing at all. `מהנ״ל`
  shipped on Ki Savo as `מהנ  ל`. Make the build fail on a raw one.

**This does not apply to** the Hebrew newsletter, which ships with real Hebrew fonts installed
(`setup-fonts.sh`) and where Rafael's nikud puns depend on exact characters; or to code comments and
notes files, which are never rendered.

## Loshon kodesh

- **Print the term in Hebrew letters. Not romanized, not glossed away.** "The awe of honour" means
  nothing; יראת כבוד is a phrase the reader already owns. Romanizing is a half measure that gains
  nothing.
- Gloss only what is genuinely unfamiliar, in a clause, never by substitution.
- **Don't stack transliterated Hebrew with dash-glosses.** One or two terms the reader already owns,
  no more.

## When Mendy dictates Hebrew

Check the nusach. He sent `המחדש בטובו בכל יום טוב תמיד מעשה בראשית`; Yotzer Ohr reads
`המחדש בטובו בכל יום תמיד מעשה בראשית`. Set it correctly and tell him. Same for grammar slips in
dictated English: adopt his wording, fix typos silently, flag anything that changes meaning.

## Translating a Hebrew source into the English newsletter

- **Swap the image, not the words.** Only expressions Americans actually say. An idiom the reader has
  never heard makes him stop and decode, and the sentence dies there.
- **A pun does not survive translation.** Say so and find an English hook, or drop it.
- **Strip the Hebrew side's CTA furniture**: Israeli phone numbers, gmail addresses, Rafael's
  sign-offs. None of it belongs in the English send.
- **Strip nikud before comparing** against Sefaria, or a verbatim quote reads as missing.

## The Hebrew newsletter itself

Hebrew newsletter work belongs in **`#gye-bot-newsletters-il`** with Rafael. Point him there in one
line. Read `rafael-preferences.md` and `style-spec.md` before the first tool call, and check
`style-spec.md` before inventing a convention; it probably already answers it.

**Answer each lead in his own language.** Chayim in English, Rafael in Hebrew. The person decides,
not the thread.

**Hebrew ships as a published page or a .docx, never a .txt** - and Word only once the issue is
final. Rafael's Slack is dead on his computer, so deliver a URL rather than a Slack file.
