# Title II date slips, part 2: state municipal leagues (pre-registration)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

Written on 2026-11-13 at about 01:45 UTC, before any page in this frame was searched for or
read in this run. It is committed in the same commit as the result (the publish lane runs
after the run ends), so the only proof of order is this note and the times below. What was
already known: part 1 (results/title2-date-slips/, 2026-11-12) read two league pages, League
of Minnesota Cities and Florida League of Cities, and both gave the rule's days. No other
league page had been read.

## Why

Part 1 found 3 of 23 guides giving Title II days that 28 CFR 35.200(b) does not have, and
all 3 were written for government officials (NACo, Delaware GIC, Texas County Progress):
3 of 9 government and association pages against 0 of 14 vendor, law and news pages. Every
wrong day was April 24 carried forward from the 2024 rule's first date. State municipal
leagues are the main source cities and towns read on this, so they are the next test.

## Frame

`leagues.csv`: one state municipal league for each of the 49 states that have one (Hawaii has
no municipal league; its four counties are not in this frame). The list and domains were
written from memory before searching; if a domain turns out wrong, the league's real domain is
found with one web search for its name and that is noted.

## Method

1. For each league, one web search limited to its domain with the fixed query
   `ADA Title II website accessibility rule compliance deadline extension` (no date words).
2. Read, in result order, up to 3 results that are pages on the league's domain about the ADA
   Title II web rule. PDFs and members-only pages that cannot be read are recorded as such.
3. For each page, quote every sentence giving a current Title II day (the extended dates) and
   compare with the rule: April 26, 2027 (50,000 or more) and April 26, 2028 (under 50,000 and
   special districts).
4. Each league gets one class:
   - `wrong`: at least one read page gives a current day the rule does not have;
   - `right`: at least one read page gives a current day, and every current day given matches;
   - `old_only`: Title II pages found, but they give only the 2024 rule's dates;
   - `no_day`: Title II pages found, but no day (months/years only, or unreadable);
   - `none`: no page about the Title II web rule in the results.

## Predictions (fixed now)

- P1: at least 1 league is `wrong`.
- P2: fewer than 1 in 3 of the leagues that give a current day are `wrong` (part 1: 3 of 9
  government and association pages).
- P3: every wrong current day found uses day 24 (April 24, 2027 or April 24, 2028).
- P4: at least 15 of the 49 leagues are `right` or `wrong` (give a current day).

## Limits known in advance

One search per league on one day; search results vary. Members-only pages are not seen.
Pages are read through an AI web reader that quotes the page; every wrong day is read twice.
