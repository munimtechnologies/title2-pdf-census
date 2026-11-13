# Title II date slips, part 5: University of California and California State University campuses (result, 2026-11-13)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

The plan and the five predictions are in `PREREG.md`, written at about 10:55 UTC on 2026-11-13,
before any page in this frame was searched for or read. Pages were searched and read between
about 10:55 and 11:50 UTC the same day. `frame-prereg.csv` is the frame as written before
searching; `campuses.csv` gives each campus's class, the pages read and the quotes;
`outside-frame.csv` lists system pages read afterwards as context and three campus pages seen
in search results but outside the method (described, not graded).

## The question

Part 4 found, outside its frame, that UC Davis's accessibility FAQ gives "the ADA Title II
deadline on April 24, 2027". The rule (28 CFR 35.200(b), as amended by AG Order No. 6742-2026,
91 FR 20912, April 20, 2026) says **April 26, 2027** for public entities of 50,000 or more, which
includes both California university systems as parts of the State. How often do public
university campuses' own accessibility pages give a day the rule does not have, and is it a
UC-system pattern?

## Result

32 campuses: all 10 UC campuses and the 22 CSU universities. One web search each, limited to the
campus domain, with the fixed query `ADA Title II website accessibility rule compliance deadline
extension`, and up to 2 relevant pages read per campus.

| Class | UC (10) | CSU (22) | All (32) |
|---|---|---|---|
| wrong: gives a current day the rule does not have | 2 | 3 | 5 |
| right: gives a current day, every one matches | 7 | 7 | 14 |
| old_only: only the 2024 rule's April 24, 2026 | 0 | 3 | 3 |
| no_day: accessibility or rule pages, but no day | 1 | 9 | 10 |
| none: no such page in the results | 0 | 0 | 0 |

**5 of the 19 campuses that give a current day give April 24, 2027**, and every wrong day is that
one. April 24, 2027 is the 2024 rule's first day (Friday, April 24, 2026) moved forward one year;
it falls on a Saturday. The rule's day is Monday, April 26, 2027.

- **UC Irvine**, ADA Title II page (read twice): "The original DOJ deadline was April 24, 2026;
  the DOJ extended the deadline to April 24, 2027." The page never gives April 26, 2027.
- **UC Davis**, Section 504 & Title II updates page (search reader, two passes; the page reader
  got 403): "The rules now set an implementation date of April 24, 2027 for public agencies to be
  compliant."
- **Cal State Northridge**, news post "The ADA in 2026" (read twice): "The revisions now take
  effect on April 24, 2027." CSUN's own ADA Title II update page gives the deadline as April 26,
  2027 but its exception cutoffs as "prior to April 24, 2027", so one page holds both days.
- **Cal State East Bay**, Online Campus compliance page (search reader, two passes; the page
  reader failed on the certificate): "a phased two-year readiness program leading up to the April
  24, 2027 ADA Title II compliance deadline".
- **Cal Poly San Luis Obispo**, Cal Poly Report of May 6, 2026 (read twice): "...extended the
  compliance deadline for large public entities, including CSU campuses, to April 24, 2027".
  Cal State Fullerton's ATI page has nearly the same sentence with April 26, 2027, so it looks
  like a shared CSU text in which the day changed.

Other things seen:

- **The system pages give the right day** (read afterwards as context, search reader): UC's
  IMT-1300 was revised on June 3, 2026 and uses April 26, 2027 as its exception cutoff, and the
  CSU Chancellor's Office "2026 Title II Update" gives April 26, 2027. So the five slips are not
  copied from a system page. UC Davis's FAQ says IMT-1300 "still identifies April 24, 2027";
  the revised policy, as the search reader quotes it, does not.
- **3 CSU campuses still give only April 24, 2026** as the deadline (Pomona, San Francisco,
  San José) on their top pages, more than six months after the extension.
- Many "right" campuses also keep April 24, 2026 on older pages, and several UC campuses tell
  staff to keep to April 24, 2026 because of UC policy. That is a stricter campus target, not
  a misquoted rule.
- **UC Santa Barbara** says the 2024 rule requires WCAG 2.1 AA "by May 2027" and gives
  departments May 11, 2027, which is the Section 504 day; it gives no Title II day.

## Predictions

- **P1 failed:** 2 of 10 UC campuses are `wrong` (at least 3 predicted). The slip is not a
  UC-system pattern in this frame, and the UC policy itself gives the right day.
- **P2 failed:** 3 of 22 CSU campuses are `wrong` (at most 2 predicted).
- **P3 held:** 20% of UC campuses (2 of 10) against 14% of CSU campuses (3 of 22) are `wrong`.
  With 2 and 3 campuses this difference means little.
- **P4 held:** no campus page gives April 28, 2028.
- **P5 held:** 19 of 32 campuses give a current day (at least 10 predicted), against 0 of 39
  counties in part 4.

## What parts 1 to 5 show together

- The wrong days come in two kinds. Pages written for local governments (NACo, ICMA, two county
  associations, three municipal leagues, Delaware's newsletter) give NACo-style pairs or April 24
  days. University pages give one kind only: April 24, 2027, a straight one-year move of the old
  day.
- Universities write about the deadline far more than counties do (19 of 32 give a current day,
  against 0 of 39 counties), and about a quarter of those that do give a day the rule does not
  have.
- In this frame the slip was not inherited from a system policy; it appeared campus by campus.

## Limits

- One search per campus on one day; results vary. Up to two pages were read per campus, so a
  campus graded `right` may have other pages with April 24, 2027 (UCSF's IT news headline does,
  and a UC Irvine news post does; see `outside-frame.csv`).
- The page reader could not open 14 of the in-frame pages it was given (403 on 4, certificate
  errors on 10). For those, the search reader's quotes are used and marked in `campuses.csv`. Two of the
  five wrong days (UC Davis, CSU East Bay) rest on two search-reader passes, not on a page read.
- Pages were read through AI page and search readers that quote the page.
- 32 campuses in one state are not a sample of US universities. MV2's queued public-colleges
  census will measure this more widely. A date on a page is what it says, not a finding about
  whether a campus is in compliance. April 24, 2027 is two days early, so planning to it is not
  late; the issue is a stated day the rule does not have.

## Use

MV2's free a11y-statement-check (https://github.com/munimtechnologies/a11y-statement-check) flags
April 24, 2027 near ADA or Title II from version 0.11.0, which is released only once its offline
tests pass (still waiting for compute on 2026-11-13).
