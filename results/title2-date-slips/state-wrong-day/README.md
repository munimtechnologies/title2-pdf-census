# Title II date slips, part 9: searching 25 state government domains for "April 24, 2027" (result)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0. Plan:
[PREREG.md](PREREG.md), written on 2026-11-13 after this run began (22:30 UTC) and before any
search in this part. The searches and reads ran later in the same run, on 2026-11-13. Data:
[states.csv](states.csv) (one row per state), [hit-pages.csv](hit-pages.csv) (every page counted,
with its quote and how it was read) and [candidates.csv](candidates.csv) (pages that looked like
hits but were not counted, and why).

**Three of four predictions held (S1, S2, S3); S4 failed. 7 of the 25 most populous states have
at least one page on their state domain giving April 24, 2027 as the ADA Title II day, 18 pages in
all. One is a state's binding IT policy: New York's statewide accessibility policy NYS-P08-005,
last modified on 7 October 2026, says "The current compliance deadline is now April 24, 2027."**

## What was done

Parts 7 and 8's method, unchanged except the levels: for each of the 25 most populous states in
the 2020 Census, one web search limited to the state's government domain (two domains for
Florida, Georgia and Wisconsin) with the fixed query `"April 24, 2027" ADA Title II
accessibility`. Every result that the search's title, snippet or summary tied to April 24, 2027
was read. A page counts as a **hit** if a sentence on it gives April 24, 2027 as an ADA Title II
(or "federal") compliance day, deadline, effective day or content cutoff. The rule, 28 CFR
35.200(b) as amended by AG Order No. 6742-2026 (91 FR 20912, April 20, 2026), has April 26, 2027
for public entities of 50,000 or more, which includes every state; before the amendment it had
April 24, 2026 for them and April 26, 2027 for smaller entities.

## What was found

| Group | Searched | With a hit | Share |
|---|---|---|---|
| States (this part) | 25 | 7 | 28% |
| CSU campuses (part 8) | 22 | 3 | 13.64% |
| UC campuses (part 7) | 10 | 2 | 20% |
| Big Ten universities (part 7) | 15 | 6 | 40% |

The 7 states: New York, Illinois, Michigan, Washington, Tennessee, Maryland and Wisconsin. Illinois's
only hit page is a regional planning agency's (`other`); without it, 6 of 25 (24%).

Who publishes the 18 pages:

| Level | Pages | Pages |
|---|---|---|
| `central` | 1 | New York ITS, statewide policy NYS-P08-005 |
| `agency` | 16 | Michigan Auditor General (9 pages with one disclaimer) and Department of Civil Rights; Maryland Division of Rehabilitation Services (2) and Board of Physical Therapy Examiners; Tennessee Comptroller's audit manual (markup copy); Washington House Democratic Caucus; Wisconsin Department of Public Instruction |
| `other` | 1 | Chicago Metropolitan Agency for Planning, training captions |

Counting the Auditor General's nine pages as one, 8 of 10 publishers are agencies and 1 is central.

None of the 18 pages was seen giving April 26, 2027 as well, though for the three PDFs the search
reader quoted only parts of the text.

### Two ways to reach the wrong day (sorted after reading; not pre-registered)

- **After the extension (5 states, 15 pages):** the page reads the April 2026 extension as "one
  year after April 24, 2026". New York's ITS policy says the Justice Department "postponed
  application of the rule ... through an Interim Final Rule published on April 20, 2026. The
  current compliance deadline is now April 24, 2027" (its December 2025 version said April 24,
  2026). Maryland's Division of Rehabilitation Services says the Department "has delayed the
  implementation of the new regulations until April 24, 2027". Michigan's Auditor General marks
  archived reports as published "before the April 24, 2027 compliance date", while its own
  accessibility statement still says "the April 24, 2026 accessibility compliance date". The
  Tennessee Comptroller's audit manual markup copy says April 24, 2027, while the final manual
  says April 26, 2027. Washington's House Democratic Caucus names "the April 24, 2027 federal
  deadline" (the page has no date, but a state's day was 2026 before the extension); Maryland's
  physical therapy board dates its archive cutoff April 24, 2027.
- **Before the extension (3 states, 3 pages):** the page gives April 24, 2027 as the 2024 rule's
  day for smaller entities, which was April 26, 2027: Wisconsin DPI's newsletter of 17 March
  2026, Michigan Civil Rights' transition plan ("smaller communities by April 24, 2027") and
  CMAP's training ("by April 26, 2026, or April 24, 2027", the two days swapped).

Michigan has pages of both kinds.

## Predictions

| Prediction | Line | Result | Held |
|---|---|---|---|
| S1: states with a hit | at least 3 | 7 of 25 | yes |
| S2: states with a hit | at most 9 | 7 of 25 | yes |
| S3: `agency` hit pages more than `central` | more | 16 against 1 (8 publishers against 1) | yes |
| S4: hit pages that also give April 26, 2027 | at least 1 | 0 seen | no |

## What this changes

State government pages carry the wrong day at a rate between the CSU's and the Big Ten's, but in a
different place. At universities, 11 of 19 hit pages were central (parts 7-8); at states, 1 of 18
is, and the central IT and accessibility offices that the search results showed in passing (for
example Georgia, North Carolina, Colorado, Minnesota, Ohio, Missouri, Massachusetts, Illinois DoIT
and New Jersey's OIT) give April 26, 2027. The exception matters most: New York's is a policy that
state entities must follow, revised on 7 October 2026, more than five months after the extension.

## Not counted (see candidates.csv)

- The search reader said New Jersey's Web Presence Hub gives April 24, 2027. That address now
  says the page has moved, and the new page gives April 26, 2027.
- The Illinois Office of Executive Inspector General dates its archive "prior to April 24, 2027"
  but names no ADA, Title II or federal rule, so the method's tie to Title II is missing.
- A Washington Liquor and Cannabis Board handout has "WCAG 2.2 requirements until April 24,
  2027", but neither search-reader pass could say which rule it means; WCAG 2.2 is not the
  Title II standard, so it is left out.
- Pages matching only the date: hunting seasons (Pennsylvania, Ohio), a park closure (Maryland),
  a park calendar (Texas, 404 when read), a contract (Ohio, Minnesota) and an election (Alabama).

## Limits

One search per state on one day. The search tool may run reworded queries of its own, and an
index does not hold every page, so 7 of 25 is a lower bound. Agencies on other domains (for
example dhs.wisconsin.gov is in the frame but floridahealth.gov is not) were not searched. Pages
were read through AI page and search readers that quote the page; three hits (New York ITS,
Michigan Civil Rights and the Tennessee Comptroller's manual, all PDFs) rest on two search-reader
passes each because the page reader could not read the file. Seven of the nine Auditor
General pages were read once, each showing the same disclaimer as the two read twice. The "two
ways" sorting was done after reading. 25 states are a fixed group, not a sample. A date on a page
is what it says, not a finding that a state is or is not in compliance, and April 24, 2027 is two
days earlier than the rule's April 26, 2027, not later.

## Use

MV2's free a11y-statement-check (https://github.com/munimtechnologies/a11y-statement-check)
version 0.11.0, queued for release, adds a note for pages that name the ADA or Title II and give
April 24, 2027, April 24, 2028 or April 28, 2028.
