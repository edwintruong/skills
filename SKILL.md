---
name: software-docs
description: Write clean, consistent software documentation that acts as a contract between backend, frontend, AI, and data engineers while remaining readable for stakeholders. Works in both directions: documenting an existing codebase or interviewing the user in rounds and writing the complete documentation set for a system that does not exist yet. References are numbered by lifecycle phase, and each provides a mandatory section layout and template. Produces Markdown with Mermaid or draw.io diagrams and a single-file HTML site. Use whenever the user asks to write, review, correct, or standardize software documentation, including system design, SDD, C4, use cases, requirements specifications, requirements elicitation, greenfield planning, actors, system boundaries, NFRs, activity diagrams, analysis classes, sequence diagrams, class diagrams, DFDs, database design, ERDs, detailed class design, UI design, screen flows, screen specifications, wireframes, mockups, API contracts, feature specifications, BRDs, business rules, ADRs, runbooks, test plans, UAT documents, user guides, CRUD matrices, decision tables, operation matrices, endpoint inventories, error catalogs, data dictionaries, use-case reviews, or Mermaid corrections, even if the user never says "documentation."
---

# Software Docs

A house style for software documentation: precise enough that two engineers on opposite sides of a boundary can build without talking, readable enough that a PM understands the top of the page. Markdown is the source of truth; HTML is a render target.

## Eleven rules that override everything

