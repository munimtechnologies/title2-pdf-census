# Title II date slips, part 4: county websites in Maryland and Michigan (result, 2026-11-13)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

The plan and the five predictions are in `PREREG.md`, written at about 08:50 UTC on 2026-11-13,
before any county website in this frame was searched for or read. Pages were searched and read
between about 08:50 and 09:45 UTC the same day. `frame-prereg.csv` is the frame as written
before searching; `counties.csv` gives each county's class and what was read; `outside-frame.csv`
lists three pages outside the frame, described and not predicted.

## The question

Part 3 (`../counties/`) found that the Maryland Association of Counties gives "April 24, 2027"
and "April 28, 2028", the same pair as the National Association of Counties (NACo), and that the
Michigan Association of Counties gives "April 24, 2027". The rule (28 CFR 35.200(b), as amended
by AG Order No. 6742-2026, 91 FR 20912, April 20, 2026) says **April 26, 2027** (50,000 or more)
and **April 26, 2028** (under 50,000). Do those wrong days reach counties' own websites?

## Result

39 counties: all 24 Maryland jurisdictions (23 counties and Baltimore City) and Michigan's 15 most
populous counties. One web search each, limited to the county's domain, with the fixed query
`ADA Title II website accessibility rule compliance deadline extension`.

| Class | Maryland (24) | Michigan (15) | All (39) |
|---|---|---|---|
| wrong: gives a current day the rule does not have | 0 | 0 | 0 |
| right: gives a current day, every one matches | 0 | 0 | 0 |
| old_only: only the 2024 rule's days | 0 | 0 | 0 |
| no_day: web accessibility or rule pages, but no day | 9 | 5 | 14 |
| none: no such page in the results | 15 | 10 | 25 |

**No county page found gives any Title II compliance day, right or wrong.** The 14 `no_day`
counties name WCAG 2.1 (Macomb's and Livingston's pages also mention WCAG 2.2 or Title II) and
give months or years at most:

- Ottawa County, MI (web guide): the 2024 rule requires WCAG 2.1 AA "by April 2026", one date
  for every entity and still the 2024 one.
- Montgomery County, MD: its Commission on People with Disabilities' 2024 annual report (posted
  March 2026) says the county must implement the guidelines "by April 2026" (search reader).
- Talbot County, MD, council meeting of May 12, 2026: "we do have until 2028. That was recently
  extended from 2027" (search reader; the years are right for a county under 50,000).
- Queen Anne's County, MD: new web policies "implemented as of April 2026" (a start date, not a
  deadline); its statement and Macomb's were last updated in April 2026 (April 13 and April 9).

## Predictions

- **P1 held:** 0 of 39 counties are `wrong` (at most 2 predicted).
- **P2 held:** 25 of 39 are `none` (at least 20 predicted).
- **P3 not graded:** no county gives any day, so the share of `old_only` among counties that
  give one has no denominator. Two counties give the 2024 rule's April 2026 as a month (Ottawa,
  Montgomery), and none gives the new day.
- **P4 held:** no county page gives April 28, 2028.
- **P5 failed:** 0 counties give a current day (at least 3 predicted).

## Outside the frame (described, not predicted)

After the frame was graded, two web-wide searches were run for the wrong days themselves
(`"April 28, 2028" ADA Title II website accessibility` and `"April 24, 2027" ADA Title II web
accessibility county deadline`). They found:

- **ICMA**, the International City/County Management Association, article "DOJ Extends Website
  Accessibility Deadline", dated Apr 28, 2026, read twice: "Local governments with populations
  over 50,000 now have a compliance date of April 24, 2027." and "Local governments with
  populations at or below 50,000 have until April 28, 2028, to comply." This is NACo's exact
  pair, in a national association for city and county managers. The page has no byline and no
  correction note. It links the Federal Register rule and does not name NACo.
- **UC Davis**, a public university and so a Title II entity itself. Its Digital Accessibility
  FAQ says: "We are also responsible for meeting the ADA Title II deadline on April 24, 2027."
  The quote was read twice through the search reader; the page reader got 403. The same page says
  University of California policy IMT-1300 "still identifies April 24, 2027 as the effective date
  of implementation". So the day may come from the university's own policy rather than from NACo.
  A UC Davis Finance, Operations and Administration post of April 22, 2026 gives the same day, and
  a later post on that blog gives April 26, 2027. This is the first page in this series where an
  entity's own accessibility page names a Title II day the rule does not have.
- The AI search summary that answered the second query said that April 24, 2027 "is now" the
  deadline, citing NACo as "the most authoritative source for counties". A wrong day on a
  trusted association page can travel into AI-written answers as well as into copied pages.

## What parts 1 to 4 show together

- Wrong days are common on pages written **for** local governments: NACo, ICMA, the Maryland and
  Michigan county associations, three state municipal leagues, Delaware's state newsletter and
  Texas County Progress.
- In this frame they were not found on counties' **own** pages, because those pages give no day
  at all. What counties tell residents is "WCAG 2.1", "an ongoing process", or a month.
- The one entity page found with a wrong day is a public university's, where the day agrees with
  its own system policy. MV2's queued public-colleges census will measure how often college pages
  give April 24, 2027.

## Limits

- One search per county on one day. Many county pages (agenda packets, PDFs) are not indexed or
  could not be read: one Frederick agenda and Talbot's transcript came back as unreadable PDFs,
  and five pages returned 403 to the page reader (their search reader quotes are used and marked).
- For some domains the search tool ran extra, reworded searches on its own, limited to the same
  domain. Queen Anne's statement came from one of them. The classes would not change without
  them, except that Queen Anne's County would be `none`.
- Two Michigan counties now use other domains: Oakland County's oakgov.com redirects to
  oaklandcountymi.gov, and Kent County uses kentcountymi.gov. Graded by the pre-registered
  domains; one extra search on each new domain found an accessibility page (Kent: "WCAG 2.0 A and
  AA") with no Title II day, so neither class would change.
- 39 counties in two states are not a sample of US counties. A page not found is not proof a
  county has none, and a date on a page is what it says, not a finding about compliance.
- Pages were read through AI page and search readers that quote the page.

## Use

MV2's free a11y-statement-check (https://github.com/munimtechnologies/a11y-statement-check) flags
April 24, 2027, April 24, 2028 and April 28, 2028 near ADA or Title II from version 0.11.0, which
is released only once its offline tests pass (still waiting for compute on 2026-11-13).
