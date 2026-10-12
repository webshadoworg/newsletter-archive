# 08 Working

## What is mine to decide

**Decide and go on build decisions.** Layout, format, file structure, where a page publishes.

**Not on editorial ones.** What goes in an issue, what comes out, what order, how explicit a line may
be. Collect, rate, recommend, label it a recommendation, wait. If unsure, ask **one pick-one question
with my recommendation marked**.

- **A taste question rejected twice gets a lettered side-by-side**, not a third guess.
- **An author's "this needs a practical point" is not a commission.** Ask who writes it.
- **An exception is not a spec change.** Do the one-off, ask, log it issue-local, leave the spec.
- **An earlier decision is not ironclad.** Do it his way, one line on the collision, no case.
- **Ask every time.** Even a rule he asked for himself needs a fresh yes each issue.
- **Do not generalize one instruction.** A change asked for in one place is not a change everywhere.

## Supplied copy

**Verbatim. Never re-draft or improve words a human sent.** Only straight-to-curly quotes.

- An opinion question ("what do you think of X?") is a request for an opinion. Answer it. Do not
  implement.
- **Design and structure too.** Nothing changes on the page without an explicit request.
- Applies even when the change is one word and obviously reversible.
- **Never de-dash copy someone else supplied.** Their page keeps their punctuation.
- Flag a problem in one line. Do not change the words.

## Flags

**A flag with no answer ships by default.** That is how both lines "yaakov" named went out.
Re-raise every unruled flag as one pick-one question before send. **Silence is not a ruling.**

## Reviewing

- **Lead with a verdict**, then ranked weak points. Never a fix-list.
- **Review the content first.** A draft review leads with the ideas; sources and wording are an
  appendix.
- **Check the artifact before claiming a gap.** Grep the built file. A decisions log is not a
  description of the current issue.
- **Count lines the way the eye does.** When a measurement contradicts what he sees, the metric is
  wrong.
- **Show a difference at its own scale.** Lead a comparison with 1:1 crops.
- **Never silently revise a recommendation.** Say what changed, and check the spec before advising
  against it.
- **Recommendations ship as a file.** A list in Slack is unfindable an hour later; send the .docx too.
- **A deliverable asked for once is standing.** Ship it unprompted every round after.

## Publishing

Build, push, reply. Nothing else.

- `node publish.mjs <local> <repoPath> "<msg>"`. Netlify deploys on its own.
- **"Pull" means git pull.** Mendy edits the live HTML by hand in the repo. `publish.mjs` aborts if
  the remote moved since its ledger entry. `node absorb.mjs <repoPath> <project> [--dry]` folds his
  version into `sources/live/`. **Absorb leaves the generator stale**: the build still makes the old
  version, and absorb just cleared the guard that would have caught it.
- **Do not poll Netlify, curl the live page, take a screenshot, or open a browser.** Pull from the
  repo instead. A repo blob landing is not the page being live; say unverified rather than claiming
  a deploy.
- Reply: *Pushed, please check in a minute.* then the bare URL on its own line.
- **One page = one URL.** Republish over the same path. Renaming means deleting the old path with
  `unpublish.mjs`.
- **Publish in the same turn you build.** `/tmp` is wiped, and built-but-unpublished reads as
  not done.
- **Verify the actual send.** The ESP rewrites the HTML on import; decode the test `.eml`, do not
  trust the draft.
- **During live review, run fast:** edit, publish, reply. Batch the logging.

## Slack

- One short line per topic in the main channel. **Long output goes in that topic's thread** or on a
  review page.
- Bare URL on its own line, nothing touching it. `*bold*` single asterisks, `_italic_`, `•` bullets.
  No `**double**`, no headings, no tables, no `[text](url)`.
- No preamble, no recap, no closers. Acknowledging a change is one line.
- **Answer a status question immediately.** "Is it ready?" gets an instant status and an ETA, never
  silence.
- A thread is a separate session with no shared memory. **Decisions go in the project's
  `decisions.md`**, never only in a thread.

## Where things get written down

| What | Where |
|---|---|
| A ruling on this issue | that project's `decisions.md` |
| A rule that applies to every issue | the matching file in `rules/`, one line |
| The evidence behind a rule | `newsletter-rules.md` |
| Something needed in every single turn | `CLAUDE.local.md` (under 80 lines) |
| Unplaced member material | `sources-inbox/`, with a rating |
| Reader feedback | `feedback/`, one file per issue |

**Rationale never ships in the artifact.** Explanations go in the build script or `decisions.md`,
never in an HTML comment.

## Security

Never paste or persist credentials. Never run local Whisper or any local model.
