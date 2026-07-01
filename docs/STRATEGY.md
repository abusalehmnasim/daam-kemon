# Daam Kemon — Strategy Memo

*A neutral price-intelligence layer for Bangladesh e-commerce. Grocery is the wedge, not the endpoint.*

---

## 1. Thesis

Bangladesh has no neutral, Bangla-native price-comparison layer. Daam Kemon's bet is
**reintermediation**: become the *front door* to every online store — the place a purchase
*starts* ("see who's cheapest, then click through") — rather than a store itself. Owning the
moment of choice is the highest-leverage position in the entire e-commerce funnel, and it can be
captured with a capital-light, scraping-first product that no incumbent is structurally able to
build.

The strategy resolves into one interlocking chain:

> **Win grocery deeply as the authority factory → let that authority carry high-margin verticals
> into search rankings → monetize those verticals plus the price dataset → compound brand into the
> only durable moat, before anyone bigger bothers to care.**

Everything below is an expansion of that sentence.

---

## 2. The opportunity

Bangladeshi shoppers don't choose between "Rupchanda 5L oil" and "Fresh 5L oil" — they choose
**5L of soybean oil from whoever's cheapest**. Existing tools (built for electronics, matching by
exact SKU) miss ~90% of that behaviour. Meanwhile:

- **No neutral aggregator exists** in the market. Global analogues (Trivago, PriceRunner, Google
  Shopping) prove the model; none serve Bangladesh well.
- **Cost-of-living is the national anxiety.** Price is emotional right now — which makes price
  content shareable and price transparency valuable.
- **Post-Evaly trust crisis.** Consumers want "cheapest *and* won't scam me," not just cheapest.
- **Incumbent SEO is weak.** Google Shopping is thin in BD; Daraz's product SEO is generic. The
  search results that decide purchases are open territory today.

---

## 3. What we're building

Not a store. A **demand-routing layer** that intercepts purchase intent, compares real prices
across stores, and routes the shopper to the best option — getting paid for the referral. The
consumer value is "know the real price"; the business value is owning the pre-purchase moment.

**Product foundation already in place:**

- A **tiered confidence-scoring matcher** + bilingual (Bangla/English) **normalizer** that collapse
  messy listings into one comparable canonical product. *This is the hard, defensible core.*
- **Five live store scrapers** (Chaldal, Shwapno, Othoba, Unimart, Daraz) feeding a normalized
  catalog; ~1,500 Daraz products live across 12 categories.
- **Basket optimizer** (cheapest single store + optimal multi-store split with delivery fees).
- **Automated daily scraping** (free GitHub Actions cron) keeping prices fresh.
- **Append-only `price_history`** — the seed of a unique, un-back-fillable dataset.
- Monetization scaffolding: neutral sponsored badge (no rank change), affiliate redirect + click
  tracking hooks.

---

## 4. The core strategic insight

The wedge and the money sit in **opposite corners** of the vertical map:

- **Grocery** = high purchase frequency (habit, daily active use) but near-zero margin (thin FMCG
  margins; most grocery stores have no affiliate program).
- **Electronics / appliances** = low frequency but real margin (bigger baskets, 4–8% affiliate).

So expansion beyond grocery isn't a nice-to-have — it's **existential to the business model**.
Grocery acquires and builds habit; the higher-margin verticals are where revenue actually lives.

But there is a deeper linkage that reorders everything (Section 5–6): **grocery is also the engine
that manufactures the domain authority the high-margin verticals need to rank.** Grocery, the
lowest-margin vertical, subsidizes the *distribution* of every vertical above it.

---

## 5. Distribution is the whole game

Reintermediation happens at the search bar. Whoever owns the result for *"rupchanda 5l tel dam
koto"* or *"cheapest fridge bangladesh"* owns the front door — before the user ever opens Daraz.

**SEO is the compounding engine, but it has its own cold-start** (3–6 months, rewards authority a
new site lacks). So distribution is a *portfolio, sequenced over time*:

