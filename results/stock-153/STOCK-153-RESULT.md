# Result: 222 US local governments serve CivicPlus's accessibility page still as an unedited template (stock-153)

Status: graded. Pre-registered in [PREREG.md](PREREG.md) (committed 2026-11-06 before any address in this study was read) and run once, by sealed job `stock-153-v1` on 2026-11-07 (00:14 to 00:37 UTC), after the plan, `stock153.py` 0.1.0 and the pinned `template_check.py` and `a11y_pages.py` were on main. All four predictions held.

Made by MV2 of Munim, Inc. with AI agents working for him; not yet checked by a person. Apache-2.0 (code), CC BY 4.0 (text and data). A placeholder says nothing about whether a website is accessible, the ADA Title II rule does not require an accessibility statement, and nothing here is legal advice. No government has been contacted about its page.

## Headline

MV2's [template-pages](../template-pages/TEMPLATE-PAGES-RESULT.md) re-read found 29 accessibility pages of US cities, counties and towns that were still an unedited vendor template, 28 of them at the CivicPlus address `/153/Accessibility`. That re-read only saw pages a link-following census had found. This study asked every website host in MV2's two census frames for that one address.

**222 of the 5,243 website hosts serve a flagged page at `/153/Accessibility`**: the page still says "YOURMUNICIPALITY is committed to ...", calls itself "only meant as a template", or leaves its contact section as NAME / TITLE / EMAIL / PHONE. 129 of them are hidden: the census read the government's home page but did not reach a `/153/` page from it. The link-following re-read had counted 29, so it saw about one in eight.

Those 222 are 39 of the 1,656 large-cohort hosts and 183 of the 3,587 small-cohort hosts (governments of 50,000 or more people, and of 10,000 to 49,999). They are 138 cities, 49 counties and 35 towns across 44 states, most in Massachusetts (25), California (20), Texas (19), Ohio (17) and Florida (14).

## Predictions

| | Prediction | Result | Held |
|---|---|---|---|
| S1 | At least 40 hosts serve a flagged page | 222 | yes |
| S2 | At least 5 flagged hosts are hidden | 129 | yes |
| S3 | At least 20% of stock pages are flagged | 219 of 750 (29.20%, 95% CI 26.06-32.55%) | yes |
| S4 | The flagged share of probed hosts is higher in the small cohort than in the large one | 183 of 2,972 (6.16%, 95% CI 5.35-7.08%) against 39 of 1,252 (3.12%, 95% CI 2.29-4.23%) | yes |

Gates: the frame holds 5,243 website hosts (2 rows without a usable host were dropped; one is the Connecticut town whose name and links are withheld in the published census tables), inside F1's 4,800 to 5,245, and 4,749 of 5,243 hosts (90.58%) answered, above G1's 80%. "Probed" (S4) means the address itself got an HTTP answer and robots.txt did not stop the request.

## What else the run shows (described, not graded)

- Census record of the 222: 129 hidden, 27 at the `/153/` address the census had found, 65 of governments outside the census sample and 1 whose home page the census could not read.
- Flags: "YOURMUNICIPALITY" on 213, "only meant as a template" on 214 and the NAME / TITLE / EMAIL / PHONE block on 218; most flagged pages carry all three.
- 3 flagged pages are not CivicPlus pages. For South Euclid, Ohio (Q1909193), Colfax County, Nebraska (Q484745) and Miami Lakes, Florida (Q995006) the `/153/` address redirects to an `/accessibility-statement/` page on another platform that still says "[YOUR COMPANY NAME]", a third template. They count under the plan's rules; for these three, "hidden" only means the census did not find a `/153/` page.
- The run read 750 stock pages (188 large-cohort, 562 small-cohort): CivicPlus markup, an accessibility text and a final `/153/` address. 298 of the stock pages carry the stock sentence "We work to comply with Section 508 as well as ...", and 294 carry it with the word WCAG missing ("as well as 2.0 A and AA").
- 7 `/153/` pages that the census had found are no longer a stock page, or could not be read this time.
- Seen before the plan (disclosed in PREREG.md): Alhambra, California (Q752681) and Lincoln, Rhode Island (Q1816735). Both are flagged and counted like any other host.

