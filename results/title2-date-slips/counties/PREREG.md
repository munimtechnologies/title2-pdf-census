# Title II date slips, part 3: state associations of counties (pre-registration)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

Written on 2026-11-13 at about 04:45 UTC, before any page in this frame was searched for or
read in this run. It is committed in the same commit as the result (the publish lane runs
after the run ends), so the only proof of order is this note and the times below. What was
already known: part 1 (results/title2-date-slips/, 2026-11-12) read the National Association of
Counties (NACo) page and Texas County Progress (County Judges and Commissioners Association of
Texas); both gave wrong days (NACo: April 24, 2027 and April 28, 2028; Texas County Progress:
April 24, 2027). Part 2 (leagues/, 2026-11-13) read the Alaska Municipal League, which is also
Alaska's county (borough) association. No state county association page had been read.

## Why

Part 1 found 3 of 9 government and association pages wrong; part 2 found 3 of 23 state
municipal leagues wrong. Counties read their state association and NACo. NACo's own page gives
two wrong days, so this frame tests whether state county associations are wrong more often
than leagues, and whether NACo's April 28, 2028 travels.

## Frame

`counties.csv`: one state association of counties for each state with county government
(all but Connecticut and Rhode Island), minus Alaska (its association, the Alaska Municipal
League, was already read in part 2): 47 entries. Texas uses the Texas Association of Counties
(county.org), not the judges' association read in part 1. The list and domains were written
from memory before searching; where the domain is unsure or the association may not exist
(Delaware, Hawaii, Illinois, Massachusetts, South Dakota, Vermont), the real domain is found
with one web search for the association's name, and that is noted. An entry with no association
or no domain found is class `none` with a note.

## Method (same as part 2)

1. For each association, one web search limited to its domain with the fixed query
   `ADA Title II website accessibility rule compliance deadline extension` (no date words).
2. Read, in result order, up to 3 results that are pages on the association's domain about the
   ADA Title II web rule. PDFs and members-only pages that cannot be read are recorded as such.
3. For each page, quote every sentence giving a current Title II day (the extended dates) and
   compare with 28 CFR 35.200(b): April 26, 2027 (50,000 or more) and April 26, 2028 (under
   50,000 and special districts).
4. Each association gets one class:
   - `wrong`: at least one read page gives a current day the rule does not have;
   - `right`: at least one read page gives a current day, and every current day given matches;
   - `old_only`: Title II pages found, but they give only the 2024 rule's dates;
   - `no_day`: Title II pages found, but no day (months/years only, or unreadable);
   - `none`: no page about the Title II web rule in the results.
5. Every wrong day is read twice, in two separate fetches.

## Predictions (fixed now)

- P1: at least 1 association is `wrong`.
- P2: fewer than 1 in 3 of the associations that give a current day are `wrong` (part 2: 3 of
  23 leagues).
- P3: at least one `wrong` association also has a read page giving the rule's days (all 3
  wrong leagues did).
- P4: at least 12 of the 47 associations give a current day (`right` or `wrong`).
- P5: at least one association page gives April 28, 2028 (NACo's wrong day).

Described only, not predicted: whether NACo's page still gives April 24, 2027 and April 28,
2028 when re-read today.

## Limits known in advance

One search per association on one day; search results vary. Members-only pages are not seen.
Pages are read through an AI web reader that quotes the page.
