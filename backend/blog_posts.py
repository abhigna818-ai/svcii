"""
Real blog post content seeded into the `posts` table by database.seed_if_empty().
Kept as a separate data module (rather than inline SQL strings) so the
content is easy to review, edit, and diff independently of the schema code.
"""

POST_1_CONTENT = """## What TROPOMI actually measures

Sentinel-5P, the European Space Agency satellite launched in 2017, carries an
instrument called TROPOMI — the TROPOspheric Monitoring Instrument. Every day,
it passes over nearly the entire planet and measures the column-averaged dry-air
mixing ratio of atmospheric methane, abbreviated XCH4, in parts per billion.
It does this by analyzing how sunlight reflected from the Earth's surface is
absorbed by methane molecules in the atmosphere above a given location. The
spatial resolution is roughly 5.5 km by 7 km per pixel for the methane product
— coarse enough that it cannot resolve a single well pad, but fine enough to
detect elevated methane concentrations over a sub-regional area like a basin.

## Why methane is the right thing to check

Methane is a disproportionately useful gas to verify independently because it
is both a potent greenhouse gas — over 80 times more warming than CO2 over a
20-year horizon — and because oil and gas operations are one of the largest
anthropogenic sources of it, mostly through leaks, venting, and incomplete
flaring rather than the intended combustion process. That means methane
emissions are largely *unintentional byproducts* of operations, which makes
them a meaningfully different signal from a company's stated production
output. A company can grow production while genuinely cutting methane
intensity, or it can report a falling intensity number while absolute
emissions still climb because production grew faster than the leak rate fell.

## How we compare a claim to a satellite trend

For each environmental claim we extract from a sustainability report, we
record whether it's framed as an absolute reduction (e.g., "cut emissions by
X tons") or an intensity reduction (e.g., "X% lower emissions per barrel
produced"), along with the claimed direction and magnitude. We then look at
the satellite-observed trend for the facility region the claim plausibly
covers, and check two things: does the *direction* match — is the
satellite-observed trend going the same way as the claim — and how close is
the *magnitude* of the satellite-observed change to the magnitude claimed.
Direction mismatches are weighted heavily in our scoring; magnitude gaps are
weighted but more forgivingly, since basin-level satellite readings and
company-level claims are never going to line up to the decimal point.

## Where this breaks down

This approach has real limits and we'd rather state them than bury them.
TROPOMI's pixel footprint can capture emissions from multiple operators
sharing a basin — a regional methane increase doesn't prove any single
company caused it. There's a temporal lag between when a company's
operational change happens and when it shows up in a multi-month satellite
average. And our current pipeline depends on which data sources are actually
reachable without paid credentials — when raw TROPOMI column data isn't
available to us (see our methodology page for exactly which API calls
succeeded and which didn't), we either substitute an alternative satellite-
informed source like Climate TRACE's asset-level emissions estimates, or we
mark the comparison as pending rather than invent a number. We'd rather show
you a gap in our data than a precise-looking figure we can't stand behind.

## Why intensity vs. absolute claims matter so much

This is probably the single most common way a technically true claim can
still be misleading. If a company doubles production and halves its
emissions *per barrel*, its intensity claim is accurate — and its absolute
emissions can still go up. Investors reading a sustainability report tend to
remember "we cut emissions" headlines more than the "per unit of production"
qualifier buried in the same sentence. That's why our E Score applies a
penalty when the claim being checked is intensity-based rather than
absolute, and why we always show which type of claim a number actually is in
the company pages, not just the headline percentage.

We built this because we think the gap between what's claimed and what's
independently observable shouldn't require a Bloomberg terminal to see. The
satellite data is public. The reports are public. We're just doing the work
of putting them next to each other.
"""