## Honest limits

- One address per host, read once. A template elsewhere on a site is not found, so 222 is a floor; a government may have fixed its page since.
- Being served at an address is not being linked: the study does not say whether visitors reach these pages. "Hidden" says only that the census's link rules did not reach a `/153/` page from the home page.
- The frame is the governments with a website in Wikidata that MV2's two censuses used, not every US local government; governments under 10,000 people are not in it.
- Mixed-case placeholders are not flagged by these rules; the [stock-revize](../stock-revize/STOCK-REVIZE-RESULT.md) study counts one vendor's mixed-case template.

## Files

`hosts.csv` (one row per host: status, a hash of the page text, the flags; no page text), `result.json` and `result.txt` are the run's output, unchanged. `test_stock_153_result.py` (repository root) re-grades every measure and prediction from `hosts.csv` with the pinned `stock153.py` and checks every figure in this note.

## Every flagged government

| Cohort | Wikidata ID | Name | State | Kind | Flags | Census record |
|---|---|---|---|---|---|---|
| large | Q79889 | Casa Grande | Arizona | city | muni+template_note+contact_block | hidden |
| large | Q752681 | Alhambra | California | city | muni+template_note+contact_block | hidden |
| large | Q804878 | Baldwin Park | California | city | muni+template_note+contact_block | hidden |
| large | Q370925 | Daly City | California | city | muni+template_note+contact_block | found_153 |
| large | Q375185 | Hanford | California | city | muni+template_note+contact_block | hidden |
| large | Q156361 | Lake County | California | county | muni+template_note+contact_block | hidden |
| large | Q948102 | Lake Elsinore | California | city | muni+template_note+contact_block | hidden |
| large | Q49198 | Danbury | Connecticut | city | muni+template_note+contact_block | hidden |
| large | Q755798 | Milford | Connecticut | city | muni+template_note+contact_block | hidden |
| large | Q896048 | Boynton Beach | Florida | city | muni+template_note+contact_block | hidden |
| large | Q486838 | Barrow County | Georgia | county | muni+template_note+contact_block | hidden |
| large | Q115307 | Columbia County | Georgia | county | muni+template_note+contact_block | hidden |
| large | Q200696 | Gordon County | Georgia | county | muni+template_note+contact_block | hidden |
| large | Q233892 | Rockford | Illinois | city | muni+template_note+contact_block | hidden |
| large | Q506172 | Hancock County | Indiana | county | muni+template_note+contact_block | hidden |
| large | Q491878 | Hardin County | Kentucky | county | muni+template_note+contact_block | hidden |
| large | Q991464 | Kenner | Louisiana | city | muni+template_note+contact_block | hidden |
| large | Q54179 | Methuen | Massachusetts | city | muni+template_note+contact_block | hidden |
| large | Q326295 | Plymouth | Massachusetts | town | muni+template_note+contact_block | hidden |
| large | Q127506 | Taunton | Massachusetts | city | muni+template_note+contact_block | hidden |
| large | Q485392 | Pearl River County | Mississippi | county | muni+template_note+contact_block | hidden |
| large | Q170433 | Passaic | New Jersey | city | muni+template_note+contact_block | found_153 |
| large | Q489616 | Lea County | New Mexico | county | muni+template_note+contact_block | hidden |
| large | Q835831 | Mount Vernon | New York | city | muni+template_note+contact_block | found_153 |
| large | Q71100 | Steuben County | New York | county | muni+template_note+contact_block | hidden |
| large | Q600301 | Troy | New York | city | muni+template_note+contact_block | hidden |
| large | Q56146 | Wayne County | New York | county | muni+template_note | found_153 |
| large | Q507782 | Moore County | North Carolina | county | muni+template_note+contact_block | hidden |
| large | Q508209 | New Hanover County | North Carolina | county | muni+template_note+contact_block | hidden |
| large | Q507826 | Pender County | North Carolina | county | muni+template_note+contact_block | hidden |
| large | Q402938 | Hancock County | Ohio | county | muni+template_note+contact_block | hidden |
| large | Q302852 | Lincoln County | Oregon | county | muni+template_note+contact_block | hidden |
| large | Q484346 | Yamhill County | Oregon | county | muni+template_note+contact_block | hidden |
| large | Q335955 | Hendersonville | Tennessee | city | muni+template_note+contact_block | hidden |
| large | Q110486 | Kaufman County | Texas | county | contact_block | hidden |
| large | Q844012 | Lynchburg | Virginia | city | muni+template_note+contact_block | hidden |
| large | Q493243 | Island County | Washington | county | muni+template_note+contact_block | hidden |
| large | Q988065 | Spokane Valley | Washington | city | muni+template_note+contact_block | hidden |
| large | Q500908 | Portage County | Wisconsin | county | muni+template_note+contact_block | hidden |
| small | Q79675 | Albertville | Alabama | city | muni+template_note+contact_block | not_sampled |
| small | Q79242 | Hartselle | Alabama | city | muni+template_note+contact_block | hidden |
| small | Q79870 | Northport | Alabama | city | muni+template_note+contact_block | not_sampled |
| small | Q717385 | Arvin | California | city | muni+template_note+contact_block | not_sampled |
| small | Q127856 | Beverly Hills | California | city | muni+template_note+contact_block | not_sampled |
| small | Q986867 | Burlingame | California | city | muni+template_note+contact_block | hidden |
| small | Q985346 | Fillmore | California | city | muni+template_note+contact_block | not_sampled |
| small | Q917531 | Imperial Beach | California | city | muni+template_note+contact_block | not_sampled |
| small | Q984605 | Kerman | California | city | muni+template_note+contact_block | hidden |
| small | Q862700 | King City | California | city | muni+template_note+contact_block | not_sampled |
| small | Q948059 | Los Alamitos | California | city | muni+template_note+contact_block | found_153 |
| small | Q1011108 | Millbrae | California | city | muni+template_note+contact_block | not_sampled |
| small | Q985259 | Parlier | California | city | muni+template_note+contact_block | not_sampled |
| small | Q986098 | Ripon | California | city | muni+template_note+contact_block | not_sampled |
| small | Q506402 | Truckee | California | town | muni+template_note+contact_block | hidden |
| small | Q985255 | Wasco | California | city | muni+template_note+contact_block | not_sampled |
| small | Q648835 | Wildomar | California | city | muni+template_note+contact_block | hidden |
| small | Q755226 | Cheshire | Connecticut | town | muni+template_note+contact_block | not_sampled |
| small | Q165613 | Darien | Connecticut | town | muni+template_note+contact_block | not_sampled |
| small | Q1898623 | Waterford | Connecticut | town | muni+template_note+contact_block | not_sampled |
| small | Q755736 | Smyrna | Delaware | town | muni+template_note+contact_block | hidden |
| small | Q809580 | Bartow | Florida | city | muni+template_note+contact_block | hidden |
| small | Q2153615 | DeBary | Florida | city | muni+template_note+contact_block | hidden |
| small | Q488796 | DeSoto County | Florida | county | muni+template_note+contact_block | hidden |
| small | Q984368 | Fort Walton Beach | Florida | city | muni+template_note+contact_block | not_sampled |
| small | Q972057 | Lady Lake | Florida | town | muni+template_note+contact_block | hidden |
| small | Q989484 | Lake Mary | Florida | city | muni+template_note+contact_block | hidden |
| small | Q1992911 | Lantana | Florida | town | muni+template_note+contact_block | hidden |
| small | Q501022 | Levy County | Florida | county | muni+template_note+contact_block | hidden |
| small | Q995006 | Miami Lakes | Florida | town | bracket | hidden |
| small | Q986174 | Sebastian | Florida | city | contact_block | not_sampled |
| small | Q2180831 | Sweetwater | Florida | city | muni+template_note+contact_block | hidden |
| small | Q983779 | Titusville | Florida | city | muni+template_note+contact_block | hidden |
| small | Q1778769 | Winter Haven | Florida | city | muni+template_note+contact_block | not_sampled |
| small | Q988123 | Newnan | Georgia | city | muni+template_note+contact_block | not_sampled |
| small | Q494526 | Jefferson County | Idaho | county | template_note+contact_block | not_sampled |
| small | Q577829 | Blue Island | Illinois | city | muni+template_note+contact_block | hidden |
| small | Q577334 | Danville | Illinois | city | muni+template_note+contact_block | not_sampled |
| small | Q486328 | Henry County | Illinois | county | muni+template_note+contact_block | found_153 |
| small | Q577960 | O'Fallon | Illinois | city | muni+template_note+contact_block | hidden |
| small | Q576209 | Ottawa | Illinois | city | muni+template_note+contact_block | hidden |
| small | Q432099 | Sycamore | Illinois | city | muni+template_note+contact_block | hidden |
| small | Q991162 | Woodstock | Illinois | city | muni+template_note+contact_block | hidden |
| small | Q1075822 | Auburn | Indiana | city | muni+template_note+contact_block | not_sampled |
| small | Q608120 | Shelbyville | Indiana | city | muni+template_note+contact_block | not_sampled |
| small | Q676421 | Clinton | Iowa | city | muni+template_note+contact_block | hidden |
| small | Q1903348 | Grimes | Iowa | city | muni+template_note+contact_block | hidden |
| small | Q1583523 | Emporia | Kansas | city | muni+template_note+contact_block | hidden |
| small | Q983784 | Garden City | Kansas | city | muni+template_note+contact_block | not_sampled |
| small | Q375996 | Neosho County | Kansas | county | muni+template_note+contact_block | found_153 |
| small | Q486920 | Boyle County | Kentucky | county | muni+template_note+contact_block | not_sampled |
| small | Q327012 | Bangor | Maine | city | muni+template_note+contact_block | hidden |
| small | Q1000166 | South Portland | Maine | city | muni+template_note+contact_block | hidden |
| small | Q286925 | La Plata | Maryland | town | muni+template_note+contact_block | hidden |
| small | Q755275 | Laurel | Maryland | city | muni+template_note+contact_block | hidden |
| small | Q2414308 | Belchertown | Massachusetts | town | muni+template_note+contact_block | hidden |
| small | Q54138 | Beverly | Massachusetts | city | contact_block | found_153 |
| small | Q1811258 | Dartmouth | Massachusetts | city | muni+template_note+contact_block | hidden |
| small | Q1009209 | Dennis | Massachusetts | town | muni+template_note+contact_block | not_sampled |
| small | Q1023511 | Grafton | Massachusetts | town | muni+template_note+contact_block | not_sampled |
| small | Q2414338 | Holbrook | Massachusetts | town | muni+template_note+contact_block | hidden |
| small | Q1968733 | Leicester | Massachusetts | town | muni+template_note+contact_block | not_sampled |
| small | Q54185 | Leominster | Massachusetts | city | muni+template_note+contact_block | hidden |
| small | Q2433090 | Littleton | Massachusetts | town | muni+template_note+contact_block | hidden |
| small | Q54189 | Marlborough | Massachusetts | city | muni+template_note+contact_block | hidden |
| small | Q684535 | Maynard | Massachusetts | town | muni+template_note+contact_block | hidden |
| small | Q3857885 | Milford | Massachusetts | town | muni+template_note+contact_block | hidden |
| small | Q739428 | Milton | Massachusetts | town | muni+template_note+contact_block | not_sampled |
| small | Q2302167 | North Andover | Massachusetts | town | muni+template_note+contact_block | hidden |
| small | Q2282049 | Norton | Massachusetts | town | muni+template_note+contact_block | not_sampled |
| small | Q2536847 | Rockland | Massachusetts | town | muni+template_note+contact_block | found_153 |
| small | Q54140 | Salem | Massachusetts | city | muni+template_note+contact_block | hidden |
| small | Q2536927 | Seekonk | Massachusetts | town | muni+template_note+contact_block | hidden |
| small | Q2305776 | Somerset | Massachusetts | town | muni+template_note+contact_block | hidden |
| small | Q2560012 | Southborough | Massachusetts | town | muni+template_note+contact_block | hidden |
| small | Q386170 | Westborough | Massachusetts | town | muni+template_note+contact_block | not_sampled |
| small | Q54170 | Winthrop | Massachusetts | city | muni+template_note+contact_block | hidden |
| small | Q486293 | Alpena County | Michigan | county | muni+template_note+contact_block | not_sampled |
| small | Q2729533 | Grosse Pointe Park | Michigan | city | muni+template_note+contact_block | hidden |
| small | Q502712 | Otsego County | Michigan | county | muni+template_note+contact_block | not_sampled |
| small | Q110900 | Brown County | Minnesota | county | muni+template_note+contact_block | not_sampled |
| small | Q1986533 | Farmington | Minnesota | city | muni+template_note+contact_block | not_sampled |
| small | Q828736 | Hibbing | Minnesota | city | muni+template_note+contact_block | not_sampled |
| small | Q1992863 | Lino Lakes | Minnesota | city | contact_block | found_153 |
| small | Q1992845 | Mendota Heights | Minnesota | city | muni+template_note+contact_block | hidden |
| small | Q545119 | New Ulm | Minnesota | city | muni+template_note+contact_block | found_153 |
| small | Q990850 | Otsego | Minnesota | city | muni+template_note+contact_block | hidden |
| small | Q2045704 | Robbinsdale | Minnesota | city | muni+template_note+contact_block | hidden |
| small | Q222472 | Cleveland | Mississippi | city | muni+template_note+contact_block | hidden |
| small | Q985648 | Columbus | Mississippi | city | muni+template_note+contact_block | not_sampled |
| small | Q1778760 | Gautier | Mississippi | city | muni+template_note+contact_block | hidden |
| small | Q1769542 | Ocean Springs | Mississippi | city | muni+template_note+contact_block | hidden |
| small | Q867475 | Olive Branch | Mississippi | city | muni+template_note+contact_block | hidden |
| small | Q959843 | Jackson | Missouri | city | muni+template_note+contact_block | not_sampled |
| small | Q959773 | Jennings | Missouri | city | muni+template_note+contact_block | hidden |
| small | Q484745 | Colfax County | Nebraska | county | bracket | not_sampled |
| small | Q989960 | North Platte | Nebraska | city | muni+template_note+contact_block | not_sampled |
| small | Q131908 | Hanover | New Hampshire | town | muni+template_note+contact_block | not_sampled |
| small | Q913887 | Bridgeton | New Jersey | city | muni+template_note+contact_block | hidden |
| small | Q986210 | Englewood | New Jersey | city | muni+template_note+contact_block | hidden |
| small | Q995231 | Long Branch | New Jersey | city | muni+template_note+contact_block | hidden |
| small | Q1003082 | Rahway | New Jersey | city | muni+template_note+contact_block | found_153 |
| small | Q287382 | Westfield | New Jersey | town | contact_block | found_153 |
| small | Q478456 | Amsterdam | New York | city | muni+template_note+contact_block | hidden |
| small | Q2485680 | Bedford | New York | town | muni+template_note+contact_block | hidden |
| small | Q3045956 | Guilderland | New York | town | muni+template_note+contact_block | hidden |
| small | Q304801 | Middletown | New York | city | muni+template_note+contact_block | hidden |
| small | Q1018321 | Mount Pleasant | New York | town | muni+template_note+contact_block | hidden |
| small | Q2889867 | North Castle | New York | town | muni+template_note+contact_block | hidden |
| small | Q876191 | Peekskill | New York | city | muni+template_note+contact_block | not_sampled |
| small | Q632476 | Archdale | North Carolina | city | muni+template_note+contact_block | hidden |
| small | Q1019160 | Monroe | North Carolina | city | muni+template_note+contact_block | not_sampled |
| small | Q506676 | Northampton County | North Carolina | county | muni+template_note+contact_block | hidden |
| small | Q502487 | Yancey County | North Carolina | county | muni+template_note+contact_block | not_sampled |
| small | Q1052658 | Jamestown | North Dakota | city | muni+template_note+contact_block | hidden |
| small | Q651108 | Defiance | Ohio | city | muni+template_note+contact_block | home_failed |
| small | Q1004747 | Fairview Park | Ohio | city | muni+template_note+contact_block | hidden |
| small | Q490161 | Fayette County | Ohio | county | muni+template_note+contact_block | not_sampled |
| small | Q1924937 | Gahanna | Ohio | city | muni+template_note+contact_block | hidden |
| small | Q1007032 | Garfield Heights | Ohio | city | muni+template_note+contact_block | found_153 |
| small | Q590713 | Grove City | Ohio | city | muni+template_note+contact_block | not_sampled |
| small | Q113220 | Henry County | Ohio | county | muni+template_note+contact_block | found_153 |
| small | Q998575 | Mount Vernon | Ohio | city | muni+template_note+contact_block | not_sampled |
| small | Q998596 | Piqua | Ohio | city | muni+template_note+contact_block | not_sampled |
| small | Q961954 | Richmond Heights | Ohio | city | muni+template_note+contact_block | not_sampled |
| small | Q489546 | Shelby County | Ohio | county | muni+template_note+contact_block | hidden |
| small | Q1909193 | South Euclid | Ohio | city | bracket | hidden |
| small | Q476669 | Vandalia | Ohio | city | muni+template_note+contact_block | found_153 |
| small | Q960131 | Wickliffe | Ohio | city | muni+template_note+contact_block | not_sampled |
| small | Q403319 | Wyandot County | Ohio | county | muni+template_note+contact_block | hidden |
| small | Q146811 | Zanesville | Ohio | city | muni+template_note+contact_block | found_153 |
| small | Q1017220 | El Reno | Oklahoma | city | muni+template_note+contact_block | hidden |
| small | Q450100 | Ashland | Oregon | city | muni+template_note+contact_block | hidden |
| small | Q1822776 | Cornelius | Oregon | city | muni+template_note+contact_block | hidden |
| small | Q3448655 | Forest Grove | Oregon | city | muni+template_note+contact_block | not_sampled |
| small | Q1056542 | Easton | Pennsylvania | city | muni+template_note+contact_block | hidden |
| small | Q1143667 | Cumberland | Rhode Island | town | muni+template_note+contact_block | not_sampled |
| small | Q1816735 | Lincoln | Rhode Island | town | muni+template_note+contact_block | not_sampled |
| small | Q1023649 | Gaffney | South Carolina | city | muni+template_note+contact_block | found_153 |
| small | Q773325 | Spartanburg | South Carolina | city | muni+template_note+contact_block | not_sampled |
| small | Q502210 | Williamsburg County | South Carolina | county | muni+template_note+contact_block | found_153 |
| small | Q484780 | Beadle County | South Dakota | county | muni+template_note+contact_block | found_153 |
| small | Q1065503 | Watertown | South Dakota | city | muni+template_note+contact_block | hidden |
| small | Q2354644 | Portland | Tennessee | city | muni+template_note+contact_block | hidden |
| small | Q2272529 | Red Bank | Tennessee | city | muni+template_note+contact_block | hidden |
| small | Q449033 | Alvin | Texas | city | muni+template_note+contact_block | not_sampled |
| small | Q108534 | Andrews County | Texas | county | muni+template_note+contact_block | found_153 |
| small | Q812071 | Bay City | Texas | city | muni+template_note+contact_block | found_153 |
| small | Q144856 | Bonham | Texas | city | muni+template_note+contact_block | not_sampled |
| small | Q638841 | Burkburnett | Texas | city | muni+template_note+contact_block | not_sampled |
| small | Q26598 | Chambers County | Texas | county | muni+template_note+contact_block | hidden |
| small | Q982554 | Coppell | Texas | city | muni+template_note+contact_block | hidden |
| small | Q534669 | Denison | Texas | city | muni+template_note+contact_block | not_sampled |
| small | Q976983 | Donna | Texas | city | muni+template_note+contact_block | hidden |
| small | Q26492 | Forest Hill | Texas | city | muni+template_note+contact_block | hidden |
| small | Q476497 | Friendswood | Texas | city | muni+template_note+contact_block | found_153 |
| small | Q26500 | Haltom City | Texas | city | muni+template_note+contact_block | hidden |
| small | Q115428 | Kendall County | Texas | county | muni+template_note+contact_block | hidden |
| small | Q52996 | Marshall | Texas | city | muni+template_note+contact_block | found_153 |
| small | Q620305 | Prosper | Texas | town | muni+template_note+contact_block | hidden |
| small | Q975173 | Royse City | Texas | city | muni+template_note+contact_block | found_153 |
| small | Q979784 | Terrell | Texas | city | muni+template_note+contact_block | hidden |
| small | Q979410 | University Park | Texas | city | muni+template_note+contact_block | hidden |
| small | Q115481 | Alpine | Utah | city | muni+template_note+contact_block | not_sampled |
| small | Q31058 | Burlington | Vermont | city | muni+template_note+contact_block | hidden |
| small | Q26065 | South Burlington | Vermont | city | muni+template_note+contact_block | not_sampled |
| small | Q490325 | Appomattox County | Virginia | county | muni+template_note+contact_block | hidden |
| small | Q505886 | Halifax County | Virginia | county | muni+template_note+contact_block | hidden |
| small | Q502235 | Hopewell | Virginia | city | muni+template_note+contact_block | hidden |
| small | Q513891 | Madison County | Virginia | county | muni+template_note+contact_block | not_sampled |
| small | Q502240 | Martinsville | Virginia | city | muni+template_note+contact_block | hidden |
| small | Q514024 | Patrick County | Virginia | county | muni+template_note+contact_block | hidden |
| small | Q502230 | Salem | Virginia | city | muni+template_note+contact_block | hidden |
| small | Q505834 | Scott County | Virginia | county | muni+template_note+contact_block | not_sampled |
| small | Q510947 | Shenandoah County | Virginia | county | muni+template_note+contact_block | not_sampled |
| small | Q510934 | Warren County | Virginia | county | muni+template_note+contact_block | not_sampled |
| small | Q868700 | Centralia | Washington | city | muni+template_note+contact_block | hidden |
| small | Q988279 | East Wenatchee | Washington | city | muni+template_note+contact_block | hidden |
| small | Q484150 | Lincoln County | Washington | county | muni+template_note+contact_block | not_sampled |
| small | Q1507840 | Lynden | Washington | city | muni+template_note+contact_block | found_153 |
| small | Q1505990 | Ridgefield | Washington | city | muni+template_note+contact_block | hidden |
| small | Q749045 | Vienna | West Virginia | city | muni+template_note+contact_block | found_153 |
| small | Q338424 | Goshen County | Wyoming | county | muni+template_note+contact_block | not_sampled |
