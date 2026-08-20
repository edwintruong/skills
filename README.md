# Software Docs

A Claude Code skill for writing software documentation that works as a **contract** between BE, FE, AI and data engineers, while the top of each page stays readable for a PM or a client. It covers the whole lifecycle — problem survey, business rules, use cases, analysis model, design (C4, database, classes, screens), API contracts, codebase and operations, testing, UAT, user guides — and it works in both directions: documenting a codebase that already exists, or designing a system that does not exist yet.

Markdown is the source of truth. HTML is a render target, and the exported page can write edits back into the `.md`, so the source never forks.

## Contents

- [Install](#install)
- [Using it](#using-it)
- [First run: the five questions](#first-run-the-five-questions)
- [The two modes](#the-two-modes)
- [What gets written, and in what order](#what-gets-written-and-in-what-order)
- [Naming and folder layout](#naming-and-folder-layout)
- [Diagrams](#diagrams)
- [HTML export](#html-export)
- [Repository layout](#repository-layout)
- [Extending it](#extending-it)
- [Troubleshooting](#troubleshooting)

## Install

Two routes, two philosophies. A **plugin** — Claude Code or Codex — subscribes you to a managed,
read-only bundle that updates when this repo does. **skills.sh** copies editable files into your
project, which you then own and can hack on. Pick one: installing both leaves the agent reading
the same router twice.

<details open>
<summary><strong>Claude Code — plugin</strong></summary>

```bash
claude plugin marketplace add edwintruong/skills
claude plugin install software-docs@edwintruong
```

Or from inside a session, `/plugin marketplace add edwintruong/skills` then
`/plugin install software-docs@edwintruong`. Update with `claude plugin marketplace update edwintruong`.

</details>

<details>
<summary><strong>Codex — plugin</strong></summary>

Codex reads the same `.claude-plugin/marketplace.json` to find the plugin, then
`.codex-plugin/plugin.json` to install it:

```bash
codex plugin marketplace add edwintruong/skills
codex plugin add software-docs@edwintruong
```

The tree lands under `~/.codex/plugins/cache/edwintruong/software-docs/<version>/`, references and
scripts included. Refresh with `codex plugin marketplace upgrade`.

</details>

<details>
<summary><strong>Cursor, Copilot, Amp and 70+ others — skills.sh</strong></summary>

```bash
npx skills@latest add edwintruong/skills
```

Pick the agents to install onto; the CLI writes editable copies into whatever folder each one reads
(`.claude/skills/`, `.agents/skills/` for Codex, `.cursor/skills/`, …), `-g` for the user-level
equivalent. Nothing updates behind your back — pull later changes with
`npx skills update software-docs`.

</details>

<details>
<summary><strong>Manual, any harness</strong></summary>

Clone straight into the skills folder the harness reads from:

```bash
git clone https://github.com/edwintruong/skills .claude/skills/software-docs    # one project
git clone https://github.com/edwintruong/skills ~/.claude/skills/software-docs  # every project
git clone https://github.com/edwintruong/skills .agents/skills/software-docs    # Codex, one project
```

</details>

Requirements:

| For | Needs |
|---|---|
| Writing documents | Nothing — Markdown only |
| HTML export / local editing server | Python 3.8+, standard library only (no `pip install`) |
| draw.io diagrams (optional) | draw.io desktop CLI v30+ and [`drawio-skill`](https://github.com/Agents365-ai/drawio-skill) |

marked.js and mermaid.js are vendored under `assets/vendor/`, so an exported page never touches the network.

## Using it

You do not have to name the skill. Ask for the document and it triggers — including when the word "documentation" never appears:

```
Write the system analysis and design documentation for the payments module
Document the AI service for the FE team
Create an API contract for /api/admin/campaigns
Draw a sequence diagram for the checkout flow
Write a test plan for release 2.1
Standardise the docs in docs/ — they were written by four people
```

You can also invoke it explicitly with `/software-docs`, or point it at a target: *"read `ai/app/agent/` and write the SDD"*.

One request that spans several document types (*"document this new feature"*) produces **several linked files**, not one giant one. One file, one purpose.

## First run: the five questions

Before writing the first document, the skill interviews you — one round, every question numbered, each with a recommended answer, so you can reply *"1 yes, 2 Vietnamese, 3 yes, 4 existing, 5 split"* in a line. It never asks for facts it can look up itself; it asks only for decisions.

| # | Question | Default |
|---|---|---|
| 1 | Which folder holds the documents? | `docs/`, or `contract-docs/` when `docs/` is taken |
| 2 | Vietnamese or English? | Vietnamese |
| 3 | Mermaid or draw.io? | Mermaid |
| 4 | Existing codebase, or greenfield design? | Read the repo and propose |
| 5 | One system, or several (admin + user)? | Ask — rarely inferable |

The answers land in `<docs_folder>/.software-docs.json`:

```json
{
  "docs_folder": "docs",
  "language": "vi",
  "diagram_mode": "mermaid",
  "mode": "greenfield",
  "systems": ["admin", "user"],
  "title": "Loan Platform Docs"
}
```

That file is read first in every later session — commit it, and nobody is asked twice. If a request contradicts it, the request wins and the file is updated.

Only these five interrupt you, because each is expensive to reverse: a wrong folder breaks every relative link, a wrong language means rewriting every sentence, a wrong diagram mode means re-authoring every diagram. Everything else has a default and is decided without asking.

**Language** governs prose only. Field names, endpoints, enums, error codes, code fences, RFC 2119 keywords (**MUST** / **SHOULD** / **MAY**) and reference IDs (`BR1`, `FR7`, `UC-2`, `TC-order-4`) stay English whatever the setting — a translated field name is a wrong field name.

## The two modes

The same document means different things depending on which one you are in.

| | **A · Document what exists** | **B · Design what does not exist yet** |
|---|---|---|
| Source of truth | The **code**; the document describes it | The **document**; the code will follow it |
| A gap means | Something is undocumented — go and read it | Something is undecided — `**TBD**` with an owner |
| Doc vs code disagree | The code wins; fix the doc, report the gap | The doc wins; the code is not written yet |
| Writing order | 4 and 5 first, then reconstruct 1–3 | 1 → 7, in order |
| Verification | Re-read the code, check every claim | Get the approvals block signed |

Mode A has one rule that overrides everything else: **do not write a sentence you have not verified against the source.** Reverse-engineered documents are trusted precisely because nobody checks them, so an invented endpoint is worse than a missing section. It also asks you the one question only a human can answer — *which of the things I found are bugs rather than features* — and that is most of what makes mode A worth doing.

Mode B has no source to read, so **the interview is the reading**. It runs as rounds over a design tree: each round asks the entire *frontier* — the decisions whose prerequisites are already settled — as numbered questions with a recommended answer, then writes the answers into the documents before computing the next round. The rounds are not improvised; `0.4` maps each one to the sections it unblocks, from *context* through *one-way doors*, and the interview ends when the frontier is empty rather than when the conversation runs out. Facts are the skill's job and decisions are yours: it never asks what it can look up. Anything it chooses for you is marked `**ASSUMPTION**` with the person who must confirm it, so a later reader can distinguish a decision from a guess.

The loop is what you actually see: **it asks a round, waits, writes those answers into the real `.md` files, tells you which files changed and what it had to assume, then asks the next round.** Nothing is written ahead of the frontier, so a document only ever contains what has been decided — and nothing is asked twice, because the open round and the hanging `Q<n>` live in `.software-docs.json` and survive a `/clear` or a new session weeks later. Starting from nothing but an idea works the same way, with one change at the front: round 1 hands you a one-page restatement of your idea to correct — product in a sentence, user groups, main flows, out of scope, all marked `**ASSUMPTION**` — because correcting a page is far faster than answering an open question. And the screens you already picture in your head are treated as evidence, not decoration: every field you name becomes a row in the data dictionary with your answer as its source, then it asks upward — which entity, who fills it, required or not.

## What gets written, and in what order

References are numbered by lifecycle phase; the numbering **is** the writing order, because each phase supplies the citations the next one needs.

| Phase | Documents | Reference |
|---|---|---|
| **0 · Standards** | House style, writing principles, diagramming, the requirements interview, how components are derived, how a diagram is checked against the real mechanism, how a management use case is broken into operations all the way down to endpoints, the constraints a single use case must satisfy, how a draft is corrected · the overview page that routes the set | `0.1`–`0.9` |
| **1 · Discovery** | Problem survey / BRD — problem and **system boundary** · needs · as-is process · functional requirements · function tree · IPO · constraints · plan; business rules and glossary | `1.1`, `1.2` |
| **2 · Specification** | Four documents plus feature specifications: `2.1` **boundary and actors** with the use case table · `2.2` overview and level-2 decomposition diagrams · `2.3` specification of every use case · `2.4` non-functional requirements · `2.5` feature specification | `2.1`–`2.5` |
| **3 · Analysis** | Four documents: `3.1` identify analysis classes (boundary/control/entity) · `3.2` sequence diagrams for every use case · `3.3` class diagrams for every use case · `3.4` data-flow diagrams · (`3.5` state machines are notation, not a separate document) | `3.1`–`3.5` |
| **4 · Design** | Architecture (decisions before the C4 container view) · database (ERD) · class details · interface design (screen inventory → navigation flow → specification → wireframe) · SDD and API contracts when several teams are involved | `4.1`–`4.5` |
| **5 · Build** | Codebase guide, setup, configuration, deployment · runbook, ADR, release notes | `5.1`, `5.2` |
| **6 · Testing** | Test plan, cases, traceability · UAT, defect reports | `6.1`, `6.2` |
| **7 · Guidance** | User guide | `7.1` |

Phase 5 sits outside the sequence — those documents are maintained continuously alongside the code.

Where an international standard already settles a question, the house style follows it rather than inventing a local convention: **ISO/IEC/IEEE 29148:2018** for what makes a requirement well-formed (singular, verifiable, traceable) and for the four verification methods (Test · Demonstration · Inspection · Analysis); **UML 2.5.1** for the *subject* (the box) and for actors as roles **external to** it, and for use case, sequence and class notation including the direction of `<<include>>` and `<<extend>>`; **ISO/IEC 25010:2023** for the nine quality characteristics the non-functional requirements are organised by; **Cockburn** design scope and the black-box rule, plus goal levels for deciding what is a use case and what is a step inside one; **Larman** for primary / supporting / offstage actors; **Jacobson / RUP use-case analysis** for the `<<boundary>>` · `<<control>>` · `<<entity>>` split and the rules for who may call whom; **DeMarco** and **Gane–Sarson** for the levelled data flow diagram and its balancing rule; the **C4 model** for the architecture levels; **IEEE 1016-2009** and **ISO/IEC/IEEE 42010** for design described as views answering stated concerns; **ISO 9241-110:2020** and **ISO 9241-143:2012** for what a screen and a form must have decided; **WCAG 2.2 Level AA** as the accessibility floor. The `2.1`, `3.1`–`3.4`, `4.1` and `4.5` references say which part comes from which.

The same applies to *how the lists are produced*, which is where a document set is usually wrong without looking wrong. `0.5` carries eleven named techniques rather than an instruction to think carefully: **event partitioning** (McMenamin & Palmer) for the use cases and processes nobody starts by clicking a button; **noun-phrase analysis** (Abbott) with the filters, followed by Larman's **conceptual class category list** for the entities the text never mentions; **CRC cards** (Beck & Cunningham) for deciding whether one controller is really two; the **CRUD matrix** (Information Engineering) as a fourth coverage check that finds the entity nobody creates and the use case that touches no data; **decision tables with a hit policy** (OMG DMN) for business rules, complete at 2ⁿ combinations and directly executable as test cases; **normalisation** (Codd) for turning classes and multiplicity into tables; an ambiguity pass built on ISO/IEC/IEEE 29148's requirement characteristics; and the **operation checklist** (`0.7`) for the half of a management use case that a correct-looking one-line row leaves out.

The documents cite each other rather than repeat each other, and the chain runs one way:

```
User need → Functional requirement → Use case → Feature spec → Design → ERD, class spec, screen spec, API contract → Test cases
  N<n>            FR<n>               UC-<n>     R<n>, AC<n>     I<n>, F<n>      field & endpoint names      TC-<area>-<n>
                  BR<n>  (business rules constrain the whole chain)
```

Inside each document the sections run in the same kind of order, and it is enforced rather than assumed: **a section that decides the shape of another comes first.** Architecture decisions sit above the container diagram they produce, the screen list above the screen-flow diagram, the interface inventory above the sequence diagrams that cite it, and anything derived — a consolidated class diagram, a traceability matrix, the plan — comes last. Reading a table of contents and asking *"does writing this section need something below it?"* is the whole check.

That chain is what makes a change traceable: move a business rule and the citations show which spec, which contract and which test cases need revisiting. The **SDD (`4.3`) is the hub** and the only document holding BE / FE / AI / Data at once — when a request touches more than one of them, start there.

**One boundary, drawn before anything crosses it.** The box being designed is named once, in `1.1.1`, and three later tables are derived from it rather than re-guessed: the actors in `2.1.1`, the external entities in `3.4`, the containers in `4.1.1`. The rule that decides all three is that **anything this project builds, releases or is on call for is inside the box** — so it is a container, never an actor. Writing your own services into the actor table is the most common defect in a document set of this kind, and the reason it survives review is that it looks like knowledge: the rows have real names and real APIs. The check is mechanical and runs both ways — no name may appear in both the actor table and the container table, and an actor table holding both an end user and one of your own services has merged two boundaries into one table.

**A name that says "manage" owes a list.** *"Manage products"* is a valid but empty use case — it does not say how many operations it contains, who performs each, what each receives, or what each returns on failure. The gap remains invisible until `4.4`, where it appears as an API contract with one endpoint instead of six, after the frontend may already have been built against the incomplete contract. Every use case with at least two operations therefore carries an **operation matrix**, swept with a fixed thirteen-operation checklist (list · search · detail · create · update · change state · delete · restore · duplicate · bulk · import/export · approve · history), with every row answered `yes` or `no, because …`. A six-question split test then determines how independently each operation is specified: a difference in *who calls whom* requires a separate sequence diagram, a difference in *what crosses the boundary* requires a separate endpoint, and a different *actor* means it was never one use case. Each operation then follows a seven-stage chain — flow, sequence, method signature with exceptions, table, endpoint, error code, test case — and every stage is checked by counting, not by reading. Reference `0.7` defines the method.

**A well-formed use case is a separate concern from a complete use case set.** Counting catches a missing use case; it cannot catch one written at the wrong level, because that block may still have every section filled. Reference `0.8` therefore checks every block: the coffee-break test and *one actor · one goal · one session* establish the level; verb + object establishes the name, while *manage / process / configure / monitor* are flagged as empty verbs that owe a `0.7` operation matrix; steps use an explicit subject, active voice, one action each, and no embedded `if` or loop — because a branch inside a sentence has no number, and that number later becomes an error code and test case. The two costliest distinctions follow: a **precondition** is checked by the system before the use case, a **business rule** is checked during it, and an **assumption** is checked by nobody; a **postcondition is a state, not an action**, because *"the system saves the order"* repeats the flow while *"an `orders` row exists with `status = pending_payment`"* tells a tester what to observe. Exceptions are swept with a fixed eight-mode list — invalid input · rule violation · permission · already deleted · concurrent conflict · external timeout · expiry · **partial success** — and the last three change the design when discovered late.

**One use case, one subsection, all the way down.** From phase 3 onward everything is written per use case: a class table in `3.1`, a sequence diagram in `3.2`, a class diagram in `3.3`, a screen block in `4.5`, a test case in `6.1`. Each gets its own section — never a representative sample, never a consolidated diagram standing in for the set — and the count is checked against the use case table before publishing.

**One numbered section, one file.** A number in the overall contents becomes part of the filename (`2.3` ⇒ `2.3-use-case-specifications.md`), because the site builds its sidebar from filenames, not headings. A file containing four sections appears as one row beside a chapter that appears as four. Inside a file, H2 carries either the next number (`## 3.2.2`) or an existing item ID (`## UC-01 — Place order`), H3 carries the fixed parts of a repeated block, and H4 does not exist: the page contents list collects H2 and H3 only, so a part written in bold cannot be reached directly. Needing another tier means splitting the file (`2.3.1-…`, `2.3.2-…`), never deepening the headings; a page with more than roughly 40 contents entries has reached that point. Products with several **subsystems** split them once in `2.1`, and every later document reuses the same names in the same order as files, allowing a reviewer to open a use case beside its sequence diagram.

**Every component is derived and carries its evidence.** A remembered list and a derived list look identical on the page — the same table and confidence — while a missing row is invisible in both. No actor, use case, class, process, store, state, table, screen, interface, or test case is therefore written from memory: each comes from the technique named by its section, and each row points to its source — an upstream item (`UC-01 b3`, `FR2`, `1.1.2 N7`), an interview answer named by topic (*round 3 — reservation expiry*), a code location (`app/api/orders.py:41`), or a marked `**ASSUMPTION**`. Question *numbers* remain in `.software-docs.json`, where the writer can verify them; a reader without the transcript cannot distinguish `Q57` from an invented citation. Keep rejected candidates instead of deleting them, because an undocumented rejection returns next month as a new idea, and a derivation that rejected nothing was never run.

**A diagram is a claim about mechanism.** Before an arrow is drawn, five questions have answers: who initiates, does the caller wait, what actually crosses, where it becomes permanent, and what happens when it fails. Unanswerable means unknown, and a picture has nowhere to write *"probably"* — so it gets a `**TBD**` in the caption rather than a plausible arrow. The check afterwards is to read the diagram *back*: every edge becomes one full sentence, and every sentence gets its evidence. A poll drawn as a push, a queue drawn as a direct call, or an event drawn before the commit that makes it visible are the three that survive review, because each of them looks exactly like knowledge of the architecture.

You will rarely ask for the whole set. Ask for one document and you get that one; if the document it should cite does not exist yet, the skill says so in a line rather than inventing the upstream content.

Every document it writes opens the same way — a metadata table (Status · Owner · Last updated · Applies to), then a 2–4 sentence plain-language summary a non-technical reader can finish. Everything technical goes below that.

The set as a whole opens with one page above the phases: `<docs_folder>/README.md`, the **overview page**. Four blocks — what the project is, a map of every document with a *when to read this* column, a reading path per role, and the conventions (statuses, ID prefixes, language). It is what a repository host shows when someone opens the folder and what the exported site opens on, and it is refreshed in the same session that adds or retires a document — a document missing from the map does not exist as far as the reader is concerned.

## Naming and folder layout

One folder holds the whole numbered set. Lowercase, hyphenated, no spaces.

```
docs/
  README.md                  the overview page — project in brief, document map,
                             reading paths; the landing page of the exported site
  .software-docs.json        the six settings, plus the interview state
  1.1-problem-survey.md
  1.2-business-rules.md
  2.1-actors-and-use-cases-admin.md     split by reader → suffix, never a subfolder
  2.1-actors-and-use-cases-user.md
  2.3.1-sales-use-cases.md    split by subsystem → the file number grows a level
  2.3.2-inventory-use-cases.md
  4.1-design.md
  4.4-api-contract-admin.md
  diagrams/
    c4-container.drawio      editable source, committed
    c4-container.svg         export, committed, embedded in Markdown
```

Two products in one repo (an admin console and an end-user app on one backend) are **split by reader and kept whole by truth**: use cases, API contracts, class and screen design, and user guides split; architecture, ERD and the test plan stay single. One document owns the seam between them and is never split.

## Diagrams

Mermaid (default) lives in fenced ` ```mermaid ` blocks inside the Markdown — diffable in review, rendered by the HTML export, nothing to install. draw.io mode authors under `diagrams/`, exports SVG and embeds it. The mode is a per-set decision (question 3), but the productive pattern is to draft in Mermaid, agree it in review, then convert once the shape settles.

Rules worth knowing before you review a diagram:

- Every diagram carries a **caption** of 2–4 sentences saying what to take away and what the picture cannot show. A diagram without one is decoration.
- Sync and async use two different notations, a queue is a box, a poll carries its interval, and an event says whether it is emitted before or after the commit. Six things no notation can carry — delivery guarantee, ordering, commit point, timeout, timezone, and what was deliberately left out — go in the caption instead.
- Keep any single diagram under ~10 nodes. Beyond that it splits into two views at different zoom levels.
- Node **labels** follow the document language; node **identifiers** stay English and terse — a Vietnamese identifier with diacritics is a Mermaid parse error waiting to happen.
- draw.io needs the local CLI (`drawio --version`, v30+). Where it is missing, the skill produces the Mermaid version and says so, rather than linking to an `.svg` it never generated.

## HTML export

Markdown is always the artifact. HTML is generated from it — never hand-written. Three scripts, three needs.

**The whole set as one browsable site** — the default when a stakeholder will not open the repo:

```bash
python3 scripts/build_site.py docs/ -o site.html --title "Loan Platform Docs"
```

Phase-grouped sidebar on the left, the document in the middle, an on-page table of contents on the right. Status pills, owners and dates are read from each document's metadata table; titles from the first `# H1`. Documents with no phase number are placed by the folder they sit in (`ops/adr/0001-….md` → phase 5, `features/2026-08-15-….md` → phase 2).

`README.md` (or `index.md`) at the folder root becomes the **landing page**, reached from an *Overview* link pinned above the phase groups and editable like any other document; without one the front page falls back to a generated grid of phase cards. Relative links between documents — `4.4-api-contract.md`, `ops/runbook-orders.md`, with or without a `#heading` — are rewritten to in-page links, so the routing tables on that page work in the exported file exactly as they do in the repo. A link to a document that is not part of the build is left as written and marked, rather than silently pointing nowhere.

**Serve it locally so edits write back into the `.md`** — the mode to hand someone who will correct text as they read:

```bash
python3 scripts/serve_docs.py docs/ --title "Loan Platform Docs"
```

Opens `http://127.0.0.1:8777`, rebuilt on every load. **Edit → Save writes the real file on disk** (`Ctrl/Cmd+S`). The editor is a split view: Markdown on the left, the rendered page on the right, **one scroll position shared between them**, and the preview re-renders as you type with tables and Mermaid exactly as the exported site shows them. Diagrams re-parse only when their own fence changes, one at a time, and a fence you are halfway through typing keeps its last good drawing dimmed instead of flashing a parse error between keystrokes — the error box arrives about a second after you stop and it is still broken. It also watches the folder, so a `.md` changed by your editor or by an assistant appears in the open page without a refresh — unless that document has unsaved edits in the browser, in which case it says so and leaves your text alone. Only `.md` files inside the served folder can be read or written, and it binds to localhost — it is a writing tool for one person on one machine, not something to expose to a network.

**Correcting a draft is a different job from writing one**, and three things in that page exist only for it — the method that uses them is `0.9`:

- **Click any block in the rendered page and the editor lands on it.** Paragraph, table row, heading, diagram: the Markdown scrolls to that block and selects it, and moving the caret in the source highlights the matching block in the render. The claim you distrust is somewhere in a 500-line file, and finding it is most of the work of fixing it.
- **A diagram opens in its own editor.** `✎` on any Mermaid figure gives source on one side, the picture redrawn as you type on the other, the parse error underneath, and insert buttons for the house node, decision, labelled edge, lane, actor and init block. Applying it replaces only the body between the two fences, on the undo stack. A Mermaid fence is the one part of a document nobody can proofread by reading it.
- **Everything you have changed carries a bar.** The baseline is the version the assistant produced — git HEAD when the file is committed, its content at start-up when it is not — with a counter and a clickable list of changed blocks. Saving does not move the baseline; `git commit` does, which is how one review pass ends and the next begins.

Editing a built `site.html` — through `npx serve`, a static host, or `file://` — has no path back to the `.md`. The page will let you type; nothing you type reaches the file.

**One document, quickly:**

```bash
python3 scripts/export_html.py docs/4.3-detailed-design.md -o design.html
```

The same renderer with the sidebar hidden — deliberately the same template, so a diagram cannot be correct in the site build and broken in the one-off export.

Flags:

| Script | Flags |
|---|---|
| `build_site.py` | `docs_root` · `-o/--output` (default `site.html`) · `--title` · `--phase-names <json>` · `--save-endpoint` |
| `serve_docs.py` | `docs_root` · `--title` · `--port` (8777) · `--host` (127.0.0.1) · `--phase-names` · `--no-open` |
| `export_html.py` | `inputs…` · `-o/--output` (single input) · `--outdir` · `--title` |

What all three give you:

- **Offline and portable.** marked.js and mermaid.js are inlined; images become base64 data URIs. No CDN, no relative paths. The cost is size — a 20-document set is roughly 4.5 MB, nearly all of it mermaid.
- **Diagrams sized to the page.** Small ones scale up, wide ones scale down, both stay legible; diagrams and wide tables get a wider track than the body text.
- **A broken Mermaid fence is visible** as an error box naming the parse failure, not a silent gap. Check for one after building.
- **No horizontal scrollbar.** Wide tables and code blocks scroll inside their own box.

The `file://` build keeps the editor too, degrading in a defined order: the companion server if the page is served, otherwise Chrome/Edge's File System Access API, otherwise a download you copy over the original. The editor bar says which applies. Unsaved edits live in `localStorage`, survive a reload, and show a dot beside the document in the sidebar rather than quietly replacing what is on disk.

## Repository layout

```
software-docs/
  SKILL.md                   the skill itself — router, workflow, rules
  .claude-plugin/            plugin.json + marketplace.json — makes this repo
                             installable with `claude plugin install`, and Codex
                             reads marketplace.json too
  .codex-plugin/             plugin.json — what `codex plugin add` installs
  agents/openai.yaml         Codex skill-picker metadata: display name, short label
  references/                one file per document type: template + failure modes
    0.1-visual-style.md      page skeleton, palette, captions, tables, file naming
    0.2-writing-principles.md  interface vs implementation, completeness, approvals
    0.3-diagramming.md       mode choice, tool per diagram, file conventions, sizing
    0.4-interview.md         mode B: design tree, frontier, rounds, round → section map
    0.5-derivation.md        how each list of components is derived: evidence rule,
                             ten named techniques, section → technique map, mode A recipes
    0.6-mechanism.md         whether the picture is true: five mechanism questions,
                             what each notation asserts, read-back, ten mechanism smells
    0.7-operations.md        what a "manage" use case actually contains: operation matrix,
                             13-operation checklist, split test, the seven-stage chain
    0.9-correcting-drafts.md  the loop for fixing a draft: click-to-source, the
                             diagram pane, marks against the baseline, 7 sweeps by kind
    0.8-use-case-constraints.md  whether one use case is well-formed: goal level and the
                             coffee-break test, empty verbs, step-sentence rules,
                             precondition vs business rule vs assumption, postcondition as
                             state, the 8 failure modes, size thresholds, 18-point check
    1.1 … 7.1                the lifecycle references listed above
  scripts/
    build_site.py            folder of .md → one self-contained site.html
    serve_docs.py            the same page, served: save-to-disk, scroll sync, watch
    export_html.py           one .md → one .html
  assets/
    site-template.html       the single shared template
    phase-names.json         phase labels, vi + en
    vendor/                  marked.min.js, mermaid.min.js
```

`references/` is read on demand, not up front: the skill reads `0.1` and `0.2` once per session and then the one file matching the document being written — each carries the section template and the mistakes specific to that type, which is why a document is never written from the router table alone.

## Extending it

- **Different phase labels** (other than `Discovery` / `Specification` / …): copy `assets/phase-names.json`, edit it, and pass `--phase-names my-phases.json`.
- **Different look**: `assets/site-template.html` is the one template both the site build and the single-file export use. Keep it single — two templates drifting apart is how a diagram ends up correct in one and broken in the other.
- **House rules of your own**: add them to the matching `references/*.md` rather than to `SKILL.md`. `SKILL.md` is loaded on every trigger; references are loaded only when relevant.
- **Cutting a release**: `version` lives in two files — `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` — and both harnesses use it to decide whether an installed user sees an update. Bump them together, in the same commit; a version that moves in one file only means half your users stay on the old skill without any error to tell them.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| It asks the five questions again | `.software-docs.json` is missing or outside the docs folder. Commit it at `<docs_folder>/.software-docs.json` |
| `No documents to include under docs/` | The folder has no `.md` files, or you pointed at the repo root |
| The front page is a grid of phase cards | No `README.md`/`index.md` in the docs folder. Write the overview page (`references/0.1-visual-style.md#the-overview-page`) and rebuild |
| A grey dotted link on the site | It points at a `.md` that is not in this build — a planned document, a typo in the path, or a file outside the docs folder |
| Sidebar full of junk groups | Files with no phase prefix in folders the skill does not recognise — rename to `<phase>.<n>-name.md`, or move under a known folder (`ops/`, `features/`, `api/`, `test/`, `guides/`) |
| A red error box where a diagram should be | Mermaid parse failure — usually a diacritic or a space in a node **identifier**, or an unescaped `(`/`"` in a label |
| A dimmed diagram labelled *"cannot parse yet — still typing"* | Normal while editing that fence: the last good drawing is held for ~1.4s. If it remains, the fence is broken and the error box replaces it |
| A diagram in the preview does not update after an edit | Only the fence you changed re-renders, so check you edited inside the ` ```mermaid ` block. If the file changed outside the browser and the sidebar shows a dot beside it, the page has unsaved edits and is deliberately not pulling from disk — save or discard first |
| Site is ~4 MB | Expected: mermaid.js is inlined so the page works offline |
| Save says "downloaded" instead of writing the file | You are on a `file://` page in a browser without the File System Access API. Use `serve_docs.py` instead |
| draw.io export never appears | The desktop CLI is missing (`drawio --version`, needs v30+). The Mermaid version is the deliverable until it is installed |
| The document contradicts the code | In mode A that is a finding, not a doc bug: the code wins, the document gets fixed, and the gap is reported |