POST_2_CONTENT = """## The claim

ExxonMobil's climate and sustainability disclosures have, in recent years,
emphasized methane intensity reductions across its upstream operations,
framed against a 2016 baseline, with the Permian Basin as one of its largest
and most closely watched production regions. Intensity-based claims like
these compare emissions to production volume — they can be entirely accurate
on their own terms while absolute regional emissions move independently,
since the Permian has also seen some of the fastest production growth of any
basin in the world over the same period.

That distinction — intensity vs. absolute — is the whole reason satellite
verification is useful here. A intensity number alone cannot tell an investor
whether the *region* is emitting more or less methane in absolute terms. An
independent, basin-level measurement can at least speak to that second
question, even if it can't attribute a regional trend to a single operator.

## What we were able to verify, and what we weren't

Here's where we want to be precise about our own pipeline's limits rather
than imply more certainty than we have. Raw Sentinel-5P TROPOMI XCH4 column
data — the gold-standard source for this kind of analysis — requires a
Copernicus Data Space Ecosystem account or Google Earth Engine credentials
that this project doesn't yet have configured. Rather than fabricate a
TROPOMI-derived trend line, our pipeline falls back to Climate TRACE, a free,
public, satellite-informed emissions inventory, and is explicit in its
output about exactly what it could and couldn't establish.

What Climate TRACE's API actually gave us, as of our last pipeline run: 19
matched oil & gas assets within 80km of the Permian Basin coordinates we use
for XOM (31.5°N, 103.5°W), with combined estimated CH4 emissions of roughly
2.03 million tonnes for 2024 — the only reporting year the API exposed for
those assets through this endpoint. That's a real number from a real,
independent source, but it is a single year, not the multi-year trend a
proper YoY comparison needs, and it covers the whole matched asset cluster
near that point, not ExxonMobil's operations specifically. We do not have,
and have not invented, a 2020-2023 satellite-derived trend line for this
facility region. Getting one requires either Copernicus credentials (for raw
TROPOMI) or Climate TRACE's bulk historical CSV downloads, neither of which
this pipeline run had access to.

## What this means in practice

We're publishing this not as a verdict on ExxonMobil's Permian Basin methane
performance, but as an honest illustration of what independent verification
looks like when it's working as intended: most of the time, getting a clean
answer is harder than getting *an* answer, and the difference matters. A
platform that quietly filled in the missing trend line with a plausible-
looking number would be worse than useless — it would look more credible
than the real data supports.

## The intensity vs. absolute distinction, again

If and when we do get a full TROPOMI or bulk Climate TRACE time series for
this region, the analysis we'll run is the same one described in our
methodology: does the satellite-observed *direction* (rising or falling
basin-level methane) match the *direction* implied by the company's claim,
and how does the *magnitude* compare. An intensity claim that's accurate on
its own terms can still coexist with rising absolute regional methane if
production growth outpaces the efficiency gain — which is precisely the kind
of nuance a single percentage figure in a sustainability report can't convey
on its own.

## For ESG fund holders

If you hold a fund that includes ExxonMobil on the strength of its methane
intensity disclosures, the responsible takeaway from this case study isn't
"the data proves a divergence" — it doesn't, yet, on what we've verified.
It's that intensity-based claims deserve a second look at the absolute trend
before they're treated as a complete picture, and that independent
verification of that absolute trend is currently harder to get than it
should be for a number this consequential. We'll update this analysis as
soon as our pipeline has access to a real multi-year satellite trend for
this facility.

**Sources:** Climate TRACE (climatetrace.org), accessed via its public API;
ExxonMobil's public sustainability and climate disclosures. Facility
coordinates and full pipeline output are in this project's
`data/satellite/methane_readings.json` and `pipeline/02_fetch_satellite_methane.py`.
"""

POST_3_CONTENT = """## What asymmetric information means

In finance, an asymmetric information problem exists when one party to a
transaction has materially better information than the other, and uses that
edge to their advantage — the classic example, from Akerlof's "Market for
Lemons," is a used car seller who knows about a defect a buyer can't see.
ESG investing has its own version of this problem, and it's a particularly
clean example: companies write their own sustainability reports, choose which
metrics to disclose, choose the baseline year and the framing (intensity vs.
absolute), and face no independent verification requirement remotely as
rigorous as the audit standards applied to their financial statements.

## Why retail investors are the most exposed

Large institutional asset managers are not powerless here. Many already pay
for commercial satellite analytics, third-party ESG ratings with proprietary
methodologies, and direct access to corporate sustainability teams. That's a
real, if imperfect, check. A retail investor choosing an ESG fund from a
prospectus, or buying a stock partly because of its sustainability
narrative, has none of that. They're reading the same report as everyone
else, with none of the tools to independently check it. The information
asymmetry isn't between the company and "the market" — it's between the
company and institutions on one side, and individual investors on the other.

## What independent satellite verification changes

This is the part we think is underappreciated: a meaningful slice of the
data needed to check certain categories of ESG claims is no longer
proprietary. Atmospheric methane data from Sentinel-5P TROPOMI, nighttime
lights from NASA's VIIRS Black Marble product, land cover from ESA
WorldCover — these are public, free, and (in principle) accessible to
anyone who can write the code to query them. The asymmetry isn't really
about who can *see* the satellite data anymore — it's about who has the
time, tooling, and motivation to actually do the comparison. A platform that
does that comparison once, publicly, and shows its work, converts a
data-access asymmetry into something much smaller: a who-bothered-to-look
asymmetry.

## The regulatory landscape is moving, slowly

Disclosure regulation is starting to catch up, unevenly. India's Business
Responsibility and Sustainability Reporting (BRSR) framework now requires
the top 1,000 listed companies by market capitalization to file standardized
ESG disclosures, including some quantified environmental metrics, and BRSR
Core introduces limited third-party assurance requirements for a subset of
large companies. In the United States, the SEC's climate disclosure rule has
moved through a contested rulemaking process focused primarily on
Scope 1/2 emissions and climate risk disclosure for larger registrants, with
its scope and survival shaped by ongoing legal challenges. Neither framework,
as currently structured, requires real-time independent physical
verification of the kind satellite data can provide — they regulate what
companies must disclose, not whether an outside party checks it against
physical reality.

## What the research says about greenwashing

A growing body of academic work has documented the gap between ESG
disclosure and ESG performance — research on "talk vs. walk" discrepancies
in corporate sustainability reporting, and on the weak correlation between
different commercial ESG rating providers' scores for the same company,
both point to the same underlying issue: self-reported, lightly verified
disclosure is a noisy signal, and the noise isn't randomly distributed — it
tends to favor the entity doing the reporting.

## What SVCII does about it

We're not trying to replace ESG ratings or render a final verdict on any
company. We're trying to do one narrow thing well: take a claim a company
makes, find the most relevant independently observable satellite proxy for
it, and show you both numbers side by side, including when we don't have a
clean answer yet. That last part matters as much as the comparison itself —
a platform that's honest about its own data gaps is more useful, not less,
than one that always has a confident-looking score. Free, open-source, and
built so anyone can check our work the same way we're trying to help you
check companies' work.
"""