- **Now → 6 months:** Facebook (the de-facto internet in BD; deal/frugal-living communities) and
  **price-anxiety content** ("oil up ৳40 this week" — inherently shareable, and we own the data to
  produce it weekly). Messaging-native alerts (Messenger/WhatsApp/Telegram), not email.
- **Compounding layer:** SEO. Win **comparison and long-tail price intent** ("X price comparison
  bd", "X dam koto", "cheapest X") — our natural territory. *Cede* brand/transactional head-terms
  to Daraz. Requires the SEO foundation we have not yet built (see Roadmap).
- **Endgame:** **brand + direct traffic** — the only un-copyable, platform-independent moat.
  Sequence: SEO + social *acquire* → alerts + habit *retain* → repeated use becomes *brand* →
  brand becomes *direct traffic* (which is itself a top ranking signal, so it compounds back).

### The keystone: the price-data flywheel

One asset — `price_history` — powers a self-reinforcing loop and five payoffs:

> price-history data → weekly **price index** → **media cites it** (a neutral price index during an
> inflation crisis is *news*) → **backlinks + brand searches** → **SEO rankings + traffic** → more
> users + richer data → (loop).

The same dataset is also the **B2B product**. One asset drives viral content, PR, backlinks, SEO
authority, *and* revenue. This is the linchpin of the entire strategy — protect and instrument it
now.

---

## 6. Vertical sequencing (a three-axis decision)

The right next vertical scores on **matching tractability × margin × SEO-winnability** (search
demand ÷ incumbent strength) — and crucially, **whether it extends grocery's PR/authority engine.**

| Vertical | Matching | Margin | SEO-winnable | Extends grocery authority engine |
|---|---|---|---|---|
| **Grocery** (now) | solved | very low | high — own it | it *is* the engine |
| **Personal care / pharma** | easy | low–med | high (adjacent, weak incumbents) | yes — same "essentials" story |
| **Beauty** | easy | med | medium | partial |
| **Electronics** | easy (model #) | high | low–med (strong spec sites + Daraz) | no — needs fresh authority |
| **Appliances** | easy | high | medium | weakly |
| **Fashion** | very hard | high | low (brand sites own SERPs) | no — defer |

**Sequence:** grocery (deep) → personal care / pharma → beauty → electronics / appliances → fashion.

Note electronics moves *later* than a pure-margin view suggests: it's the biggest money, but it
can't inherit grocery's PR engine and faces the toughest SERPs — so enter it once domain authority
is strong enough to compete. **Go deep before wide:** Google rewards topical authority, so
dominating BD grocery-price search *completely* comes before opening vertical #2. Expansion also
gets cheaper each time — the Nth vertical inherits the domain authority the 1st built.

---

## 7. Monetization

A capital-light business with thin per-unit economics — profitability comes from *scale × high-margin
mix × a data line that breaks the per-click ceiling.*

| Stream | Mechanic | BD reality |
|---|---|---|
| Affiliate commissions | Cut of referred sales | Daraz has a program (~4–8% electronics, ~1–4% grocery); most grocery stores have none. Early revenue ≈ electronics-on-Daraz. |
| Sponsored placement | Paid *neutral* badge, no rank change | Modest but real; protects trust only if rank stays unbought. |
| **B2B price intelligence** | Sell the dataset to brands, retailers, researchers, NGOs | Highest-margin, most defensible; monetizes grocery data affiliate can't. Year-2+, sales-heavy. |
| Direct CPA / lead-gen | Negotiated per-sale deals | For stores without affiliate programs; needs traffic leverage. |

**Per-unit math is brutal** (~৳30 per 100 sessions on electronics; near zero on grocery) — which is
exactly why free, compounding SEO is existential and the data line matters. **But cost structure is
tiny** (no inventory/logistics; free-tier hosting). Near-zero burn = long runway = time for SEO to
compound. A disciplined bootstrapper outlasts a funded competitor who must monetize before their SEO
matures.

**Monetization stages:** (0) don't monetize — build catalog + traffic + trust; (1) opportunistic
affiliate on high-margin verticals to cover hosting; (2) affiliate + sponsored become real at
traffic scale *with* a high-margin mix; (3) the B2B data line — the defensible, high-margin revenue.

---

## 8. Defensibility

Not a network-effects business, so no winner-take-all lock. Defensibility = a **compounding stack of
soft moats** + the discipline to accumulate faster than anyone catches up.

**Threat analysis:**

- **Daraz builds comparison** — *unlikely to matter.* A marketplace can't credibly compare against
  itself; users won't trust its neutrality. That structural conflict is our permanent wedge.
- **Google Shopping expands in BD** — *the real threat, but blunt.* Google under-invests in small
  markets: weak Bangla, no grocery, no basket optimizer, no local trust. Beat it by being deeper in
  one market than Google bothers to go.
- **Funded copycat** — *the highest threat.* The model is copyable, but they start at zero domain
  authority, zero price history, zero brand — years behind if we keep compounding.

**Moats, ranked by durability:** (1) brand + direct traffic (un-copyable); (2) the historical price
dataset (literally cannot be back-filled — a pure time-moat); (3) SEO real estate / domain authority
(years to accumulate); (4) matching engine + BD vocabulary (a head start, ultimately replicable);
(5) neutrality (structural vs Daraz; cheap to claim, expensive to hold — never sell rank).

**The real risk is not competition — it's never reaching escape velocity.** Most comparison sites
die from irrelevance, not from being crushed. Defense is a late-stage worry; getting to traffic-and-
habit scale is the current fight.

---

## 9. Roadmap

**Phase 1 — Win grocery + build the distribution foundation (now).**
- Build the SEO foundation that doesn't yet exist: server-rendered **product pages**
  (`/product/[slug]`) with `Product`/`Offer` JSON-LD for rich price snippets; **category hub** pages;
  a **dynamic sitemap**; ISR so pages serve instantly from the edge regardless of the free-tier
  backend. *This is the single highest-leverage build in the project.*
- Stand up the **price-index content/PR engine** off `price_history` (weekly report → Facebook + BD
  media).
- Deepen grocery coverage; instrument and preserve the price dataset (the time-moat).

**Phase 2 — First adjacent vertical.**
- Add personal care / pharma (easy matching, extends the essentials brand + PR engine).
- Turn on opportunistic affiliate (Daraz) on any high-margin traffic.

**Phase 3 — High-margin verticals + the data line.**
- Enter electronics / appliances once domain authority can compete.
- Launch the B2B price-intelligence product.

**Ongoing:** convert rented distribution (SEO/social) into owned brand; guard neutrality
religiously; stay capital-light.

---

## 10. Metrics to watch

- **Leading (Phase 1):** indexed pages, search impressions, keyword rankings on comparison/long-tail
  intent, share-of-search for "daam kemon", catalog completeness, scrape freshness.
- **Lagging (Phase 2–3):** organic sessions, outbound click-through rate, affiliate conversion &
  revenue, direct/brand traffic share, media citations / backlinks, B2B pipeline.

---

## 11. Honest caveats

- SEO is slow (3–6 months to compound) — the highest-*leverage* channel, not the fastest.
- Per-unit economics are thin; this is a 2–3-year asset-building play, not fast cash.
- The model is fundamentally copyable — defensibility is the compounding stack, not any single lock.
- Grocery monetizes poorly on its own; the whole thesis depends on the authority→high-margin handoff
  actually working.
- Neutrality is the one structural edge — selling ranking throws it away permanently.

---

*The strategy is coherent precisely because the pieces are not independent: grocery is the authority
factory, distribution is how authority becomes traffic, the price dataset is the flywheel and the
moat, and brand is the endgame that survives whatever Daraz or Google decides to do.*