1. **Read the matching reference file before writing.** The router picks it. Never write from the router row alone.
2. **The reference's section layout is mandatory.** Its numbered sections, headings and order are fixed — do not rename, reorder, merge, drop or add one. Copy its template into the new document and fill it in. A section that does not apply gets one line saying so, never a deletion. This fixed shape is the product.
3. **A section written "per use case", "per operation," or "per screen" means every one of them, each with its own subsection.** Never use a representative sample, merge two because they look alike, or let one consolidated diagram stand in for the set. Before publishing, **count**: subsections must equal rows in the use case table, and operations must equal rows in that use case's operation matrix (rule 11). Write a consolidated overview diagram *after* the per-item diagrams, never instead of them.
4. **One numbered section of the overall table of contents is one `.md` file, and the filename carries that number.** `2.3` in the contents ⇒ `2.3-use-case-specifications.md`. This is mechanical, not aesthetic: `build_site.py` builds the sidebar **from filenames** (`PHASE_FILENAME_RE`), never from headings. A single file containing four sections therefore appears as **one** sidebar row beside a chapter that appears as four, making equivalent content look unevenly divided. Inside a file, **H2** carries either the file number plus one level (`## 3.2.2`) or an existing ID (`## UC-01 — Place order`) — use one form per document, never both. **H3** is an unnumbered named heading; **H4 does not exist**. **If another tier is needed, split the file instead of deepening the headings** (`2.3-…` → `2.3.1-…`, `2.3.2-…`): the ceiling is H3, not a digit count. The page contents list collects **H2 and H3 only**, so the fixed parts of a repeated block (*Purpose*, *Operation matrix*, …) must be **headings, not bold text**; they are reader destinations. Split a file once it exceeds roughly 40 contents entries rather than demoting headings. **A section that determines the shape of another comes first** — decisions before the diagram they produce, inventory before the picture, derived summaries last. The subsystem axis is decided once in [2.1](references/2.1-actors-and-use-cases.md) and reused with the same names and order in 2.3, 3.1–3.3, 4.3, and 4.5 — as **files**, not as another heading tier. Rules, examples, what happens to the Changelog and Open questions after a split, and the cross-document chain are in [0.1](references/0.1-visual-style.md#section-numbering-and-subsystem-tiers) and [Section order](references/0.1-visual-style.md#section-order).

5. **Never invent** an endpoint, column, rule or number. Unknown becomes `**TBD** — <what is missing> (owner: <who>)`. In mode B you may *propose* — marked `**ASSUMPTION** — <what you assumed> (confirm: <who>)` until a human confirms it. Anything unmarked means someone said it.
6. **Finish the set in the same session**: write the `.md`, update the overview page `<docs_folder>/README.md`, then rebuild the HTML site (below). A document not in the site and not on the overview page does not exist for the reader.
7. **Close the use case list before phase 3.** [2.1](references/2.1-actors-and-use-cases.md) provides six discovery passes and two coverage checks; run all of them and record the closing date. Having all use cases is one thing; ensuring that each one is **at the correct goal level and testable** is another. Run [0.8](references/0.8-use-case-constraints.md) against every block: a step at the wrong level, an unverifiable precondition, or a postcondition written as an action leaves no empty cell, so the defect appears only in [6.1](references/6.1-test-plan.md), when nobody knows what to observe. Everything downstream is written per use case, so one omission here means a missing class table, sequence diagram, screen, and test case.
8. **Draw the boundary before anything crosses it.** Name the black box being designed in [1.1.1](references/1.1-problem-survey.md#111-problem-and-system-boundary), then derive from it. **Anything this project builds, releases, or supports on call is *inside*:** it is a container in [4.1.1](references/4.1-design.md), never an actor in 2.1.1 or an external entity in 3.4. An actor table containing both an end user and one of your own services merges two boundaries — the most common defect in the entire set because it looks like architectural knowledge. Tests and worked examples: [2.1.1](references/2.1-actors-and-use-cases.md#211-identify-actors).
9. **Every component is derived and carries its evidence — but evidence and citation are different things.** No actor, use case, class, process, store, state, table, screen, interface, or test case is written from memory; each is produced by the technique named in its section ([0.5](references/0.5-derivation.md)). The `Source` cell contains the half a **reader can look up**: an upstream item (`UC-01 b3`, `FR2`, `BR-CAMP-01`, `1.1.2 N7`), a location in the code (`app/api/orders.py:41`), or a marked `**ASSUMPTION**`. The half only the *writer* can check — which interview answer settled it — lives in the `interview` block of `.software-docs.json`, because a reader without the transcript cannot verify `Q57` or distinguish a real citation from a dangling one. **Name a question by its topic, not its code** (*"round 3 — reservation expiry"*), so it still points somewhere after the codes are removed. **A `Q<n>` never becomes the subject of a sentence** — write *"The reservation expires after 60 minutes (round 3 — reservation expiry),"* never *"`Q63` determines the reservation expiry."* Codes confined to the `Source` cell and parentheses can be removed in one command; codes used as nouns must be rewritten by hand. A remembered list and a derived list look identical on the page; the difference is visible only in that column, while a missing row is invisible in both. **An empty `Source` cell is a defect**, not a blank — fill it or write `**TBD**`. Run the two-way check and **count** before publishing.

10. **A diagram is a claim about mechanism.** Before drawing an arrow, answer the five questions in [0.6](references/0.6-mechanism.md): who initiates, whether the caller waits, what actually crosses, where it becomes permanent, and what happens when it fails. If a question cannot be answered, the mechanism is unknown — put `**TBD**` in the caption instead of drawing a plausible arrow, because a picture has nowhere to say *"perhaps"* and is read as certain. Verify the diagram by reading it back: every edge becomes one sentence, and every sentence receives evidence.
11. **A name that says "manage" owes a list.** *"Manage products"* is a valid but empty use case: it does not say how many operations it contains, who performs each one, what each receives, or what each returns when it fails. That gap becomes visible only in [4.4](references/4.4-api-contract.md), as an API contract with one endpoint instead of six. Every use case with at least two operations carries an **operation matrix**, swept with the thirteen-operation checklist in [0.7](references/0.7-operations.md). Each operation is then **derived down the chain**: a numbered flow, a sequence diagram or labelled `alt`, a method with a full signature and exceptions, a table it writes, an endpoint, an error code, and a test case. Operations that differ in *who calls whom* get separate diagrams; operations that differ in *what crosses the boundary* get separate endpoints. Check by counting at every one of those seven stages. The same rule applies to *"process,"* *"configure,"* and *"monitor."*

## Two modes

| | **A · Document what exists** | **B · Design what does not exist yet** |
|---|---|---|
| Source of truth | **The code** — the document describes it | **The document** — the code will follow it |
| Your job | Read the source; write only what you verified | Interview in rounds ([0.4](references/0.4-interview.md)); propose as a marked assumption; record decisions |
| A gap means | Undocumented — go read it | Undecided — `**TBD**` with an owner |
| Doc vs code disagree | Code wins; fix the doc, report the gap | Document wins |
| Order | 4 and 5 first (readable off the code), then 1–3 as **reconstructions**, marked as such | 1 → 7 in order |

**Mode A's overriding rule: do not write a sentence you have not verified against the source.** Cite the origin (`app/agent/pipeline.py:40`) while drafting. Reverse-engineered documentation is trusted precisely because nobody rechecks it, so an invented endpoint is worse than a missing section. Intent cannot be read from code — a business rule inferred from an `if` remains a hypothesis until a human confirms it. The artifact to inspect for each component and the ways it can be misread are in [0.5](references/0.5-derivation.md#mode-a-extracting-components-from-code); every arrow in a reconstructed diagram needs its own call site before it may be drawn ([0.6](references/0.6-mechanism.md#mode-a-every-arrow-has-an-address)).

**Mode B's overriding rule: the interview is the reading.** There is no source to check against, so what would have been a wrong sentence becomes a wrong *system*. Run it as rounds over a design tree — [0.4](references/0.4-interview.md) carries the engine, the round → section map, and the question shapes that surface exception paths. Three of the techniques in [0.5](references/0.5-derivation.md) run *before* anyone answers — event partitioning, the entity category list, the empty cells of the CRUD matrix — and a half-filled table is a faster question than an open one. The two modes mix: an existing codebase plus a new feature is mode A for what is there and mode B for what is not.

## Setup: round 0

Six things are settled before the first document, by asking — all in one round, numbered, each with your recommended answer. Look up anything discoverable yourself; ask only for decisions. This is round 0 of the engine in [0.4](references/0.4-interview.md): mode A stops here and reads the code, mode B keeps running rounds through phases 1–4.

| # | Question | Default |
|---|---|---|
| 1 | **Docs folder?** One folder holds the whole numbered set | `docs/` |
| 2 | **Vietnamese or English?** See [Language](#language) | **Vietnamese** |
| 3 | **Mermaid or draw.io?** | Mermaid |
| 4 | **Existing codebase or greenfield?** The two modes above | Read the repo and propose |
| 5 | **One system or several** (admin vs user)? See [System shape](#system-shape) | Ask; rarely inferable |
| 6 | **Who is the author?** The name on every document and every changelog row | `git config user.name`; propose it and confirm |

They are worth interrupting for because each is expensive to reverse: the wrong folder breaks every link, the wrong language rewrites every sentence, the wrong diagram mode reauthors every diagram, the wrong mode writes fiction, the wrong shape splits the set later, and a missing author name puts *Claude* in the `Author` column of every changelog in the set — a document nobody signed is a document nobody owns. Everything else has a default; decide it without asking.

All five answers go into `<docs_folder>/.software-docs.json`. **Read that file first**; if it exists, those questions are already answered. In mode B, its `interview` block also records the open round, unresolved `Q<n>` items, and completed sections, so a new session resumes instead of asking again ([0.4](references/0.4-interview.md#resuming-an-interview-in-a-later-session)).

```json
{ "docs_folder": "docs", "language": "vi", "diagram_mode": "mermaid",
  "mode": "greenfield", "systems": ["admin", "user"], "author": "Alex Nguyen",
  "title": "Loan Platform Docs" }
```

Later rounds are content questions and only become answerable after round 1: what the system must never do, which flows are the money paths, what is out of scope, which decisions are one-way doors — and in mode A, which of the things you found are bugs rather than features.

## Language

One language per set. **Vietnamese is the default.** The setting governs *prose*: headings, table text, captions, explanations. It never governs anything that also exists in code or on the wire:

| Always English | Why |
|---|---|
| Field, table, column, endpoint, enum, error-code names | The doc is a contract against real identifiers |
| Code fences, JSON, SQL, shell | Copied and run verbatim |
| **MUST**, **MUST NOT**, **SHOULD**, **MAY** (RFC 2119) | Defined terms, not adjectives |
| Reference IDs — `BR1`, `FR7`, `UC-02`, `NFR3`, `TC-order-4` | Greppable across documents |
| Diagram node IDs (the identifier, not the label) | Labels are translated, IDs are not |

When a sentence in the document language names an English field, leave the field unchanged: *"`order_status` changes to `SHIPPED` when the warehouse confirms the shipment."* Agree on one term for each domain concept in the glossary ([1.2](references/1.2-business-rules.md)), then use only the document language. Reference-template headings are written in English; preserve them in generated documents unless the configured document language requires a translation.

## System shape

Many products are two: an admin console and an end-user app on one backend. **Split by reader, keep together by truth.** Splitting the whole set is the failure to avoid — two architecture diagrams of one system diverge.

| Phase | Split? |
|---|---|
| 1 Discovery | **Shared** — one business problem; the split shows up inside 1.1.2 and 1.1.7 |
| 2.1–2.3 Use cases, 2.5 feature spec | **Split** — a use case is defined by its actor. `UC-A<n>` admin, `UC-U<n>` user |
| 2.4 NFR | **Shared** — one platform, one set of quality bars; the `Applies to` column says which half a row binds |
| 3.1–3.3 Analysis | **Split like the use cases** |
| 3.4 Data flow | **Shared** — one system, one flow, or neither half balances |
| 4.1 Design | **Split 4.1.3 and 4.1.4, keep 4.1.1 and 4.1.2 whole** — one platform has one C4 and one ERD |
| 4.2 Data model · 6 Test plan | **Shared** (test cases tagged per system) |
| 4.3 SDD | Per subsystem, plus one for the seam |
| 4.4 API contract · 4.5 UI design · 7 User guide | **Split** — different consumers, different readers |

Name by suffix, never subfolder: `2.1-actors-and-use-cases-admin.md`, `2.3-use-case-specs-user.md`. **One document owns the seam and is never split** — what admin publishes, when the user side sees it, what happens when it arrives half-written. Record `"systems"` in `.software-docs.json`.

## Workflow

1. Settle the six setup questions (skip what `.software-docs.json` answers).
2. Identify the document type in the router, then **decide the file split before writing a line**: one numbered section of the contents is one file (rule 4), so a request spanning several types produces several linked files — one file, one purpose. If the shape of a repeated block needs three tiers (subsystem → use case → fixed parts), the split is already decided.
3. Collect what you know: in mode A, read the code, schema, routes, and migrations; in mode B, run **one** interview round ([0.4](references/0.4-interview.md#how-one-round-works)) — ask the entire frontier as numbered questions with a recommendation for each, wait, write the sections that the round unblocks into the real files, name those files to the user, and only then ask the next round. Never write ahead of the frontier, and never ask ahead of what has been written. When the user has only an idea and a picture of the screens, round 1 begins with a one-page restatement for correction rather than open questions, and every field imagined on a screen is recorded as an entity attribute as soon as it is mentioned ([0.4](references/0.4-interview.md#when-there-is-only-an-idea)).
4. Read the matching reference, plus `0.1` and `0.2` once per session, plus `0.5` whenever the document produces a list of components, `0.6` and `0.3` if there are diagrams, **`0.8` whenever the document contains use cases** — 2.1, 2.3, 2.5, and any review of one — and **`0.7` whenever the document produces operations or endpoints** — use case specs, sequence diagrams, class specs, the schema, the API contract, the test plan.
5. Write the Markdown, following the reference's template section by section — deriving each list by the technique `0.5` names for that section, never from memory.
6. Run that reference's **self-check table** before declaring it done, plus the list check in `0.5` and the diagram check in `0.6`.
7. Update `<docs_folder>/README.md` — the row for what you wrote, and the reading path if a new reader now has somewhere to start. Template: [0.1](references/0.1-visual-style.md#the-overview-page).
8. Rebuild the site, then **look at it** — counting headings in Markdown is not the check:
   ```bash
   python3 scripts/build_site.py <docs_folder> -o <docs_folder>/site.html --title "<title>"
   python3 scripts/serve_docs.py <docs_folder> --title "<title>"   # :8777, the rendered page
   ```
   The build prints every problem it can see on its own — `! image not found`, **dead `.md` links and `#fragments` that hit no heading**, H4 headings no contents list will show, and pages past the ~40-entry contents budget. Fix all of them before saying the set is done; a dead internal link is never reported by a reader, and a router row you satisfied by folding the content into a neighbour (`4.2` into `4.1.2`) leaves every link to it dangling. Then open the page and check the two things only the render shows: **the sidebar** — does every chapter break into a comparable number of rows, or does one chapter show a single fat file — and **the in-page contents** — are the parts a reader jumps to actually listed. A section written in bold instead of as a heading looks finished in Markdown and is invisible on the page.

## Router — one row per reference

Phase 0 applies to everything; phases 1–7 run in order. **Bold** names the document produced.

| Phase | Reference | Produces · carries |
|---|---|---|
| 0 | `0.1-visual-style.md` | Page skeleton, **section numbering + subsystem tiers**, palette, captions, tables, file naming, **the overview page** template |
| 0 | `0.2-writing-principles.md` | Interface vs implementation, completeness checklist, where to spend detail, design smells, approvals |
| 0 | `0.3-diagramming.md` | Mermaid vs draw.io per diagram type, file conventions, rendered size |
| 0 | `0.4-interview.md` | **Mode B engine** — design tree, frontier, rounds; **the ask → wait → write → show → next-round loop** and its three prohibitions; round → section map; **resuming a half-finished interview** from the `interview` block; **starting from nothing but an idea** — restatement-first round 1, and screen fields as entity evidence; question shapes; `TBD` vs `ASSUMPTION`; who can answer what |
| 0 | `0.5-derivation.md` | **Deriving components** — the evidence rule, derivation table, two-way checks, and **eleven named techniques** (events · nouns and categories · CRC · CRUD matrix · multiplicity · decision tables · states · interfaces · class-to-table mapping · vague-language detection · operation inventory), plus the section-to-technique map and mode A extraction recipes |
| 0 | `0.6-mechanism.md` | **Drawing the mechanism accurately** — the five mechanism questions, what each notation asserts, read-back verification, ten mechanism smells, one altitude per diagram, and what a picture cannot carry |
| 0 | `0.7-operations.md` | **Completing the operation set** — the operation matrix, thirteen-operation checklist, six-question split test (separate use case / diagram / endpoint), seven-stage chain for each `T<n>`, exception-to-error-code mapping, and read versus search |
| 0 | `0.9-correcting-drafts.md` | **Correcting drafts** — the read/edit/observe loop in `serve_docs.py`: click a rendered block to jump to its source, edit Mermaid with live redraw, and mark blocks that differ from the baseline; seven review passes by content type; use `TBD`/`ASSUMPTION` instead of deleting uncertainty; track the propagation of each correction |
| 0 | `0.8-use-case-constraints.md` | **Use case constraints** — six constraint families applied to **one** use case block: goal level (coffee-break test · one actor, one goal, one session) · naming (empty verbs) · flow sentences · precondition versus rule versus assumption · postcondition as state · **eight failure modes** · frequency and size thresholds; an 18-point self-check for every use case |
| 1 | `1.1-problem-survey.md` | **Discovery / BRD** — eight mandatory sections: context and **system boundary** · users · as-is process · functional requirements · function tree · IPO · constraints · plan |
| 1 | `1.2-business-rules.md` | **Business rules + glossary** — rule table, boundaries, effective dates |
| 2 | `2.1-actors-and-use-cases.md` | **2.1 Actors and use cases** — **boundary and actors** · use case table with a `Subsystem` column. Includes the three-question actor test, six discovery passes, and two coverage checks. **Establishes the subsystem axis for the entire set** and owns the Open questions table for phase 2 |
| 2 | `2.2-use-case-diagrams.md` | **2.2 Use case diagrams** — one overview diagram plus one level-2 decomposition diagram per group, each with a relationship table and conditions |
| 2 | `2.3-use-case-specs.md` | **2.3 Use case specifications** — one H2 section per use case, with seven H3 parts: attributes · purpose · **operation matrix** · flow · data fields · activity diagram. Split more than roughly five use cases by subsystem into `2.3.1-…`, `2.3.2-…` |
| 2 | `2.4-nfr.md` | **2.4 Non-functional requirements** — NFR table covering the nine ISO/IEC 25010 characteristics, with one threshold and verification method per row |
| 2 | `2.5-feature-spec.md` | **Feature specification** — one feature end to end, divided across teams, with acceptance criteria. Outside the formal report chain, use unnumbered headings |
| 3 | `3.1-analysis-classes.md` | **3.1 Identifying analysis classes** — boundary/control/entity, one table per use case. Also contains the phase 3 overview and its three rules without exceptions |
| 3 | `3.2-sequence-diagrams.md` | **3.2 Sequence diagrams for each use case** — one diagram per use case **and one per operation that changes who calls whom**, a message table with `I<n>`, plus failures, asynchrony, timeouts, and model calls |
| 3 | `3.3-class-diagrams.md` | **3.3 Class diagrams for each use case** — one diagram per use case, attributes on every entity, one operation per `T<n>`, multiplicity, and the consolidated diagram last |
| 3 | `3.4-data-flow.md` | **3.4 Data-flow diagrams** — levelled DFDs, balancing, the third coverage check, lineage altitude, and the freshness contract |
| 3 | `3.5-state-machines.md` | Notation, not a document: entity lifecycle, transition table, drawn once and referenced |
| 4 | `4.1-design.md` | **Design** — four sections: C4 · database design (ERD) · detailed class design · interface design. Sections 4.1.3 and 4.1.4 are derived from detailed use cases, not memory |
| 4 | `4.2-data-model.md` | Deep reference for 4.1.2 — ERD template, nine-column data dictionary, per-table header block, operation-level CRUD matrix, and derived tables |
| 4 | `4.5-ui-design.md` | Deep ref for 4.1.4 — six screen passes, the seven-block screen spec, worked example, wireframe vs mockup |
| 4 | `4.3-detailed-design.md` · `4.4-api-contract.md` | **SDD** and **API contract** — separate deliverables when work crosses BE/FE/AI/Data. 4.4 carries the grouped endpoint inventory, the per-group operation matrix, the field tables with constraint/unit/error columns, the service-wide error catalogue and the use case ↔ API traceability matrix |
| 5 | `5.1-codebase-guide.md` · `5.2-operations.md` | **Codebase guide** · **runbook, ADR, release notes** |
| 6 | `6.1-test-plan.md` · `6.2-uat-and-defects.md` | **Test plan**, cases, traceability · **UAT** and defect reports |
| 7 | `7.1-user-guide.md` | **User guide** — task-oriented, screenshots, tone |

If the request does not fit cleanly, ask one short question rather than guessing.

## How the layers connect

```
User need → Functional requirement → Use case → Feature spec → Design → ERD, class spec, screen spec, API contract → Test cases
  N<n>            FR<n>              UC-<n>     R<n>, AC<n>    I<n>, F<n>      field & endpoint names        TC-<area>-<n>
                                     └ T<n>  each operation runs the same chain: flow → sequence → method → table → endpoint → error code → case
                  BR<n>   business rules constrain the whole chain
                 NFR<n>   stated in 2.1, designed for in 4.1 and 4.3, verified in 6.1
```

Every numbered item cites the one to its left; that is what makes a change traceable. When writing in the middle of the chain, check the upstream citation exists — a requirement with no business rule behind it is a gap worth naming, not quietly filling.

## Order of writing

The numbering is the writing order — each phase supplies the citations the next one needs.

```
1 Discovery → 2 Specification → 3 Analysis → 4 Design → 6 Testing → 7 Guidance
```

- Phase 5 sits outside the sequence — maintained continuously alongside the code.
- **Mode A inverts it**: 4 and 5 first, then reconstruct 1–3.
- **Mode B's writing order is the interview order** — [0.4](references/0.4-interview.md) maps each round onto the sections it unblocks, so a document is written when its round closes, not at the end. A round that ends without a changed `.md` on disk did not end.
- **Phase 2 is four documents plus feature specifications** — 2.1 actors and use cases → 2.2 diagrams → 2.3 specifications → 2.4 NFRs — in that order, because each closes what the next requires: the list must close before its diagram can be drawn, and the diagram settles `<<include>>`/`<<extend>>` before the flow can be written. Point-in-time feature specifications in 2.5 sit outside that chain.
- **Phase 3 requires a closed use case list** (rule 7) and contains **four documents** — 3.1 analysis classes → 3.2 sequences → 3.3 class diagrams → 3.4 data flows — written in that order because each depends on the previous one. Section 3.4 then performs a third coverage check from the data perspective: a process with no use case, or a store that nothing writes to, reveals a missed use case.
- **Within phase 4, sections are a dependency chain**: containers decide where data can live, the schema decides what classes hold, classes decide what a screen can ask for.
- The overview page is created as soon as the set has two documents and is the last file touched every session afterwards.

When the user asks for one document in the middle, write that one — and if what it should cite does not exist, say so in a line rather than inventing the upstream content.

## Rules for every document

**Open with the metadata table**, immediately after the H1 (the overview page is the one exception — it carries everyone else's status):

```markdown
# <Document title>

| | |
|---|---|
| **Status** | Draft / In review / Approved / Deprecated |
| **Owner** | <name or team accountable for the content staying true> |
| **Author** | <who wrote this draft — round 0, question 6> |
| **Last updated** | YYYY-MM-DD |
| **Applies to** | <service, version, or release> |
```

**Author is not Owner.** The Author wrote the document and appears in the `Author` column of the changelog. The Owner remains accountable for its accuracy a year later and is often a team rather than a person. They change on different occasions: a handover changes the Owner while leaving every Author row untouched.

**Then 2–4 jargon-free sentences**: what this is, who it is for, why it exists. Everything technical goes below. That shallow layer is what lets one document serve engineers and stakeholders without watering down the deep layer.

- **Say what is binding.** RFC 2119 keywords in normative statements only, so a bolded **MUST** always means "break this and you break someone else's code".
- **Keep interface separate from implementation.** A document is either what a consumer observes (API contract, ERD, wireframe, user guide) or how something works inside (SDD, runbook). Leaking internals into an interface document is a failed abstraction — and the corollary is that the interface document must then be *complete*.
- **Name the sides**: *Producer: BE (orders-service) · Consumer: FE (web checkout), Data (ingest)*. Cross-boundary bugs trace back to a document that never said whose job something was.
- **Tables over prose** for anything with repeating structure — fields, endpoints, states, errors, permissions. Scannable, diffable, and they force you to notice missing values.
- **Show it, then say only what the picture cannot.** The diagram is the section, the prose is its caption. Density, not brevity: cutting a qualifier that changes the meaning makes the document shorter and wrong.
- **Every diagram gets a caption** — 2–4 sentences on what to take away plus what the diagram cannot show (async, retries, ownership). Without one it is decoration.
- **Link, don't duplicate.** A field defined in the ERD is referenced, never restated. Duplicated facts diverge silently.
- **Leave gaps visible**, never filled with a guess that reads like a decision.
- **Write the interface before building behind it**, and change the document in the same pull request as the behaviour.

## Visual restraint

- **Heading depth stops at H3, and depth beyond it is a new file** — never an H4, because the page's contents list collects h2 and h3 only and an H4 is a section nobody can jump to (rule 4).
- **The fixed parts of a repeated block are headings, not bold text.** `**Purpose**` is emphasis; `### Purpose` is a navigable place in the document.
- No emoji, no decorative separators, no ASCII banners. Bold for normative keywords and table labels; italics sparingly.
- Bullets are one line. A bullet needing a sub-bullet and a sentence wants to be a table row.
- Code fences always carry a language tag. A fence containing another fence uses four backticks.
- Any single diagram stays under ~10 nodes; past that, split into two zoom levels rather than shrinking boxes.
- One word per concept throughout a set (*order*, not order/purchase/transaction).

## HTML export

Markdown is always the artifact; HTML is generated from it, never hand-written.

```bash
python3 scripts/build_site.py <docs_folder> -o site.html --title "Project Docs"   # whole set, one file
python3 scripts/serve_docs.py <docs_folder> --title "Project Docs"                # same page at :8777, Edit→Save writes the .md
python3 scripts/export_html.py <input.md> [-o out.html]                           # one document, sidebar hidden
```

The site build reads each document's `#` H1 for its title and the metadata table for the status pill, so a document written to these templates needs no extra front matter. Files are grouped into the phase sidebar by their numeric prefix (`4.1-…` → phase 4); unnumbered ones are placed by folder (`ops/adr/0001-….md` → phase 5). `README.md` or `index.md` at the folder root becomes the landing page, pinned above the phase groups, and relative `.md` links (with or without `#fragment`) are rewritten to in-page links.

- **Offline**: marked.js and mermaid.js are inlined from `assets/vendor/`, images as data URIs. A 20-document set is roughly 4.5 MB.
- **A broken Mermaid fence renders as an error box** naming the parse failure — look for one after building. While you are typing in the editor it is softer: the diagram holds its last good drawing, dimmed, and the error box arrives about a second after you stop typing and it is still broken. A published page is always loud immediately.
- Diagrams and wide tables get a wider track than the body text; nothing scrolls the page horizontally.
- Same renderer for all three scripts, deliberately: two templates drifting apart is how a diagram ends up correct in the site and broken in the export.

`serve_docs.py` is the writing **and correcting** loop: Markdown on the left, the rendered page on the right, **one scroll position across both**, live preview as you type, `Ctrl/Cmd+S` writing the real `.md`. Three affordances exist for correcting a draft rather than writing one, and the method that uses them is [0.9](references/0.9-correcting-drafts.md): **click any block in the rendered page** — paragraph, table row, heading, diagram — and the editor jumps to that block in the Markdown and selects it (the caret highlights the block in reverse); **✎ on a diagram** opens a Mermaid pane with the source on one side and the picture redrawn as you type on the other, plus insert buttons for the house node, decision, labelled edge, lane and init block; and **every block that differs from the baseline carries a bar** — git HEAD when the file is committed, its content at start-up when it is not — with a counter and a clickable list, so *"which words here are still the assistant's"* is answerable after an hour of corrections. Editing a static `site.html` through `npx serve` or `file://` has no path back to the `.md` and is the one way to lose a session's work. It also watches the folder, so a file changed by your editor — or by the assistant — arrives in the open page without a refresh; a document with unsaved edits in the browser is never overwritten, it says so instead. Edit there rather than in a file and rebuilding: the preview renders tables and Mermaid exactly as the exported site will.

**Diagrams in the preview only re-parse when their own fence changes**, one render at a time, and a fence you are mid-way through typing keeps its last good drawing rather than flashing an error box between keystrokes. Editing a paragraph therefore leaves every diagram on the page untouched, and editing a diagram costs exactly one re-render.
